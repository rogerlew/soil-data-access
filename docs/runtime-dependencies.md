# Runtime dependency decision

2026-11-18: accept this stack for local implementation/evaluation, subject to the
public release gates. Precedent: docs/dependency-evaluation.md and WEPPpy's
precedent registry. No owned geospatial/model component supplies HTTP SQL admission
or PostgreSQL transport; this stack does not replace those components.

Axum 0.8.9, Tokio 1.54.1, tokio-postgres 0.7.18, futures-util 0.3.34, Serde 1.0.228,
serde_json 1.0.145, and sqlparser 0.64.0 are pinned with a lockfile. The selected direct dependencies use MIT/Apache licenses compatible with this
service; the transitive inventory also includes BSD, Unicode, Zlib, and LLVM
exception terms. Alternative LGPL expressions have permissive alternatives.
Preserve third-party notices when distributing binaries. The resolved graph initially contains 118 external
packages including target-specific dependencies, not 118 Linux runtime libraries.
Exact licenses/repositories are retained in artifacts/runtime/dependencies.json;
cargo-audit.json reports no known advisories at its recorded RustSec revision.
Repeat the audit when the lockfile changes; absence of findings is not proof of safety.

Axum binds us to Tokio/Hyper/Tower but not a database/model abstraction. The direct
PostgreSQL driver preserves owned SQL and dynamic text projections; no ORM or pool
is needed for the initial bounded per-request connection implementation. Futures
utilities consume database rows incrementally, allowing response bounds without
first buffering every row. sqlparser retains its existing recursion protection.
Build requires the pinned Rust toolchain plus the native stack-protection build
prerequisites already present in the Rust image. No new model runtime is introduced.

The earlier assessment retains upstream activity/contributor observations. Current
versioned documentation confirms the APIs used here; a precise annual breaking-change
rate, funding continuity, and current active-maintainer bus factor are unverified.
Treat pre-1.0 Axum/sqlparser upgrades as explicit compatibility work. Rust/PostgreSQL
and Tokio retain their stable public-version lines; this is not a maintenance guarantee.
No throughput superiority claim is made. Database/network performance and capacity
must be measured on the declared source release before public deployment.

Compose evaluates PostgreSQL 17/PostGIS 3.7 on a pinned digest, separate from existing
databases. PostGIS is not exercised by the tabular profile. The image's GPL PostGIS
and PostgreSQL licensing remain third-party component licenses; MIT does not relicense
them. OS/image vulnerability review remains a public deployment gate.

Primary API references: https://docs.rs/axum/0.8.9/axum/,
https://docs.rs/tokio-postgres/0.7.18/tokio_postgres/,
https://docs.rs/tokio/1.54.1/tokio/ and https://hub.docker.com/r/postgis/postgis.
