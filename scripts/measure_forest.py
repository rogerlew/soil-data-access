import concurrent.futures
import json
import statistics
import time
import urllib.parse
import urllib.request
from pathlib import Path
from redis import Redis
from rq.job import Job
keys=json.loads(Path('/official/raw-parity.json').read_text())['SSURGO']['mukeys']
query=json.loads(Path('/contracts/wepppy-queries.json').read_text())['queries'][0]['request']['form']['query'].replace('1001,1002',','.join(map(str,keys)))
body=urllib.parse.urlencode({'query':query,'format':'JSON+COLUMNNAME'}).encode()
def request(_):
    start=time.monotonic()
    with urllib.request.urlopen('http://soil-api:8080/Tabular/post.rest',data=body,timeout=10) as response:
        payload=json.load(response)
        assert response.status==200 and response.headers['X-Soil-Release']=='forest-id-20261001-vi-20161013-v1'
    return (time.monotonic()-start)*1000,len(payload['Table'])-1
results={}
for workers in (1,4):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        values=list(pool.map(request,range(40)))
    times=sorted(v[0] for v in values)
    results[str(workers)]={'requests':40,'component_rows_per_request':values[0][1],'p50_ms':statistics.median(times),'p95_ms':times[37],'max_ms':max(times)}
jobs={}
for dataset in ('id','vi'):
    report=json.loads(Path('/evidence/queued-'+dataset+'-final.json').read_text())
    for case,value in report['cases'].items():
        job=Job.fetch(value['job_id'],connection=Redis(host='qualification-redis'))
        jobs[dataset+'_'+case]=(job.ended_at-job.started_at).total_seconds()
Path('/evidence/query-timings.json').write_text(json.dumps({'scope':'warm regional 100-MUKEY component queries; local forest image; not national capacity claim','requests':results,'queued_seconds':jobs},indent=2)+'\n')
