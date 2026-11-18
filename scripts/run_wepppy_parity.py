#!/usr/bin/env python3
"""Build the legacy cache reference offline. This is not mirror/API acceptance."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PINNED_WEPPPY = '917708c90dce46bbab920ecf9ce5f315e8611290'
COMMENT_VALUES = re.compile(rb'(?m)^(#[ \t]*(?:Build Date|Source File):[ \t]*)[^\r\n]*')


def canonical(data):
    """Replace exactly the two predeclared volatile comment values, nothing else."""
    return COMMENT_VALUES.sub(lambda m: m[1] + b'<reference-metadata>', data)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inspect_cache(path):
    conn = sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)
    try:
        def keys(table, column):
            return {r[0] for r in conn.execute(f'SELECT "{column}" FROM "{table}"')}
        mukeys = keys('component','mukey') | keys('bad_component_mukey','mukey')
        cokeys = keys('component','cokey')
        chkeys = keys('chorizon','chkey')
        gaps = {}
        for table, column, wanted, negative in (
            ('chorizon','cokey',cokeys,'bad_chorizon_cokey'),
            ('corestrictions','cokey',cokeys,'bad_corestrictions_cokey'),
            ('chfrags','chkey',chkeys,'bad_chfrags_chkey'),
            ('chtexturegrp','chkey',chkeys,'bad_chtexturegrp_chkey'),
        ):
            absent = wanted - keys(table,column) - keys(negative,column)
            if absent: gaps[table] = sorted(absent)
        coverage = {
            'requested_mukeys':len(mukeys),
            'multiple_components':conn.execute('SELECT count(*) FROM (SELECT mukey FROM component GROUP BY mukey HAVING count(*)>1)').fetchone()[0],
            'multiple_horizons':conn.execute('SELECT count(*) FROM (SELECT cokey FROM chorizon GROUP BY cokey HAVING count(*)>1)').fetchone()[0],
            'profile_bottom_le_50cm':conn.execute('SELECT count(*) FROM (SELECT cokey FROM chorizon GROUP BY cokey HAVING max(hzdepb_r)<=50)').fetchone()[0],
            'horizons_with_null_texture_or_hydraulic_field':conn.execute('SELECT count(*) FROM chorizon WHERE ksat_r IS NULL OR sandtotal_r IS NULL OR claytotal_r IS NULL OR dbthirdbar_r IS NULL').fetchone()[0],
            'restriction_kinds':[r[0] for r in conn.execute('SELECT DISTINCT reskind FROM corestrictions ORDER BY reskind')],
            'fragment_rows':conn.execute('SELECT count(*) FROM chfrags').fetchone()[0],
            'texture_rows':conn.execute('SELECT count(*) FROM chtexturegrp').fetchone()[0],
            'negative_rows':sum(conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in ('bad_component_mukey','bad_chorizon_cokey','bad_corestrictions_cokey','bad_chfrags_chkey','bad_chtexturegrp_chkey')),
        }
        return sorted(mukeys), gaps, coverage
    finally:
        conn.close()


def artifact_info(path, root):
    data=path.read_bytes()
    return {'file':str(path.relative_to(root)), 'bytes':len(data),
            'raw_sha256':digest(data),'canonical_sha256':digest(canonical(data))}


def environment_receipt(wepppy_root):
    import rosetta
    import numpy
    import numpy.core._multiarray_umath as numpy_native
    import duckdb.duckdb as duckdb_native
    rosroot=Path(rosetta.__file__).parent
    rosfiles=[p for p in rosroot.rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.duckdb','.sqlite','.db') or p.suffix=='.so')]
    rosmanifest={str(p.relative_to(rosroot)):digest(p.read_bytes()) for p in sorted(rosfiles)}
    return {'wepppy_revision':PINNED_WEPPPY,'python':sys.version,'platform':platform.platform(),
            'machine':platform.machine(),'numpy':numpy.__version__,
            'scipy':importlib.metadata.version('scipy'),'duckdb':importlib.metadata.version('duckdb'),
            'numpy_native_sha256':digest(Path(numpy_native.__file__).read_bytes()),
            'duckdb_native_sha256':digest(Path(duckdb_native.__file__).read_bytes()),
            'rosetta_files':rosmanifest,
            'thread_environment':{k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')}}


def run_case(case, output, ssurgo):
    manifest=json.loads((case/'cache.manifest.json').read_text())
    source=case/'cache.sqlite'; before=digest(source.read_bytes())
    if before!=manifest['snapshot']['sha256']:raise ValueError('Fixture hash mismatch')
    mukeys,gaps,coverage=inspect_cache(source)
    report={'case_id':case.name,'snapshot_sha256':before,'coverage':coverage,'cache_gaps':gaps}
    if gaps:
        report['status']='incomplete_cache_not_a_reference'
        return report
    config_path=case/'reference-inputs.json'
    config=json.loads(config_path.read_text()) if config_path.exists() else None
    profile=config['base'] if config else {'use_statsgo':manifest['cache_label']=='statsgo','initial_sat':0.75,'ksflag':True,'version':'7778'}
    report['profile']=profile
    report['profile_basis']=config['profile_basis'] if config else 'authored_reference_profile_not_historical_settings'
    if config:
        report['configuration_sha256']=digest(config_path.read_bytes())
        report['captured_assignments']=config['assignments']
    work=output/case.name; work.mkdir()
    cache=work/'working.sqlite'; shutil.copyfile(source,cache)
    soils=work/'base';soils.mkdir()
    collection=ssurgo.SurgoSoilCollection(mukeys,use_statsgo=profile['use_statsgo'],cache_db_path=str(cache))
    if collection._sync_n!=0:raise ValueError('Unexpected cache synchronization miss')
    collection.makeWeppSoils(initial_sat=profile['initial_sat'],ksflag=profile['ksflag'],max_workers=1)
    collection.writeWeppSoils(wd=str(soils),version=profile['version'])
    decisions=[]
    for key in mukeys:
        valid=key in collection.weppSoils
        soil=collection.weppSoils[key] if valid else collection.invalidSoils[key]
        record={'mukey':key,'valid':valid}
        if soil is not None:
            component=getattr(soil,'majorComponent',None)
            record['cokey']=None if component is None else int(component.cokey)
            record['urban']=soil.is_urban;record['water']=soil.is_water
            horizons=getattr(soil,'horizons',None)
            record['horizons']=[] if horizons is None else [int(h.chkey) for h in horizons]
            record['restriction_index']=getattr(soil,'res_lyr_i',None)
            if not valid:record['failure_log']=soil.log
        else:record['failure_log']='builder_returned_no_soil'
        decisions.append(record)
    report['decisions']=decisions
    report['valid_count']=len(collection.weppSoils);report['invalid_count']=len(collection.invalidSoils)
    report['historical_comparisons']=[]
    if config:
        from wepppy.nodb.mods.disturbed.disturbed import read_disturbed_land_soil_lookup
        from wepppy.wepp.soils.utils import WeppSoilUtil, simple_texture
        from wepppy.nodb.core.wepp import prep_soil
        lookup_path=case/config['treatment']['lookup_file']
        if digest(lookup_path.read_bytes())!=config['source_hashes']['disturbed/disturbed_land_soil_lookup.csv']['sha256']:
            raise ValueError('Treatment lookup hash mismatch')
        lookup=read_disturbed_land_soil_lookup(str(lookup_path))
        key=config['historical_artifact_mukey']; source_soil=soils/f'{key}.sol'
        if not source_soil.exists():raise ValueError('Paired project reference soil is invalid')
        util=WeppSoilUtil(str(source_soil))
        ofe=util.obj['ofes'][0];horizon=ofe['horizons'][0]
        texture=simple_texture(clay=horizon['clay'],sand=horizon['sand'])
        treatment=config['treatment']
        replacements=lookup[(texture,treatment['disturbed_class'])]
        treated=util.to_over9000(replacements,h0_max_om=treatment['h0_max_om'],version=treatment['version'],recompute_wp_fc_using_rosetta_on_bd_override=treatment['recompute_wp_fc_using_rosetta_on_bd_override'])
        treated_file=work/'treated.sol';treated.write(str(treated_file))
        model_file=work/'model-input.sol';prep=config['preparation']
        prep_soil((config['historical_model_topaz_id'],str(treated_file),str(model_file),prep['kslast'],None,profile['initial_sat'],prep['clip_soils'],prep['clip_soils_depth'],prep['clip_soils_minimum'],prep['clip_soils_minimum_depth']))
        for role,current,historical in (('base',source_soil,case/'artifacts/source.sol'),('treated',treated_file,case/'artifacts/treated.sol'),('model_input',model_file,case/'artifacts/model-input.sol')):
            old=historical.read_bytes();new=current.read_bytes()
            report['historical_comparisons'].append({'role':role,'historical_sha256':digest(old),'rebuilt_sha256':digest(new),'canonical_equal':canonical(old)==canonical(new),'historical_canonical_sha256':digest(canonical(old)),'rebuilt_canonical_sha256':digest(canonical(new))})
    report['artifacts']=[artifact_info(p,work) for p in sorted(work.rglob('*.sol'))]
    report['status']='reference_built_historical_comparison_separate'
    collection.conn.close()
    if digest(source.read_bytes())!=before:raise ValueError('Frozen fixture changed')
    return report


def worker(args):
    parent=os.environ['REFERENCE_PARENT_NETNS']
    namespace=os.readlink('/proc/self/ns/net')
    if namespace==parent:raise RuntimeError('Network namespace was not isolated')
    with socket.socket() as sock:
        sock.settimeout(0.1)
        try:sock.connect(('198.51.100.1',9))
        except OSError as exc:blocked_errno=exc.errno
        else:raise RuntimeError('External network unexpectedly reachable')
    if blocked_errno!=101:raise RuntimeError(f'Expected network unreachable, received errno {blocked_errno}')
    sys.path.insert(0,str(args.wepppy_root))
    import wepppy.soils.ssurgo.ssurgo as ssurgo
    if not Path(ssurgo.__file__).resolve().is_relative_to(args.wepppy_root.resolve()):raise RuntimeError('Wrong WEPPpy imported')
    args.output.mkdir(parents=True,exist_ok=False)
    from verify_transport_contract import verify as verify_transport
    report={'claim':'legacy_reference_only_not_mirror_parity','environment':environment_receipt(args.wepppy_root),
            'network':{'parent_namespace':parent,'worker_namespace':namespace,'external_connect_errno':blocked_errno},
            'transport_contract':verify_transport(ssurgo), 'cases':[]}
    cases=sorted((ROOT/'fixtures/wepppy').glob('*/cache.manifest.json'))
    for manifest in cases:
        if args.case and manifest.parent.name!=args.case:continue
        print('Building '+manifest.parent.name,flush=True)
        report['cases'].append(run_case(manifest.parent,args.output,ssurgo))
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['cases']:raise ValueError('No matching cases')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wepppy-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--case');p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    a=p.parse_args();a.wepppy_root=a.wepppy_root.resolve();a.output=a.output.resolve()
    revision=subprocess.check_output(['git','-C',str(a.wepppy_root),'rev-parse','HEAD'],text=True).strip()
    if revision!=PINNED_WEPPPY:raise ValueError('Wrong reference revision')
    if subprocess.check_output(['git','-C',str(a.wepppy_root),'status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('Reference checkout has tracked changes')
    if a.worker:worker(a);return
    if a.output.exists():raise FileExistsError(a.output)
    env=os.environ.copy();env['REFERENCE_PARENT_NETNS']=os.readlink('/proc/self/ns/net')
    env.update({key:'1' for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')})
    cmd=['unshare','--user','--map-root-user','--net',sys.executable,str(Path(__file__).resolve()),'--worker','--wepppy-root',str(a.wepppy_root),'--output',str(a.output)]
    if a.case:cmd+=['--case',a.case]
    subprocess.run(cmd,env=env,check=True,timeout=1200)


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        # CLI boundary: WEPPpy installs an exception renderer; retain local diagnostics.
        import traceback
        traceback.print_exception(exc, file=sys.__stderr__)
        raise SystemExit(1)
