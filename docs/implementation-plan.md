# Deliver a WEPPpy-compatible soil service during the SDA outage


This ExecPlan is living. Keep Progress, Surprises & Discoveries, Decision Log,
and Outcomes & Retrospective current. The normative rules are in docs/contract.md
and docs/wepppy-release-gate.md. The scope is faithful preservation of WEPPpy soil
behavior through a new database/API/JSON path; scaffolding is not acceptance.

The 2026-11-18 [mirror-first amendment](mirror-first-rollout.md) supersedes earlier
no-failover and comprehensive pre-rollout parity language in this plan. It provides
the next implementation sequence and acceptance scope.

## Purpose


Enable WEPPpy soil construction without contacting the unavailable USDA Soil Data
Access (SDA) service. The first release supports the five existing tabular query
families, with verified project-cache and generated-soil parity. It is a public,
unofficial, MIT-licensed service with Docker Compose support. Full SDA wire and
public-client compatibility are separate follow-up work, not initial deployment
prerequisites. Security, operational readiness, and actual output validation are
still deployment prerequisites.

## Progress

- [x] (2026-11-18) Incident recovery: national SSURGO and STATSGO2 active on forest; 22,073,263 imported rows; staged/HTTP parity for both datasets; cavernous-oxygen rebuilt with 32 verified prepared soils; 152 canary inputs match references. See docs/nationwide-recovery-plan.md and artifacts/national.


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
- [x] (2026-11-18 UTC) Capture allowlisted paired-project configuration and actual treatment lookup.
- [x] (2026-11-18 UTC) Repeat pinned offline reference builds: 499 valid soils, six non-valid outcomes, 501 matching canonical artifacts.
- [x] (2026-11-18 UTC) Freeze authored JSON profile, eleven legacy extraction cases, reference schema, and comparison rules.
- [ ] Complete workflow coverage: fallback/assignment execution, treatment variants, and full historical/native lineage gaps.
- [x] (2026-11-18 UTC) Implement Rust/PostgreSQL/PostGIS local runtime and test-only cache replay adapter.
- [x] (2026-11-18 UTC) Validate committed 9dc2264 in fresh Compose: 24,049 cache records, eleven wire cases, containment and lifecycle checks.
- [x] (2026-11-18 UTC) Wire explicit WEPPpy JSON transport/provenance; real-service fresh-cache replay matches 501 canonical artifacts in the reference numerical environment.
- [x] Load broader source data; validate import mechanics and bounded independent projections.
- [x] Implement mirror-first deployment defaults, bounded SDA fallback and selection provenance.
- [x] Run focused forest worker, bounded performance and runtime recovery acceptance in Compose.
- [x] (2026-11-20 UTC) Compare live SDA and the pinned mirror across five query families for eight SSURGO and four STATSGO2 map units. See [live assessment](live-sda-parity.md).
- [x] (2026-11-20 UTC) Verify prepared soil inputs for two selected SSURGO fragment ties and one restriction control. All 228 model-input payloads match.
- [x] (2026-11-20 UTC) Verify a paired live SDA and mirror multi-OFE prescribed-fire canary across 68 hillslopes and 240 segments. Read back treatment on the same 93 segments and compare prepared soil and management inputs.
- [ ] Extend geographic coverage and assess other treatment workflows.
- [x] (2026-11-20 UTC) Verify live cold USDA fallback and fresh mirror recovery on the forest normal queue. Both phases match the reference base soil and all 76 prepared inputs.
- [x] (2026-11-20 UTC) Measure [paired forest client latency](sda-performance-benchmark.md) for 11 JSON workloads and cold/warm WEPPpy acquisitions.
- [x] Start new soil API/database services in forest dev Compose.
- [x] Integrate protected Compose change and activate shared forest client defaults; four normal-queue canary jobs pass.
- [ ] Later scope: forest1 and production activation.
- [x] (2026-11-20 UTC) Retain reviewed SDA success, empty, error, null/decimal, metadata and XML observations.
- [ ] Deferred: establish full SDA/public-client/spatial compatibility before claiming it.

## Context and Orientation


The service repository is /workdir/soil-data-access. It currently contains contracts,
source audits, offline references, the Rust runtime in src/, migrations/001_replay.sql,
a test-only cache adapter, and compose.yaml. No production importer exists. The original query inventory is
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

