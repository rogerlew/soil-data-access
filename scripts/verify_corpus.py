#!/usr/bin/env python3
"""Verify committed cache fixtures, not WEPPpy parity or release readiness."""
import hashlib
import json
from pathlib import Path
import sqlite3
from publish_cache_fixture import logical_hash, logical_rows

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    manifests = sorted((root/'fixtures/wepppy').glob('*/cache.manifest.json'))
    if not manifests:
        raise ValueError('No corpus manifests')
    databases = set((root/'fixtures/wepppy').glob('*/cache.sqlite'))
    if databases != {p.parent/'cache.sqlite' for p in manifests}:
        raise ValueError('Every fixture must have exactly one adjacent manifest')
    results = []
    for path in manifests:
        manifest = json.loads(path.read_text())
        if manifest['case_id'] != path.parent.name:
            raise ValueError('Case ID mismatch')
        db = path.parent/'cache.sqlite'
        payload = db.read_bytes()
        if payload.startswith(b'version https://git-lfs'):
            raise ValueError('LFS objects missing; run git lfs pull')
        if len(payload) != manifest['snapshot']['bytes'] or hashlib.sha256(payload).hexdigest() != manifest['snapshot']['sha256']:
            raise ValueError('Fixture checksum mismatch')
        if hashlib.sha256((root/'contracts/wepppy-cache-schema.json').read_bytes()).hexdigest() != manifest['schema_contract_sha256']:
            raise ValueError('Schema contract changed since fixture publication')
        # This is a hashed, frozen local fixture, never a live production database.
        conn = sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        try:
            if conn.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                raise ValueError('Fixture integrity failure')
            names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if names != set(manifest['tables']):
                raise ValueError('Table set mismatch')
            for table, spec in manifest['tables'].items():
                rows = logical_rows(conn, table)
                if len(rows) != spec['rows'] or logical_hash(rows) != spec['logical_sha256']:
                    raise ValueError('Logical records differ from manifest')
                if [list(c)[1:6] for c in conn.execute(f'PRAGMA table_info("{table}")')] != spec['columns']:
                    raise ValueError('Column contract mismatch')
            if [r[0] for r in conn.execute('SELECT DISTINCT mukey FROM component ORDER BY mukey')] != manifest['mukeys']:
                raise ValueError('Selected key inventory mismatch')
            artifact_manifest = path.parent/'artifacts.manifest.json'
            actual_artifacts = set(path.parent.glob('artifacts/*.sol'))
            declared_artifacts = set()
            if artifact_manifest.exists():
                for artifact in json.loads(artifact_manifest.read_text())['artifacts']:
                    artifact_path = path.parent/artifact['file']
                    if not artifact_path.resolve().is_relative_to(path.parent.resolve()):
                        raise ValueError('Artifact escapes case directory')
                    declared_artifacts.add(artifact_path)
                    data = artifact_path.read_bytes()
                    if len(data) != artifact['bytes'] or hashlib.sha256(data).hexdigest() != artifact['sha256']:
                        raise ValueError('Soil artifact checksum mismatch')
                    soil_payload = b''.join(line for line in data.splitlines(keepends=True) if not line.lstrip().startswith(b'#'))
                    if hashlib.sha256(soil_payload).hexdigest() != artifact['noncomment_payload_sha256']:
                        raise ValueError('Model payload mismatch')
                    if not conn.execute('SELECT 1 FROM component WHERE mukey=? AND cokey=?', (artifact['mukey'], artifact['cokey'])).fetchone():
                        raise ValueError('Historical soil component absent from paired cache')
            if actual_artifacts != declared_artifacts:
                raise ValueError('Every soil artifact must be declared')

        finally:
            conn.close()
        results.append({'case_id':manifest['case_id'],'bytes':len(payload),'status':'verified_snapshot_not_parity'})
    return results


if __name__ == '__main__':
    print(json.dumps(verify(),indent=2))
