# Unofficial Soil Data Access contract

Status: WEPPpy-first acceptance baseline, 2026-11-17. No runtime is implemented.
The operator approved [project-cache and soil-artifact parity](wepppy-release-gate.md)
as the first deployment gate. Full SDA wire parity is deferred, not required for
that bounded release; the [earlier assessment](milestone-1-assessment.md) retains outage evidence.

## Purpose and ownership

Provide a public-facing, open-source, independently hosted service for querying
USDA soil survey snapshots during upstream outages. A separate service repository
owns API behavior, imports, tests, images, and portable Docker Compose deployment.
The open-wepp-org infrastructure repository owns environment configuration and
public routing. The provisional local service path is /workdir/soil-data-access.
Repository: https://github.com/rogerlew/soil-data-access.
Code and documentation use the MIT License, selected by the operator.
The code license does not relicense third-party datasets. Clearly identify the service as unofficial and attribute USDA data.

## Architecture and deployment

Use the Rust recommendation as the implementation direction with PostgreSQL/PostGIS;
finish evaluation and pinning of the complete runtime stack before adoption.
Docker Compose is a required supported deployment, including a reproducible local
API/database acceptance environment. Exact dependency versions and image digests
must be evaluated and pinned before implementation. There is no selected public
host, hostname, TLS integration, capacity allocation, or availability commitment.
Do not assume Compose can run on the existing Talos nodes or reuse postgres-01.
No new queue, Redis cache, replication layer, or SQL Server emulation platform is
part of the initial complexity budget.

## Compatibility scope

Initial integration direction: POST /Tabular/post.rest with a coordinated WEPPpy
JSON client migration. Freeze an explicitly service-owned JSON+COLUMNNAME profile
from the pinned WEPPpy contract and offline fixtures before implementation, including
column order, types, nulls, empty results, and errors. Live SDA capture is not a
prerequisite; do not describe authored response fixtures as observed SDA parity.
Use application/x-www-form-urlencoded query and format fields, percent-encoding
plus signs. The [compatibility matrix](../contracts/compatibility.json) distinguishes
initial WEPPpy release gates from deferred SDA wire-compatibility gaps.
Current WEPPpy uses form-encoded requests with format=xml; the extracted queries
record that baseline, not a requirement that the new service implement XML first.
XML support is a separate compatibility-matrix decision based on public clients.
Do not claim unchanged-client compatibility if XML is not implemented.
The initial five query families and selected columns are in
../contracts/wepppy-queries.json. They read component joined to muaggatt, chorizon,
chfrags, chtexturegrp, and corestrictions. Test both SSURGO and STATSGO2 key sets.
The fixture keys are synthetic query-generation inputs, not verified USDA keys.

Preserve ordered columns, null representation, numeric precision, aliases,
response structure and escaping, and explicitly requested row ordering. Preserve row
multiplicity. Unordered results are compared as multisets; ties in an incomplete
ORDER BY have no implied stable ordering. Live upstream success/empty/error capture is required before claiming exact SDA
wire compatibility, but does not block the service-owned WEPPpy profile. Never
label locally designed errors or source-derived fixtures as observed USDA behavior.

SQL Server/T-SQL compatibility is bounded by a published feature matrix.
Resolve identifier case, implicit key casts, nulls, decimals, collation, functions,
and spatial semantics explicitly. PostgreSQL accepting a query is not parity.
Initial scope excludes SOAP, WMS/WFS, persistent AOIs, interpretation/report
engines, arbitrary multi-statement T-SQL, and unrestricted SQL passthrough.
These remain discoverable gaps, not successful empty responses.

## Service-owned metadata and errors

These operational contracts are our own design, not observed USDA error parity.
GET /v1/metadata returns HTTP 200 with application/json matching
[metadata.schema.json](../contracts/metadata.schema.json). It identifies the
unofficial service, contract version, code revision, readiness, and one active
release manifest containing individually identified SSURGO/STATSGO2 source releases.
Before data activation, ready is false and active_release is null. Ready true
requires a validated active release; a responding process alone is not ready.
Scope labels must describe actual coverage, never infer nationwide completeness.

Rejected requests return application/json matching
[error.schema.json](../contracts/error.schema.json). Codes map to HTTP status:
invalid_request=400, unsupported_query=422, request_too_large=413,
rate_limited=429, overloaded=503, not_ready=503, query_timeout=504,
internal_error=500. Messages must not expose SQL text, credentials, internal
paths, or database exception details; request_id permits correlation with
restricted diagnostics. Do not return an empty successful table for failures.
These explicit codes permit callers to distinguish invalid requests from temporary
capacity or readiness failures without pretending to duplicate USDA's errors.
[Service examples](../contracts/service-examples.json) are authored examples.

## Data contract

Acquire SSURGO and STATSGO2 independently of the live query service. Inspect the
actual downloadable schema and coverage; the advertised 28 GB SSURGO file does
not establish STATSGO2 inclusion or full Soil Data Mart coverage. Retain source
URLs, release identifiers, acquisition time, checksums, schema version, row counts,
key coverage, and import software revision. Audit missing tables/columns explicitly.
Preserve identifiers without lossy conversion and numeric values without invented
fallbacks. Validate foreign-key relationships and spatial reference systems.

