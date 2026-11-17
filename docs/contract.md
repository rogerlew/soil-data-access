# Unofficial Soil Data Access contract

Status: initial contract baseline, 2026-11-17. No runtime is implemented.

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

Evaluate PostgreSQL with PostGIS as the initial database candidate. Evaluate Rust
or Go for a stateless API after identifying SQL parsing and serialization needs.
Docker Compose is a required supported deployment, including a reproducible local
API/database acceptance environment. Exact dependency versions and image digests
must be evaluated and pinned before implementation. There is no selected public
host, hostname, TLS integration, capacity allocation, or availability commitment.
Do not assume Compose can run on the existing Talos nodes or reuse postgres-01.
No new queue, Redis cache, replication layer, or SQL Server emulation platform is
part of the initial complexity budget.

## Compatibility scope

Initial integration direction: POST /Tabular/post.rest using an explicitly selected
SDA JSON response format, with a coordinated WEPPpy parser migration. Capture the
actual upstream JSON envelope, column metadata, types and null behavior before
freezing the executable schema. Request encoding remains to be selected and tested.
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
ORDER BY have no implied stable ordering. Capture upstream success, empty, and
error responses before freezing exact response schemas. Do not invent upstream
error codes or label locally designed errors compatible.

SQL Server/T-SQL compatibility is bounded by a published feature matrix.
Resolve identifier case, implicit key casts, nulls, decimals, collation, functions,
and spatial semantics explicitly. PostgreSQL accepting a query is not parity.
Initial scope excludes SOAP, WMS/WFS, persistent AOIs, interpretation/report
engines, arbitrary multi-statement T-SQL, and unrestricted SQL passthrough.
These remain discoverable gaps, not successful empty responses.

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

Parity tests identify both source releases and distinguish upstream data drift
from translation/serialization defects. Include missing keys, nulls, duplicate
rows, special characters, decimal edges, large batches, and invalid requests.
Validate existing XML extraction against the migrated JSON extraction using
equivalent recorded data, then compare final WEPP soil artifacts for representative
SSURGO and STATSGO2 runs. Retain duplicate handling, ordering, key normalization,
and null/numeric conversion behavior unless a separate change is justified. Include public
client queries before claiming compatibility beyond WEPPpy.

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
This does not authorize removing XML support for unrelated callers or claiming
full SDA compatibility without evidence.

## References

- https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx
- https://ncss-tech.github.io/soilDB/articles/sda.html
- https://www.nrcs.usda.gov/resources/data-and-reports/ssurgo-portal
- /workdir/wepppy/wepppy/soils/ssurgo/ssurgo.py
