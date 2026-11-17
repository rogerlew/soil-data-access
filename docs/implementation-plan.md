# Establish and implement an unofficial Soil Data Access service

This ExecPlan is living. Keep Progress, Surprises & Discoveries, Decision Log,
and Outcomes & Retrospective current. The normative behavior is docs/contract.md.

## Purpose

Enable existing soil clients to query independently hosted USDA data through a
measured, explicitly bounded compatible API during upstream outages. Deliver a
portable Docker Compose stack and an environment-specific open-wepp-org handoff.

## Progress

- [x] Inspect WEPPpy requests and open-wepp-org deployment boundaries.
- [x] Establish initial contract and extract five real query families.
- [x] Scaffold separate soil-data-access repository for operator-requested main publication.
- [ ] Confirm target deployment environment.
- [x] Audit official SSURGO Guam and STATSGO2 Virgin Islands downloads; retain schemas, hashes, keys, and ten query-family results.
- [x] Capture availability failures on both SDA hosts; each returned 502.
- [ ] Capture live success/empty/error fixtures and paired XML after SDA recovers.
- [x] Define compatibility matrix and service-owned metadata/error schemas.
- [ ] Freeze SDA wire response schemas and release-matched parity fixtures.
- [x] Run pinned Rust/Go parser probes and dependency scans; recommend Rust.
- [ ] Adopt and pin the complete runtime stack during milestone 2.
- [ ] Implement importer and bounded API using PostgreSQL/PostGIS.
- [ ] Validate Compose end-to-end, artifact parity, security, and performance.
- [ ] Prepare reviewed infrastructure integration and public-release handoff.

## Surprises & Discoveries

WEPPpy currently uses form-encoded POST and XML. The operator is open to migrating
it to JSON, so XML is an observed baseline rather than a mandatory first target. The open-wepp-org checkout is
an existing Talos/Kubernetes infrastructure repository. Docker Compose support
must not silently mutate that platform or assume Talos can host Docker.
The current national SSURGO archive is listed at 31,549,528,132 compressed bytes;
the official STATSGO2 download inspected is dated 2016. Neither a national listing
nor sample coverage establishes full SDA parity. SQLite rejects the component
query's unqualified ORDER BY mukey; the source audit records an explicit qualified
adaptation. GoSQLX 1.17.0 rejects the tested geometry::STGeomFromText intersection;
Rust sqlparser 0.64.0 parses it. Both parse unsafe constructs, so neither is an
admission-control boundary.

## Decision Log

2026-11-17: Recommend Rust after pinned probes (5/5 core queries for both;
13/13 candidate queries for Rust, 12/13 for Go). This is a suitability decision,
not a service-performance claim or blanket dependency approval. See
[dependency evaluation](dependency-evaluation.md).

2026-11-17: Keep milestone 1 open while upstream is unavailable. Download-derived
results are explicitly not wire fixtures. Continue bounded offline work; do not
invent null/error/empty-response semantics. Choose form-encoded JSON+COLUMNNAME
for WEPPpy and record soilDB's metadata format as a separate compatibility target.

2026-11-17: Operator selected MIT licensing and requested scaffold commit/push
to main. Include LICENSE and keep third-party data attribution separate.

2026-11-17: Prefer JSON-first integration with a coordinated WEPPpy migration,
following operator steering. Prove parser and generated-soil artifact parity;
evaluate XML separately for broader compatibility.

2026-11-17: Start with the contract and extracted consumer queries. The operator
explicitly requested contract-first work. Keep Rust/Go and exact dependency
versions undecided until compatibility and dependency evaluation are recorded.
Use /workdir/soil-data-access as a provisional separate service repository;
open-wepp-org owns eventual environment integration. No live target is selected.

## Context and Orientation

This repository initially contains documentation and contracts/wepppy-queries.json.
The latter was extracted without importing or executing WEPPpy module code.
Its synthetic keys exercise query construction only. Source code is at
/workdir/wepppy/wepppy/soils/ssurgo/ssurgo.py. Infrastructure guidance resides in
/workdir/open-wepp-org/AGENTS.md and its docs/planning deployment roadmap.
SDA means USDA Soil Data Access. T-SQL is SQL Server's SQL dialect. PostGIS adds
spatial operations to PostgreSQL. Parity means equivalent observable results on
equivalent source data, not just successful requests.

## Milestone 1: Freeze an executable compatibility baseline

