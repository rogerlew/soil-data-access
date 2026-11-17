"""Verify retained assessment evidence; --require-live fails while M1 is incomplete."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root, require_live=False):
    matrix = json.loads((root / "contracts/compatibility.json").read_text())
    if matrix["runtime_implemented"]:
        raise ValueError("This assessment receipt cannot attest runtime implementation")
    for source in matrix["sources"]:
        if not (root / source).is_file():
            raise ValueError(f"Missing evidence: {source}")
    for label in ("ssurgo-gu", "statsgo2-vi"):
        report = json.loads((root / f"artifacts/assessment/{label}.json").read_text())
        examples = report["query_examples"]
        if examples["evidence_kind"] != "official_download_query_results_not_sda_wire_fixture":
            raise ValueError("Download results must not be mislabeled as SDA wire fixtures")
        if len(examples["queries"]) != 5 or any(report["orphan_counts"].values()):
            raise ValueError("Source audit is incomplete or has orphaned keys")
        for query in examples["queries"]:
            if any(len(row) != len(query["columns"]) for row in query["rows"]):
                raise ValueError("Query row width differs from selected columns")
    observations_path = root / "artifacts/assessment/sda-capture-01/observations.json"
    observations = json.loads(observations_path.read_text())
    for observation in observations:
        if "body_file" in observation:
            payload = (observations_path.parent / observation["body_file"]).read_bytes()
            if hashlib.sha256(payload).hexdigest() != observation["body_sha256"]:
                raise ValueError("Captured body checksum mismatch")
        if observation.get("status", 500) >= 500 and "not_parity_fixture" not in observation["classification"]:
            raise ValueError("Availability failure mislabeled as parity")
    corpus = json.loads((root / "contracts/parser-corpus.json").read_text())
    ids = [case["id"] for case in corpus]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate parser case identifiers")
    for language in ("rust", "go"):
        results = json.loads((root / f"artifacts/assessment/{language}-parser-results.json").read_text())
        if [result["id"] for result in results] != ids:
            raise ValueError("Parser results are stale or incomplete")
        if any(not result["parsed"] for result in results if result["category"] == "core"):
            raise ValueError("Core consumer query not parsed")
    if require_live and matrix["blocking_gaps"]:
        raise ValueError("Milestone 1 remains incomplete: " + "; ".join(matrix["blocking_gaps"]))
    return "Offline evidence checks passed; live wire parity and full milestone acceptance remain unproven."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-live", action="store_true")
    args = parser.parse_args()
    try:
        print(verify(ROOT, args.require_live))
    except (ValueError, FileNotFoundError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
