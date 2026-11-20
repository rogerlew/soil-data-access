"""Pair fresh gridded soil builds and prescribed-fire multi-OFE preparation."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

from run_live_sda_parity import RELEASE
from run_prepared_soil_tie_parity import hashes


def stage_inputs(template, wd):
    """Copy the spatial inputs and untreated landuse from a local qualification run."""
    untreated = template / '_pups/omni/scenarios/undisturbed'
    files = {name + '.nodb': template / (name + '.nodb')
             for name in ('ron', 'watershed', 'wepp', 'climate', 'disturbed')}
    files['landuse.nodb'] = untreated / 'landuse.nodb'
    for name in ('dem/wbt/subwta.tif', 'soils/ssurgo.tif', 'watershed/mofe.tif',
                 'watershed/hillslopes.parquet', 'watershed/channels.parquet',
                 'disturbed/disturbed_land_soil_lookup.csv', 'landuse/nlcd.tif'):
        files[name] = template / name
    for base, glob in ((template, 'watershed/slope_files/hillslopes/hill_*.mofe.slp'),
                       (untreated, 'landuse/hill_*.mofe.man')):
        for path in base.glob(glob):
            files[str(path.relative_to(base))] = path
    wd.mkdir()
    receipt = {}
    for relative, source in sorted(files.items()):
        target = wd / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        receipt[relative] = sha256(data).hexdigest()
        if target.suffix == '.nodb':
            document = json.loads(data)
            state = document.get('py/state', document)
            state['wd'] = str(wd)
            if '_parent_wd' in state:
                state['_parent_wd'] = None
            target.write_text(json.dumps(document))
        else:
            shutil.copy2(source, target)
    treatment = template / '_pups/omni/scenarios/prescribed_fire/treatments.nodb'
    data = treatment.read_bytes()
    receipt['prescribed_fire/treatments.nodb'] = sha256(data).hexdigest()
    document = json.loads(data)
    mapping = document.get('py/state', document)['_treatments_domlc_d']
    if not mapping or set(mapping.values()) != {'142'}:
        raise ValueError('Expected the saved prescribed-fire assignments')
    return mapping, receipt


def prepare(wepp, watershed, landuse, directory, prep_workers):
    from wepppy.wepp.soils.utils import WeppSoilUtil

    wd = Path(wepp.wd)
    runs = Path(wepp.runs_dir)
    runs.mkdir(parents=True, exist_ok=True)
    translator = watershed.translator_factory()
    wepp._prep_multi_ofe(translator, max_workers=prep_workers)
    directory.mkdir()
    stacks = {}
    for topaz in landuse.domlc_mofe_d:
        topaz = str(topaz)
        wepp_id = translator.wepp(top=int(topaz))
        path = runs / f'p{wepp_id}.sol'
        staged = wd / 'soils' / f'hill_{topaz}.mofe.sol'
        util = WeppSoilUtil(str(path))
        segments = landuse.domlc_mofe_d[topaz]
        if len(util.obj['ofes']) != len(segments):
            raise ValueError(f'Prepared OFE count disagrees with assignment for {topaz}')
        for suffix in ('sol', 'man', 'slp'):
            source = path.with_suffix('.' + suffix)
            shutil.copy2(source, directory / source.name)
        stacks[topaz] = {
            'file': path.name,
            'segment_classes': {key: landuse.managements[value].disturbed_class
                                for key, value in segments.items()},
            'staged_soil': hashes(staged),
            'prepared_soil': hashes(path),
            'prepared_management_sha256': sha256(path.with_suffix('.man').read_bytes()).hexdigest(),
        }
    if len(stacks) != watershed.sub_n:
        raise ValueError('Prepared hillslope set does not match the watershed')
    return stacks


def build(template, wd, source, prep_workers):
    from wepppy.nodb.core import Ron, Soils, Wepp

    treatment, inputs = stage_inputs(template, wd)
    path = str(wd)
    config = Ron.getInstance(path).config_stem
    soils = Soils(path, config + '.cfg')
    soils.configure_soil_data_source(**source)
    if Path(soils.ssurgo_cache_db_path).exists():
        raise ValueError('Expected a fresh SSURGO cache')
    wepp = Wepp.getInstance(path)
    if not wepp.multi_ofe:
        raise ValueError('Expected a multi-OFE run')
    soils.build(max_workers=1, retrieve_gridded_ssurgo=False)
    return prepare_treatment_pair(wd, treatment, inputs, prep_workers)


def prepare_treatment_pair(wd, treatment, inputs, prep_workers):
    from wepppy.nodb.core import Landuse, Ron, Soils, Watershed, Wepp
    from wepppy.nodb.mods.treatments import Treatments
    from wepppy.soils.ssurgo.source import read_artifact_provenance

    path = str(wd)
    config = Ron.getInstance(path).config_stem
    wepp = Wepp.getInstance(path)
    watershed = Watershed.getInstance(path)
    soils = Soils.getInstance(path)
    base_assignments = dict(soils.ssurgo_domsoil_d)
    if any(not str(key).isdigit() for key in base_assignments.values()):
        raise ValueError('Expected SSURGO map unit assignments')
    base = {}
    for key in sorted(set(base_assignments.values())):
        soil = wd / 'soils' / f'{key}.sol'
        provenance = read_artifact_provenance(str(soil))
        binding = provenance['source']['binding']
        fetches = provenance['source']['fetches']
        if binding['identity'] != soils.soil_data_source or not fetches:
            raise ValueError(f'Missing expected fresh-source provenance for {key}')
        base[key] = {'component': provenance['cokey'], 'soil': hashes(soil)}
    before = prepare(wepp, watershed, Landuse.getInstance(path), wd / 'before-treatment', prep_workers)

    controller = Treatments(path, config + '.cfg')
    controller.treatments_domlc_d = treatment
    controller.build_treatments()
    after = prepare(wepp, watershed, Landuse.getInstance(path), wd / 'after-treatment', prep_workers)
    soils = Soils.getInstance(path)
    if base_assignments != soils.ssurgo_domsoil_d:
        raise ValueError('Treatment modified the base soil assignments')
    changed_segments = sum(
        cls != after[topaz]['segment_classes'][segment]
        for topaz, stack in before.items() for segment, cls in stack['segment_classes'].items()
    )
    changed_hillslopes = [topaz for topaz in before
                         if before[topaz]['prepared_soil']['model_input_sha256']
                         != after[topaz]['prepared_soil']['model_input_sha256']]
    if not changed_segments or not changed_hillslopes:
        raise ValueError('Treatment must affect assigned segments and prepared soils')
    return {
        'input_hashes': inputs, 'config': config, 'source': binding['identity'],
        'fetches': [{key: fetch[key] for key in ('table', 'observed_at', 'response_sha256',
                                                 'key_count', 'row_count')} for fetch in fetches],
        'base_assignments': base_assignments, 'base_soils': base,
        'treatment_targets': len(treatment), 'changed_segments': changed_segments,
        'changed_hillslopes': changed_hillslopes, 'before': before, 'after': after,
    }


def compare(usda, mirror):
    for key in ('input_hashes', 'config', 'treatment_targets'):
        if usda[key] != mirror[key]:
            raise ValueError(f'Canary inputs differ: {key}')
    differences = {}
    for stage in ('before', 'after'):
        left, right = usda[stage], mirror[stage]
        if left.keys() != right.keys():
            raise ValueError(f'Different hillslope sets at {stage}')
        differences[stage] = {
            field: [key for key in left if left[key][field] != right[key][field]]
            for field in ('segment_classes', 'prepared_management_sha256')
        }
        for field in ('staged_soil', 'prepared_soil'):
            differences[stage][field] = {
                kind: [key for key in left if left[key][field][kind] != right[key][field][kind]]
                for kind in ('canonical_sha256', 'model_input_sha256')
            }
    differences['base_assignments'] = [
        key for key in usda['base_assignments'].keys() | mirror['base_assignments'].keys()
        if usda['base_assignments'].get(key) != mirror['base_assignments'].get(key)
    ]
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--mirror-base', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prep-workers', type=int, default=1)
    args = parser.parse_args()
    if args.prep_workers < 1:
        parser.error('--prep-workers must be positive')
    args.output.mkdir(parents=True, exist_ok=False)
    mirror_source = {'endpoint': args.mirror_base.rstrip('/') + '/Tabular/post.rest',
                     'profile': 'wepppy-json-v1', 'release': RELEASE}
    result = {}
    for label, source in (('usda', {}), ('mirror', mirror_source)):
        result[label] = build(args.template, args.output / f'{args.output.name}-{label}', source, args.prep_workers)
        (args.output / f'{label}.json').write_text(json.dumps(result[label], indent=2) + '\n')
    comparison = compare(result['usda'], result['mirror'])
    (args.output / 'comparison.json').write_text(json.dumps(comparison, indent=2) + '\n')


if __name__ == '__main__':
    main()
