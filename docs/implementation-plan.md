# Deliver a WEPPpy-compatible soil service during the SDA outage


This ExecPlan is living. Keep Progress, Surprises & Discoveries, Decision Log,
and Outcomes & Retrospective current. The normative rules are in docs/contract.md
and docs/wepppy-release-gate.md. The scope is faithful preservation of WEPPpy soil
behavior through a new database/API/JSON path; scaffolding is not acceptance.

## Purpose


Enable WEPPpy soil construction without contacting the unavailable USDA Soil Data
Access (SDA) service. The first release supports the five existing tabular query
families, with verified project-cache and generated-soil parity. It is a public,
unofficial, MIT-licensed service with Docker Compose support. Full SDA wire and
public-client compatibility are separate follow-up work, not initial deployment
prerequisites. Security, operational readiness, and actual output validation are
still deployment prerequisites.

## Progress


- [x] Inspect current WEPPpy requests and infrastructure ownership.
- [x] Publish scaffold, initial contracts, and extracted query inventory.
- [x] Audit official SSURGO Guam and STATSGO2 Virgin Islands samples.
- [x] Retain SDA 502 observations and source/probe evidence.
- [x] Evaluate Rust/Go parsers and dependencies; recommend Rust.
- [x] (2026-11-17) Record operator-approved WEPPpy-first acceptance and deferred SDA parity.
- [x] (2026-11-18 UTC) Bounded read-only discovery on wepp1: 35 SSURGO cache candidates.
- [x] (2026-11-18 UTC) Acquire and validate three selected SSURGO cache snapshots.
- [x] (2026-11-18 UTC) Implement WAL-aware acquisition, clean logical reconstruction, and LFS fixture verification.
- [x] (2026-11-18 UTC) Find positive STATSGO model inputs through an SSURGO-named project cache; retain paired artifacts and shared STATSGO cache.
- [ ] Complete coverage-directed discovery, configuration/assignment lineage, and offline reference rebuild.
- [ ] Freeze corpus manifest, reference build, JSON profile, and comparison rules.
- [ ] Implement Rust/PostgreSQL/PostGIS service and test-only cache replay adapter.
- [ ] Wire WEPPpy JSON transport and verify empty-cache offline execution.
- [ ] Verify official-data import independently from historical cache replay.
- [ ] Prove corpus parity, release coverage, capacity, security, and recovery in Compose.
- [ ] Prepare and execute authorized environment-specific deployment.
- [ ] Deferred: capture live SDA success/empty/error/XML fixtures after recovery.
- [ ] Deferred: establish full SDA/public-client/spatial compatibility before claiming it.

## Context and Orientation


The service repository is /workdir/soil-data-access. It currently contains contracts,
source audit scripts, parser probes, and offline tests, but no server, production
importer, or Compose stack. The original query inventory is
contracts/wepppy-queries.json; contracts/compatibility.json records supported-scope
intent and evidence status. Existing audit observations remain immutable in
artifacts/assessment; they are not proof that a release is ready.

WEPPpy source is /workdir/wepppy/wepppy/soils/ssurgo/ssurgo.py. SurgoSoilCollection
reads project-local soils/ssurgo_tabular_cache.sqlite or
soils/statsgo_tabular_cache.sqlite and fetches missing records. Read-only discovery
on wepp1 uses host /geodata/wc1/runs/ (container /wc1/runs/); see
docs/wepp1-cache-discovery.md and ignored data/parity/discovery/ for candidates.
Consult WEPPpy's nearest AGENTS
and tests before its eventual implementation edits; use a separate task worktree.
The current working tree contains unrelated work and is not a fixture sandbox.

A project cache stores processed records, not raw SDA tables/responses. Its
component records include muaggatt attributes; existing extraction removes some
duplicate records. An oracle is the frozen reference result used for comparison.
PostGIS adds spatial types/operations to PostgreSQL. Neither adopting PostGIS nor
parsing a spatial query makes spatial API compatibility part of the first release.
Environment-specific host/routing/storage ownership is /workdir/open-wepp-org,
which manages Talos/Kubernetes; do not assume those nodes run Docker Compose.

## Surprises & Discoveries


