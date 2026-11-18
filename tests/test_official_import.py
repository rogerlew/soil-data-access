"""Scientific-value conversion and malformed source rejection."""
import csv
import io
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from import_official import copy_cell, exact_key


class ImportTests(unittest.TestCase):
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
