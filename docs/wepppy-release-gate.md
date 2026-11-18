# Initial WEPPpy release acceptance

Status: operator-approved acceptance policy, 2026-11-17. **No release has passed.**
This is the normative first-release gate. Full SDA parity is deferred and must not
be implied by satisfying this gate.

## Authority, rationale, and claim

The operator approved using existing WEPPpy soils and project SQLite caches as the
parity target during the extended USDA outage. Waiting for live SDA fixtures is
removed as a prerequisite for a bounded deployment. The permitted initial claim
is "validated for the published WEPPpy soil-building workflows and source release."
Public availability does not expand the supported query/workflow set.

Initial scope is the five tabular query families in contracts/wepppy-queries.json,
SSURGO and STATSGO2 coverage explicitly listed in a release manifest, and a
service-owned JSON profile consumed by a coordinated WEPPpy client change. Publish
unsupported behavior clearly. Broader SQL, live SDA response/error equivalence,
XML, soilDB metadata/multipart compatibility, and spatial services are deferred.
Existing workflows requiring unsupported remote spatial services are not covered
by tabular parity; prove a local path or exclude them explicitly.

## Gate 1: independent reference corpus

Create immutable, consistent SQLite snapshots using the backup API, not a bare
copy of a potentially live WAL-backed database. Check integrity and preserve the
source. Record source hashes, available provenance/vintage, schema, selected keys,
WEPPpy/native dependency revisions, configuration, and generated-artifact hashes.
Unknown source dates remain unknown; they are not proof of a matched current release.
Sanitize public manifests and keep private project data outside the public repository.

Freeze the coverage matrix before candidate evaluation. Include both datasets and
ordinary soils, multiple components/horizons, restrictive layers, shallow profiles,
nulls, textures/fragments, invalid soils, missing records, fallback behavior, and
supported treatment variants. Missing cases must be filled or their workflows
explicitly excluded from the declared scope before release. Do not remove failed
cases or alter the reference to achieve a pass.

Regenerate reference soils with pinned existing WEPPpy and identical configuration,
reading snapshot copies with network fetches prohibited. Compare existing project
artifacts as a historical cross-check and retain differences attributable to older
code/configuration. Incomplete caches cannot silently fetch data or become complete
reference cases; retain them as negative/missing-data cases.

## Gate 2: matched-input software parity

Project caches are processed projections: component records incorporate muaggatt
fields and extraction can discard duplicate records. A test-only adapter may seed
PostgreSQL to replay those preserved records, with every transformation documented
and conflicting attributes rejected. It cannot certify reconstruction of raw SDA
tables, response order, or lost duplicates. Keep it separate from production import.

Run the actual Compose database/API and migrated WEPPpy JSON client using empty,
separate candidate caches, USDA access disabled, and request evidence proving the
API was used. Compare parsed records, persisted cache semantics, component/horizon
selection, invalid/fallback decisions, .sol files, assignments/summaries, and final
soil inputs under wepp/runs/. Warm-cache success or mocked fetch functions cannot
satisfy this gate.

For matched inputs, require byte-identical model-consumed soil artifacts and no
unexplained behavior differences across the frozen corpus. Any permitted non-model
metadata exclusions must be listed before comparison. Do not introduce rounding,
numeric tolerances, blanket row sorting, or broad text normalization to hide changes.
Resolve selection ties and duplicate semantics explicitly; add raw-row cases from
independent downloads or authored fixtures through legacy extraction and the new
JSON path. Synthetic XML is permissible as labeled test input, never as live evidence.

## Gate 3: production source import and coverage

Validate official source imports independently of the cache adapter. Check hashes,
schemas, relationship/key coverage, units, precision, nulls, and source-record
projections against a direct reference reader that does not reuse the candidate
importer/translator. Preserve the source values. Do not repair a mismatch by copying
expected outputs into the candidate database or patching data to match old caches.

Record source-version differences separately from software parity. Each difference
needs affected keys/fields, available provenance, generated-output effects, and an
explicit release disposition. Date differences alone do not explain value changes.
Unexplained model-affecting differences block release. Actual coverage must match
the advertised release; sample tests cannot support a national-coverage claim.
Current SDA access is not required, and the service must report the actual selected
snapshot vintage rather than claim it matches the latest live USDA data.

## Gate 4: operational and security readiness

Preserve query parsing/admission, least-privilege serving, separate import roles,
request/response/resource bounds, cancellation, and explicit failures. A dedicated
security review of the final code/configuration is required; unresolved high findings
block public deployment. These controls are not deferred because of the outage.

Set numerical latency/capacity/error targets before load testing. Exercise supported
batch sizes and concurrency on the intended dataset/hardware, record CPU/memory/I/O,
and prove overload/cancellation recovery. Validate actual intended Compose identities,
mounts, permissions, restart, failed imports, consistent release activation, and
rollback. Changing an HTTP timeout is not evidence of server-side cancellation.

## Gate 5: release evidence and rollout

Tie every acceptance result to the exact code, image, dataset manifests, configuration,
and corpus hashes. Missing/stale evidence fails closed. Record all cases, including
failures and exclusions. Assessment/parser tests are not deployment acceptance tests.

Use explicit endpoint/profile selection and isolated cache provenance. Preserve the
existing upstream XML workflow and original caches; no silent endpoint failover or
mixing releases. Stage a selected canary and inspect freshly generated inputs before
expansion. Rollback restores the previous tested endpoint/profile/cache and, after
the first local release, the prior validated local image/data pair. A still-down
USDA endpoint must not be described as an available recovery path.

open-wepp-org owns the exact host, routing, TLS, storage, secrets, capacity, and live
handoffs. No live target or public route is selected by this policy. The operator's
acceptance-policy decision does not claim that any deployment gate has passed.

## Deferred work

Capture and compare live SDA JSON/XML success, empty, null/decimal, and error cases
when the service recovers; identify matched source releases. Expand soilDB, SQL,
spatial, and other public-client compatibility through versioned contracts and tests.
Retain the existing WEPPpy parity suite on every change. Deferred work is not waived
or automatically complete when the bounded first release is accepted.
