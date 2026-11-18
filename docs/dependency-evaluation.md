# Rust versus Go: implementation recommendation

Date: 2026-11-17. **Recommend Rust for implementation**, using an owned SQL
admission/translation layer over `sqlparser` and PostgreSQL/PostGIS. This is an
assessment recommendation, not a claim that the full runtime stack is approved,
implemented, secure, or faster than a Go service.

## Decision basis

The unusual requirement is accepting a bounded SQL Server dialect while executing
against PostgreSQL/PostGIS. HTTP serving is straightforward in either language;
the parser, semantic validation, and spatial translation are the differentiators.

Two pinned, runnable probes use the same 26-query corpus. It includes five actual
WEPPpy families, thirteen candidate queries (including adapted soilDB queries),
six deliberately disallowed but syntactically valid queries, and two malformed
queries. These are correctness smoke probes, not load benchmarks or safety filters.

| Result | Rust: sqlparser 0.64.0 | Go: GoSQLX 1.17.0 |
| --- | --- | --- |
| WEPPpy query families parsed | 5/5 | 5/5 |
| Candidate queries parsed | 13/13 | 12/13 |
| Malformed queries rejected | 2/2 | 2/2 |
| Disallowed queries parsed | 6/6 | 6/6 |
| SQL Server spatial intersection expression | Parsed and rendered | Rejected at `geometry::STGeomFromText` |
| Parser license | Apache-2.0 | Apache-2.0 |
| Probe toolchain | Rust 1.92.0 | Go 1.26.11; module requires 1.26.1 |

[Corpus](../contracts/parser-corpus.json), [Rust results](../artifacts/assessment/rust-parser-results.json),
and [Go results](../artifacts/assessment/go-parser-results.json) are retained.
Rust preserves the spatial expression in its rendered AST. That is syntax
preservation, **not conversion into PostGIS SQL**. Neither parser checks database
permissions, decides acceptable functions, or guarantees semantic equivalence.
Both accept writes, SELECT INTO, catalog access, and expensive/unsafe functions.
The service must reject those with its own allowlisted semantic validator.

## Suitability and tradeoffs

| Concern | Rust | Go |
| --- | --- | --- |
| SQL compatibility work | MsSqlDialect plus typed AST; strongest result in this corpus | Viable, but tested parser needs spatial grammar repair or a scoped exclusion |
| HTTP and PostgreSQL | Axum/Tokio and tokio-postgres are candidates | Standard net/http and pgx are candidates |
| Resource lifecycle | Explicit ownership; cancellation/connection cleanup still needs design and tests | Request contexts are convenient; database cancellation and pool cleanup still need tests |
| Implementation effort | More type/async complexity; existing owned Rust stack experience helps | Simpler service scaffolding; would spend additional effort on compatibility gaps |
| Runtime performance | Unmeasured for this service | Unmeasured for this service |
| Compose packaging | Feasible compiled service; parser defaults add stack-protection native build dependencies | Feasible compiled service; actual imported parser code requires no additional third-party module |

My recommendation follows the demonstrated spatial grammar result and parser
maintenance breadth. It does not assume Rust makes PostgreSQL queries faster.
Retain Go as a viable alternative if scope becomes a native PostgreSQL API or
its parser closes the required compatibility gaps with retained tests.

## Dependency evaluation gates

### Precedent and capability overlap

The WEPPpy dependency-evaluation registry contains no prior SDA parser evaluation.
Existing weppcloud-wbt, wepppyo3, oxidized-rasterstats, and peridot own geospatial
processing, not a public SDA SQL compatibility service. This proposal does not
replace those compute paths or substitute pure Python for native geometry work.
PostGIS would execute the agreed database spatial operations. No separate queue,
cache service, SQL Server emulator, or second parser runtime is proposed.

### Maintenance, licensing, and dependency cost

Public project snapshots and contributor counts are retained in
[upstream projects](../artifacts/assessment/upstream-projects.json) and
[contributor snapshot](../artifacts/assessment/contributor-snapshot.json).
The tag arrays are observations, not authoritative latest-version lists for
multi-crate repositories such as Axum and rust-postgres.

