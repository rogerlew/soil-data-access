"""Qualify cold live SDA failover and mirror recovery in a fresh forest run."""

import argparse
from contextlib import closing
import errno
import json
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import time

from run_live_sda_parity import RELEASE
from run_prepared_soil_tie_parity import hashes
from run_wepppy_parity import digest

RUN_ROOT = Path('/wc1/runs/so')
MUKEY = 78905
UNREACHABLE = 'http://127.0.0.1:9/Tabular/post.rest'
REFERENCE = RUN_ROOT / 'soil-mirror-national-20261118-ssurgo'
TABLES = {'component', 'chorizon', 'chfrags', 'chtexturegrp', 'corestrictions'}


def cache_readback(path):
    from wepppy.soils.ssurgo.source import cache_evidence

    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
        result = cache_evidence(conn)
        result['component_count'] = conn.execute('SELECT count(*) FROM component').fetchone()[0]
        has_history = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='soil_data_selection'"
        ).fetchone()
        result['selection_history'] = [
            json.loads(event) for event, in conn.execute('SELECT event FROM soil_data_selection ORDER BY id')
        ] if has_history else []
        result['logical_sha256'] = digest('\n'.join(conn.iterdump()).encode())
    return result


def completed_job_receipt(job):
    return {'id': job.id, 'worker': job.worker_name, 'queue': job.origin,
            'started_at': job.started_at.isoformat(), 'ended_at': job.ended_at.isoformat()}


def run_job(queue, function, runid):
    from rq.job import JobStatus

    job = queue.enqueue(function, runid, job_timeout=180, result_ttl=86400)
    print(runid, function, job.id, flush=True)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        status = job.get_status(refresh=True)
        if status == JobStatus.FINISHED:
            job.refresh()
            return completed_job_receipt(job)
        if status in (JobStatus.FAILED, JobStatus.CANCELED, JobStatus.STOPPED):
            raise RuntimeError(f'{function} job {job.id} ended {status}: {job.exc_info}')
        time.sleep(1)
    raise TimeoutError(f'{function} job {job.id} is still pending')


def read_build(queue, wd, supplier, expected_attempts, expected_cache, expected_files, *, build=None):
    from wepppy.nodb.core import Soils
    from wepppy.soils.ssurgo.selection import validate_selection
    from wepppy.soils.ssurgo.source import read_artifact_provenance, response_origin

    soils = Soils.getInstance(str(wd))
    primary = Path(soils.ssurgo_cache_db_path)
    if build is None:
        if expected_cache.exists():
            raise FileExistsError(f'Expected a cold source cache: {expected_cache}')
        build = run_job(queue, 'wepppy.rq.project_rq.build_soils_rq', wd.name)
    prep = run_job(queue, 'wepppy.rq.wepp_rq._prep_soils_rq', wd.name)
    base = wd / 'soils' / f'{MUKEY}.sol'
    provenance = read_artifact_provenance(str(base))
    selection = provenance['selection']
    validate_selection(selection, supplier)
    sidecar = json.loads(Path(str(primary) + '.selection.json').read_text())
    cache = cache_readback(expected_cache)
    fetches = cache['fetches']
    if (selection['configured_primary'] != soils.soil_data_source or sidecar != selection
            or cache['selection_history'] != [selection]
            or provenance['cache_file'] != expected_cache.name
            or provenance['source']['binding'] != cache['binding']
            or provenance['source']['fetches'] != fetches
            or cache['binding']['identity'] != supplier
            or selection['historical_rows_unknown']
            or cache['binding']['historical_rows_unknown']
            or cache['component_count'] <= 0):
        raise ValueError('Soil artifact, cache and selection provenance disagree')
    if [(a['outcome'], a['reason']) for a in selection['attempts']] != expected_attempts:
        raise ValueError(f'Unexpected source selection: {selection}')
    if {f['table'] for f in fetches} != TABLES or any(
        f['identity'] != supplier or f['response_origin'] != response_origin(supplier['endpoint'])
        or not re.fullmatch('[a-f0-9]{64}', f['response_sha256'])
        for f in fetches
    ):
        raise ValueError('Expected live retrieval evidence for every query family')
    prepared = {p.name: hashes(p) for p in sorted((wd / 'wepp/runs').glob('p*.sol')) if p.stat().st_size}
    if set(prepared) != expected_files:
        raise ValueError('Prepared soil files do not match the reference hillslopes')
    return {'jobs': {'build': build, 'prepare': prep}, 'selection': selection, 'cache': cache,
            'base': hashes(base), 'prepared': prepared}


def compare(reference, candidate):
    return {
        kind: {
            'base_equal': reference['base'][kind] == candidate['base'][kind],
            'different_prepared_files': [
                name for name, calculated in candidate['prepared'].items()
                if calculated[kind] != reference['prepared'][name][kind]
            ],
        } for kind in ('canonical_sha256', 'model_input_sha256')
    }


