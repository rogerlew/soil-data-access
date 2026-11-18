# Official tabular import for forest

Import an immutable GeoPackage SSURGO source and legacy STATSGO2 ZIP
into one scoped release of the existing six-table API. The first forest release
uses Idaho SSURGO (October 2026 download) and Virgin Islands STATSGO2 (2016 archive).
This broadens data beyond project-cache fixtures; it is not nationwide coverage.

Read sources without modifying them. Require declared URL, source release, scope,
file checksum and schema columns. Legacy ZIP field order comes from its mstabcol
metadata; empty legacy cells map to SQL NULL. GeoPackage NULL and empty strings
remain distinct. Validate nonnegative signed-64-bit keys, finite numeric values,
source relationships and unique parent keys. Require disjoint MUKEY/COKEY/CHKEY
parent domains between the selected datasets; reject overlap rather than silently
choosing a vintage. Preserve all child rows, including duplicates, and input rowid
order as the documented tie order; retain source order as ordinal. This is a stable
import convention, not a claim about unspecified live SDA row order.

Use streaming PostgreSQL COPY in one transaction with a candidate release manifest.
The importer emits SQL to an ignored local file; an operator executes it with the
existing local import role. Reusing a release ID fails. Assert imported table counts
and parent relationships before updating the active-release pointer at transaction
end. Any conversion, COPY or validation failure preserves the previous active release.
Each source manifest uses SSURGO or STATSGO2, with actual scope/vintage and hash;
never label official sources WEPPPY_CACHE_REPLAY. Retain per-table counts, parent-key
coverage and archive/extracted-file hashes in an import receipt.

Validate representative projections using a separate direct-reader path that executes
the frozen query catalog against the original files and compares actual HTTP results.
Do not use the candidate importer to generate expected rows. Compare unordered raw
row multisets with exact numeric equality, no tolerance. Retain first-row selection
and final-artifact checks separately under the actual worker environment. Existing
processed-cache replay remains a regression tool, not an official-source oracle.

## Container readiness and credentials

The API accepts exactly one of DATABASE_URL or DATABASE_URL_FILE; file credentials
are read once at startup, trimmed, and never logged. The PostgreSQL initializer
similarly accepts exactly one of SOIL_SERVE_PASSWORD or SOIL_SERVE_PASSWORD_FILE.
Existing environment configuration remains supported. Forest mounts credentials
from ignored host secret files, readable by the existing container identities.

The API's --healthcheck command probes local /v1/metadata with a three-second
absolute deadline and a 64 KiB response limit. Success requires HTTP 200, ready=true,
and, when SOIL_DATA_RELEASE is configured, that exact active release. It returns a
nonzero exit status without response/credential logging on failure. A missing or
wrong release must not appear healthy. Clients do not depend on API health for
startup: their bounded SDA fallback must remain available during mirror outages.

## Nationwide rollout and staged import

The shared forest default requires nationwide SSURGO and STATSGO2. The initial
Idaho/VI import is historical qualification only, not sufficient shared coverage.
Use the official national archives and retain their actual catalog/scope/vintage.

The importer accepts --no-activate to commit a fully validated candidate release
without changing soil.active_release. Default behavior remains atomic import and
activation for existing callers. The receipt records whether activation is included.
Staged loading avoids suspending shared job processing throughout a national COPY.
Activate the validated candidate in a separate transaction only while coordinating
client release pins and the API healthcheck. Old releases and caches remain intact.
