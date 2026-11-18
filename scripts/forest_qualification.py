"""Owned forest qualification projects: real RQ, NoDb builders and prepared inputs.

The legacy reference cache is seeded from direct official-file queries, not an SDA
response or the candidate importer. Its original retrieval provenance stays unknown.
Run only inside the explicitly configured qualification worker/Redis namespace.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import time
from xml.etree import ElementTree

PREFIX = 'soil-mirror-qualification-'
ROOT = Path('/wc1/runs/so')
RELEASE = 'forest-id-20261001-vi-20161013-v1'


def canonical(path):
    from run_wepppy_parity import COMMENT_VALUES
    return COMMENT_VALUES.sub(rb'\1<excluded>', path.read_bytes())


def build_and_prepare(runid):
    if not runid.startswith(PREFIX):
        raise ValueError('Qualification run prefix required')
    from wepppy.rq.project_rq import build_soils_rq
    from wepppy.nodb.core import Soils, Watershed, Wepp
    from rq import get_current_job
    build_soils_rq(runid)
    wd = str(ROOT / runid)
    soils = Soils.getInstance(wd)
    wepp = Wepp.getInstance(wd)
    Path(wepp.runs_dir).mkdir(parents=True, exist_ok=True)
    wepp._prep_soils(Watershed.getInstance(wd).translator_factory(), max_workers=1)
    files = sorted((ROOT / runid / 'wepp/runs').glob('p*.sol'))
    if not files or not all(path.stat().st_size for path in files):
        raise AssertionError('Prepared soil inputs absent')
    base = ROOT / runid / 'soils' / next(iter(soils.soils.values())).fname
    provenance = json.loads(Path(str(base) + '.provenance.json').read_text())
    return {'job_id': get_current_job().id, 'base_file': str(base), 'provenance': provenance,
            'base_canonical_sha256': hashlib.sha256(canonical(base)).hexdigest(),
            'prepared': {path.name: hashlib.sha256(canonical(path)).hexdigest() for path in files}}


def seed_reference(path, mukey, dataset):
    from wepppy.soils.ssurgo.ssurgo import SurgoSoilCollection, _extract_table, _extract_unique
    collection = SurgoSoilCollection([], cache_db_path=str(path))
    catalog = json.loads(Path('/qualification/../contracts/wepppy-queries.json').read_text())['queries']
    if dataset == 'SSURGO':
        source = sqlite3.connect('file:/official/SQLite_SSURGO_ID/SQLite_SSURGO_ID.gpkg?mode=ro&immutable=1', uri=True)
    else:
        from audit_sources import load_legacy
        source, _ = load_legacy(Path('/official-statsgo.zip'))
    try:
        cokeys = [row[0] for row in source.execute('SELECT cokey FROM component WHERE mukey=?', (mukey,))]
        chkeys = [row[0] for row in source.execute('SELECT chkey FROM chorizon WHERE cokey IN (' + ','.join(map(str,cokeys)) + ')')]
        keysets = [[mukey], cokeys, chkeys, chkeys, cokeys]
        tables = ['component','chorizon','chfrags','chtexturegrp','corestrictions']
        for definition, keys, table in zip(catalog, keysets, tables):
            query = definition['request']['form']['query'].replace('1001,1002', ','.join(map(str,keys)))
            cursor = source.execute(query.replace('ORDER BY mukey', 'ORDER BY component.mukey'))
            columns = [item[0] for item in cursor.description]
            root = ElementTree.Element('NewDataSet')
            for row in cursor:
                item = ElementTree.SubElement(root, 'Table')
                for column,value in zip(columns,row):
                    ElementTree.SubElement(item,column).text = None if value is None else str(value)
            extract = _extract_table if table in ('component','chorizon') else _extract_unique
            rows = extract(ElementTree.tostring(root))
            if rows:
                collection.conn.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in columns)+')',rows)
            missing = set(map(int,keys)) - {row[0] for row in rows}
            collection.conn.executemany('INSERT INTO bad_'+table+'_'+columns[0]+' VALUES (?)',[(key,) for key in missing])
        for table in ('soil_data_fetch','soil_data_source'):
            collection.conn.execute('DROP TABLE '+table)
        collection.conn.commit()
    finally:
        collection._disconnect(); source.close()


def create(tag, suffix, mukey, source_wd, dataset, *, reference=False, unreachable=False):
    from wepppy.nodb.core import Ron, Soils, SoilsMode, Wepp, Watershed
    from wepppy.nodb.redis_prep import RedisPrep
    wd = ROOT / (PREFIX + tag + '-' + suffix)
    wd.mkdir(exist_ok=False)
    Ron(str(wd), '0.cfg')
    shutil.copy2(Path(source_wd) / 'watershed.nodb', wd / 'watershed.nodb')
    (wd / 'watershed').mkdir()
    for name in ('hillslopes.parquet','channels.parquet'):
        shutil.copy2(Path(source_wd) / 'watershed' / name, wd / 'watershed' / name)
    watershed = Watershed.getInstance(str(wd))
    with watershed.locked():
        watershed._mods = []
    soils = Soils.getInstance(str(wd))
    soils.mode = SoilsMode.Single
    soils.single_selection = mukey
    Wepp.getInstance(str(wd))
    RedisPrep(str(wd))
    if reference:
        soils.configure_soil_data_source()
        Path(soils.soils_dir).mkdir(exist_ok=True)
        seed_reference(Path(soils.ssurgo_cache_db_path), mukey, dataset)
    elif unreachable:
        soils.configure_soil_data_source(endpoint='http://127.0.0.1:9/Tabular/post.rest',
            profile='wepppy-json-v1', release=RELEASE, fallback_to_sda=True)
    return wd


def run(source_wd, mukey, run_tag, dataset):
    import re
    if not re.fullmatch(r'[a-z0-9-]{1,40}', run_tag):
        raise ValueError('Invalid qualification tag')
    receipt_path = Path('/evidence/queued-' + run_tag + '.json')
    if receipt_path.exists():
        raise FileExistsError(receipt_path)
    from redis import Redis
    from rq import Queue
    from wepppy.nodb.core import Soils
    connection = Redis(host='qualification-redis')
    queue = Queue('soil-forest-qualification', connection=connection)
    report = {'scope':'single-soil-mode real queued qualification; direct official reference; no live SDA claim',
              'mukey':mukey, 'dataset':dataset, 'release':RELEASE, 'cases':{}}
    def submit(name, wd, fails=False):
        job = queue.enqueue("forest_qualification.build_and_prepare", wd.name, job_timeout=180, result_ttl=86400, failure_ttl=86400)
        deadline = time.monotonic()+200
        while time.monotonic()<deadline:
            job.refresh()
            if job.is_finished or job.is_failed:
                break
            time.sleep(0.5)
        if fails:
            assert job.is_failed, job.get_status()
            event_path = Path(Soils.getInstance(str(wd)).ssurgo_cache_db_path + '.selection.json')
            event = json.loads(event_path.read_text())
            assert event['actual_supplier'] is None and len(event['attempts']) == 2
            report['cases'][name] = {'job_id':job.id,'failed':True,'selection':event}
        else:
            assert job.is_finished, job.exc_info
            report['cases'][name] = job.return_value()
        receipt_path.write_text(json.dumps(report,indent=2)+'\n')
    primary = create(run_tag,'primary',mukey,source_wd,dataset)
    submit('primary_cold',primary)
    submit('primary_warm',primary)
    reference = create(run_tag,'reference',mukey,source_wd,dataset,reference=True)
    submit('official_reference',reference)
    fallback = create(run_tag,'fallback',mukey,source_wd,dataset,unreachable=True)
    (fallback/'soils').mkdir(exist_ok=True)
    shutil.copy2(reference/'soils/ssurgo_tabular_cache.sqlite', fallback/'soils/ssurgo_tabular_cache.sqlite')
    submit('fallback_warm',fallback)
    both = create(run_tag,'both-down',mukey,source_wd,dataset,unreachable=True)
    submit('both_unavailable',both,fails=True)
    expected = report['cases']['official_reference']
    for name in ('primary_cold','primary_warm','fallback_warm'):
        actual = report['cases'][name]
        assert actual['base_canonical_sha256'] == expected['base_canonical_sha256'], name
        assert actual['prepared'] == expected['prepared'], name
    report['exact_base_and_prepared_parity'] = True
    receipt_path.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source-wd',required=True)
    p.add_argument('--mukey',required=True,type=int)
    p.add_argument('--run-tag', required=True)
    p.add_argument('--dataset', choices=['SSURGO','STATSGO2'], required=True)
    args=p.parse_args()
    run(args.source_wd,args.mukey,args.run_tag,args.dataset)
