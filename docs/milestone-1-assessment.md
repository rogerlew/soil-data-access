# Milestone 1: source and compatibility assessment

Date: 2026-11-17. Status: **partially complete; upstream wire capture blocked**.
The source audit, offline query evidence, compatibility inventory, and language
assessment are complete for the inspected samples. There is no runtime service.

## What was observed

Both official SDA hostnames returned HTTP 502 and HTML to a bounded SELECT query.
The capture tool stopped each endpoint after its first 5xx. Saved bodies and
SHA-256 checksums are in [capture evidence](../artifacts/assessment/sda-capture-01/observations.json).
These are availability observations, not examples of SDA's application error contract.

The independent USDA Box downloads were reachable. The [published listing](../artifacts/assessment/download-listings.json)
contains `SQLite_SSURGO_US.7z` at **31,549,528,132 bytes** (31.55 GB compressed).
The accompanying README identifies the October 1, 2026 release, comprising the
GeoPackage plus separate national/regional rasters. The older website's 28 GB
figure is not the current archive size. National extracted size, PostgreSQL index
size, and full key coverage were not measured; the national archive was not fetched.

## Actual download audits

| Observation | SSURGO Guam | STATSGO2 Virgin Islands |
| --- | --- | --- |
| Source artifact | `SQLite_SSURGO_GU.7z` | `wss_gsmsoil_VI_[2016-10-13].zip` |
| Download bytes | 4,231,766 | 2,685,941 |
| Inspected storage | 21,622,784-byte GeoPackage | Pipe-delimited text plus embedded table/column metadata |
| Survey catalog | GU640; version 11; 2026-09-11 | US; version 3; 2016-10-13 |
| Map units | 56 | 8 |
| Components | 220 | 99 |
| Horizons | 543 | 370 |
| Six required source tables | All present | All present |
| Checked relationship orphan counts | Zero | Zero |
| Real selected mukey | 465534 | 1390211 |

See [SSURGO audit](../artifacts/assessment/ssurgo-gu.json) and
[STATSGO2 audit](../artifacts/assessment/statsgo2-vi.json) for complete selected-table
schemas, counts, checksums, source keys, and query results. The latter archive is
an official downloadable sample, but its 2016 vintage is not evidence of parity
with today's SDA. The currently linked STATSGO2 CONUS archive is also named for
2016-10-13 and listed at 446,108,728 bytes. Confirm current SDA vintage after recovery.

All five WEPPpy query families were exercised against each sample. For the legacy
STATSGO2 archive, an in-memory SQLite inspection database retains text values and
converts empty source fields to null. It is an audit representation, not a
production PostgreSQL import or a wire-format golden fixture.

## Findings that affect implementation

1. The original component join ends in `ORDER BY mukey`. SQLite reports an
   ambiguous column; the audit explicitly qualifies it as `component.mukey` and
   preserves both SQL forms. The translator must resolve output names and aliases
   from the parsed query and schema, rather than blindly replace SQL text.
2. GeoPackage keys are stored as integers in the inspected sample; legacy metadata
   defines keys as strings. PostgreSQL schema and literal binding need an explicit
   common representation without losing identifiers or changing numeric semantics.
3. The GeoPackage geometry column is `shape`; SDA spatial queries use
   `mupolygongeo` and SQL Server methods. The inspected spatial reference is EPSG:4326.
   A compatibility view/expression mapping and geometric parity tests are required.
4. The SSURGO texture query returned 19 rows for 16 horizons. Do not collapse rows
   by horizon key in the service; WEPPpy's existing downstream selection behavior
   must be evaluated separately during JSON migration.
5. The selected SSURGO fragment query has no rows, providing a useful source-data
   empty case. It does not tell us how SDA serializes an empty response.
6. The national SSURGO listing and a sample cannot establish inclusion of all
   STATSGO2 keys. Keep separate source manifests and verify coverage explicitly.

## Public-client and wire contract

[Compatibility matrix](../contracts/compatibility.json) distinguishes initial
targets, candidates, exclusions, and evidence status. No entry claims implemented
runtime support. [Capture cases](../contracts/capture-cases.json) contain real
sample keys, the five query families for both datasets, XML/JSON metadata variants,
an empty-key query, invalid syntax, and null/decimal values.

The initial request encoding is form-urlencoded, retaining `query` and `format`.
Use `JSON+COLUMNNAME` as the initial WEPPpy integration target. The plus signs must
be percent-encoded in the form, not decoded to spaces. Exact JSON value types,
null representation, and empty-result envelopes remain unfrozen pending observation.

The inspected soilDB client requests `JSON+COLUMNNAME+METADATA`. Its parser expects
column names first, metadata strings second, then data rows. Supporting only the
WEPPpy format will not satisfy that client. soilDB also exercises multiple result
sets, survey joins, CTE-style aggregation, and spatial helper functions; multipart
queries remain explicitly excluded from the initial service. The pinned source
revision and inspected files are in [source provenance](../artifacts/assessment/soildb-source.json).

Service-owned metadata/error schemas are defined independently of USDA parity in
[the contract](contract.md#service-owned-metadata-and-errors). Examples are marked
as authored service examples, not captured SDA output. This allows implementation
of operational behavior while retaining honest wire-compatibility boundaries.

## Reproduce and resume

From the repository root, run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_assessment.py
python3 scripts/verify_assessment.py --require-live
```

The first two commands pass. The third intentionally exits 1 while live evidence
is missing. This is a closure gate, not a failed claim of completed parity.

Archive source URLs, hashes, and local filenames are retained in
`artifacts/assessment/*.manifest.json`. Reacquire those exact public URLs, verify
the hashes, and extract the Guam archive using 7-Zip. Keep large data in ignored
`data/`. Repeat the source audit with:

```bash
python3 scripts/audit_sources.py \
  --gpkg data/gu/SQLite_SSURGO_GU/SQLite_SSURGO_GU.gpkg \
  --statsgo-zip data/STATSGO2_VI_2016.zip \
  --output artifacts/assessment
```

After upstream recovers, create a new capture directory (never overwrite evidence):

```bash
python3 scripts/capture_sda.py --output artifacts/assessment/sda-capture-02
```

Review captured release identity and raw responses before promoting them to parity
fixtures. Freeze success/empty/error schemas and expected types only from that
review. Add case-sensitive names, decimal/null cases, and paired XML-to-JSON
consumer tests; then update the matrix and close milestone 1. National import,
PostgreSQL semantic execution, security review, and service load testing remain
later gates. No USDA load testing is authorized by this assessment.

## Sources

- [USDA SSURGO Portal](https://www.nrcs.usda.gov/resources/data-and-reports/ssurgo-portal)
- [USDA STATSGO2 description and download gateway](https://www.nrcs.usda.gov/resources/data-and-reports/description-of-statsgo2-database)
- [Official SSURGO download folder](https://nrcs.app.box.com/s/w0gtf7ooxqfcd0cgfht5zprcmc8qvu0i)
- [Official STATSGO2 download folder](https://nrcs.app.box.com/v/soils/folder/422953242128)
- [soilDB source](https://github.com/ncss-tech/soilDB)
