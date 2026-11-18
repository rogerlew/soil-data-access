#!/usr/bin/env python3
"""Verify two independent legacy reference builds and optionally publish canonical files."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
from run_wepppy_parity import ROOT, PINNED_WEPPPY, canonical, inspect_cache


def sha(data):return hashlib.sha256(data).hexdigest()


def verify_run(directory):
    report=json.loads((directory/'report.json').read_text())
    if report['claim']!='legacy_reference_only_not_mirror_parity' or report['environment']['wepppy_revision']!=PINNED_WEPPPY:
        raise ValueError('Wrong reference identity')
    net=report['network']
    if net['parent_namespace']==net['worker_namespace'] or net['external_connect_errno']!=101:
        raise ValueError('Missing network isolation evidence')
    ids=[c['case_id'] for c in report['cases']]
    expected={p.parent.name for p in (ROOT/'fixtures/wepppy').glob('*/cache.manifest.json')}
    if len(ids)!=len(set(ids)) or set(ids)!=expected:raise ValueError('Case set is incomplete or duplicated')
    for case in report['cases']:
        case_id=case['case_id'];fixture=ROOT/'fixtures/wepppy'/case_id
        if case['snapshot_sha256']!=sha((fixture/'cache.sqlite').read_bytes()):raise ValueError('Stale source snapshot')
        keys,gaps,_=inspect_cache(fixture/'cache.sqlite')
        if case['cache_gaps']!=gaps:raise ValueError('Incorrect cache completeness claim')
        if gaps:
            if case['status']!='incomplete_cache_not_a_reference' or 'artifacts' in case:raise ValueError('Incomplete cache cannot be a built reference')
            continue
        if case['status']!='reference_built_historical_comparison_separate':raise ValueError('Complete reference was not built')
        decisions=case['decisions'];decision_keys=[d['mukey'] for d in decisions]
        if sorted(decision_keys)!=keys:raise ValueError('Missing or duplicated key decision')
        if sum(d['valid'] for d in decisions)!=case['valid_count'] or len(decisions)-case['valid_count']!=case['invalid_count']:
            raise ValueError('Invalid decision totals')
        config=fixture/'reference-inputs.json'
        if config.exists() and case['configuration_sha256']!=sha(config.read_bytes()):raise ValueError('Stale reference configuration')
        seen=set()
        for artifact in case['artifacts']:
            path=directory/case_id/artifact['file']
            if not path.resolve().is_relative_to((directory/case_id).resolve()):raise ValueError('Artifact path escapes case')
            if path in seen:raise ValueError('Duplicate artifact')
            seen.add(path);data=path.read_bytes()
            if len(data)!=artifact['bytes'] or sha(data)!=artifact['raw_sha256'] or sha(canonical(data))!=artifact['canonical_sha256']:
                raise ValueError('Reference artifact checksum mismatch')
        if seen!=set((directory/case_id).rglob('*.sol')):raise ValueError('Unreported generated artifacts')
        if {p.name for p in seen if p.parent.name=='base'}!={str(d['mukey'])+'.sol' for d in decisions if d['valid']}:
            raise ValueError('Valid keys and emitted base soils differ')
    return report


def compare(first,second):
    a=verify_run(first);b=verify_run(second)
    if a['environment']!=b['environment']:raise ValueError('Reference environments differ')
    results=[]
    for left,right in zip(a['cases'],b['cases']):
        for key in ('case_id','snapshot_sha256','status','cache_gaps','coverage','profile','profile_basis','decisions','captured_assignments','configuration_sha256'):
            if left.get(key)!=right.get(key):raise ValueError('Reference differs for '+left['case_id']+': '+key)
        la={x['file']:x['canonical_sha256'] for x in left.get('artifacts',[])}
        ra={x['file']:x['canonical_sha256'] for x in right.get('artifacts',[])}
        if la!=ra:raise ValueError('Repeated soil output differs for '+left['case_id'])
        results.append({'case_id':left['case_id'],'status':left['status'],'valid':left.get('valid_count',0),'invalid':left.get('invalid_count',0),'canonical_artifacts':len(la),'repeatable':True if la else None})
    return {'claim':'legacy_reference_repeatability_not_release_acceptance','reference_revision':PINNED_WEPPPY,'runs':[sha((p/'report.json').read_bytes()) for p in (first,second)],'cases':results,'all_generated_artifacts_match':True},b


def publish(directory,report,output):
    if not output.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Publication must stay inside repository')
    if output.exists():raise FileExistsError(output)
    members={}
    for case in report['cases']:
        for item in case.get('artifacts',[]):
            name=case['case_id']+'/'+item['file']
            data=canonical((directory/name).read_bytes())
            if sha(data)!=item['canonical_sha256']:raise ValueError('Output changed before publication')
            members[name]=data
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as zipped, tarfile.open(fileobj=zipped,mode='w') as archive:
        for name,data in sorted(members.items()):
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;info.mtime=0
            archive.addfile(info,io.BytesIO(data))
    return {'file':str(output.relative_to(ROOT)), 'bytes':output.stat().st_size,'sha256':sha(output.read_bytes()),'members':{name:sha(data) for name,data in sorted(members.items())}}


def verify_archive(path,manifest):
    if sha(path.read_bytes())!=manifest['sha256']:raise ValueError('Reference archive checksum mismatch')
    with tarfile.open(path,'r:gz') as archive:
        members=archive.getmembers()
        if len(members)!=len(manifest['members']) or {m.name for m in members}!=set(manifest['members']):raise ValueError('Archive member set differs')
        for member in members:
            if not member.isfile() or Path(member.name).is_absolute() or '..' in Path(member.name).parts:raise ValueError('Unsafe archive member')
            with archive.extractfile(member) as stream:
                if sha(stream.read())!=manifest['members'][member.name]:raise ValueError('Archive content differs')


def verify_published():
    evidence = ROOT / 'artifacts/wepppy-parity'
    receipt = json.loads((evidence / 'reference-repeatability.json').read_text())
    reports = [evidence / f'reference-run-{name}.json' for name in ('a', 'b')]
    if [sha(path.read_bytes()) for path in reports] != receipt['runs']:
        raise ValueError('Published report hashes differ')
    report = json.loads(reports[1].read_text())
    if report['environment']['wepppy_revision'] != PINNED_WEPPPY:
        raise ValueError('Wrong published reference revision')
    expected = {}
    for case in report['cases']:
        fixture = ROOT / 'fixtures/wepppy' / case['case_id']
        if sha((fixture / 'cache.sqlite').read_bytes()) != case['snapshot_sha256']:
            raise ValueError('Published source snapshot differs')
        config = fixture / 'reference-inputs.json'
        if config.exists() and sha(config.read_bytes()) != case['configuration_sha256']:
            raise ValueError('Published configuration differs')
        if config.exists():
            inputs = json.loads(config.read_text())
            lookup = fixture / inputs['treatment']['lookup_file']
            if sha(lookup.read_bytes()) != inputs['source_hashes']['disturbed/disturbed_land_soil_lookup.csv']['sha256']:
                raise ValueError('Published treatment lookup differs')
        for item in case.get('artifacts', []):
            expected[case['case_id'] + '/' + item['file']] = item['canonical_sha256']
    if expected != receipt['archive']['members']:
        raise ValueError('Published archive differs from reference report')
    archive_path = (ROOT / receipt['archive']['file']).resolve()
    if not archive_path.is_relative_to(ROOT.resolve()):
        raise ValueError('Archive path escapes repository')
    verify_archive(archive_path, receipt['archive'])
    return {'published_reference_artifacts': len(expected), 'verified': True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first',type=Path,nargs='?');parser.add_argument('second',type=Path,nargs='?')
    parser.add_argument('--verify-published',action='store_true')
    parser.add_argument('--publish',type=Path);parser.add_argument('--receipt',type=Path)
    args=parser.parse_args()
    if args.verify_published:
        print(json.dumps(verify_published(),indent=2))
        return
    if not all((args.first,args.second,args.receipt)):
        parser.error('first, second, and --receipt are required for comparison')
    receipt,report=compare(args.first,args.second)
    if args.publish:
        receipt['archive']=publish(args.second,report,args.publish.resolve())
        verify_archive(args.publish,receipt['archive'])
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='archive'},indent=2))


if __name__=='__main__':main()
