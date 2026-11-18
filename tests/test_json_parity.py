import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from run_wepppy_json_parity import compare_cache


class JsonParityTests(unittest.TestCase):
    def test_positive_change_fails_but_duplicate_negative_is_same_absence(self):
        reference = ROOT / 'fixtures/wepppy/ssurgo-004/cache.sqlite'
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'candidate.sqlite'
            shutil.copyfile(reference, candidate)
            self.assertTrue(all(x['equal'] for x in compare_cache(reference, candidate).values()))
            with sqlite3.connect(candidate) as conn:
                conn.execute('INSERT INTO bad_chfrags_chkey SELECT * FROM bad_chfrags_chkey LIMIT 1')
            self.assertTrue(all(x['equal'] for x in compare_cache(reference, candidate).values()))
            with sqlite3.connect(candidate) as conn:
                conn.execute('UPDATE chorizon SET sandtotal_r=0 WHERE rowid=(SELECT min(rowid) FROM chorizon)')
            with self.assertRaisesRegex(ValueError, 'Cache mismatch: chorizon'):
                compare_cache(reference, candidate)


if __name__ == '__main__':
    unittest.main()
