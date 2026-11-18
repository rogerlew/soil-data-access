#!/usr/bin/env python3
"""Exercise an isolated local Compose replay stack; never a production importer."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import sqlite3
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from replay_cache import generate, literal, TYPES, ROOT
from verify_transport_contract import validate_table

CATALOG = json.loads((ROOT / 'contracts/runtime-query-catalog.json').read_text())


def psql(sql, check=True):
    return subprocess.run(['docker', 'compose', 'exec', '-T', 'db', 'psql', '-X', '-qAt', '-U', 'soil_import', '-d', 'soil', '-v', 'ON_ERROR_STOP=1'],
                          input=sql, text=True, capture_output=True, check=check)


def request(base, query=None, body=None):
    if query is not None:
        body = urllib.parse.urlencode({'query': query, 'format': 'JSON+COLUMNNAME'}).encode()
    path = '/v1/metadata' if body is None else '/Tabular/post.rest'
    req = urllib.request.Request(base + path, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        response = urllib.request.urlopen(req, timeout=12)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, dict(response.headers), json.load(response)


def query_for(family, keys):
    return family['template'].replace('1001,1002', ','.join(map(str, keys)))


def check_case(base, case):
    sql, manifest = generate(case)
    psql(sql)
    status, _, metadata = request(base)
    assert status == 200 and metadata['active_release'] == manifest
    cache = ROOT / 'fixtures/wepppy' / case / 'cache.sqlite'
    source = sqlite3.connect(cache.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    candidate = sqlite3.connect(':memory:')
    results = []
    try:
        for family in CATALOG:
            table = family['family']
            key = family['columns'][0]
            expected = source.execute(f'SELECT * FROM {table} ORDER BY {key}, rowid').fetchall()
            keys = sorted({row[0] for row in expected}) or [9223372036854775807]
            candidate.execute(source.execute('SELECT sql FROM sqlite_master WHERE name=?', (table,)).fetchone()[0])
            rows = []
            requests = 0
            for start in range(0, len(keys), 4000):
                status, headers, response = request(base, query_for(family, keys[start:start + 4000]))
                assert status == 200, response
                headers = {k.lower(): v for k, v in headers.items()}
                assert headers['x-soil-profile'] == 'wepppy-json-v1'
                assert headers['x-soil-release'] == manifest['id']
                rows.extend(validate_table(response, family['columns']))
                requests += 1
            # Apply the actual cache table's affinities, independently of the replay type map.
            candidate.executemany(f'INSERT INTO {table} VALUES (' + ','.join('?' for _ in family['columns']) + ')', rows)
            observed = candidate.execute(f'SELECT * FROM {table} ORDER BY {key}, rowid').fetchall()
            assert observed == expected, (case, table, next(((a, b) for a, b in zip(expected, observed) if a != b), 'row count'))
            status, _, response = request(base, query_for(family, [9223372036854775807]))
            assert status == 200 and response == {'Table': [family['columns']]}
            results.append({'family': table, 'rows': len(rows), 'requests': requests + 1, 'cache_records_equal': True,
                            'records_sha256': hashlib.sha256(json.dumps(expected).encode()).hexdigest()})
        # A conflicting import fails without changing active data.
        failure = psql(sql, check=False)
        assert failure.returncode != 0
        assert request(base)[2]['active_release'] == manifest
    finally:
        source.close()
        candidate.close()
    return {'case': case, 'release': manifest, 'families': results, 'duplicate_import_rolled_back': True}


def authored_rows(base):
    source = ROOT / 'contracts/wepppy-json-examples.json'
    examples = json.loads(source.read_text())['cases']
    results = []
    for case in examples:
        family = next(f for f in CATALOG if f['family'] == case['query_family'])
        columns, *rows = case['response']['Table']
        release = 'authored-' + case['id']
        manifest = {'id': release, 'datasets': [{'dataset': 'WEPPPY_CACHE_REPLAY', 'release_id': release,
            'scope': 'Authored raw-row transport test; not source data',
            'source_url': 'https://github.com/rogerlew/soil-data-access',
            'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]}
        sql = ['BEGIN;', 'INSERT INTO soil.release VALUES (' + literal(release, 'text') + ',' + literal(json.dumps(manifest), 'text') + '::jsonb);']
        aggregates = set()
        for ordinal, row in enumerate(rows):
            values = dict(zip(columns, row))
            tables = [family['family']]
            if family['family'] == 'component' and values['mukey'] not in aggregates:
                aggregates.add(values['mukey'])
                tables.append('muaggatt')
            for table in tables:
                sql.append(f'INSERT INTO soil.{table}(release_id,ordinal,' + ','.join(TYPES[table]) + ') VALUES (' +
                    ','.join([literal(release, 'text'), str(ordinal)] + [literal(values[n], t) for n, t in TYPES[table].items()]) + ');')
        sql += ['UPDATE soil.active_release SET release_id=' + literal(release, 'text') + ';', 'COMMIT;']
        psql('\n'.join(sql))
        keys = sorted({int(row[0]) for row in rows}) or [1]
        status, _, body = request(base, query_for(family, keys))
        assert status == 200 and body == case['response'], (case['id'], body)
        results.append({'id': case['id'], 'raw_rows_and_exact_wire_values_match': True})
    return results


def controls(base):
    query = query_for(CATALOG[2], [1])
    rejected = []
    attacks = [query + '; SELECT 1', query.replace('fragvol_r', 'pg_sleep(10)'), query.replace(' IN (1)', ' IN (1) OR 1=1'),
               query.replace('chfrags', 'pg_catalog.pg_authid'), query.replace('SELECT', 'SELECT TOP 1'), query + ' DESC',
               query.replace('IN (1)', "IN ('1;DROP TABLE component')")]
    for attack in attacks:
        status, _, body = request(base, attack)
        assert status == 422 and body['error']['code'] == 'unsupported_query', body
        rejected.append(status)
    for body, expected in [(b'query=SELECT+1&format=xml', 400), (b'query=x&format=JSON+COLUMNNAME', 400), (b'x' * 131073, 413)]:
        status, _, result = request(base, body=body)
        assert status == expected and 'error' in result
    # Privilege failure even if the connection's read-only default is disabled.
    denial = psql('SET ROLE soil_serve; SET default_transaction_read_only=off; DELETE FROM soil.release;', check=False)
    assert denial.returncode != 0 and 'permission denied' in denial.stderr
    # Hold a lock so real requests wait inside PostgreSQL, then saturate all eight slots.
    lock = subprocess.Popen(['docker', 'compose', 'exec', '-T', 'db', 'psql', '-X', '-qAt', '-U', 'soil_import', '-d', 'soil', '-v', 'ON_ERROR_STOP=1'],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lock.stdin.write("BEGIN; LOCK soil.chfrags IN ACCESS EXCLUSIVE MODE; SELECT 'locked'; SELECT pg_sleep(8); COMMIT;\n")
    lock.stdin.close()
    assert lock.stdout.readline().strip() == 'locked'
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        pending = [pool.submit(request, base, query) for _ in range(8)]
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            count = int(psql("SELECT count(*) FROM pg_stat_activity WHERE usename='soil_serve' AND wait_event_type='Lock';").stdout.strip())
            if count == 8:
                break
            time.sleep(0.05)
        assert count == 8, count
        assert request(base, query)[0] == 503
        timed_out = [future.result()[0] for future in pending]
        assert timed_out == [504] * 8, timed_out
    assert lock.wait(timeout=12) == 0
    assert request(base, query)[0] == 200
    remaining = int(psql("SELECT count(*) FROM pg_stat_activity WHERE usename='soil_serve' AND state='active';").stdout.strip())
    assert remaining == 0, remaining
    return {'unsupported_queries_rejected': len(rejected), 'malformed_or_oversized_requests_rejected': 3,
            'role_write_denied': True, 'overload_status': 503, 'server_statement_timeouts': 8,
            'recovery_status': 200, 'remaining_active_serving_queries': remaining}


def output_limits(base):
    release = request(base)[2]['active_release']['id']
    # Dedicated authored rows are removed transactionally after checking each bound.
    psql("INSERT INTO soil.chtexturegrp VALUES (" + literal(release, 'text') + ",0,1,repeat('x',16777216));")
    try:
        assert request(base, query_for(CATALOG[3], [1]))[0] == 413
    finally:
        psql("DELETE FROM soil.chtexturegrp WHERE release_id=" + literal(release, 'text') + " AND chkey=1;")
    psql("INSERT INTO soil.chfrags SELECT " + literal(release, 'text') + ",i,1,1 FROM generate_series(1,100001) AS i;")
    try:
        assert request(base, query_for(CATALOG[2], [1]))[0] == 413
    finally:
        psql("DELETE FROM soil.chfrags WHERE release_id=" + literal(release, 'text') + " AND chkey=1;")
    assert request(base, query_for(CATALOG[2], [1]))[0] == 200
    return {'response_bytes_exceeded_status': 413, 'row_count_exceeded_status': 413, 'recovery_status': 200}


def wait_locked(count=1):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        observed = int(psql("SELECT count(*) FROM pg_stat_activity WHERE usename='soil_serve' AND wait_event_type='Lock';").stdout.strip())
        if observed == count:
            return
        time.sleep(0.05)
    raise AssertionError('Request did not reach database lock')


def hold_lock(seconds):
    process = subprocess.Popen(['docker', 'compose', 'exec', '-T', 'db', 'psql', '-X', '-qAt', '-U', 'soil_import', '-d', 'soil', '-v', 'ON_ERROR_STOP=1'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.stdin.write(f"BEGIN; LOCK soil.chfrags IN ACCESS EXCLUSIVE MODE; SELECT 'locked'; SELECT pg_sleep({seconds}); COMMIT;\n")
    process.stdin.close()
    assert process.stdout.readline().strip() == 'locked'
    return process


def lifecycle(base):
    family = CATALOG[2]
    psql("UPDATE soil.active_release SET release_id='authored-fragments-decimal';")
    old_release = request(base)[2]['active_release']['id']
    lock = hold_lock(2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(request, base, query_for(family, [1003]))
        wait_locked()
        psql("UPDATE soil.active_release SET release_id=(SELECT id FROM soil.release WHERE id LIKE 'replay-statsgo-001-%');")
        status, headers, body = future.result()
        assert status == 200 and body['Table'][1:] == [['1003', '12.50']]
        assert {k.lower(): v for k, v in headers.items()}['x-soil-release'] == old_release
    assert lock.wait(timeout=5) == 0
    assert request(base, query_for(family, [1003]))[2]['Table'] == [family['columns']]
    lock = hold_lock(7)
    parsed = urllib.parse.urlparse(base)
    payload = urllib.parse.urlencode({'query': query_for(family, [1]), 'format': 'JSON+COLUMNNAME'}).encode()
    sock = socket.create_connection((parsed.hostname, parsed.port), timeout=3)
    sock.sendall((f'POST /Tabular/post.rest HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(payload)}\r\n\r\n').encode() + payload)
    wait_locked()
    started = time.monotonic()
    sock.close()
    deadline = started + 6
    while time.monotonic() < deadline:
        active = int(psql("SELECT count(*) FROM pg_stat_activity WHERE usename='soil_serve' AND state='active';").stdout.strip())
        if active == 0:
            break
        time.sleep(0.1)
    assert active == 0
    cleanup_seconds = time.monotonic() - started
    assert lock.wait(timeout=10) == 0
    before = request(base)[2]
    subprocess.run(['docker', 'compose', 'restart', 'api'], check=True, capture_output=True)
    deadline = time.monotonic() + 10
    while True:
        try:
            after = request(base)[2]
            break
        except urllib.error.URLError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.1)
    assert before == after
    return {'inflight_release_and_rows_stay_consistent': True, 'next_request_observes_new_release': True,
            'disconnect_cleanup_seconds': cleanup_seconds, 'restart_preserves_release': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:18080')
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    if urllib.parse.urlparse(args.base_url).hostname not in ('127.0.0.1', 'localhost'):
        raise ValueError('This mutating replay harness is local-only')
    if psql('SELECT count(*) FROM soil.release;').stdout.strip() != '0':
        raise ValueError('Use a new isolated Compose project/database; releases already exist')
    assert request(args.base_url)[2]['ready'] is False
    assert request(args.base_url, CATALOG[0]['template'])[0] == 503
    report = {'claim': 'local_api_cache_record_parity_not_wepppy_soil_or_release_acceptance', 'cases': []}
    for case in ('ssurgo-001', 'ssurgo-002', 'ssurgo-003', 'ssurgo-004', 'statsgo-001'):
        report['cases'].append(check_case(args.base_url, case))
    report['authored_rows'] = authored_rows(args.base_url)
    report['controls'] = controls(args.base_url)
    report['lifecycle'] = lifecycle(args.base_url)
    report['output_limits'] = output_limits(args.base_url)
    report['database_version'] = psql('SELECT version(); SELECT postgis_full_version();').stdout.strip()
    report['metadata'] = request(args.base_url)[2]
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'cases': len(report['cases']), 'controls': report['controls']}, indent=2))


if __name__ == '__main__':
    main()
