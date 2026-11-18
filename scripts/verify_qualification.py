#!/usr/bin/env python3
"""Read back retained qualification outputs; run inside the qualified WEPPpy image."""
import hashlib
import json
from pathlib import Path

from forest_qualification import canonical
from wepppy.soils.ssurgo.source import read_artifact_provenance

def verify(receipt_path):
    receipt = json.loads(receipt_path.read_text())
    assert receipt['exact_base_and_prepared_parity'] is True
    results = []
    for name in ('primary_warm', 'official_reference', 'fallback_warm'):
        case = receipt['cases'][name]
        base = Path(case['base_file'])
        provenance = read_artifact_provenance(str(base))
        assert provenance == case['provenance']
        assert hashlib.sha256(canonical(base)).hexdigest() == case['base_canonical_sha256']
        wd = base.parent.parent
        observed = {p.name:hashlib.sha256(canonical(p)).hexdigest() for p in (wd/'wepp/runs').glob('p*.sol')}
        assert observed == case['prepared'] and observed
        if name != 'official_reference':
            event = provenance['selection']
            assert event['actual_supplier'] == provenance['source']['binding']['identity']
            assert event['historical_rows_unknown'] == provenance['source']['binding']['historical_rows_unknown']
            if name == 'primary_warm':
                assert len(event['attempts']) == 1 and event['attempts'][0]['reason'] == 'cache_reused'
            else:
                assert len(event['attempts']) == 2 and event['attempts'][-1]['reason'] == 'cache_reused'
                assert event['historical_rows_unknown'] is True
        results.append({'case':name,'base_sha256_verified':True,'prepared_files':len(observed)})
    failed = receipt['cases']['both_unavailable']
    assert failed['selection']['actual_supplier'] is None
    assert [attempt['reason'] for attempt in failed['selection']['attempts']] == ['connection_failed','connection_failed']
    failure_wd = Path(receipt['cases']['primary_warm']['base_file']).parent.parent.with_name(
        Path(receipt['cases']['primary_warm']['base_file']).parent.parent.name.removesuffix('-primary')+'-both-down')
    assert not list((failure_wd/'soils').glob('*.sol'))
    assert not list((failure_wd/'wepp/runs').glob('p*.sol'))
    return {'receipt':receipt_path.name,'readback':results,'failed_job_has_no_generated_soils':True,
            'note':'Cold and warm canonical hashes were compared per job; warm build replaces the same primary artifact paths.'}

if __name__ == '__main__':
    reports = [verify(Path('/evidence/queued-'+name+'-final.json')) for name in ('id','vi')]
    Path('/evidence/artifact-readback.json').write_text(json.dumps(reports,indent=2)+'\n')
    print('Verified both datasets, base sidecar hashes, prepared files, supplier identities and failed-job artifact absence.')