SDA remains unavailable in retained observations. Independent official downloads
are reachable. The national SSURGO archive is listed at 31,549,528,132 compressed
bytes; the inspected STATSGO2 archive is dated 2016. Sample contents do not prove
national coverage or equivalence to current SDA.

WEPPpy currently uses form-urlencoded POST with XML. It can migrate to JSON while
retaining soil behavior. The source audit found ambiguous ORDER BY mukey in the
component join and integer-versus-text key storage differences. These require
explicit resolution and tests. Rust sqlparser parsed all tested candidate syntax;
GoSQLX rejected the spatial intersection example. Neither parser enforces safety.

Project caches preserve useful historical reference data but lose some upstream
row multiplicity/order. Cache replay alone therefore cannot establish raw import
correctness, live wire parity, or duplicate-selection behavior on unseen raw data.

The wepp1 discovery found 35 SSURGO caches in bounded samples, with generated
model inputs for 28 of the first 31. Thirty of those caches had WAL files and
4 KiB database files. Sidecars suggest useful negative-record coverage, but cannot
prove completeness. The explicit STATSGO-named cache found by follow-up discovery was empty.
However, catalog-key searches found two projects with STATSGO map-unit/component
IDs in actual WEPP soil inputs under the SSURGO cache path. One is retained as
ssurgo-004 with base, treated, and model-input files. The shared STATSGO cache is
retained as statsgo-002. Both upstream query paths share helpers and have no
dataset predicate; gNATSGO combines source families. Cache labels are not provenance. See docs/wepp1-cache-discovery.md for the initial evidence
and docs/wepppy-corpus.md for the snapshot follow-up.

Historical negative-key tables lack primary keys. Preserve their duplicates and
rowids rather than coercing them to the initialized schema. The first read-only
SQLite open appears to have created empty sidecars for a WAL-mode database that
had none; the collector now rejects that condition before opening SQLite. See
docs/corpus-snapshot-contract.md for the incident and regression coverage.

## Decision Log


2026-11-18 UTC: the operator clarified that gNATSGO and the shared SDA queries
cover both source families. Code, NRCS documentation, and project artifacts confirm
that STATSGO MUKEYs can use the default SSURGO cache path. Preserve the unified
key-query contract and classify source coverage using independent catalog/release
evidence, never filenames or collection labels.

2026-11-18 UTC: the operator explicitly authorized committing selected sanitized
cache snapshots through Git LFS. This supersedes the blanket data exclusion only
for fixtures/wepppy/. Keep source mappings, raw backups, and project configuration
private; rebuild public SQLite files to remove unused/deleted pages while proving
exact logical equality. Cache fixtures alone cannot close corpus/reference parity.

2026-11-18 UTC: the operator selected wepp1 for read-only discovery. Retain private
candidate paths locally and publish only aggregate evidence. Bound production
metadata scans; freeze snapshots before inspecting database contents or claiming
coverage. This avoids treating an expensive full-tree scan as a prerequisite.

2026-11-17, operator-approved: replace live SDA availability as an initial release
gate with WEPPpy cache/soil parity. The extended outage makes waiting for live wire
fixtures unnecessary for a narrowly claimed WEPPpy deployment. The prior decision
to hold milestone 1 for upstream recovery is superseded. Full SDA validation remains
tracked; no existing security, recovery, or end-to-end gate is waived.

2026-11-17: use two independent evidence paths. Historical cache replay isolates
software/transport changes. Official-download validation checks import correctness
and source-release differences. Treating a processed cache as a raw national source,
or forcing new source values to match old files, was rejected as circular testing.

2026-11-17: freeze an explicitly service-owned JSON profile offline, informed by
existing client behavior. It may use the SDA-style path and format token but must
not claim observed SDA wire equivalence. Preserve the current upstream XML path
for existing configurations; select the new JSON service explicitly and namespace
new caches by endpoint profile and source release.

Earlier decisions retained: MIT license; separate service repository and
open-wepp-org infrastructure ownership; Docker Compose support; PostgreSQL/PostGIS
candidate; Rust recommended from pinned syntax/dependency evidence. Full runtime
dependency selection and numerical capacity targets remain to be completed.

