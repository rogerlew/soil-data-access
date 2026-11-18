#!/usr/bin/env python3
"""Compare API raw row multisets with independent queries against original downloads."""
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import urllib.parse
import urllib.request

from audit_sources import digest, load_legacy

ROOT = Path(__file__).resolve().parents[1]
TEXT = {'compname', 'hydricrating', 'drainagecl', 'muname', 'flodfreqdcd',
        'hydgrpdcd', 'drclassdcd', 'taxclname', 'geomdesc', 'taxorder', 'taxsuborder',
        'hzname', 'desgnmaster', 'texture', 'reskind'}


def canonical(rows, columns):
    return Counter(tuple(None if value is None else str(value) if column in TEXT
                         else Decimal(str(value)) for column, value in zip(columns, row))
                   for row in rows)


def verify(conn, base, release, count):
    all_keys = [int(row[0]) for row in conn.execute('SELECT DISTINCT mukey FROM component ORDER BY CAST(mukey AS INTEGER)')]
    step = max(1, len(all_keys) // count)
    mukeys = all_keys[::step][:count]
    results = []
    families = json.loads((ROOT / 'contracts/wepppy-queries.json').read_text())['queries']
    components = [int(row[0]) for row in conn.execute('SELECT cokey FROM component WHERE mukey IN (' + ','.join(map(str, mukeys)) + ')')]
    horizons = [int(row[0]) for row in conn.execute('SELECT chkey FROM chorizon WHERE cokey IN (' + ','.join(map(str, components)) + ')')]
    keys = {'_fetch_components': mukeys, '_fetch_chorizon': components,
            '_fetch_chfrags': horizons, '_fetch_chtexturegrp': horizons,
            '_fetch_corestrictions': components}
    for definition in families:
        values = keys[definition['id']]
        total = 0
        for offset in range(0, len(values), 500):
            query = definition['request']['form']['query'].replace('1001,1002', ','.join(map(str, values[offset:offset+500])))
            # SQLite requires qualification of the joined ORDER BY; projection is unchanged.
            cursor = conn.execute(query.replace('ORDER BY mukey', 'ORDER BY component.mukey'))
            columns = [item[0] for item in cursor.description]
            expected = cursor.fetchall()
            request = urllib.request.Request(base + '/Tabular/post.rest', data=urllib.parse.urlencode(
                {'query': query, 'format': 'JSON+COLUMNNAME'}).encode())
            with urllib.request.urlopen(request, timeout=15) as response:
                assert response.headers['X-Soil-Release'] == release
                payload = json.load(response, parse_float=Decimal)
            observed_columns, *observed = payload['Table']
            assert observed_columns == columns
            assert canonical(expected, columns) == canonical(observed, columns), definition['id']
            total += len(expected)
        results.append({'family': definition['id'], 'rows': total, 'exact_raw_multiset_equal': True})
    return {'mukeys': mukeys, 'families': results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gpkg', type=Path, required=True)
    p.add_argument('--statsgo-zip', type=Path, required=True)
    p.add_argument('--base-url', required=True)
    p.add_argument('--release', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    with sqlite3.connect(args.gpkg.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as conn:
        ssurgo = verify(conn, args.base_url, args.release, 100)
    conn, _ = load_legacy(args.statsgo_zip)
    try:
        statsgo = verify(conn, args.base_url, args.release, 100)
    finally:
        conn.close()
    result = {'claim': 'official_download_raw_projection_parity_not_live_SDA_or_nationwide_parity',
              'release': args.release, 'source_sha256': [digest(args.gpkg), digest(args.statsgo_zip)],
              'SSURGO': ssurgo, 'STATSGO2': statsgo}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'ssurgo_mukeys': len(ssurgo['mukeys']), 'statsgo_mukeys': len(statsgo['mukeys'])}))


if __name__ == '__main__':
    main()
