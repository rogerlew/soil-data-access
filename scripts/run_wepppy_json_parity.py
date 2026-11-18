#!/usr/bin/env python3
"""Compare a fresh real-HTTP build with the frozen offline reference, one release at a time.

Run inside a client container attached only to the Compose internal database
network. Activate the matching test replay release separately before each case.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import sqlite3
import sys

from run_wepppy_parity import ROOT, digest, environment_receipt, run_case


def compare_cache(reference, candidate):
    """Compare positive row multisets and negative-key sets; historical negatives repeat."""
    from collections import Counter
    tables = ('component', 'chorizon', 'corestrictions', 'chfrags', 'chtexturegrp',
              'bad_component_mukey', 'bad_chorizon_cokey', 'bad_corestrictions_cokey',
              'bad_chfrags_chkey', 'bad_chtexturegrp_chkey')
    result = {}
    with sqlite3.connect(reference) as old, sqlite3.connect(candidate) as new:
        for table in tables:
            left = old.execute(f'SELECT * FROM {table}').fetchall()
            right = new.execute(f'SELECT * FROM {table}').fetchall()
            # Request order is immaterial to storage; selection/output comparisons below
            # independently detect any effect of retrieval order on model behavior.
            equal = set(left) == set(right) if table.startswith('bad_') else Counter(left) == Counter(right)
            result[table] = {'reference_rows': len(left), 'candidate_rows': len(right), 'equal': equal}
            if not equal:
                raise ValueError(f'Cache mismatch: {table}')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wepppy-root', type=Path, required=True)
    parser.add_argument('--wepppy-revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--endpoint', required=True)
    args = parser.parse_args()
    case = ROOT / 'fixtures/wepppy' / args.case
    if case not in [p.parent for p in (ROOT / 'fixtures/wepppy').glob('*/cache.manifest.json')]:
        raise ValueError('Unknown fixture')
    with socket.socket() as sock:
        sock.settimeout(0.5)
        try:
            sock.connect(('198.51.100.1', 9))
        except OSError as exc:
            blocked_errno = exc.errno
        else:
            raise RuntimeError('External route is enabled')
    if blocked_errno != 101:
        raise RuntimeError(f'Expected network unreachable, got {blocked_errno}')
    sys.path.insert(0, str(args.wepppy_root))
    import wepppy.soils.ssurgo.ssurgo as ssurgo
    from wepppy.soils.ssurgo.source import read_artifact_provenance
    if not Path(ssurgo.__file__).resolve().is_relative_to(args.wepppy_root.resolve()):
        raise RuntimeError('Wrong WEPPpy imported')
    manifest = json.loads((case / 'cache.manifest.json').read_text())
    release = f"replay-{case.name}-{manifest['snapshot']['sha256'][:12]}"
    identity = {'endpoint': args.endpoint, 'profile': 'wepppy-json-v1', 'release': release}
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'claim': 'bounded_cache_replay_json_artifact_parity_not_release_acceptance',
              'network': {'namespace': os.readlink('/proc/self/ns/net'), 'external_connect_errno': blocked_errno},
              'environment': environment_receipt(args.wepppy_root),
              'candidate_source_sha256': {name: digest((args.wepppy_root / name).read_bytes()) for name in (
                  'wepppy/soils/ssurgo/ssurgo.py', 'wepppy/soils/ssurgo/source.py', 'wepppy/nodb/core/soils.py')},
              'source': identity}
    report['environment']['wepppy_revision'] = args.wepppy_revision
    result = run_case(case, args.output, ssurgo, source_identity=identity)
    report['case'] = result
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    reference = json.loads((ROOT / 'artifacts/wepppy-parity/reference-run-a.json').read_text())
    expected = next(item for item in reference['cases'] if item['case_id'] == args.case)
    if result['status'] == 'incomplete_cache_not_a_reference':
        report['comparison'] = 'excluded_incomplete_cache'
    else:
        for field in ('decisions', 'valid_count', 'invalid_count', 'profile'):
            if result[field] != expected[field]:
                raise ValueError(f'Reference {field} differs')
        actual_artifacts = {item['file']: item['canonical_sha256'] for item in result['artifacts']}
        expected_artifacts = {item['file']: item['canonical_sha256'] for item in expected['artifacts']}
        if actual_artifacts != expected_artifacts:
            raise ValueError('Canonical soil artifacts differ')
        report['cache_comparison'] = compare_cache(case / 'cache.sqlite', args.output / case.name / 'working.sqlite')
        sidecars = []
        for soil in sorted((args.output / case.name / 'base').glob('*.sol')):
            evidence = read_artifact_provenance(str(soil))
            if evidence['source']['binding']['identity'] != identity or not evidence['source']['fetches']:
                raise ValueError('Missing or mismatched base-soil provenance')
            sidecars.append({'file': soil.name + '.provenance.json', 'sha256': digest(Path(str(soil) + '.provenance.json').read_bytes())})
        report['provenance_sidecars'] = sidecars
        report['comparison'] = 'all_decisions_cache_semantics_and_canonical_artifacts_equal'
    report['native_reference_comparison'] = {key: report['environment'][key] == reference['environment'][key]
        for key in ('numpy', 'scipy', 'duckdb', 'numpy_native_sha256', 'duckdb_native_sha256', 'rosetta_files', 'thread_environment')}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'case': args.case, 'comparison': report['comparison'], 'artifacts': len(result.get('artifacts', []))}), flush=True)


if __name__ == '__main__':
    main()
