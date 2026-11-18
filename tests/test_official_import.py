"""Scientific-value conversion and malformed source rejection."""
import csv
import io
import sys
from pathlib import Path
import unittest
import sqlite3
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from import_official import copy_cell, exact_key, generate
from replay_cache import TYPES


class ImportTests(unittest.TestCase):
    def test_staged_import_preserves_validation_without_active_pointer_write(self):
        def source(path, key):
            conn = sqlite3.connect(path)
            for table, columns in TYPES.items():
                conn.execute('CREATE TABLE ' + table + '(' +
                             ','.join(name + ' ' + ('INTEGER' if kind == 'bigint' else 'TEXT')
                                      for name, kind in columns.items()) + ')')
                values = [key if kind == 'bigint' else None for kind in columns.values()]
                conn.execute('INSERT INTO ' + table + ' VALUES (' +
                             ','.join('?' for _ in values) + ')', values)
            conn.execute('CREATE TABLE mapunit(mukey INTEGER)')
            conn.execute('INSERT INTO mapunit VALUES (?)', (key,))
            conn.execute('CREATE TABLE sacatalog(areasymbol TEXT,saversion INTEGER,saverest TEXT)')
            conn.commit()
            return conn

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gpkg, legacy = root / 'source.gpkg', root / 'legacy.sqlite'
            source(gpkg, 1).close()
            source(legacy, 2).close()
            for staged in (False, True):
                output, receipt = root / f'{staged}.sql', root / f'{staged}.json'
                with patch('import_official.load_legacy',
                           side_effect=lambda path: (sqlite3.connect(path), {})):
                    result = generate(gpkg, legacy, f'test-{staged}',
                                      'https://example.com/ssurgo', 'https://example.com/statsgo',
                                      output, receipt, '2026', '2016', 'US', 'US',
                                      no_activate=staged)
                sql = output.read_text()
                self.assertEqual('INSERT INTO soil.active_release' in sql, not staged)
                self.assertEqual(result['activation_included'], not staged)
                self.assertEqual(set(result['import_row_counts'].values()), {2})
                self.assertIn("RAISE EXCEPTION 'Imported relationship differs'", sql)
                self.assertTrue(sql.startswith('BEGIN;'))
                self.assertTrue(sql.endswith('COMMIT;\n'))

    def test_csv_preserves_text_and_null_distinction(self):
        self.assertEqual(copy_cell(None, 'text'), '')
        self.assertEqual(copy_cell('', 'text'), '""')
        for text in ('ordinary', 'comma,quote"newline\nnext', '\\.', '\\N'):
            self.assertEqual(next(csv.reader(io.StringIO(copy_cell(text, 'text'))))[0], text)

    def test_exact_numeric_and_identifier_boundaries(self):
        self.assertEqual(copy_cell('0.123456789012345678901', 'numeric'), '"0.123456789012345678901"')
        self.assertEqual(exact_key('9223372036854775807'), 9223372036854775807)
        for value in ('9223372036854775808', '-1', '1e3', '1.0', None, '1;drop table x'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exact_key(value)
        for value in ('NaN', 'Infinity', '-Infinity', 'bad'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                copy_cell(value, 'numeric')
        with self.assertRaises(ValueError):
            copy_cell('a\x00b', 'text')


if __name__ == '__main__':
    unittest.main()