Imports build a candidate release without changing the serving release. Validate
it before activation; each request must use one consistent release. Retain the
previous validated release for rollback. Requests must succeed without contacting
USDA after import. Expose the active data release and compatibility version through
a documented service-owned metadata endpoint; finalize its schema before coding.
Refresh scheduling follows actual published releases, not an assumed calendar-only
availability guarantee.

## Cache labels and source-family coverage

WEPPpy's SSURGO and STATSGO collection paths share the same tabular query helpers
and endpoint; the five queries have no source-dataset predicate. A cache filename
or `Surgo`/`StatsGo` header is a client-path label, not row-level provenance.
gNATSGO combines SSURGO, STATSGO2, and Raster Soil Survey data, so the default
SSURGO cache can contain STATSGO2 map units. See the
[NRCS composition description](https://www.nrcs.usda.gov/resources/data-and-reports/gridded-national-soil-survey-geographic-database-gnatsgo)
and [retained corpus evidence](wepppy-corpus.md).

Preserve one supported key-query contract across the source families. Do not
partition query routing or exclude keys using cache labels. Validate the selected
official import's coverage against actual gNATSGO/WEPPpy keys, retain source-release
provenance, and reject unexplained conflicting source records. A SSURGO-only source
name is insufficient evidence of coverage; a combined gNATSGO source is a candidate
for independent import assessment, not automatically validated by its name.

## Public query containment

Define an allowlisted parsed query grammar and exposed tables/functions. Reject
unrecognized constructs before execution. Regex keyword filtering is insufficient.
Use a dedicated minimally privileged serving role and separate import credentials.
A read-only transaction is necessary but does not prevent expensive queries or all
function side effects. Set and test request, concurrency, time, memory/temp-space,
row and response-byte budgets before public deployment. Propagate client cancellation
and deadlines to database work. Ensure overload is explicit and recoverable.
No database port is publicly published. Retain a security review covering parser
bypasses, function access, catalog leakage, resource exhaustion, and secrets.

## Acceptance evidence

[Initial WEPPpy release acceptance](wepppy-release-gate.md) defines the required
corpus, comparison, import, security, and operational gates. Freeze consistent
project SQLite snapshots and regenerate reference soils with pinned existing WEPPpy.
Exercise the real PostgreSQL/API/JSON client with empty candidate caches and USDA
blocked. Require matched-input parity through final soil files in wepp/runs/,
including component selection, invalid soils, fallbacks, and assignments.

Caches are processed projections, not raw SDA response fixtures. Keep the cache
replay adapter test-only and validate production imports independently against
official source records. Add raw duplicate/null/order cases that caches cannot
preserve. Track source-version differences with affected fields/output effects and
explicit disposition; never weaken software parity or patch data to match history.
Select the endpoint/profile explicitly and isolate cache provenance to avoid mixed
releases. Existing project caches and upstream XML behavior remain intact.

Full live SDA and general public-client parity are deferred. Passing this gate
permits only the published WEPPpy workflow/source-release claim. No gate has passed
yet; the corpus and runtime remain unimplemented.

Benchmarks report hardware, image/code revisions, dataset/checksums, indexes,
connection limits, concurrency, warm/cold conditions, throughput, error rate,
p50/p95/p99 latency, CPU, memory, disk I/O, and cancellation/overload recovery.
Define workload-specific numerical acceptance targets before running benchmarks;
no target or performance claim is established by this baseline. Do not load-test
USDA. Bounded live parity sampling and recorded responses are separate activities.
Compose acceptance must exercise actual roles, mounts, restart, failed import,
release switching, and rollback with USDA connectivity disabled.

## Decisions and rationale

The operator requested a contract-first, public open-source mirror, performance
and parity testing, PostgreSQL/PostGIS assessment, Rust/Go assessment, and Docker
Compose deployment with open-wepp-org involvement. Separate source ownership keeps
API releases and compatibility testing independent of infrastructure operations.
A PostgreSQL/PostGIS candidate permits joint spatial/tabular assessment; it does
not prove SQL Server compatibility. Start with real consumer queries. The operator subsequently identified migration
of WEPPpy away from XML as acceptable: JSON-first integration with artifact parity
is the chosen assessment direction, rather than making legacy XML mandatory.
The operator then approved using existing project SQLite caches and soils to
validate WEPPpy behavior and defer full SDA parity during the multi-day outage.
The earlier live-capture prerequisite is superseded for the bounded release.
Waiting for upstream recovery was rejected as unnecessary for that narrow claim;
treating processed caches as raw import truth was rejected as circular validation.
Security, performance/capacity, recovery, and fresh-output gates remain mandatory.
This does not authorize removing XML support for unrelated callers or claiming
full SDA compatibility without evidence.

## References

- https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx
- https://ncss-tech.github.io/soilDB/articles/sda.html
- https://www.nrcs.usda.gov/resources/data-and-reports/ssurgo-portal
- /workdir/wepppy/wepppy/soils/ssurgo/ssurgo.py

## Assessment recommendation

[The Rust/Go evaluation](dependency-evaluation.md) recommends Rust based on the
26-query syntax probe and parser maintenance breadth. The full runtime stack is
not adopted yet. Rust sqlparser parses the tested SQL Server spatial intersection
expression that GoSQLX rejects. Neither parser translates semantics or enforces
query safety; PostgreSQL/PostGIS parity and resource containment remain gates.
