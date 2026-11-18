import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_runtime_evidence import ROOT, verify


class RuntimeEvidenceTests(unittest.TestCase):
    def test_retained_local_evidence(self):
        self.assertIn('release acceptance remain unproven', verify())

    def test_missing_stale_or_failed_evidence_rejected(self):
        path = ROOT / 'artifacts/runtime/compose-validation.json'
        original = Path.read_text
        for mutation in ('missing_case', 'stale_code', 'failed_cleanup', 'changed_trace'):
            receipt = json.loads(original(path))
            if mutation == 'missing_case':
                receipt['cases'].pop()
            elif mutation == 'stale_code':
                receipt['source_files']['src/main.rs'] = '0' * 64
            elif mutation == 'failed_cleanup':
                receipt['controls']['remaining_active_serving_queries'] = 1
            else:
                receipt['request_trace']['sha256'] = '0' * 64
            def read(target, *args, **kwargs):
                return json.dumps(receipt) if target == path else original(target, *args, **kwargs)
            with self.subTest(mutation=mutation), patch.object(Path, 'read_text', read), self.assertRaises(ValueError):
                verify()


if __name__ == '__main__':
    unittest.main()
