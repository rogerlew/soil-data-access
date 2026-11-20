"""Compare fresh WEPPpy cache and base-soil builds with USDA and the national mirror."""

import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import sys
import time

from run_wepppy_parity import canonical, digest

RELEASE = 'forest-us-ssurgo-20261001-statsgo2-20161013-v1'
SAMPLES = {
    'SSURGO': (49315, 465534, 784526, 1415043, 1703249, 2250500, 2566696, 2850878),
    'STATSGO2': (677200, 677316, 1390211, 2790091),
}
TABLES = {
    'component': 'mukey',
    'chorizon': 'cokey',
    'chfrags': 'chkey',
    'chtexturegrp': 'chkey',
    'corestrictions': 'cokey',
}


def compare_rows(reference, candidate):
    """Keep multiplicity for positive rows and absence semantics for negative keys."""
    return {
        table: {
            'legacy_only': sorted((rows - candidate[table]).elements(), key=repr),
            'candidate_only': sorted((candidate[table] - rows).elements(), key=repr),
        }
        for table, rows in reference.items()
    }


def build(directory, dataset, profile, source_args):
    from wepppy.soils.ssurgo.source import ACQUISITION_DEADLINE, cache_evidence, read_artifact_provenance
    from wepppy.soils.ssurgo.ssurgo import SurgoSoilCollection

    directory.mkdir(parents=True)
    deadline = time.monotonic() + 30 if profile == 'bounded_xml' else None
    token = ACQUISITION_DEADLINE.set(deadline)
    try:
        collection = SurgoSoilCollection(
            SAMPLES[dataset], use_statsgo=dataset == 'STATSGO2',
            cache_db_path=str(directory / 'cache.sqlite'), **source_args,
        )
    finally:
        ACQUISITION_DEADLINE.reset(token)
    try:
        collection.makeWeppSoils(max_workers=1)
        collection.writeWeppSoils(wd=str(directory))
        artifacts = {}
        for key in sorted(collection.weppSoils):
            path = directory / f'{key}.sol'
            provenance = read_artifact_provenance(str(path))
            if provenance is None or not provenance['source']['fetches']:
                raise ValueError(f'Missing fetch provenance for {path}')
            artifacts[str(key)] = {
                'cokey': provenance['cokey'],
                'sha256': provenance['soil_sha256'],
                'canonical_sha256': digest(canonical(path.read_bytes())),
            }
        cache_rows = {}
        for table, key in TABLES.items():
            cache_rows[table] = Counter(tuple(row) for row in collection.conn.execute(f'SELECT * FROM {table}'))
            negative = f'bad_{table}_{key}'
            cache_rows[negative] = Counter({tuple(row) for row in collection.conn.execute(f'SELECT * FROM {negative}')})
        return {
            'source': cache_evidence(collection.conn),
            'artifacts': artifacts,
            'invalid': sorted(collection.invalidSoils),
            'cache_row_counts': {table: sum(rows.values()) for table, rows in cache_rows.items()},
        }, cache_rows
    finally:
        collection._disconnect()


def selected_artifacts(result):
    return {key: (artifact['cokey'], artifact['canonical_sha256'])
            for key, artifact in result['artifacts'].items()}


def main():
    import wepppy.all_your_base.all_your_base as base
    from wepppy.soils.ssurgo import ssurgo, source

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mirror-base', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    mirror = {'endpoint': args.mirror_base.rstrip('/') + '/Tabular/post.rest',
              'profile': 'wepppy-json-v1', 'release': RELEASE}
    report = {
        'scope': 'bounded base-soil comparison using fresh WEPPpy acquisitions',
        'python': sys.version.split()[0],
        'machine': platform.machine(),
        'wepppy_module_hashes': {
            module.__name__: digest(Path(module.__file__).read_bytes())
            for module in (base, ssurgo, source)
        },
        'datasets': {},
    }
    for dataset, keys in SAMPLES.items():
        result = {'mukeys': keys, 'builds': {}}
        legacy, legacy_rows = build(args.output / dataset / 'legacy', dataset, 'legacy', {})
        result['builds']['legacy'] = legacy
        for profile, source_args in (('bounded_xml', {}), ('mirror', mirror)):
            candidate, rows = build(args.output / dataset / profile, dataset, profile, source_args)
            candidate['cache_differences'] = compare_rows(legacy_rows, rows)
            expected = selected_artifacts(legacy)
            actual = selected_artifacts(candidate)
            candidate['different_artifact_keys'] = sorted(
                key for key in expected.keys() | actual.keys() if expected.get(key) != actual.get(key)
            )
            candidate['same_invalid_keys'] = legacy['invalid'] == candidate['invalid']
            result['builds'][profile] = candidate
        report['datasets'][dataset] = result
        print(dataset, {name: build['different_artifact_keys']
                        for name, build in result['builds'].items() if name != 'legacy'}, flush=True)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