The recovered SDA service uses an empty string for some component `geomdesc`
values stored as null in the mirror. Both paths yield null in the WEPPpy cache.
For two SSURGO keys, the raw rows agree and incomplete ordering yields different
first rows in the cache. The sampled base model-input lines are identical. The
prepared follow-up found two more fragment selection differences on the first
exported horizon. Both cases produced identical prepared model-input lines.

The development-image paired build failed two base diagnostic-comment values by
about 2e-15; Python/libc/Rosetta differ from the frozen reference. Retain the failure.
Matched read-only numerical-environment mounts restore exact canonical artifacts;
this is not deployment-image equivalence.



All five complete cache cases reconstruct consistent muaggatt attributes and match
API results after SQLite cache affinities. Immediate disconnect cancellation is not
proven: PostgreSQL statement_timeout bounded the observed cleanup to about five
seconds. Docker internal-only networking suppressed localhost port publishing, so
the API uses an HTTP bridge and an internal database bridge; upstream confinement
for the future WEPPpy build remains open. See docs/runtime-security-review.md.

The offline reference repeats exactly after the two declared metadata exclusions.
The paired historical base soil predates the October 200 mm writer boundary change;
its treated and model-input artifacts already contain that boundary and match.
One legacy builder exception comes from null sand combined with high clay; five
other keys lack valid horizons. The shared STATSGO cache lacks restriction coverage
for COKEY 14179042 and cannot be a complete reference. No missing row was invented.
Details and dispositions are in docs/reference-deviations.md.

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

2026-11-20 UTC: Use matching USDA survey versions and timestamps for this bounded
comparison. Retain the observed duplicate order and cache selections for review.
Keep the mirror profile and source precision intact. Retain the three prepared
cases as bounded evidence and preserve current selection semantics because
the observed differences did not alter prepared model-input lines. The prescribed-fire
canary uses frozen spatial inputs so the comparison isolates tabular source
behavior. Keep scratch-directory comments visible in the byte-level report.

2026-11-18 operator correction: nationwide SSURGO AND STATSGO2 are required for the shared default. Regional-only activation did not meet the intended outage-recovery requirement. Full live SDA parity remains deferred; nationwide data loading does not. See docs/nationwide-recovery-plan.md for execution and project migration.

2026-11-18: the operator accepts fixture generalization for the five query families
and directs mirror-first deployment defaults with SDA fallback. Move comprehensive
geographic/live parity to post-recovery follow-up; preserve import integrity and
source-separated provenance. The next work is implementation, not more nationwide
pre-rollout fixture collection.


2026-11-18: preserve the fixed comparison exclusions. Use explicit persisted
endpoint/profile/release with cache-bound identity and sidecars to meet the operator
provenance request. Keep deployment-image parity separate from matched-environment
transport parity; never widen tolerances to conceal environment differences.



2026-11-18 UTC: implement the bounded runtime under docs/runtime-contract.md.
Use exact parsed query shapes and owned parameterized statements, per-request
connections with bounded concurrency, and separate replay releases. Add explicit
WEPPPY_CACHE_REPLAY metadata instead of claiming official source lineage. Replay
ordinals preserve cached tie order only; production ordering remains unproved.

2026-11-18 UTC: pin the observed production checkout revision for the legacy
reference, with networking blocked by a Linux network namespace. Preserve only
Build Date and Source File comment-value exclusions; repeatability compares all
remaining bytes. Use authored profiles for unpaired caches, actual captured values
for the paired forest case, and keep historical unknowns explicit. Preserve the
known 200 mm change and invalid/error outcomes instead of changing model defaults
or historical fixtures. The JSON contract is service-owned, not live SDA evidence.

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
candidate; Rust selected from pinned syntax/dependency evidence. Runtime dependencies are
pinned in Cargo.lock and docs/runtime-dependencies.md; capacity targets remain open.

## Milestone 1: Freeze the project corpus and WEPPpy contract


