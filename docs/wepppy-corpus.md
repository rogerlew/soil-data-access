# WEPPpy cache fixtures

These are historical processed WEPPpy caches, acquired on wepp1 on
2026-11-18 UTC (2026-11-17 Pacific), and published with operator authorization.
They are not raw USDA tables, a complete parity corpus, or proof of deployment
readiness. Source release, historical WEPPpy/native revisions, and build
configuration remain unknown. Current host checkout observation was
`917708c90dce46bbab920ecf9ce5f315e8611290`; this does not date the original outputs.

## Contents

| Case | Cached map units | Components | Horizons | SQLite bytes |
| --- | ---: | ---: | ---: | ---: |
| ssurgo-001 | 237 | 1,041 | 3,086 | 819,200 |
| ssurgo-002 | 38 | 133 | 713 | 200,704 |
| ssurgo-003 | 227 | 758 | 3,828 | 843,776 |
| ssurgo-004 | 3 | 22 | 75 | 69,632 |
| statsgo-001 | 0 | 0 | 0 | 61,440 |
| statsgo-002 | 353 | 4,096 | 13,055 | 3,084,288 |

All five negative-key tables are included. SSURGO fixtures contain 1,619, 265,
and 1,212 negative-key rows respectively. Those rows record cache lookups, not
verified invalid-soil or fallback decisions. The STATSGO fixture is entirely
empty, including its negative-key tables; it tests an empty historical cache,
not successful STATSGO soil construction. Coverage-directed selection, named fallback-path
coverage and complete reference regeneration remain necessary.

ssurgo-004 is a project cache containing three MUKEYs in the vendored STATSGO
catalog. Its base, forest-treated, and actual WEPP model-input artifacts for
MUKEY 667003 / component 14222716 (Hutson) are retained in Git LFS under
`ssurgo-004/artifacts/`, with hashes in `artifacts.manifest.json`. The source
header says `Surgo`; catalog membership establishes why the cache label cannot
classify the data. Project paths in two provenance comments are redacted according
to the snapshot contract; all model payload bytes are unchanged.

statsgo-002 is the older shared WEPPpy tabular cache, not a project-local cache.
Its source bytes match the local checkout and wepp1 (SHA256
`b816dd1b5b0a1b815a2e3dddb60243d3af634c40a62667096c1db7c3fbe05a7f`).
It provides positive STATSGO records but is not assumed to match the current
USDA release or the exact input vintage of any historical generated soil.

## Dataset interpretation and discovery

WEPPpy's `use_statsgo` flag sets the collection label; the caller chooses the cache
path. Both paths use the same `_fetch_*` helpers and SDA endpoint, filtering by
MUKEY/COKEY/CHKEY without a dataset predicate. Therefore `cache_label`, case prefixes,
and generated `Source Data` headers do not establish source-dataset membership.
NRCS describes gNATSGO as a combination of SSURGO, STATSGO2 gap-fill data, and Raster
Soil Surveys ([source](https://www.nrcs.usda.gov/resources/data-and-reports/gridded-national-soil-survey-geographic-database-gnatsgo)).

The direct-run inventory checked 25,357 candidates and found only one explicitly
STATSGO-named cache, which was empty. A separate search using catalog MUKEYs found
two projects with matching STATSGO map-unit/component IDs in actual `wepp/runs`
soil inputs, despite their SSURGO cache names and `Surgo` headers. One project is
retained as ssurgo-004. Exact run mappings remain private.

[Catalog classification](../artifacts/wepppy-parity/statsgo-catalog-classification.json)
records matching MUKEYs and catalog hashes. Nonmembership in that older catalog
is not proof of SSURGO provenance; current release coverage still needs independent
validation. The named STATSGO fallback execution path has not been proved merely
by finding STATSGO data through the ordinary gridded path.

## Storage

Each case lives under `fixtures/wepppy/<case>/`: `cache.sqlite` is a Git LFS
object; `cache.manifest.json` is normal Git JSON with fingerprints, schema,
row counts, per-table logical hashes, keys, and explicit unknown provenance.
Do not change frozen fixtures to match candidate output. Add a new version/case
and explain any future replacement.

The upstream soil information is attributed to USDA NRCS SSURGO/STATSGO2 as
reported by the project sidecars. WEPPpy processed and cached these projections.
The repository MIT license applies to code/documentation; it does not imply USDA
endorsement or relicense third-party data. No private run names, project paths,
raw configuration, or deleted database pages are published.

## Retrieve and verify

From this repository with Git LFS installed:

    git lfs pull
    python3 scripts/verify_corpus.py
    python3 -m unittest discover -s tests -v

The corpus verifier fails for missing LFS objects, changed bytes, schema-contract
hash drift, logical-row differences, or integrity errors. Its success message is
`verified_snapshot_not_parity`. It does not rebuild soils or verify the mirror.
The implementation uses the Python standard library; acquisition requires Python
3.11 or later for SQLite serialization and file hashing.

## Acquisition and publication

The [snapshot contract](corpus-snapshot-contract.md) defines source access,
historical schema variants, privacy boundaries, and the SQLite sidecar incident.
`scripts/snapshot_project_corpus.py` accepts `--source`, `--dataset` and
`--expected-host`; it emits private acquisition JSON on stdout. On wepp1 the script
was streamed into `nice -n 15 python3 -` over SSH, with explicit host verification.
Raw acquisition JSON and source-to-case mappings stay in ignored `data/parity/`.
No temporary snapshot files were written on wepp1. Existing SQLite shared-memory
reader coordination is distinct from changing source database/WAL contents.

For an already acquired private payload, publish to a new case path:

    python3 scripts/publish_cache_fixture.py data/parity/acquired/CASE.json fixtures/wepppy/CASE/cache.sqlite --case-id CASE

Replace CASE with an approved `ssurgo-NNN` or `statsgo-NNN` identifier. The tool
refuses an existing destination. It reconstructs a fresh database with only the
allowlisted schema, copies all values and rowids, compares type-aware logical
hashes, and requires zero free pages plus a successful integrity check. Nulls,
precision, duplicates, and historical negative-table constraints are preserved.
The public database hash intentionally differs from the private backup hash.

## Remaining reference work

Capture matching model configuration, dependency revisions, and soil assignments.
Expand the paired `.sol`/`wepp/runs` artifact capture beyond ssurgo-004 with change
detection; the cache and file acquisitions are not an atomic whole-project snapshot.
Rebuild the reference offline, classify historical differences, and measure case
coverage (shallow/null/restriction/missing/fallback/treatments) before freezing the
complete corpus. Snapshot integrity alone cannot close that release gate.

## Offline reference extension

The paired ssurgo-004 case now includes an allowlisted reference-inputs.json and
the captured treatment-lookup.csv (LFS). Raw NoDb files and source paths remain
private. Other caches use explicitly authored profiles. The canonical generated
reference is fixtures/wepppy/reference-v1.tar.gz (LFS), with two complete reports
and a member-hash receipt under artifacts/wepppy-parity. See the
[reference contract](offline-reference-contract.md) for reproduction and
[deviation ledger](reference-deviations.md) for the incomplete shared cache,
legacy invalid/error outcomes, historical writer drift, and coverage gaps.