## Milestone 1: Freeze the project corpus and WEPPpy contract


scripts/snapshot_project_corpus.py now acquires private read-only-source backups;
scripts/publish_cache_fixture.py publishes clean logical copies against
contracts/wepppy-cache-schema.json; scripts/verify_corpus.py verifies their hashes,
records, and integrity. See docs/wepppy-corpus.md for commands. The broader
contracts/wepppy-corpus.schema.json and configuration/artifact capture remain to
be defined before freezing the complete replay corpus.
Inventory cache-bearing runs read-only; select SSURGO and STATSGO2 plus restrictive
layers, shallow profiles, multiple components/horizons/textures/fragments, null and
missing fields, invalid soils, missing keys, fallback behavior, and relevant burn
or treatment variants. Record a coverage matrix rather than an arbitrary project
count. Uncovered supported behavior blocks acceptance or must be excluded from the
release scope before implementation, not silently skipped.

Use SQLite's backup API to create consistent snapshots, including committed WAL
content; never copy a live .sqlite file alone or checkpoint/mutate the source.
Check snapshot integrity and record input hashes, schema, row counts, provenance
sidecars, source vintage (explicitly unknown where absent), model/configuration,
reference code/native-library versions, negative-cache markers, completeness, and
selected/generated artifact hashes.
Store private acquisitions and working copies in ignored data/parity. Store
reviewed cache fixtures through LFS under fixtures/wepppy, with adjacent manifests;
retain aggregate operational evidence under artifacts/wepppy-parity. Do not publish
entire project directories or private paths.

Implement the reference runner in scripts/run_wepppy_parity.py. Regenerate soils
from snapshot copies with pinned WEPPpy/configuration and remote fetching disabled.
Use existing project .sol files as an additional historical check, not an assumed
current-code oracle. Classify historical mismatches by code/configuration/source
lineage; exclude incomplete caches from the complete replay set and retain them
as explicit missing-data cases. Do not refill reference snapshots through the mirror.

Before implementing transport, define contracts/wepppy-json.schema.json and authored
fixtures for success, empty results, nulls, decimals, identifier normalization,
column order, errors, and duplicate handling. Keep the five query families as the
first supported SQL scope. Define numeric precision and selection/tie behavior from
the pinned reference; do not invent an ordering rule to make a test pass. For raw
row cases that caches cannot represent, run independently authored or download-
derived rows through the unchanged legacy extraction logic and the new JSON path;
label synthetic XML honestly. Live XML is not required for those offline tests.

Acceptance: the reference rebuild is reproducible with USDA unavailable; corpus
coverage and deviations are explicit; authored schemas/fixtures can be checked
offline. Milestone 1 does not require a recovered SDA endpoint.

## Milestone 2: Implement and wire the bounded service


Use the Rust recommendation, finishing dependency/license/security evaluation for
the complete HTTP/database stack before adoption. Create src/, importer tools,
schema migrations, Dockerfile, and compose.yaml with pinned versions. Parse only
the agreed grammar, resolve schema names/types, bind literals, and emit PostgreSQL
SQL from an owned query representation. Reject unsupported SQL and functions.
Implement the service-owned JSON, metadata, and error profiles first. Keep import
credentials separate from the read-only serving role. No unrestricted passthrough,
queue, cache daemon, or SQL Server emulator is included.

Add a clearly test-only cache-to-PostgreSQL adapter. Explicitly map the processed
component/muaggatt projection; reject inconsistent repeated attributes instead of
inventing source rows. Record all reconstruction assumptions. Exercise the real
server and database, not a mock of _fetch_* or a fake HTTP response. This replay
adapter is not the production importer and cannot certify production source data.

In a WEPPpy task worktree, add explicit endpoint/profile selection and JSON parsing
without changing model formulas, defaults, or existing upstream XML behavior.
Specify a backward-compatible cache provenance/isolation design before editing
persistence: retain original project caches and create candidate caches separately.
Never silently merge historical and candidate releases or automatically fail over
between endpoints. Add focused consumer and downstream regression tests following
WEPPpy's own contract-first and artifact standards.

