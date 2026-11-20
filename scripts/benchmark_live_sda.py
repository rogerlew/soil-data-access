"""Bounded serial SDA latency comparison from a WEPPpy worker environment."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import statistics
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from run_live_sda_parity import RELEASE, SAMPLES
from verify_official import canonical

ROOT = Path(__file__).resolve().parents[1]
SDA = 'https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest'
MIRROR = 'http://soil-api:8080/Tabular/post.rest'
FAMILIES = ('components', 'chorizon', 'chfrags', 'chtexturegrp', 'corestrictions')
HTTP_REPEATS = 7
ACQUISITION_REPEATS = 5
EXTERNAL_HTTP_INTERVAL_SECONDS = 1.25
EXTERNAL_ACQUISITION_INTERVAL_SECONDS = 10.0


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def workloads():
    cases = json.loads((ROOT / 'contracts/capture-cases.json').read_text())
    definitions = {c['id']: c['form']['query'] for c in cases}
    selections = [
        (f'{dataset}_fetch_{family}', definitions[f'{dataset}_fetch_{family}'])
        for dataset in ('ssurgo', 'statsgo2') for family in FAMILIES
    ]
    batch = json.loads((ROOT / 'artifacts/national/http-parity.json').read_text())['SSURGO']['mukeys']
    forms = json.loads((ROOT / 'contracts/wepppy-queries.json').read_text())['queries']
    query = forms[0]['request']['form']['query'].replace('1001,1002', ','.join(map(str, batch)))
    selections.append(('ssurgo_components_100_mukey', query))
    return selections


def measure_http(endpoint, query):
    payload = urlencode({'query': query, 'format': 'JSON+COLUMNNAME'}).encode()
    req = Request(endpoint, data=payload)
    started_at = utc_now()
    start = time.perf_counter()
    with urlopen(req, timeout=15) as response:
        headers_ms = (time.perf_counter() - start) * 1000
        body = response.read(2_097_153)
        total_ms = (time.perf_counter() - start) * 1000
        if response.status != 200 or len(body) > 2_097_152:
            raise ValueError(f'Unexpected response status or size from {endpoint}')
        if endpoint == MIRROR and response.headers.get('X-Soil-Release') != RELEASE:
            raise ValueError('Mirror release changed during measurement')
    table = json.loads(body).get('Table', [])
    header, *rows = table or [[]]
    if any(len(row) != len(header) for row in rows):
        raise ValueError('Unexpected response column count')
    stamp = {'started_at': started_at, 'headers_ms': headers_ms,
             'total_ms': total_ms, 'status': 200, 'rows': len(rows),
             'bytes': len(body), 'body_sha256': sha256(body).hexdigest()}
    return stamp, header, rows


def comparable_rows(left, right):
    left_header, left_rows = left
    right_header, right_rows = right
    if not left_rows and not right_rows:
        return True, True
    if left_header != right_header:
        return False, False
    if canonical(left_rows, left_header) == canonical(right_rows, right_header):
        return True, True
    if 'geomdesc' not in left_header:
        return False, False
    column = left_header.index('geomdesc')

    def null_geomdesc(rows):
        return [row[:column] + [None if row[column] == '' else row[column]] + row[column + 1:]
                for row in rows]

    return False, (
        canonical(null_geomdesc(left_rows), left_header)
        == canonical(null_geomdesc(right_rows), right_header)
    )


def stats(values):
    return {'samples': len(values), 'median_ms': statistics.median(values),
            'min_ms': min(values), 'max_ms': max(values)}


def measure_acquisition(endpoint, cache_path):
    from wepppy.soils.ssurgo.source import ACQUISITION_DEADLINE, cache_evidence
    from wepppy.soils.ssurgo.ssurgo import SurgoSoilCollection

    args = {'endpoint': endpoint, 'profile': 'wepppy-json-v1', 'release': RELEASE} if endpoint == MIRROR else {}
    started_at = utc_now()
    start = time.perf_counter()
    token = ACQUISITION_DEADLINE.set(time.monotonic() + 30)
    try:
        collection = SurgoSoilCollection(
            SAMPLES['SSURGO'], cache_db_path=str(cache_path), **args,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
    finally:
        ACQUISITION_DEADLINE.reset(token)
    try:
        evidence = cache_evidence(collection.conn)
        fetches = evidence['fetches']
        tables = ('component', 'chorizon', 'chfrags', 'chtexturegrp', 'corestrictions')
        return {
            'started_at': started_at, 'total_ms': elapsed_ms, 'fetches': len(fetches),
            'response_origins': sorted({record['response_origin'] for record in fetches}),
            'tables': {table: collection.conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                       for table in tables},
        }
    finally:
        collection._disconnect()


def wait_interval(previous, minimum):
    if previous is not None:
        time.sleep(max(0, minimum - (time.monotonic() - previous)))
    return time.monotonic()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output
    target.mkdir(parents=True, exist_ok=False)
    with urlopen(MIRROR.removesuffix('/Tabular/post.rest') + '/v1/metadata', timeout=5) as response:
        metadata = json.load(response)
    if metadata.get('ready') is not True or metadata.get('active_release', {}).get('id') != RELEASE:
        raise ValueError('Unexpected mirror metadata')
    report = {'started_at': utc_now(), 'python': platform.python_version(),
              'architecture': platform.machine(), 'mirror_metadata': metadata,
              'source_endpoints': {'sda': SDA, 'mirror': MIRROR}, 'http': {},
              'cold_acquisition': {}, 'warm_acquisition': {}}
    query_cases = workloads()
    for case, query in query_cases:
        report['http'][case] = {'query': query, 'trials': []}
    receipt = target / 'benchmark.json'

    def save():
        receipt.write_text(json.dumps(report, indent=2) + '\n')

    previous_sda = None
    for repeat in range(HTTP_REPEATS):
        for index, (case, query) in enumerate(query_cases):
            order = (SDA, MIRROR) if (repeat + index) % 2 == 0 else (MIRROR, SDA)
            collected = {}
            for endpoint in order:
                if endpoint == SDA:
                    previous_sda = wait_interval(previous_sda, EXTERNAL_HTTP_INTERVAL_SECONDS)
                collected[endpoint] = measure_http(endpoint, query)
            sda, sda_header, sda_rows = collected[SDA]
            mirror, mirror_header, mirror_rows = collected[MIRROR]
            exact, normalized = comparable_rows((sda_header, sda_rows), (mirror_header, mirror_rows))
            report['http'][case]['trials'].append({
                'sda_first': order[0] == SDA, 'sda': sda, 'mirror': mirror,
                'exact_row_multiset_equal': exact, 'equal_with_empty_geomdesc_as_null': normalized,
            })
        print(f'Completed paired HTTP round {repeat + 1}/{HTTP_REPEATS}', flush=True)
        save()

    for entry in report['http'].values():
        entry['summary'] = {source: stats([trial[source]['total_ms'] for trial in entry['trials']])
                            for source in ('sda', 'mirror')}

    for repeat in range(ACQUISITION_REPEATS):
        order = (SDA, MIRROR) if repeat % 2 == 0 else (MIRROR, SDA)
        for endpoint in order:
            name = 'sda' if endpoint == SDA else 'mirror'
            if endpoint == SDA:
                previous_sda = wait_interval(previous_sda, EXTERNAL_ACQUISITION_INTERVAL_SECONDS)
            cache = target / f'{name}-{repeat}.sqlite'
            cold = measure_acquisition(endpoint, cache)
            warm = measure_acquisition(endpoint, cache)
            if cold['fetches'] != 5 or warm['fetches'] != cold['fetches'] or warm['tables'] != cold['tables']:
                raise ValueError(f'Unexpected cold/warm cache evidence for {endpoint}')
            report['cold_acquisition'].setdefault(name, []).append(cold)
            report['warm_acquisition'].setdefault(name, []).append(warm)
        print(f'Completed paired acquisition round {repeat + 1}/{ACQUISITION_REPEATS}', flush=True)
        save()
    for condition in ('cold_acquisition', 'warm_acquisition'):
        report[condition + '_summary'] = {
            source: stats([trial['total_ms'] for trial in trials])
            for source, trials in report[condition].items()
        }
    report['finished_at'] = utc_now()
    save()


if __name__ == '__main__':
    main()
