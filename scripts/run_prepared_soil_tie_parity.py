"""Generate paired prepared WEPP soils from fresh explicit USDA and mirror sources."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3

from run_live_sda_parity import RELEASE
from run_wepppy_parity import canonical

CASES = {
    2250500: ('corestrictions', 'cokey', 'reskind', 27881215),
    344485: ('chfrags', 'chkey', 'fragvol_r', 86576543),
    460290: ('chfrags', 'chkey', 'fragvol_r', 83755309),
}


def model_input(path):
    return b''.join(line for line in path.read_bytes().splitlines(keepends=True)
                    if not line.lstrip().startswith(b'#'))


def hashes(path):
    data = path.read_bytes()
    return {
        'sha256': sha256(data).hexdigest(),
        'canonical_sha256': sha256(canonical(data)).hexdigest(),
        'model_input_sha256': sha256(model_input(path)).hexdigest(),
    }


def build(directory, template, mukey, source):
    from wepppy.nodb.core import Ron, Soils, SoilsMode, Watershed, Wepp
    from wepppy.soils.ssurgo.source import read_artifact_provenance

    directory.mkdir()
    wd = str(directory)
    Ron(wd, '0.cfg')
    shutil.copy2(template / 'watershed.nodb', directory / 'watershed.nodb')
    (directory / 'watershed').mkdir()
    for name in ('hillslopes.parquet', 'channels.parquet'):
        shutil.copy2(template / 'watershed' / name, directory / 'watershed' / name)
    watershed = Watershed.getInstance(wd)
    with watershed.locked():
        watershed._mods = []
    soils = Soils.getInstance(wd)
    soils.mode = SoilsMode.Single
    soils.single_selection = mukey
    soils.configure_soil_data_source(**source)
    cache = Path(soils.ssurgo_cache_db_path)
    if cache.exists():
        raise ValueError(f'Expected fresh cache: {cache}')

    wepp = Wepp.getInstance(wd)
    soils.build()
    soils = Soils.getInstance(wd)
    translator = watershed.translator_factory()
    expected = {f'p{translator.wepp(top=int(topaz_id))}.sol' for topaz_id, _ in soils.sub_iter()}
    if not expected or len(expected) != watershed.sub_n:
        raise ValueError(f'Incomplete single-soil assignment in {directory}')
    prepared = Path(wepp.runs_dir)
    prepared.mkdir(parents=True, exist_ok=True)
    wepp._prep_soils(translator, max_workers=1)
    files = sorted(prepared.glob('p*.sol'))
    if {path.name for path in files} != expected or not all(path.stat().st_size for path in files):
        raise ValueError(f'Unexpected prepared soil files in {directory}')

    base = Path(soils.soils_dir) / soils.soils[str(mukey)].fname
    provenance = read_artifact_provenance(str(base))
    evidence = provenance['source']
    fetches = evidence['fetches']
    if evidence['binding']['identity'] != soils.soil_data_source or len(fetches) != 5:
        raise ValueError(f'Unexpected source provenance for {base}')
    table, key, field, value = CASES[mukey]
    with sqlite3.connect(cache.resolve().as_uri() + '?mode=ro', uri=True) as conn:
        selected, = conn.execute(f'SELECT {field} FROM {table} WHERE {key}=?', (value,)).fetchone()
        cokey = provenance['cokey']
        horizons = [row[0] for row in conn.execute(
            'SELECT chkey FROM chorizon WHERE cokey=? ORDER BY hzdept_r, chkey', (cokey,),
        )]
    if value not in (horizons if table == 'chfrags' else [cokey]):
        raise ValueError(f'Tie key {value} is outside selected component {cokey}')
    return {
        'source': evidence['binding']['identity'],
        'fetches': [{k: f[k] for k in ('table', 'observed_at', 'response_sha256')} for f in fetches],
        'selected_component': cokey,
        'selected_component_horizons': horizons,
        'cache_selection': selected,
        'base': hashes(base),
        'prepared': {path.name: hashes(path) for path in files},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--mirror-base', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    mirror = {'endpoint': args.mirror_base.rstrip('/') + '/Tabular/post.rest',
              'profile': 'wepppy-json-v1', 'release': RELEASE}
    report = {}
    for mukey, (table, key, field, value) in CASES.items():
        pair = {}
        for label, source in (('usda', {}), ('mirror', mirror)):
            directory = args.output / f'{args.output.name}-{mukey}-{label}'
            pair[label] = build(directory, args.template, mukey, source)
            print(mukey, label, pair[label]['cache_selection'], len(pair[label]['prepared']), flush=True)
        usda, mirror_case = pair['usda'], pair['mirror']
        if set(usda['prepared']) != set(mirror_case['prepared']):
            raise ValueError(f'Different prepared hillslope sets for {mukey}')
        different = {}
        for name in ('sha256', 'canonical_sha256', 'model_input_sha256'):
            different[name] = [file for file in usda['prepared']
                               if usda['prepared'][file][name] != mirror_case['prepared'][file][name]]
        report[mukey] = {
            'tie': {'table': table, 'key': key, 'value': value, 'field': field},
            'prepared_differences': different,
            **pair,
        }
        print(mukey, 'prepared differences', {k: len(v) for k, v in different.items()}, flush=True)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
