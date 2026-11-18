# Offline reference findings and remaining coverage

Evidence: [repeatability receipt](../artifacts/wepppy-parity/reference-repeatability.json),
[full second-run report](../artifacts/wepppy-parity/reference-run-b.json), and
[negative diagnostic](../artifacts/wepppy-parity/reference-negative-diagnostic.json).
This is a legacy reference, not a candidate service acceptance result.

## Observed outcomes

| Case | Valid soils | Non-valid outcomes | Canonical files |
| --- | ---: | ---: | ---: |
| ssurgo-001 | 232 | 5 | 232 |
| ssurgo-002 | 38 | 0 | 38 |
| ssurgo-003 | 226 | 1 | 226 |
| ssurgo-004 | 3 | 0 | 5 |
| statsgo-001 | 0 | 0 | 0 |
| statsgo-002 | incomplete | not built | 0 |

All 501 emitted files match between independent runs after the declared Build Date
and Source File comment-value exclusions. The 499 valid counts are case/key
instances, not necessarily unique national MUKEYs. The empty cache is an empty-input
case, never positive STATSGO coverage. Positive STATSGO coverage is in ssurgo-004.

## Historical comparison disposition

The paired project's MUKEY 667003 base file has three historical layers versus four
in the current writer. The sole model-payload difference is insertion of the 200 mm
boundary within identical material. WEPPpy ADR-0110, dated 2026-10-29, specifies this
serialization rule. Historical treated and model-input files already have that
boundary and match their rebuilt counterparts. Keep the historical file unchanged;
use the four-layer pinned-code output as the candidate comparison target. Do not
widen canonicalization to ignore layers. The project's recorded commit is unknown;
this observation does not establish its complete historical code lineage.

## Negative outcomes

MUKEYs 464804, 3233036, 3233148, 3233152 (ssurgo-001) and 3424867 (ssurgo-003) have
no valid horizons in the legacy build. Preserve their selected component and
failure logs. MUKEY 474429 returns no soil after a caught legacy worker exception:
null sand becomes the existing 66.8 default alongside 47.5 clay, producing negative
silt rejected by Rosetta. The retained direct worker diagnostic identifies COKEY
28482446 and CHKEY 85480619. Do not repair source data or change model defaults in
this mirror project. A candidate must preserve these outcomes and the diagnostic
cause; a different exception returning no soil is not equivalent evidence.

The shared statsgo-002 snapshot lacks both a corestrictions row and a negative
marker for COKEY 14179042. It is explicitly excluded from complete-cache rebuilds,
retained as a missing-data case, and must not be filled through the candidate API.

## Coverage and limitations

Reports record multiple components/horizons, shallow profiles (maximum bottom at
most 50 cm), null hydraulic/texture fields, restriction kinds, fragment/texture
rows, and negative-cache markers. These are input coverage counts, not proof that
every branch executed or every source family is represented nationwide.

Only ssurgo-004 uses captured project settings, assignments, and the actual forest
treatment lookup. Other complete caches use the documented authored base profile.
The runner exercises real base construction, soil conversion, and model-input
preparation; it does not execute full NoDb/RQ orchestration, recompute raster
assignments, or prove project-level invalid-soil substitution/fallback behavior.
Burn/treatment variants, overrides, multi-OFE behavior, and those assignment paths
remain uncovered. Complete their evidence or explicitly exclude them from the
initial supported workflows before release.

The numerical environment receipt includes Python/package versions, NumPy/DuckDB
native module hashes, Rosetta source/model hashes, and thread settings. It is not a
fully packaged reproducible image or the unknown historical native environment.
Legacy imports attempt optional Redis diagnostics inside the isolated namespace;
those connections fail with network-unreachable while soil construction completes.
No live NoDb objects or services are used. Raw diagnostics and source state remain
private; published inputs contain only the reviewed scientific projection.

Eleven JSON cases are authored and tested against actual legacy XML extraction.
Run B adds those checks to the report; Run A lacks that additional metadata. Both
runs use identical pinned model code, scientific inputs, and numerical environment.
No live SDA response, PostgreSQL translation, migrated client, or production import
is validated by these cases. Raw upstream tie order remains a separate gap.