Inspect official downloads and record release/checksum/schema/coverage manifests.
Acquire bounded upstream response fixtures when available, including JSON success,
empty and invalid requests and paired XML responses for migration comparison. Do not fabricate observations during outages. Build
contracts/compatibility.json and fixture validation with explicit supported and
unsupported entries, then define the metadata and error schemas. Add known real
SSURGO and STATSGO2 keys; retain synthetic examples separately. Extend beyond the
five WEPPpy families with representative soilDB and spatial queries. Acceptance:
fixtures are provenance-tagged and expected results can be checked offline.

## Milestone 2: Implement one reproducible vertical slice

Evaluate parser, database driver, HTTP stack, license, maintenance, dependency tax,
and security exposure before selecting language/libraries. Record the result in
docs/dependency-evaluation.md. Implement import tools, migrations, bounded parsed
query translation, JSON serialization, coordinated WEPPpy JSON extraction, and API endpoints against the frozen contract.
Create compose.yaml and a Dockerfile with pinned dependencies. Keep imports and
serving roles separate. Start with one isolated database and API instance.
Acceptance: a real imported subset answers all initial query families, rejects
unsupported operations, and produces results consumable by WEPPpy offline.

## Milestone 3: Prove public-service readiness

Import the national release(s), measure actual database/index/workspace storage,
run parity and representative load tests, and retain sanitized evidence. Freeze
numerical latency/error/capacity targets before measurements. Validate bounds,
client cancellation, restart, interrupted import, atomic activation, and rollback.
Run WEPPpy soil generation through the candidate endpoint and compare generated
soil files. A security review must cover the final code/configuration; unresolved
high findings prevent publication. Tiny synthetic data cannot close this milestone.

## Milestone 4: Environment integration

Prepare a governed package in open-wepp-org identifying the exact Compose-capable
host, capacity, storage, secrets, routing, TLS, image digest, rollback, and operator
handoffs. Preserve existing Talos and WEPPcloud deployments. Portable Compose
support and live public deployment are separate acceptance states. Review public
branding and source-data attribution before a public service release. Code and
documentation use the operator-selected MIT License.

## Concrete Steps and Validation

From /workdir/soil-data-access, run `python3 -m unittest discover -s tests -v`
and `python3 scripts/verify_assessment.py`; ten tests and offline evidence checks
pass. `python3 scripts/verify_assessment.py --require-live` must currently exit 1.
Run `cargo run --locked --manifest-path evaluation/rust/Cargo.toml --
contracts/parser-corpus.json` and, from evaluation/go, `go run .
../../contracts/parser-corpus.json` to reproduce parser probes. See the
[milestone 1 report](milestone-1-assessment.md#reproduce-and-resume) for exact source
audit and upstream recapture commands. No runtime command or success is claimed.
Later acceptance includes Compose rendering/execution, real data parity,
resource-bound tests, and benchmark reports.

## Idempotence and Recovery

Use new candidate data releases and isolated Compose projects. Never overwrite
source downloads or the active database while importing. Failed candidates remain
inactive and cannot become ready. Roll back by selecting the prior validated data
and image pair; prove that procedure before public deployment. Do not remove
persistent volumes as routine cleanup.

## Outcomes & Retrospective

The repository scaffold is published on main. Milestone 1 now has a representative
official source audit, live outage receipts, a compatibility matrix, service-owned
schemas, ten offline tests, and reproducible Rust/Go suitability probes. Rust is
recommended. Milestone 1 is partially complete because live SDA responses and
matched release identity remain unavailable. No runtime implementation, national
import, PostgreSQL semantic parity, benchmark, or deployment has occurred.
Next: recapture live responses after recovery and freeze the remaining wire
contract. Source and parser findings are retained in artifacts/assessment.

## Artifacts and Dependencies

contracts/wepppy-queries.json records the WEPPpy Git revision and source-file hash.
No new service runtime dependencies have been adopted. Pinned parser dependencies
are confined to evaluation/rust and evaluation/go. Rust is recommended; the full
HTTP/database stack and PostgreSQL/PostGIS versions await milestone 2 evaluation. This plan does not authorize an unbounded SQL
service or a different deployment topology.

Revision: 2026-11-17, initial baseline records operator intent and observed XML
consumer behavior before runtime implementation; amended to record the operator
permitting JSON migration rather than requiring XML-first compatibility.

Revision: 2026-11-17, added sample audits, outage observations, service schemas,
parser evidence, and Rust recommendation; left blocked wire-parity work open.
