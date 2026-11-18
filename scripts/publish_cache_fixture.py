#!/usr/bin/env python3
"""Reconstruct an acquired cache into a reviewed, free-page-clean public fixture."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'contracts/wepppy-cache-schema.json'
PRIVATE_MARKERS = ('/geodata/', '/wc1/', '/workdir/', '/home/', '@', '-----BEGIN ')


def logical_rows(conn, table):
    return conn.execute(f'SELECT rowid, * FROM "{table}" ORDER BY rowid').fetchall()


def logical_hash(rows):
    # float.hex preserves binary64 exactly, including signed zero; tag every type.
    def cell(v):
        if isinstance(v, bytes): return ['blob', v.hex()]
        if isinstance(v, float): return ['float', v.hex()]
        return [type(v).__name__, v]
    payload = [[cell(v) for v in row] for row in rows]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()


def publish(acquisition, output, case_id):
    if not re.fullmatch(r'(ssurgo|statsgo)-[0-9]{3}', case_id):
        raise ValueError('Invalid anonymous case ID')
    if acquisition['dataset'] != case_id.split('-')[0] or not acquisition['source_unchanged']:
        raise ValueError('Dataset mismatch or unstable acquisition')
    schema = json.loads(SCHEMA.read_text())
    data = base64.b64decode(acquisition['backup_base64'], validate=True)
    if hashlib.sha256(data).hexdigest() != acquisition['backup_sha256']:
        raise ValueError('Backup checksum mismatch')
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # A disk-backed private scratch allows SQLite to open a serialized WAL-mode DB.
    with tempfile.TemporaryDirectory() as scratch:
        raw = Path(scratch) / 'acquired.sqlite'; raw.write_bytes(data)
        src = sqlite3.connect(raw.as_uri() + '?mode=ro', uri=True)
        dst_path = Path(scratch) / 'public.sqlite'
        dst = sqlite3.connect(dst_path)
        try:
            src.execute('PRAGMA query_only=ON')
            if src.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise ValueError('Acquired backup failed integrity check')
            actual = src.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL").fetchall()
            normalize = lambda s: ''.join(s.split()).lower()
            table_specs = dict(schema['tables'])
            objects = {(t, n): sql for t, n, sql in actual}
            for name, variant in schema.get('negative_table_variants', {}).items():
                if normalize(objects.get(('table', name), '')) == normalize(variant['sql']):
                    table_specs[name] = variant
            expected = {('table', k): v['sql'] for k, v in table_specs.items()}
            expected.update({('index', k): v for k, v in schema['indexes'].items()})
            if {k: normalize(v) for k,v in objects.items()} != {k: normalize(v) for k,v in expected.items()}:
                raise ValueError('Unexpected cache schema; review before publication')
            tables = {}
            for table, spec in table_specs.items():
                columns = [list(c)[1:6] for c in src.execute(f'PRAGMA table_info("{table}")')]
                if columns != spec['columns']:
                    raise ValueError('Column contract mismatch')
                rows = logical_rows(src, table)
                for row in rows:
                    for value in row:
                        if isinstance(value, bytes) or (isinstance(value, str) and any(x in value for x in PRIVATE_MARKERS)):
                            raise ValueError('Unexpected blob or potentially private text; review required')
                dst.execute(spec['sql'])
                placeholders = ','.join('?' for _ in range(len(columns)+1))
                dst.executemany(f'INSERT INTO "{table}"(rowid,' + ','.join('"'+c[0]+'"' for c in columns) + f') VALUES ({placeholders})', rows)
                if logical_hash(logical_rows(dst, table)) != logical_hash(rows):
                    raise ValueError('Logical content changed during reconstruction')
                tables[table] = {'rows': len(rows), 'logical_sha256': logical_hash(rows), 'columns': columns}
            for sql in schema['indexes'].values(): dst.execute(sql)
            dst.commit()
            if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise ValueError('Public fixture integrity failure')
            if dst.execute('PRAGMA freelist_count').fetchone()[0] != 0:
                raise ValueError('Public fixture has unexpected free pages')
            mukeys = [r[0] for r in dst.execute('SELECT DISTINCT mukey FROM component ORDER BY mukey')]
        finally:
            src.close(); dst.close()
        published = dst_path.read_bytes()
        # Exclusive creation prevents silently replacing previously frozen fixtures.
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.fixture-', suffix='.tmp') as stream:
            stream.write(published)
            stream.flush()
            os.fsync(stream.fileno())
            os.link(stream.name, output)
    sidecar = acquisition.get('metadata_text') or ''
    generated = re.search(r'\| Generated at \(UTC\) \| ([^|]+) \|', sidecar)
    return {'case_id': case_id, 'cache_label': acquisition['dataset'],
            'source_kind': acquisition.get('source_kind', 'project_cache'), 'status': 'snapshot_only_reference_not_rebuilt',
            'observed_at': acquisition['observed_at'], 'source_release': None,
            'historical_wepppy_revision': None, 'historical_configuration': None,
            'sidecar_generated_at': generated.group(1).strip() if generated else None,
            'source_fingerprints': acquisition['source_fingerprints'], 'source_unchanged': True,
            'acquired_backup_sha256': acquisition['backup_sha256'],
            'snapshot': {'file': output.name, 'bytes': len(published), 'sha256': hashlib.sha256(published).hexdigest()},
            'reconstruction': 'Fresh SQLite schema, all records and rowids retained; logical hashes verified; no free pages',
            'schema_contract_sha256': hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),
            'integrity_check': 'ok', 'mukeys': mukeys, 'tables': tables,
            'coverage_complete': False, 'sqlite_acquisition_version': acquisition['sqlite_version'],
            'sqlite_publication_version': sqlite3.sqlite_version}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('acquisition', type=Path); p.add_argument('output', type=Path); p.add_argument('--case-id', required=True)
    args = p.parse_args()
    manifest = publish(json.loads(args.acquisition.read_text()), args.output, args.case_id)
    args.output.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__': main()
