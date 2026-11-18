import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import verify_wepppy_reference as verification
from run_wepppy_parity import inspect_cache, PINNED_WEPPPY

ROOT=Path(__file__).resolve().parents[1]


class ReferenceVerificationTests(unittest.TestCase):
    def test_network_decisions_and_snapshot_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture=root/'fixtures/wepppy/ssurgo-004';fixture.mkdir(parents=True)
            cache=fixture/'cache.sqlite';shutil.copyfile(ROOT/'fixtures/wepppy/ssurgo-004/cache.sqlite',cache)
            (fixture/'cache.manifest.json').write_text('{}')
            output=root/'output';(output/'ssurgo-004').mkdir(parents=True)
            keys,gaps,coverage=inspect_cache(cache)
            case={'case_id':'ssurgo-004','snapshot_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'cache_gaps':gaps,'coverage':coverage,'status':'reference_built_historical_comparison_separate','decisions':[{'mukey':k,'valid':False} for k in keys],'valid_count':0,'invalid_count':len(keys),'artifacts':[]}
            report={'claim':'legacy_reference_only_not_mirror_parity','environment':{'wepppy_revision':PINNED_WEPPPY},'network':{'parent_namespace':'parent','worker_namespace':'worker','external_connect_errno':101},'cases':[case]}
            def save():(output/'report.json').write_text(json.dumps(report))
            save()
            with patch.object(verification,'ROOT',root):
                verification.verify_run(output)
                removed=case['decisions'].pop();save()
                with self.assertRaisesRegex(ValueError,'key decision'):verification.verify_run(output)
                case['decisions'].append(removed)
                report['network']['worker_namespace']='parent';save()
                with self.assertRaisesRegex(ValueError,'isolation'):verification.verify_run(output)
                report['network']['worker_namespace']='worker';case['snapshot_sha256']='0'*64;save()
                with self.assertRaisesRegex(ValueError,'snapshot'):verification.verify_run(output)

    def test_archive_rejects_unsafe_members_and_changed_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'reference.tar.gz'
            for name,unsafe in [('case/base/1.sol',False),('../outside.sol',True)]:
                data=b'7778\n1 0\n'
                with tarfile.open(path,'w:gz') as archive:
                    info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
                manifest={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'members':{name:hashlib.sha256(data).hexdigest()}}
                if unsafe:
                    with self.assertRaisesRegex(ValueError,'Unsafe'):verification.verify_archive(path,manifest)
                else:
                    verification.verify_archive(path,manifest)
                    with path.open('ab') as out:out.write(b'changed')
                    with self.assertRaisesRegex(ValueError,'checksum'):verification.verify_archive(path,manifest)


if __name__=='__main__':unittest.main()