Acceptance: a candidate rebuild with an empty cache reaches the real Compose API,
queries PostgreSQL, populates a new cache, and produces the reference soil outputs
with USDA blocked. Retain request counts/traces demonstrating that the API was used.
Check parsed records, cache contents, selection decisions, invalid/fallback results,
.sol artifacts, assignments/summaries, and actual soil inputs in wepp/runs/.
Implemented API code without that wired run cannot close this milestone.

## Milestone 3: Validate the official release and operational gates


Import official source downloads through the production importer. Validate hashes,
all required columns, keys/relationships, units/nulls/precision, and advertised
coverage independently of the cache replay adapter. For matched raw inputs, compare
results against a direct source reference outside the Rust importer/translator.
If source vintages differ from historical caches, record field-level differences
and their effects on soil outputs. Known dataset changes are not automatically
software defects; they still need explicit release disposition. Unexplained
model-affecting differences block release. Do not patch new source data to match
old cached values or bless differences merely because timestamps differ.

Serve only the declared validated coverage. Measure the intended release's actual
storage, indexes, staging space, and key coverage; a national availability claim
requires national evidence, not the Guam/Virgin Islands samples. Identify workflows
that still require upstream spatial services; either prove their local path or
exclude them from the initial supported workflow list.

Define numerical load targets and resource budgets before measurements. Validate
representative batches and concurrent builds, including latency percentiles,
throughput, errors, CPU, memory, I/O, deadlines, and cancellation recovery. Test
unsupported/malicious queries, privilege boundaries, overload, server restart,
failed/interrupted import, one-release-per-request activation, and rollback.
Run acceptance under actual intended identities, mounts, permissions, and Compose
configuration. Retain a dedicated security review; unresolved high findings block
public deployment. Full SDA parity does not replace or waive these gates.

Acceptance: docs/wepppy-release-gate.md is satisfied with evidence tied to the
candidate code/image/data/configuration. Do not repurpose verify_assessment.py's
offline evidence check into a deployment approval; add a release evidence validator
when actual runtime evidence exists and test its rejection of missing/stale evidence.

## Milestone 4: Deploy the bounded WEPPpy release


Create the environment work package in open-wepp-org. Identify the exact Compose-
capable host, storage, capacity, secret delivery, immutable image, hostname, TLS,
routing, monitoring, and rollback. Reconcile its roadmap/ADRs as required. Existing
Talos/WEPPcloud deployments remain intact. Start with an explicitly selected canary
workflow and retained old endpoint/profile/cache configuration. Verify fresh-cache
artifact parity and operational signals before widening the supported workflow set.

Acceptance permits the claim "validated for the published WEPPpy soil-building
workflows and source release." It does not permit "full SDA mirror" or general
soilDB/spatial compatibility. Planning authority is not authorization for an
unidentified live host, public route, or shared-database mutation; apply the
infrastructure repository's target verification and deployment handoffs.

## Milestone 5: Deferred SDA and broader-client compatibility


After SDA recovers, use scripts/capture_sda.py with a new output directory to
capture bounded success/empty/error/null/decimal and paired XML responses. Identify
source releases, compare actual wire semantics, and extend independent client and
spatial coverage. Keep discrepancies public in the compatibility matrix. Changes
to the released WEPPpy profile require versioned/additive evolution and its parity
suite. This milestone is not a prerequisite for the bounded first deployment and
must not be marked complete simply because WEPPpy passes.

## Concrete Steps and Validation


From /workdir/soil-data-access, current runnable checks are:

    python3 -m unittest discover -s tests -v
    python3 scripts/verify_assessment.py
    python3 scripts/verify_assessment.py --require-live
    git lfs pull
    python3 scripts/verify_corpus.py

The first two verify tests and retained assessment evidence. The --require-live
command remains an optional full-SDA evidence check and currently exits 1; it must not gate the initial WEPPpy
release. Parser probes remain reproducible with cargo run --locked using
evaluation/rust/Cargo.toml and go run from evaluation/go as documented in the
assessment. The corpus verifier checks committed snapshot bytes and logical content; it does
not validate rebuilt soils or runtime acceptance.

