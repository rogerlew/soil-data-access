"""Offline checks for evidence integrity and false-completion prevention."""

import io
import json
import unittest
import zipfile

from scripts.audit_sources import identifier, zip_rows
from scripts.capture_sda import classify
from scripts.verify_assessment import ROOT, verify


class AssessmentTests(unittest.TestCase):
    def test_retained_evidence(self):
        self.assertIn("unproven", verify(ROOT))

    def test_deferred_sda_check_rejects_unproven_wire_parity(self):
        with self.assertRaisesRegex(ValueError, "Deferred SDA wire parity remains unproven"):
            verify(ROOT, require_live=True)

    def test_html_outage_is_not_parity(self):
        self.assertEqual(classify(502, "text/html"), "upstream_unavailable_not_parity_fixture")

    def test_html_success_still_needs_review(self):
        self.assertEqual(classify(200, "text/html"), "unexpected_content_requires_review")

    def test_success_is_only_a_candidate(self):
        self.assertIn("requires_release_and_semantic_review", classify(200, "application/json"))

    def test_http_error_not_claimed_as_known_contract(self):
        self.assertEqual(classify(400, "application/json"), "http_error_requires_contract_review")

    def test_quote_identifier(self):
        self.assertEqual(identifier('a"b'), '"a""b"')

    def test_legacy_windows_zip_paths_and_quoted_pipes(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("survey\\tabular\\mapunit.txt", '"a|b"|"42"\n')
        with zipfile.ZipFile(buffer) as archive:
            self.assertEqual(zip_rows(archive, "mapunit"), [["a|b", "42"]])

    def test_ambiguous_zip_table_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("first/tabular/mapunit.txt", "1")
            archive.writestr("second/tabular/mapunit.txt", "2")
        with zipfile.ZipFile(buffer) as archive:
            with self.assertRaisesRegex(ValueError, "Expected one"):
                zip_rows(archive, "mapunit")

    def test_source_queries_preserve_columns_and_multiple_rows_per_key(self):
        report = json.loads((ROOT / "artifacts/assessment/ssurgo-gu.json").read_text())
        queries = report["query_examples"]["queries"]
        component = next(q for q in queries if q["id"].endswith("_fetch_components"))
        self.assertEqual(component["columns"][:2], ["mukey", "cokey"])
        self.assertTrue(component["audit_adaptation"])
        self.assertNotEqual(component["sql"], component["audit_execution_sql"])
        textures = next(q for q in queries if q["id"].endswith("_fetch_chtexturegrp"))
        self.assertGreater(len(textures["rows"]), len({row[0] for row in textures["rows"]}))


if __name__ == "__main__":
    unittest.main()
