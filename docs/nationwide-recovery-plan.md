# Restore nationwide SSURGO and STATSGO2 coverage on forest

This active ExecPlan extends docs/implementation-plan.md. Maintain Progress,
Surprises & Discoveries, Decision Log, and Outcomes & Retrospective.

## Purpose

The shared forest default must serve nationwide SSURGO and STATSGO2 during the
USDA outage. Job 447e29eb-976d-43a5-84ed-2726bb3b15c8 for cavernous-oxygen failed:
the regional mirror returned zero components for its 22 Colorado keys and USDA
returned HTTP 5xx. Success requires a real queued rebuild and generated soil
artifacts, plus independent source/import checks for both national datasets.

## Progress

- [x] Diagnose both source failures and preserve existing project caches.
- [x] Start national SSURGO acquisition; acquire national STATSGO2.
- [ ] Validate archive integrity, provenance and geographic/key coverage.
- [ ] Prepare and validate the national import with the existing six-table schema.
- [ ] Coordinate active release, environment defaults and saved regional mirror pins.
- [ ] Rebuild cavernous-oxygen through RQ and validate base and prepared soil artifacts.
- [ ] Retain SSURGO/STATSGO2 direct-source parity, timings and operational evidence.

## Context

Source repository: /workdir/soil-data-access, task branch fix/nationwide-soil-coverage.
Shared forest runs the service as docker-soil-api-1 and database docker-soil-db-1.
WEPPpy consumers use /workdir/wepppy and its canonical wctl dev Compose stack.
Do not reset or overwrite unrelated shared checkout changes. Existing release is
forest-id-20261001-vi-20161013-v1. The API serves one active release; clients check
its immutable ID and fail on mismatched pins. Never relabel the old regional
release or reuse its negative caches as national data.

The national sources are the official USDA Box SSURGO October 1, 2026 archive
(file 2495234965465, 31,549,528,132 bytes) and STATSGO2 October 13, 2016 archive
(file 157053109886, 446,108,728 bytes). Downloads and SQL stay under ignored
data/national; sanitized receipts go under artifacts/national. Preserve vintage
differences; do not claim these snapshots equal current unavailable SDA.

## Plan of Work

Acquire both sources using the public shared download URLs, validate sizes and
archive integrity, and hash source files. Extract the SSURGO GeoPackage only;
the existing WEPPpy national raster supplies map-unit identifiers. Inspect source
catalogs and national STATSGO2 membership of Alaska/island keys. Supplement only
if actual missing official coverage is established.

Use scripts/import_official.py with a new immutable release ID, source URLs,
vintages and scopes. It validates source schema, parent relationships, disjoint
source identifiers, finite values, and emits transactional PostgreSQL COPY.
Use the soil_import role, never serving credentials. National-scale failures
must be diagnosed and minimally corrected with focused regression evidence.

Before shared mutation, retain the prior active pointer and source configuration,
and inventory saved projects pinned to the old mirror identity. Preserve unrelated
explicit USDA/custom sources. Use the canonical worker dequeue fence and wait for
active jobs before switching; if import staging and activation need separation,
make that explicit in the importer contract with a regression check. Coordinate
the active release, SOIL_DATA_RELEASE environment, API healthcheck and consumers.
Use Soils.configure_soil_data_source under its normal lock for identified old
regional mirror projects; retain prior settings for rollback and all old caches.

Queue build_soils_rq for cavernous-oxygen, then the ordinary soil preparation
job where watershed/landuse prerequisites exist. Validate sidecar hashes,
actual supplier/release, assignments and generated wepp/runs soil files.
Exercise positive national STATSGO2 keys and retain the existing Idaho/VI smoke.

## Validation and Acceptance

Run independent direct-source projections with scripts/verify_official.py against
the actual candidate API for both sources; include the failing project's keys.
Check count and relationship assertions from the actual PostgreSQL import.
Sample all five query families, not just the component query. Retain source
counts/catalog and national archive scope alongside hashes.

Require zero errors over 40 representative 100-map-unit component requests at
concurrency one and four, with p95 below two seconds and all requests below the
existing five-second database statement limit. Record resource usage and database
size. This is a bounded operational check, not exhaustive geographic parity.

Actual RQ success alone is insufficient: generated soil files must exist, be
nonempty, have valid supplier provenance at their canonical base artifacts, and
match independent source-derived results under existing canonical comparison
rules. Full live SDA validation remains deferred.

## Compatibility and Recovery

Only the dataset release and explicitly inventoried old mirror pins change.
Preserve field names, soil formulas, project IDs, caches and unrelated defaults.
Source-bound national caches get a new identity; do not delete old caches.
Retain the old database release. If activation fails, restore the active pointer,
environment and migrated project pins together, then resume workers. The old
regional release is partial recovery only; unavailable USDA is not a working
national rollback. Do not clear or resume a worker fence owned by another operation.

## Surprises & Discoveries

The default served only Idaho plus Virgin Islands. cavernous-oxygen requests 22
Colorado keys; its mirror cache contains zero components and 22 negative markers.
The national STATSGO2 archive contains 9,562 map units, including all eight keys
in the previously downloaded VI archive. Its catalog explicitly describes the
Alaska redevelopment; the earlier CONUS-only listing label is not reliable scope
evidence. Confirm remaining geographic evidence before declaring completeness.

## Decision Log

2026-11-18: The operator explicitly requires nationwide coverage with both SSURGO
and STATSGO. A Colorado-only patch is rejected because it repeats the deployment
scope failure. Use the existing importer and serving schema before considering
new infrastructure. Source-value and runtime parity checks remain bounded; no
location-by-location live SDA comparison is required.

## Outcomes & Retrospective

In progress. The regional default is still active while national data is prepared.
The failed project has not been rebuilt or modified yet.

Revision note: created after the operator corrected the regional deployment scope.
