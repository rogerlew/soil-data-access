# Forest regional release qualification

The forest API/database are running on WEPPpy's existing Compose network, using
runtime 9d09f7f and release forest-id-20261001-vi-20161013-v1. Shared web/workers
retain their existing client defaults until protected Compose integration approval.
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
