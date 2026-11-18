#!/usr/bin/env python3
"""Check retained local runtime evidence integrity; never grants release acceptance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    receipt = json.loads((root / 'artifacts/runtime/compose-validation.json').read_text())
    if receipt['claim'] != 'local_api_cache_record_parity_not_wepppy_soil_or_release_acceptance':
        raise ValueError('Wrong evidence scope')
    if receipt['code_revision'] != receipt['metadata']['code_revision']:
        raise ValueError('Metadata code revision differs')
    required = {'Cargo.lock', 'compose.yaml', 'Dockerfile', 'src/main.rs', 'src/planner.rs',
                'scripts/replay_cache.py', 'scripts/verify_runtime.py', 'migrations/001_replay.sql'}
    if set(receipt['source_files']) != required:
        raise ValueError('Missing source binding')
    for name, expected in receipt['source_files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Stale runtime evidence: ' + name)
    cases = receipt['cases']
    expected_cases = {'ssurgo-001', 'ssurgo-002', 'ssurgo-003', 'ssurgo-004', 'statsgo-001'}
    if len(cases) != 5 or {case['case'] for case in cases} != expected_cases:
        raise ValueError('Incomplete runtime corpus')
    families = {f['family'] for f in json.loads((root / 'contracts/runtime-query-catalog.json').read_text())}
    for case in cases:
        cache = root / 'fixtures/wepppy' / case['case'] / 'cache.sqlite'
        if hashlib.sha256(cache.read_bytes()).hexdigest() != case['release']['datasets'][0]['sha256']:
            raise ValueError('Stale fixture binding')
        if len(case['families']) != 5 or {f['family'] for f in case['families']} != families:
            raise ValueError('Missing query family')
        if not case['duplicate_import_rolled_back'] or not all(f['cache_records_equal'] for f in case['families']):
            raise ValueError('Failed record comparison or rollback')
    expected_examples = {c['id'] for c in json.loads((root / 'contracts/wepppy-json-examples.json').read_text())['cases']}
    if len(receipt['authored_rows']) != len(expected_examples) or {c['id'] for c in receipt['authored_rows']} != expected_examples:
        raise ValueError('Missing authored wire case')
    if not all(c['raw_rows_and_exact_wire_values_match'] for c in receipt['authored_rows']):
        raise ValueError('Wire comparison failed')
    controls = receipt['controls']
    if controls != {'unsupported_queries_rejected': 7, 'malformed_or_oversized_requests_rejected': 3,
                    'role_write_denied': True, 'overload_status': 503, 'server_statement_timeouts': 8,
                    'recovery_status': 200, 'remaining_active_serving_queries': 0}:
        raise ValueError('Incomplete or failed containment evidence')
    lifecycle = receipt['lifecycle']
    if not all(lifecycle[k] for k in ('inflight_release_and_rows_stay_consistent', 'next_request_observes_new_release', 'restart_preserves_release')) or not 0 <= lifecycle['disconnect_cleanup_seconds'] <= 6:
        raise ValueError('Lifecycle checks failed')
    if receipt['output_limits'] != {'response_bytes_exceeded_status': 413, 'row_count_exceeded_status': 413, 'recovery_status': 200}:
        raise ValueError('Output limits failed')
    trace = receipt['request_trace']
    path = (root / trace['file']).resolve()
    if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != trace['sha256']:
        raise ValueError('Request trace differs')
    return 'Local runtime evidence verified; WEPPpy soil parity and release acceptance remain unproven.'


if __name__ == '__main__':
    print(verify())
