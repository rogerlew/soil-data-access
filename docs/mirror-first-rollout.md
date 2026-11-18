# Mirror-first rollout with USDA SDA fallback

Status: operator-approved direction, 2026-11-18 UTC; not implemented or deployed.
The operator accepts the SSURGO/STATSGO fixture results as sufficient evidence to
proceed beyond those locations. Comprehensive geographic/live SDA parity is a
post-rollout follow-up when SDA recovers, not a prerequisite for the first rollout.

## Acceptance and remaining implementation

The 24,049 matched records, 501 canonical artifacts and preserved invalid outcomes
support generalization of the five query families and soil-building logic. Do not
require a location-by-location national comparison before activation. Retain those
regressions and a bounded real worker smoke check in each environment.

A serving dataset still must be loaded: the existing replay importer contains only
fixture releases. Implement the broader source import with source hashes, schema,
row/key counts, relationship checks, and small independent projection samples.
This verifies that the import loaded its declared data, rather than requiring
comprehensive agreement with live SDA. Record actual source vintage/coverage and
handle unavailable keys through the fallback policy. Exhaustive source-version
comparisons and expanded geographic parity move to the recovery follow-up.

## Intended default and fallback

Deployment configuration selects the mirror endpoint and immutable release as the
default for new/unconfigured projects. Preserve explicit project source overrides
and existing artifacts/caches. Existing persisted selections require a deliberate
migration; do not infer whether an old saved XML identity was an explicit override.
Keep XML-only selection as an operator override and rollback option.

Try the mirror first, including valid matching warm-cache reuse. Permit a bounded
USDA SDA attempt after connection failure, timeout, HTTP 429/5xx/not-ready, or a
missing required map-unit component/explicit coverage miss. Missing optional
restriction, fragment or texture rows are legitimate results, not outage signals.
Do not substitute another source merely because the numerical builder rejects a
soil. Local cache corruption, identity mismatch, malformed responses and unsupported
queries remain explicit defects; they are not ordinary availability fallback.

Keep fallback at collection construction: retry the entire requested collection
against SDA in its own source-bound cache before soil construction. Do not combine
mirror components with SDA horizons or write SDA rows into a mirror-release cache.
Reuse a valid SDA cache when available, retaining unknown historical provenance
where applicable. One source supplies each successfully constructed collection.
Return to mirror-first on the next construction; do not persist a temporary outage
as a permanent project source switch. Bound attempts across the complete fallback
operation, including the legacy XML request path, so an SDA outage cannot cause an
unbounded build delay. Choose and test the concrete total budget in the client contract.

Record the configured primary, attempted sources, reason/time of fallback, actual
supplier, and any unknown upstream release. Link this selection event to SQLite
retrieval history and base-soil provenance. Both-source failure must retain both
failure reasons and fail explicitly, never masquerade as an empty successful query.
The SDA service need not be reachable to test this: controlled HTTP endpoints can
exercise primary success, fallback success and dual failure now.

## Implementation sequence

First extend the WEPPpy source contract, error classification and selection
provenance. Add the transport-policy ADR and the repository-required reviews before
executable changes. Implement one collection-selection path shared by all six
consumers; retain explicit-source behavior and cache binding. Test fallback after a
partially populated primary cache and prove the generated soil uses one source.

In parallel with that work, implement the source importer and Compose wiring for
forest dev, forest1 test-production and wepp.cloud production. Keep the service-owned
portable Compose definition; integrate environment wiring through WEPPpy's existing
Compose files and installed wctl/deploy-production entry point. These hosts are not
an openwepp.org Kubernetes deployment. Connect all soil-building worker roles to
the selected endpoint, keep the database private, and configure persistent storage,
readiness, secrets and restart behavior. Do not create an additional deployment system.

Run forest first with actual queued builds and provenance inspection, then forest1
with production-equivalent settings, then enable the production default with a bounded
canary. Reuse completed release evidence; perform focused capacity/restart/rollback
checks rather than national revalidation or repeated full suites on every host.
Document the observed numerical-environment comment difference; do not silently
widen canonical exclusions. Resolve its deployment-image disposition with the
smallest same-image legacy-versus-JSON comparison.

When SDA recovers, expand live geographic/source-version comparisons, including
unseen duplicate/null cases, and use discrepancies to improve the service. Full SDA
wire/public-client compatibility remains separate from the WEPPpy default rollout.

## Rationale

This supersedes the earlier no-automatic-failover rollout direction and any reading
of the release gates that demands comprehensive national parity before activation.
Waiting for SDA recovery would defeat the outage-resilience purpose. The existing
fixtures justify proceeding with implementation and a bounded rollout; they do not
create rows that have not been imported. Provenance and separate source caches make
fallback observable without falsely attributing USDA data to a mirror snapshot.
