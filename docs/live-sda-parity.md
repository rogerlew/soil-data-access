# Live USDA SDA comparison

This assessment resumes the live capture deferred by the
[milestone 1 assessment](milestone-1-assessment.md#reproduce-and-resume).
The national forest mirror continues to use the published
`wepppy-json-v1` profile and the pinned archive release.
SDA is an independent reference for the five WEPPpy tabular query families.

## Comparison rules

Identify survey versions with `sacatalog.areasymbol`, `saversion` and
`saverest`. A matching record supports the sampled survey vintage. SDA
does not expose a checksum for the entire archive.

Compare raw rows with multiplicity and preserve all text values, including
empty strings and nulls. Compare ordered columns and the requested sort key.
Within ties on that key, compare the row multiset and also record any change
to the first row consumed by WEPPpy. Compare fresh legacy SDA XML, bounded SDA
XML and mirror JSON caches, validity decisions, selected components, and
generated base soils. Compare exact file bytes with the predeclared build
date and source-file comment values excluded. Inspect and record any
remaining difference, including diagnostic comments.

The probe uses selected map units and default base-soil generation.
Workflow and geographic acceptance require additional sampling and prepared
run inputs. XML and USDA-specific JSON metadata and errors remain separate
from the mirror profile.

## Reproduction

Use the deployed national mirror's reachable base URL. Run the following in
the WEPPpy Python environment with the intended WEPPpy checkout on
`PYTHONPATH`. The command writes fresh caches and soil files in the new
output directory. It reads from USDA and the mirror and does not submit jobs.

```bash
PYTHONPATH=/workdir/wepppy /workdir/wepppy/.venv/bin/python \
  scripts/run_live_sda_parity.py \
  --mirror-base "${SOIL_MIRROR_BASE}" --output data/live-sda-parity-repeat
```

Use `scripts/capture_sda.py` with a new output path to repeat wire capture
independently. Its older 502 captures remain historical availability evidence.

## November 20, 2026 UTC results

Both USDA hosts returned the same bodies for 18 queries each. The
[observations](../artifacts/assessment/sda-capture-02/observations.json) retain
hashes for both hosts and selected original bodies for the offline regression.
The [raw comparison](../artifacts/assessment/live-sda-raw-parity.json) records
matches against the mirror's October 1, 2026 SSURGO archive for eight sampled
surveys and the October 13, 2016 national STATSGO2 archive for the US catalog
entry. These are survey-catalog matches.

All sampled raw rows agreed as multisets for horizons, fragments, textures,
and restrictions after exact numeric parsing. Component values differed only
for `geomdesc` on 2 of 26 SSURGO rows and 63 of 74 STATSGO2 rows. SDA JSON
returned an empty string in those cells, while the mirror returned null. The
paired STATSGO2 XML capture contains empty elements for all 26 Virgin Islands
components. The three WEPPpy paths cached the same component rows.

In the [base-soil probe](../artifacts/assessment/live-sda-base-parity.json),
legacy and bounded SDA XML produced the same caches and canonical files.
All three paths agreed on the 11 valid map units and the invalid map unit
49315. The mirror had two first-row selection differences:

| Query | Key | SDA selection | Mirror selection | Observed effect |
| --- | --- | --- | --- | --- |
| Fragments | `chkey=85308733` | 5 | 1 | The changed row belongs to a component that was not selected for map unit 2566696. |
| Restrictions | `cokey=27881215` | Lithic bedrock | Paralithic bedrock | One diagnostic comment changed for map unit 2250500. |

The mirror and legacy builds produced identical model-input lines in all 11
base soils. Ten files were identical after excluding the predeclared volatile
comment values. The restriction diagnostic remained a canonical difference.
Both responses include both tied rows, and the queries only order by the key.
A stable, shared selection rule would require separate scientific acceptance.
Prioritize samples where a tied row affects the selected component or horizon,
and compare prepared run inputs before expanding the parity claim.

## Prepared soils for selected duplicate keys

The follow-up screened the 100 SSURGO map units in the national mirror's
[archive comparison](../artifacts/national/http-parity.json). The archive
prefilter selected the highest-percentage component and its first plausible
horizon. A bounded live screen compared 31 fragment keys, 12 texture keys,
and one restriction key with multiple distinct values. It found two
fragment first-row differences and reproduced the restriction control. The
three sampled survey versions and timestamps matched SDA and the archive.

For each selected case, the standard NoDb single-soil build and WEPP soil
preparation ran on both sources with fresh caches and the same 76-hillslope
watershed template. The build logs confirmed that both tied fragment horizons
were the first exported horizon in their respective soils. The
[prepared-soil receipt](../artifacts/assessment/live-sda-prepared-tie-parity.json)
records the source, selected components and horizons, and output hashes.

| Map unit | Key | SDA cache | Mirror cache | Prepared soil comparison |
| --- | --- | --- | --- | --- |
| 344485 | `chkey=86576543` | 1 | 2 | All 76 files matched after excluding the build-date value. |
| 460290 | `chkey=83755309` | 2 | 10 | All 76 files matched after excluding the build-date value. |
| 2250500 | `cokey=27881215` | Lithic bedrock | Paralithic bedrock | All 76 model-input payloads matched. Each file retained the bedrock diagnostic difference. |

All 228 prepared file pairs had identical model-input lines. The result is
consistent with the current builder deriving WEPP rock content from the
horizon's sieve and size-fraction fields and using the restriction kind for
diagnostics. Retain the samples as bounded single-soil parity evidence.
Broader geographic, multi-OFE, and treatment coverage remain open.

To repeat the preparation, make the comparison scripts available in a
WEPPpy worker environment with access to both services and pass a read-only
template containing `watershed.nodb` and the hillslope and channel parquet
files. Use a new private output directory. The probe calls the ordinary
controllers directly in that environment.

```bash
WEPPPY_NCPU=1 python scripts/run_prepared_soil_tie_parity.py \
  --template /wc1/runs/so/soil-mirror-national-20261118-ssurgo \
  --mirror-base "http://soil-api:8080" \
  --output /tmp/live-sda-prepared-ties
```