Both tested parser repositories had activity on 2026-11-17. Rust sqlparser's top
five historical contributors each had 93–246 commits in the snapshot. GoSQLX's
leading contributor had 586, with the next four at 1–4 each. This suggests greater
maintenance concentration for GoSQLX; historical counts are not an active
maintainer count, funding guarantee, or computed bus factor. Funding continuity
is unverified for both. Pin versions and rerun the corpus on every upgrade.
sqlparser is pre-1.0; its AST is version-sensitive. No breaking-changes-per-year
rate was measured, and neither library's release activity proves compatibility.

The Rust probe lockfile has **27 dependency packages**, including its JSON harness.
Default recursive-protection brings recursive/stacker and native build tooling;
do not disable it merely to shrink the count. The Go probe's resolved module
graph has **76 external modules**, but its compiled third-party imports come from
**only GoSQLX**. The larger graph includes library tests/tools and must not be
represented as 76 runtime dependencies. These are parser-probe counts, not full
API stack counts. Exact versions/licenses are in the retained
[dependency footprint](../artifacts/assessment/dependency-footprint.json).

The Rust lockfile audit reported zero known advisories or warnings at the recorded
RustSec revision. Go govulncheck 1.9.0 reported no reachable findings for the probe
using Go 1.26.11. These scans have different scopes and do not establish absence
of vulnerabilities. The initial govulncheck 1.1.4 could not load Go 1.26 syntax;
the successful newer pinned scan supersedes that tooling failure. See
[Rust audit](../artifacts/assessment/rust-audit.json) and
[Go scan receipt](../artifacts/assessment/go-vulncheck.json).

Other evaluated options: pg_query_go parses PostgreSQL using its C parser, so it
does not resolve the T-SQL input requirement. ha1tch/tsqlparser is T-SQL-specific
but declares GPL-3.0; it was not selected for this MIT-oriented implementation
assessment. No claim is made that these are the only possible Go parsers.

### Proposed Rust implementation shape

Use sqlparser 0.64.0 as the evaluated parser baseline. Convert accepted AST nodes
to a small owned query representation; resolve columns and types against our
schema catalog; bind literals; then emit PostgreSQL expressions. Do not execute
`AST.to_string()` as translated SQL. Names/functions not in the allowed catalog
must fail explicitly. Keep input size/depth/time budgets around parsing as well
as database execution; recursive protection alone is insufficient.

Evaluate Axum/Tokio for HTTP and tokio-postgres for database access in milestone 2.
Current documentation inspected Axum 0.8.9 and tokio-postgres 0.7.18. They are
candidates, not new committed runtime dependencies. A direct PostgreSQL driver
fits dynamically selected columns; no ORM is required. Test decimal/key decoding,
connection reuse after cancellation, read-only transaction enforcement, and actual
server-side cancellation. An HTTP timeout alone does not prove query cancellation.
Pin the complete stack and repeat dependency/license/security checks before adoption.

### Performance and promotion gates

No comparative runtime benchmark was run; build time and parser acceptance counts
are not throughput evidence. Milestone 3 must measure real imported national data,
index plans, response sizes, concurrency, latency percentiles, error rates, CPU,
memory, disk I/O, and cancellation/overload recovery on target hardware. Define
numerical acceptance targets first. Retain database and API measurements separately
so SQL execution cost is not attributed to the implementation language.

## Reproduction

From the repository root:

```bash
cargo run --locked --manifest-path evaluation/rust/Cargo.toml -- contracts/parser-corpus.json
cd evaluation/go
go run . ../../contracts/parser-corpus.json
```

The probes only parse and render SQL. They never execute it against a database.
Their pinned manifests and lockfiles are evaluation assets, not the future server.

## Primary references

- [Rust sqlparser and its syntax/semantics boundary](https://github.com/apache/datafusion-sqlparser-rs)
- [MsSqlDialect](https://docs.rs/sqlparser/0.64.0/sqlparser/dialect/struct.MsSqlDialect.html)
- [GoSQLX source](https://github.com/ajitpratap0/GoSQLX/tree/v1.17.0)
- [pg_query_go](https://github.com/pganalyze/pg_query_go)
- [T-SQL Go parser](https://github.com/ha1tch/tsqlparser)
- [Axum](https://docs.rs/axum/0.8.9/axum/)
- [tokio-postgres cancellation](https://docs.rs/tokio-postgres/0.7.18/tokio_postgres/struct.CancelToken.html)
- [pgx pgconn](https://pkg.go.dev/github.com/jackc/pgx/v5/pgconn)