scripts/snapshot_project_corpus.py now acquires private read-only-source backups;
scripts/publish_cache_fixture.py publishes clean logical copies against
contracts/wepppy-cache-schema.json; scripts/verify_corpus.py verifies their hashes,
records, and integrity. See docs/wepppy-corpus.md for commands. The reference schema is now contracts/wepppy-corpus.schema.json; the paired project
has captured scientific configuration/assignments and an actual treatment CSV.
The complete workflow corpus remains open; see docs/offline-reference-contract.md
for the frozen reference subset, commands, and retained deviations.
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
    python3 scripts/verify_runtime_evidence.py
    cargo test --locked
    cargo clippy --locked --all-targets -- -D warnings

The first two verify tests and retained assessment evidence. The --require-live
command remains an optional full-SDA evidence check and currently exits 1; it must not gate the initial WEPPpy
release. Parser probes remain reproducible with cargo run --locked using
evaluation/rust/Cargo.toml and go run from evaluation/go as documented in the
assessment. The corpus verifier checks committed snapshot bytes and logical content; it does
not validate rebuilt soils or runtime acceptance.

The offline reference and local runtime are implemented. Execute the local Compose
commands in README.md, then scripts/verify_runtime.py against a new isolated database.
It checks all complete fixtures and authored cases, privilege denial, overload,
statement timeout cleanup, release consistency, response bounds and restart. Next,
wire the actual WEPPpy client and complete the missing workflow coverage. Before creating candidate caches,
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