Initial cache discovery and snapshot tooling are implemented. Next, complete the
coverage matrix, capture configuration/artifact lineage, and build the reference. Before creating candidate caches,
record compatibility/regression expectations in the WEPPpy work package. As each
runner/CLI is implemented, add its exact invocation and retained output here;
proposed file paths above are not commands that already exist. Run WEPPpy tests
through its wctl wrappers against the actual candidate worktree/container checkout.
Run docker compose config --quiet and real Compose workflow tests before deployment.

## Validation and Acceptance


For matched inputs, require byte-identical model-consumed soil files and unchanged
assignments, component/invalid/fallback decisions, and cache semantics. Any excluded
non-model metadata must be named and justified before comparison; no blanket
rounding, tolerance, sorting, or comment removal may hide model changes. Where
ordering is not fully specified, prove selection stability or explicitly resolve
and approve the behavior before release. Source-release differences use a separate
reviewed ledger, not a relaxed software-parity threshold.

Every supported corpus case must pass. Tests must prove fresh candidate caches and
blocked upstream access, exercise the real database/API/consumer path, and inspect
final generated files. Missing evidence, stale revisions, failed comparisons,
undeclared coverage, or unresolved security/recovery failures prevent release.
No successful test, corpus, deployment, or full compatibility is inferred from
this planning revision.

## Idempotence and Recovery


Keep immutable source snapshots and manifests; use scratch working copies for
reference and candidate builds. Never clear or overwrite production caches.
Snapshot publication must be all-or-nothing and repeatable without modifying
original projects. Stage data imports separately from the active database and
retain the prior validated release/image pair. Rollback restores the prior
endpoint/profile and its separate cache; upstream being down is not a usable
recovery guarantee. Retain a tested prior local release once deployed. Do not
remove persistent volumes as routine cleanup.

## Outcomes & Retrospective


Six cache fixtures are acquired and stored through Git LFS: three initial
SSURGO-labeled project caches, a fourth project cache containing confirmed STATSGO
catalog keys, one empty STATSGO-labeled project cache, and the positive shared
STATSGO cache. Three paired historical soil files for the fourth project include
an actual WEPP model input. Publication strips only the private project path in
two Source File comments; numeric/model payload bytes remain exact.

Nineteen tests, fixture verification, documentation lint, and a fresh remote
LFS checkout passed; artifacts/wepppy-parity/snapshot-validation.json pins the
validated code and object hashes. Source fingerprints, logical comparisons,
integrity checks, and unknown historical
revision/configuration are explicit. Raw acquisition and private run mapping stay
outside Git. No reference soils have been rebuilt, no complete workflow corpus
frozen, no server implemented, and no deployment validated. Complete configuration,
assignment and native-library lineage, behavioral coverage, and the reference/JSON
contract next. The SQLite sidecar incident motivated a pre-open guard and regression
test; the snapshot contract records that filesystem effect. Collection/cache labels
cannot distinguish source families; the positive STATSGO evidence resolved the
misleading result of searching only STATSGO-named cache files.

## Artifacts and Dependencies


Historical observations remain under artifacts/assessment and can be read at commit
d311ddb. New cache/soil evidence belongs under artifacts/wepppy-parity, with large
or sensitive acquisitions in ignored data/parity. Operator-authorized clean cache
fixtures are stored in Git LFS under fixtures/wepppy with adjacent manifests. Rust
is the recommended implementation language; exact runtime versions await evaluation.
The code and documentation remain MIT-licensed; third-party data attribution is
separate. Initial complexity is one API, one PostgreSQL/PostGIS database, import
and validation tooling, and explicit WEPPpy client configuration.

Revision: 2026-11-17. Supersedes the upstream-availability milestone dependency with
operator-approved WEPPpy parity acceptance. Separates historical replay from source
import validation, preserves runtime/security gates, and defers broader SDA parity.

Revision: 2026-11-18 UTC. Record bounded wepp1 discovery, WAL observations, private
candidate evidence, and outstanding STATSGO/snapshot coverage without claiming parity.

Revision: 2026-11-18 UTC. Record operator-authorized LFS publication, implemented
snapshot tools, historical schema preservation, and the sidecar creation guard.

Revision: 2026-11-18 UTC. Retain positive STATSGO project model inputs and clarify
that unified SDA queries and gNATSGO coverage cross cache/collection labels.