def main():
    from wepppy.nodb.core import Ron, Soils, SoilsMode, Watershed, Wepp
    from wepppy.soils.ssurgo.selection import deployment_default
    from wepppy.soils.ssurgo.source import read_artifact_provenance

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag', help='Unique lowercase alphanumeric tag for the disposable run')
    args = parser.parse_args()
    if not re.fullmatch('[a-z0-9]{6,24}', args.tag):
        parser.error('tag must be 6–24 lowercase alphanumeric characters')
    primary, policy = deployment_default()
    if policy != 'mirror-first' or primary['release'] != RELEASE:
        raise ValueError('Forest deployment is not using the expected mirror-first release')
    with socket.socket() as sock:
        sock.settimeout(2)
        if sock.connect_ex(('127.0.0.1', 9)) != errno.ECONNREFUSED:
            raise ValueError('Canary-only endpoint did not refuse connections')

    reference_base = REFERENCE / 'soils' / f'{MUKEY}.sol'
    if read_artifact_provenance(str(reference_base))['selection']['actual_supplier'] != primary:
        raise ValueError('Reference soil is not from the current national release')
    reference = {'base': hashes(reference_base), 'prepared': {
        p.name: hashes(p) for p in sorted((REFERENCE / 'wepp/runs').glob('p*.sol')) if p.stat().st_size
    }}
    wd = RUN_ROOT / f'soil-sda-cold-failover-{args.tag}'
    wd.mkdir()
    path = str(wd)
    Ron(path, '0.cfg')
    shutil.copy2(REFERENCE / 'watershed.nodb', wd / 'watershed.nodb')
    (wd / 'watershed').mkdir()
    for filename in ('hillslopes.parquet', 'channels.parquet'):
        shutil.copy2(REFERENCE / 'watershed' / filename, wd / 'watershed' / filename)
    watershed = Watershed.getInstance(path)
    with watershed.locked():
        watershed._mods = []
    if len(reference['prepared']) != watershed.sub_n:
        raise ValueError('Reference prepared soils do not cover the watershed')
    soils = Soils.getInstance(path)
    soils.mode = SoilsMode.Single
    soils.single_selection = MUKEY
    Path(Wepp.getInstance(path).runs_dir).mkdir(parents=True, exist_ok=True)
    qualify(wd, primary, reference)


def qualify(wd, primary, reference, *, completed_fallback_build=None):
    from redis import Redis
    from rq import Queue
    from rq.suspension import is_suspended
    from wepppy.config.redis_settings import RedisDB, redis_connection_kwargs
    from wepppy.nodb.core import Soils
    from wepppy.soils.ssurgo.source import SoilDataSource

    path = str(wd)
    soils = Soils.getInstance(path)
    cache_dir = wd / 'soils'
    sda_cache = cache_dir / 'ssurgo_tabular_cache.sqlite'
    mirror_cache = Path(soils.ssurgo_cache_db_path)
    sda = SoilDataSource().identity()
    report = {'runid': wd.name, 'mukey': MUKEY, 'reference': REFERENCE.name,
              'prepared_pairs': len(reference['prepared'])}
    with Redis(**redis_connection_kwargs(RedisDB.RQ)) as connection:
        if is_suspended(connection):
            raise RuntimeError('Forest RQ dequeue is suspended')
        queue = Queue('default', connection=connection)
        soils.configure_soil_data_source(**(primary | {'endpoint': UNREACHABLE}), fallback_to_sda=True)
        failed_primary_cache = Path(soils.ssurgo_cache_db_path)
        try:
            report['fallback'] = read_build(
                queue, wd, sda, [('unavailable', 'connection_failed'), ('success', 'selected')],
                sda_cache, set(reference['prepared']), build=completed_fallback_build,
            )
            failed_primary = cache_readback(failed_primary_cache)
            if failed_primary['component_count'] or failed_primary['fetches'] or failed_primary['selection_history']:
                raise ValueError('Failed mirror cache contains acquired data or success history')
            report['failed_mirror_cache'] = failed_primary
        finally:
            Soils.getInstance(path).configure_soil_data_source(**primary, fallback_to_sda=True)
        report['restored_mirror'] = read_build(
            queue, wd, primary, [('success', 'selected')], mirror_cache, set(reference['prepared']),
        )
    sda_after = cache_readback(sda_cache)
    if sda_after != report['fallback']['cache']:
        raise ValueError('Mirror recovery altered the separate SDA cache')
    report['sda_cache_preserved'] = True
    report['comparisons'] = {
        'fallback_vs_reference': compare(reference, report['fallback']),
        'restored_mirror_vs_reference': compare(reference, report['restored_mirror']),
        'fallback_vs_restored_mirror': compare(report['restored_mirror'], report['fallback']),
    }
    (wd / 'live-sda-failover.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['comparisons'], indent=2), flush=True)
    if any(not pair['model_input_sha256']['base_equal']
           or pair['model_input_sha256']['different_prepared_files']
           for pair in report['comparisons'].values()):
        raise ValueError('Model-input differences retained in the comparison receipt')


if __name__ == '__main__':
    main()