2026-11-20 UTC: Twelve sampled map units had the same validity decisions across
legacy SDA, bounded SDA XML and mirror JSON. All eleven valid mirror base soils
matched the legacy model-input lines, with a restriction diagnostic difference
for one soil. The targeted NoDb follow-up verified 228 prepared file pairs
for three SSURGO cases. The bedrock diagnostic carried through the control
case. Full live compatibility and broader prepared-run parity remain open.
The paired prescribed-fire canary matched prepared model inputs at both stages
across 68 hillslopes, with the same treatment effects on 93 segments. See
[live assessment](live-sda-parity.md#prescribed-fire-multi-ofe-canary).
The forest canary also verified live USDA retrieval after a project-only
connection refusal and fresh mirror selection after restoring the endpoint.
See [forest validation](forest-validation.md#cold-live-sda-failover-and-mirror-recovery).

The rollout policy is revised; no runtime default changed in this documentation
checkpoint. Next implement the mirror-first contract, broader importer and Compose
wiring, then execute forest -> forest1 -> wepp.cloud bounded acceptance.


WEPPpy 39f24ce92 with runtime 9dc2264 passes the bounded fresh-cache replay:
24,049 positive records, 34 successful HTTP fetch events, 499 valid soils, six
non-valid outcomes, 501 canonical artifacts and 499 verified base sidecars.
The incomplete case remains excluded. See artifacts/wepppy-parity/json-client/validation.json.
No production import, full workflow coverage, capacity, or deployment gate is claimed.



Six cache fixtures are acquired and stored through Git LFS: three initial
SSURGO-labeled project caches, a fourth project cache containing confirmed STATSGO
catalog keys, one empty STATSGO-labeled project cache, and the positive shared
STATSGO cache. Three paired historical soil files for the fourth project include
an actual WEPP model input. Publication strips only the private project path in
two Source File comments; numeric/model payload bytes remain exact.

The earlier snapshot validation is retained in snapshot-validation.json. The new
reference repeats 499 valid soils plus two paired downstream files, with five
invalid-horizon outcomes and one legacy builder error retained. Twenty-seven tests
cover acquisition, canonicalization, missing cache coverage, report/archive
integrity, and transport shapes. Eleven authored synthetic XML cases passed through
the actual pinned legacy extractors. Canonical output is in the LFS archive
fixtures/wepppy/reference-v1.tar.gz; reports retain selections, hashes, environment,
coverage, and separate historical comparisons. See docs/reference-deviations.md.
A fresh remote clone retrieved all LFS objects and passed fixture/archive checks
and all 27 tests at d991fec; reference-validation.json retains the verification
receipt. This verifies published artifact integrity, not another numerical replay.

The bounded Rust/PostgreSQL service and test-only cache replay now execute all
five families through local Compose. Each complete fixture matches independent
SQLite records; eleven authored cases preserve raw rows and exact wire values.
The exact runtime receipt is artifacts/runtime/compose-validation.json at code
9dc2264; it pins both image IDs, source hashes, fixture hashes, database version and
request traces. An evidence checker rejects stale source, missing cases and failed
controls. Thirty-three Python tests and two Rust test groups pass; Clippy and docs
lint are clean. Disconnect cleanup in the final run was 5.08 seconds, consistent
with the explicit timeout limitation. These checks do not close milestone 2: the
actual WEPPpy client and generated-soil path are still unwired.
The WEPPpy JSON client and bounded fresh-cache replay are implemented; complete workflow coverage and official import remain next. This reference is a useful baseline, not full NoDb/RQ/raster execution or
mirror parity. Only one captured forest treatment profile is paired downstream;
other treatment/fallback/assignment behaviors still need evidence or explicit scope
exclusion before release. Historical commit/native lineage remains unknown. No production importer, migrated
WEPPpy client, full Compose workflow acceptance, or deployment exists.
The source caches, historical files, and WEPPpy production behavior remain intact.

## Artifacts and Dependencies


Historical observations remain under artifacts/assessment and can be read at commit
d311ddb. New cache/soil evidence belongs under artifacts/wepppy-parity, with large
or sensitive acquisitions in ignored data/parity. Operator-authorized clean cache
fixtures are stored in Git LFS under fixtures/wepppy with adjacent manifests. Rust
is the implementation language; versions and licenses are retained under artifacts/runtime.
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

Revision: 2026-11-18 UTC. Retain two offline reference runs and authored JSON
contracts; document historical drift, incomplete cache, and workflow coverage gaps.

Revision: 2026-11-18 UTC. Implement bounded local Rust/PostgreSQL replay, preserve
explicit metadata provenance, and keep client/workflow/public gates open.

Revision: 2026-11-18 UTC. WEPPpy 39f24ce92 implements explicit JSON selection,
source-bound caches, atomic retrieval events and base-soil provenance sidecars.
Retain real-service parity and the initial development-image numerical mismatch
in artifacts/wepppy-parity/json-client; no expanded comment exclusions.

Revision: 2026-11-18 UTC. Adopt operator-approved mirror-first/SDA-fallback direction
and defer comprehensive geographic/live parity; see mirror-first-rollout.md.

## Forest implementation scope in progress

Execute docs/official-import-contract.md for Idaho SSURGO plus Virgin Islands
STATSGO2, then wire the explicit release into a forest-only Compose integration.
The files are official source downloads, not corpus replay. Use the existing six-table
serving schema and transactional COPY, an independent projection reader and actual
queued fresh-cache builds. No new runtime database driver/dependency is required:
Python stdlib reads sources, psql loads PostgreSQL, and existing Rust serves queries.
Client contract checkpoint lives in WEPPpy at 43c78bf95; its source-selection factory
must pass real fallback/deadline/provenance tests before dev activation.

Progress: official import and independent raw projections pass; forest soil services
are healthy. Real queued SSURGO/STATSGO2 builds pass exact base/prepared parity through
primary cold/warm and warm fallback; dual failure leaves no generated soils.
See docs/forest-validation.md and artifacts/forest.

Surprises & Discoveries: ANALYZE after COPY is necessary before relational joins.
Canceling the first slow validation preserved the active release. Initial queued
comparison used an incorrect whitespace-sensitive comment filter; the final runs use
the frozen canonicalizer with only Build Date/Source File value exclusions.

Decision Log: serving data is explicitly regional; comprehensive geographic/live
parity remains deferred. WEPPpy dev Compose owns forest wiring; public hosting and
production activation remain separate. Exact source approval is required for the
protected WEPPpy Compose diff before changing shared-client defaults.

Outcomes & Retrospective: local operational and bounded scientific gates pass.
The service is usable on forest's internal Compose network; no public/national
deployment or shared-client default activation is claimed.

Final operational discovery: socket-only pg_isready can briefly succeed against
PostgreSQL's initialization server. Both portable and forest soil-DB probes now use
TCP localhost, which becomes available after initialization. Restart/readiness
and the fresh runtime suite pass; no existing shared PostgreSQL service was changed.

Forest activation is complete: operator-approved WEPPpy PR #675 is merged; all five
shared consumers have mirror-first settings. Four normal-queue RQ jobs validate both
datasets and 152 exact-reference prepared soils. Source/configuration backups and
unrelated shared work are preserved. See artifacts/forest/activation for receipts.
