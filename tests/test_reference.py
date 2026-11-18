import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_wepppy_parity import canonical, inspect_cache

ROOT=Path(__file__).resolve().parents[1]


class ReferenceContractTests(unittest.TestCase):
    def test_only_declared_comment_values_are_excluded(self):
        a=b'7778\r\n# Build Date: yesterday\r\n# Source File: /private/path\r\n# important explanation\r\n1 0\r\n0.75\r\n'
        b=a.replace(b'yesterday',b'today').replace(b'/private/path',b'/scratch/path')
        self.assertEqual(canonical(a),canonical(b))
        self.assertNotEqual(canonical(a),canonical(a.replace(b'0.75',b'0.76')))
        self.assertNotEqual(canonical(a),canonical(a.replace(b'important',b'changed')))
        self.assertNotEqual(canonical(a),canonical(a.replace(b'\r\n',b'\n')))
        self.assertEqual(canonical(b'Build Date: is model text'),b'Build Date: is model text')

    def test_negative_markers_are_required_for_absent_lookups(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'cache.sqlite'
            shutil.copyfile(ROOT/'fixtures/wepppy/ssurgo-004/cache.sqlite',target)
            _,gaps,_=inspect_cache(target)
            self.assertEqual(gaps,{})
            with sqlite3.connect(target) as c:
                key=c.execute('SELECT cokey FROM component LIMIT 1').fetchone()[0]
                c.execute('DELETE FROM corestrictions WHERE cokey=?',(key,))
                c.execute('DELETE FROM bad_corestrictions_cokey WHERE cokey=?',(key,))
            _,gaps,_=inspect_cache(target)
            self.assertIn(key,gaps['corestrictions'])
            with sqlite3.connect(target) as c:
                c.execute('INSERT INTO bad_corestrictions_cokey VALUES(?)',(key,))
            _,gaps,_=inspect_cache(target)
            self.assertEqual(gaps,{})

    def test_empty_cache_is_distinguished_from_missing_records(self):
        keys,gaps,coverage=inspect_cache(ROOT/'fixtures/wepppy/statsgo-001/cache.sqlite')
        self.assertEqual((keys,gaps),([],{}))
        self.assertEqual(coverage['requested_mukeys'],0)


if __name__=='__main__':unittest.main()
