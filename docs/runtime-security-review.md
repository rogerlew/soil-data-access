# Local runtime threat model and review

Scope: the initial Rust/Compose cache-replay implementation. This is an author
review with exercised controls, not the independent public-deployment security
review required by the release gate. No public route is authorized by this artifact.

## Boundaries and controls

Untrusted form bodies enter bounded parsing. Only five normalized parsed shapes
select owned SQL; caller text never becomes executed SQL. Integer key arrays and
release IDs are bound parameters. Extra predicates, projections, functions, catalog
access and multiple statements fail. Shape serialization is an admission fingerprint,
not a SQL translation engine; every accepted request still selects fixed SQL.

The API container runs as 10001:10001 with a read-only root, dropped capabilities,
no-new-privileges, PID/memory limits, and localhost-only HTTP publishing. PostgreSQL
has no host port. The serving role has SELECT grants, no table/schema creation or
write grants, and defaults to read-only transactions. Imports use a separate role.
Local generated passwords are exclusive mode-0600 .env values, excluded from Git
and build context. Do not print rendered Compose configuration or container envs.

Each request gets a bounded new database connection. Repeatable-read transactions
pin the active release and rows; activation cannot mix releases within a response.
Eight in-flight operations, body/key/recursion/row/byte limits, server statement
and idle-transaction timeouts, and an outer deadline bound local work. Rejected
requests return structured messages without SQL, source paths or credentials.
Success logs record request ID, family, release and row count, not query text.

## Exercised checks

The runtime harness verifies all five frozen families and eleven authored raw-row
examples, including precision, nulls, Unicode, empty results and duplicates. It
also exercises query rejection, serving-role write denial even with its default
read-only setting disabled, duplicate-import rollback, overload, database lock
statement timeouts, active-query cleanup, consistent release switching, response
size/row failures, and restart recovery. Retained results belong in
artifacts/runtime/compose-validation.json for committed runtime 9dc2264.
The final observed disconnect cleanup was 5.08 seconds; all eight timed-out queries
were gone before recovery was accepted. This is local containment evidence only.

## Open deployment gates and limitations

Immediate cancellation on peer disconnect is not established. In the initial
observation the request continued until PostgreSQL's five-second statement timeout;
cleanup was observed at about 4.8 seconds after disconnect. The harness requires
cleanup within six seconds. The handler connection task is dropped when its future
ends, but HTTP disconnect is not assumed to end that future immediately. Any tighter
cancellation SLO needs implementation and proof before deployment.

There is no per-client rate policy, TLS/public routing integration, target-host
capacity evidence, complete malformed HTTP/parser fuzzing, image CVE disposition,
or independent security review yet. The HTTP bridge allows egress; Docker internal
networks alone suppressed localhost port publishing in this environment. The database
network remains internal. This runtime check therefore does not prove an upstream-
blocked WEPPpy build; the candidate workflow needs explicit network confinement.
No upstream HTTP client exists in the Rust service.

The importer is a trusted test tool. Production official imports need separate
validation/activation authority, immutable release policy, field-size validation,
and disk/index/backup budgets. The local import role is the initialization owner;
it is not a proposed production least-privilege importer. Authored test rows and
processed caches must never be advertised as national source data.
