# Bounded runtime and cache replay contract

This implements the five frozen query families for local acceptance. Public release,
production source import, and full WEPPpy workflow acceptance remain separate gates.

## Admission and execution

Parse one SELECT using sqlparser's SQL Server dialect and a recursion limit of 64.
Accept only the complete AST shape of one frozen query, with its IN list replaced
by 1–4096 nonnegative signed-64-bit integer keys (unquoted or single-quoted decimal).
Case and whitespace may vary; bracketed names, aliases, different projections,
additional predicates, functions, joins, statements, or sort modifiers are outside
this initial grammar. Reject unsupported SQL with 422. Resolve the component
ORDER BY to component.mukey. Emit only owned PostgreSQL statements, never rendered
caller SQL. Bind release and key arrays separately. This deliberately narrow
admission can be extended only with contract fixtures and acceptance evidence.

The initial operational bounds are 128 KiB encoded request, 64 KiB decoded query,
4096 keys, eight concurrent requests (including metadata), five-second server
statement timeout, three-second connect timeout, and eight-second operation deadline.
Reject excess concurrency immediately with overloaded/503. Limit output to 100,000
rows and 16 MiB JSON; fail explicitly with request_too_large/413, never truncate a
successful table. These are initial containment settings, not capacity claims.

Each operation opens its own bounded connection and repeatable-read, read-only
transaction, reads the active release once, then queries that release's rows.
Connection tasks are aborted when their handler future ends; connections are not
returned to a pool. Peer disconnect does not currently guarantee immediate handler
cancellation; observed database cleanup is bounded by the five-second statement timeout. PostgreSQL's statement/idle-transaction deadlines also bound
orphaned work. Test cancellation and recovery before public deployment. Local
Compose uses a private database network without a published database port; NoTls
is scoped to that local network, not a remote database deployment contract.

Keep the existing JSON/error contracts, including empty headers and release/profile
response headers. Invalid form/content-type/format fails with invalid_request/400;
body limit violations use request_too_large/413. No active release gives not_ready/503
for queries and ready=false metadata. Database failures must not expose SQL or
credentials. An unknown route or method gets a structured invalid_request response.

## Replay data and atomic activation

The six named tables use exact bigint keys, numeric scientific values, and text
categories. Every row carries release_id and a replay-only ordinal. Component
records are separated into component and muaggatt; repeated MUKEY aggregate
attributes must agree exactly, including nulls. Reject inconsistencies before
writing SQL. Keep each cache as a separate immutable release; never merge cases.
Preserve SQLite rowid order for equal requested sort keys in replay. The ordinal
is replay provenance, not an invented upstream sorting guarantee. Production source
ordering and duplicate selection remain unproved.

The test adapter reads only hashed, complete frozen fixtures. It emits transactional
SQL for explicit local operator import, rejects existing release IDs, and changes
the one active-release pointer only after all rows and manifest are inserted.
An import error rolls the entire transaction back. Negative markers represent
absence; they are retained in source evidence, not fabricated into positive rows.
The incomplete shared STATSGO fixture is rejected. Empty fixtures remain empty.

Metadata gains the additive dataset enum WEPPPY_CACHE_REPLAY so processed caches
are not misrepresented as official SSURGO/STATSGO2 releases. Its manifest includes
case, fixture hash, source URL, and explicit processed-cache scope. The serving role
has SELECT only; the import role is separate. Replay SQL is test tooling, not the
national importer. Existing project caches and production infrastructure are intact.

## Validation

Before claiming runtime completion, test all five families against the real Compose
API and PostgreSQL for every complete fixture, including negatives and empty inputs.
Compare typed records against an independent SQLite reader. Exercise authored raw
rows for duplicate/null/large-identifier semantics. Retain malicious-query rejection,
role write denial, timeout/cancellation, overload, restart, failed import, and release
activation evidence. Then wire the actual WEPPpy JSON client in a separate worktree
and compare fresh-cache generated soils; API record parity alone is insufficient.
