import sys
from pathlib import Path
import unittest
import tempfile
import sqlite3
import json
import hashlib
import shutil
from unittest.mock import patch
import replay_cache
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from replay_cache import generate, literal


class ReplayTests(unittest.TestCase):
    def test_literal_precision_nulls_and_quoting(self):
        self.assertEqual(literal('9007199254740993', 'bigint'), '9007199254740993')
        self.assertEqual(literal('0.000000000000001', 'numeric'), '0.000000000000001')
        self.assertEqual(literal(None, 'text'), 'NULL')
        self.assertEqual(literal("O'Brien", 'text'), "'O''Brien'")
        for value, kind in [('NaN', 'numeric'), ('1.5', 'bigint'), (-1, 'bigint'), ('1;DROP TABLE x', 'bigint')]:
            with self.assertRaises(ValueError):
                literal(value, kind)

    def test_incomplete_reference_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete cache'):
            generate('statsgo-002')

    def test_conflicting_mapunit_projection_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / 'fixtures/wepppy/ssurgo-004'
            case.mkdir(parents=True)
            shutil.copyfile(replay_cache.ROOT / 'fixtures/wepppy/ssurgo-004/cache.sqlite', case / 'cache.sqlite')
            with sqlite3.connect(case / 'cache.sqlite') as conn:
                key = conn.execute('SELECT mukey FROM component GROUP BY mukey HAVING count(*)>1 LIMIT 1').fetchone()[0]
                conn.execute("UPDATE component SET muname='deliberately conflicting' WHERE cokey=(SELECT min(cokey) FROM component WHERE mukey=?)", (key,))
            checksum = hashlib.sha256((case / 'cache.sqlite').read_bytes()).hexdigest()
            (case / 'cache.manifest.json').write_text(json.dumps({'snapshot': {'sha256': checksum}}))
            with patch.object(replay_cache, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Conflicting cached muaggatt'):
                generate('ssurgo-004')

    def test_empty_release_is_explicit_and_transactional(self):
        sql, manifest = generate('statsgo-001')
        self.assertTrue(sql.startswith('BEGIN;'))
        self.assertTrue(sql.endswith('COMMIT;\n'))
        self.assertNotIn('INSERT INTO soil.component', sql)
        self.assertEqual(manifest['datasets'][0]['dataset'], 'WEPPPY_CACHE_REPLAY')


if __name__ == '__main__':
    unittest.main()
