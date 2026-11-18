#!/usr/bin/env python3
"""Generate test-only, transactional PostgreSQL replay SQL from a frozen cache."""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sqlite3
from run_wepppy_parity import inspect_cache

ROOT = Path(__file__).resolve().parents[1]
TYPES = json.loads((ROOT / 'contracts/replay-column-types.json').read_text())


def literal(value, kind):
    if value is None:
        return 'NULL'
    if kind in ('bigint', 'numeric'):
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError('Non-numeric cached scientific field') from exc
        if not number.is_finite():
            raise ValueError('Non-finite source value')
        if kind == 'bigint' and (number != int(number) or not 0 <= number <= 9223372036854775807):
            raise ValueError('Invalid exact key')
        return format(number, 'f')
    if not isinstance(value, str):
        value = str(value)
    if '\x00' in value:
        raise ValueError('PostgreSQL text cannot represent NUL')
    return "'" + value.replace("'", "''") + "'"


def generate(case_id):
    if case_id not in {p.parent.name for p in (ROOT / 'fixtures/wepppy').glob('*/cache.manifest.json')}:
        raise ValueError('Unknown fixture case')
    case = ROOT / 'fixtures/wepppy' / case_id
    cache = case / 'cache.sqlite'
    manifest = json.loads((case / 'cache.manifest.json').read_text())
    checksum = hashlib.sha256(cache.read_bytes()).hexdigest()
    if checksum != manifest['snapshot']['sha256']:
        raise ValueError('Fixture checksum differs')
    _, gaps, _ = inspect_cache(cache)
    if gaps:
        raise ValueError('Incomplete cache cannot seed a positive reference: ' + json.dumps(gaps))
    release = f'replay-{case_id}-{checksum[:12]}'
    metadata = {'id': release, 'datasets': [{'dataset': 'WEPPPY_CACHE_REPLAY', 'release_id': release,
        'scope': f'Processed project cache {case_id}; test replay only; source vintage unknown',
        'source_url': f'https://github.com/rogerlew/soil-data-access/tree/231c424/fixtures/wepppy/{case_id}',
        'sha256': checksum}]}
    data = {name: [] for name in TYPES}
    aggregates = {}
    conn = sqlite3.connect(cache.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        for table in TYPES:
            if table == 'muaggatt':
                continue
            cursor = conn.execute(f'SELECT rowid, * FROM "{table}" ORDER BY rowid')
            names = [d[0] for d in cursor.description][1:]
            for row in cursor:
                ordinal, values = row[0], dict(zip(names, row[1:]))
                data[table].append([ordinal] + [values[n] for n in TYPES[table]])
                if table == 'component':
                    aggregate = [values[n] for n in TYPES['muaggatt']]
                    key = values['mukey']
                    if key in aggregates and aggregates[key][1:] != aggregate:
                        raise ValueError('Conflicting cached muaggatt attributes for MUKEY ' + str(key))
                    aggregates.setdefault(key, [ordinal] + aggregate)
    finally:
        conn.close()
    data['muaggatt'] = list(aggregates.values())
    sql = ["BEGIN;", "SET LOCAL standard_conforming_strings=on;", "SET LOCAL statement_timeout='30s';",
           'INSERT INTO soil.release(id,manifest) VALUES (' + literal(release, 'text') + ',' + literal(json.dumps(metadata), 'text') + '::jsonb);']
    for table, columns in TYPES.items():
        rows = data[table]
        for start in range(0, len(rows), 200):
            values = []
            for row in rows[start:start + 200]:
                values.append('(' + ','.join([literal(release, 'text'), literal(row[0], 'bigint')] +
                    [literal(value, kind) for value, kind in zip(row[1:], columns.values())]) + ')')
            sql.append(f'INSERT INTO soil.{table}(release_id,ordinal,' + ','.join(columns) + ') VALUES\n' + ',\n'.join(values) + ';')
    sql.append('INSERT INTO soil.active_release(singleton,release_id) VALUES(true,' + literal(release, 'text') + ') ON CONFLICT(singleton) DO UPDATE SET release_id=EXCLUDED.release_id;')
    sql.append('COMMIT;')
    return '\n'.join(sql) + '\n', metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sql, metadata = generate(args.case)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(sql)
    print(json.dumps(metadata))


if __name__ == '__main__':
    main()
