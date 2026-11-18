"""Capture bounded upstream responses, preserving outages separately from parity.

No retries or load generation. A 5xx or transport failure stops that endpoint.
Use --endpoint to restrict capture to one host. Default probes both official hosts.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ("https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest",
         "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest")
MAX_RESPONSE = 2 * 1024 * 1024  # Assessment capture bound, not a production API limit.


def classify(status, content_type):
    if status >= 500:
        return "upstream_unavailable_not_parity_fixture"
    if status >= 400:
        return "http_error_requires_contract_review"
    if "json" not in content_type.lower() and "xml" not in content_type.lower():
        return "unexpected_content_requires_review"
    return "candidate_wire_fixture_requires_release_and_semantic_review"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", choices=HOSTS, action="append")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Do not overwrite previous observations, even when upstream recovers.
    args.output.mkdir(parents=True, exist_ok=False)
    cases = json.loads((ROOT / "contracts/capture-cases.json").read_text())
    records = []
    for index, endpoint in enumerate(args.endpoint or HOSTS):
        for case in cases:
            body = urllib.parse.urlencode(case["form"]).encode()
            request = urllib.request.Request(endpoint, data=body, headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                "User-Agent": "soil-data-access-contract-assessment/0.1"})
            record = {"endpoint": endpoint, "case_id": case["id"], "form": case["form"],
                      "observed_at": datetime.now(timezone.utc).isoformat()}
            try:
                try:
                    response = urllib.request.urlopen(request, timeout=20)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    payload = response.read(MAX_RESPONSE + 1)
                    if len(payload) > MAX_RESPONSE:
                        raise ValueError("Capture response exceeded 2 MiB; nothing truncated into a fixture")
                    record.update(status=response.status, content_type=response.headers.get("Content-Type", ""))
                filename = f"host-{index}-{case['id']}.body"
                (args.output / filename).write_bytes(payload)
                record.update(body_file=filename, body_sha256=hashlib.sha256(payload).hexdigest(),
                              body_bytes=len(payload), classification=classify(record["status"], record["content_type"]))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                record.update(classification="transport_failure_not_parity_fixture", error=str(error))
            records.append(record)
            print(endpoint, case["id"], record.get("status"), record["classification"], flush=True)
            if record.get("status", 500) >= 500:
                break
    (args.output / "observations.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
