# Forest regional release qualification

The forest API/database are running on WEPPpy's existing Compose network, using
runtime 9d09f7f and release forest-id-20261001-vi-20161013-v1. Shared forest web/workers now use mirror-first defaults following protected Compose
integration approval.
No forest1, production or public hosting activation is included.

## Retained evidence

- artifacts/forest/import-and-readiness.json: official source manifests/hashes,
  imported counts, duplicate rollback, serving write denial and expected-release health.
- artifacts/forest/official-raw-parity.json: exact raw projection multisets from
  original Idaho GeoPackage and Virgin Islands STATSGO2 ZIP versus actual API.
  Covers 100 SSURGO and all eight selected STATSGO2 map units.
- artifacts/forest/queued-id-final.json and queued-vi-final.json: actual RQ jobs
  for unseen MUKEYs 78905 and 1390208, primary cold/warm, direct-file reference,
  warm fallback and explicit dual failure. All successful cases produce 76 prepared
  soils with exact canonical base/prepared parity.
- artifacts/forest/artifact-readback.json: independent base-sidecar hash and prepared
  file verification, supplier/binding agreement and no soils after failed jobs.
- artifacts/forest/query-timings.json: 80 warm requests for 100 MUKEYs/289 component
  rows; p95 40.8 ms at concurrency one and 48.6 ms at concurrency four on forest.
- artifacts/forest/validation.json: image, source-file and WEPPpy candidate hashes.
- artifacts/runtime/compose-validation.json: rebuilt service replay, malformed/large
  requests, read-only role, overload/timeout, active-release consistency, restart and
  response bounds. Historical runtime receipt remains in artifacts/runtime/archive.

No numeric tolerance or additional comment exclusion was introduced. Cold/warm
canonical hashes are retained per job; warm builds replace the same primary files.
The SDA fallback cache was independently seeded from official source files and
remains marked historical_rows_unknown=true. Controlled real TLS tests prove cold
XML fallback; these jobs do not claim successful live SDA retrievals.

## Reproduction and limits

scripts/import_official.py emits transactional COPY SQL and an import receipt.
scripts/verify_official.py compares original files independently of that importer.
scripts/forest_qualification.py runs the actual build_soils_rq and final soil-prep
path; scripts/verify_qualification.py reads the resulting artifacts.
scripts/measure_forest.py records bounded warm-query and queued-job timings.
The retained qualification Compose file uses a separate Redis/queue, actual worker
UID/GID and /wc1 mounts; SDA DNS failure is confined to that qualification worker.

Official source downloads and complete logs stay in ignored data directories.
Do not rerun qualification against an existing run tag or use the mutating replay
harness on the serving database. Keep existing volumes when stopping test stacks.
Broader data imports, comprehensive live SDA comparisons, raster assignment,
treatment variants and public capacity/hosting remain distinct follow-up work.

The retained publication snapshot is WEPPpy 09f6633e660c73570cc3f181bef75c6b49853ef3.
Queued builds preceded only the additive selection-sidecar cache-clear entry and
TCP database readiness refinement. Scientific acquisition/model paths are unchanged;
four real NoDb tests cover cache clearing, and the new forest database was restarted
with its release and API readiness preserved. A fresh runtime suite also validates
the final service source after the readiness-test Clippy correction.

## Completed forest activation

artifacts/forest/activation records exact operator approval, WEPPpy merge revision
0ae17ad8a393a4fbe250241b2253b77cc475d06b, runtime source hashes, consumer defaults
and four live RQ canary jobs. Normal-queue builds and soil preparation produced 152
exact-reference model inputs with verified base hashes and mirror provenance.
Existing explicit project choices and unrelated shared work are preserved; web,
RQ and soil services are healthy and dequeue is resumed. Earlier pending-approval
receipts are historical observations, superseded by this activation record.

## National release recovery, 2026-11-18 UTC

The regional release above is historical qualification. Forest now defaults to
forest-us-ssurgo-20261001-statsgo2-20161013-v1: national SSURGO October 2026 plus
national STATSGO2 October 2016. All 22,073,263 rows passed imported count and
relationship checks; independent source/PostgreSQL projections matched all five
query families for both datasets, including the failed Colorado project's keys.

cavernous-oxygen rebuilt through the normal queue without SDA fallback: 21 base
provenance hashes and the complete set of 32 prepared hillslope inputs passed
readback. National-release SSURGO and STATSGO2 canaries matched all 152 prepared
reference files. Eighty local HTTP component requests had zero errors and p95
below 47 ms. Authenticated homepage, profile and project requests returned 200.
See [national evidence](../artifacts/national/activation-receipt.json) and the
[recovery plan](nationwide-recovery-plan.md). Full live SDA parity remains deferred.

## Cold live SDA failover and mirror recovery

The recovery canary uses the national SSURGO single-soil reference for map unit
78905 and an empty project cache. It changes the primary endpoint only on the
disposable project to a closed local port. The normal queue builds soils and
prepares hillslope inputs. The test verifies the supplier through the artifact
sidecar, SQLite binding and retrieval history, and selection receipt.

The canary restores the project's primary to the current national mirror
endpoint with mirror-first selection. It then rebuilds and prepares soils
again. The restored mirror cache starts empty, while the separate USDA cache
remains populated. The second build must contact the mirror and select it on
its first attempt.

The November 20, 2026 UTC [failover receipt](../artifacts/forest/live-sda-failover.json)
records four successful normal-queue jobs. The connection refusal triggered a
cold live USDA XML retrieval with response hashes for all five tabular query
families. The failed primary cache contained zero components and no retrieval
rows. After restoration, the project retrieved fresh mirror JSON on its first
attempt and left the separate USDA cache logically identical.

Both phases matched the reference base soil and all 76 prepared hillslope
soils after the established volatile-comment exclusion. The USDA and archive
catalog records for the sampled survey also agree. This qualifies the
project-scoped connection-refusal case on forest against one SSURGO map unit.

To repeat, copy the comparison scripts into a forest worker environment and
run the following with a fresh tag. The runner creates a new canary directory
and submits the two build and two preparation jobs to the normal queue.

```bash
python scripts/run_forest_live_sda_failover.py coldcanary01
```
