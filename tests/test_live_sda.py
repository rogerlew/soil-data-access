"""Check retained USDA wire cases independently of the live service."""

import hashlib
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / 'artifacts/assessment/sda-capture-02'


class LiveSdaCaptureTests(unittest.TestCase):
    def body(self, case, status=200):
        rows = json.loads((CAPTURE / 'observations.json').read_bytes())
        record, alias = (row for row in rows if row['case_id'] == case)
        self.assertNotEqual(record['endpoint'], alias['endpoint'])
        self.assertEqual((record['status'], alias['status']), (status, status))
        body = (CAPTURE / record['body_file']).read_bytes()
        self.assertEqual(hashlib.sha256(body).hexdigest(), record['body_sha256'])
        self.assertEqual(record['body_sha256'], alias['body_sha256'])
        return body

    def test_empty_decimal_and_error_envelopes(self):
        self.assertEqual(json.loads(self.body('empty')), {})
        self.assertEqual(json.loads(self.body('null-decimal')),
                         {'Table': [['missing', 'value'], [None, '0.125']]})
        error = ElementTree.fromstring(self.body('invalid', status=400))
        self.assertEqual(error.tag, '{http://www.opengis.net/ogc}ServiceExceptionReport')

    def test_statsgo_geomdesc_wire_and_archive(self):
        columns, *data = json.loads(self.body('statsgo2_fetch_components'))['Table']
        metadata_columns, types, *meta_data = json.loads(self.body('statsgo2-vi-metadata'))['Table']
        self.assertEqual(metadata_columns, columns)
        self.assertEqual(meta_data, data)
        self.assertEqual(len(types), len(columns))
        key_col, geom_col = columns.index('cokey'), columns.index('geomdesc')
        self.assertEqual(len(data), 26)
        self.assertEqual({row[geom_col] for row in data}, {''})

        xml = ElementTree.fromstring(self.body('statsgo2-vi-xml'))
        cells = {row.findtext('cokey'): row.find('geomdesc') for row in xml.findall('Table')}
        self.assertEqual(set(cells), {row[key_col] for row in data})
        for cell in cells.values():
            self.assertIsNotNone(cell)
            self.assertIsNone(cell.text)

        archive = json.loads((ROOT / 'artifacts/assessment/statsgo2-vi.json').read_bytes())
        query = next(q for q in archive['query_examples']['queries']
                     if q['id'] == 'statsgo2_fetch_components')
        self.assertEqual(query['columns'], columns)
        self.assertEqual({row[key_col] for row in query['rows']}, set(cells))
        self.assertEqual({row[geom_col] for row in query['rows']}, {None})

    def test_ssurgo_legacy_xml_contains_five_components(self):
        xml = ElementTree.fromstring(self.body('ssurgo-gu-xml'))
        self.assertEqual(xml.tag, 'NewDataSet')
        rows = xml.findall('Table')
        self.assertEqual(len(rows), 5)
        self.assertEqual({row.findtext('mukey') for row in rows}, {'465534'})
