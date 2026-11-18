# WEPP1 cache discovery

Observed on verified host `wepp1`, 2026-11-18 00:12–00:17 UTC
(2026-11-17 16:12–16:17 PST). This is bounded discovery, not a complete
host inventory or a frozen parity corpus.

## Findings

Two metadata passes found **35 distinct SSURGO caches**. The first scanned 190
direct run directories and found 31 caches: 30 had `.sol` files in `soils`,
28 had `.sol` inputs in `wepp/runs`, and 30 had SQLite WAL files. The second
sampled 33 runs across other prefixes and found four additional SSURGO caches.
No STATSGO caches were observed; absence from these samples does not establish
absence on the host. Neither pass reported permission errors.

Three SSURGO provenance sidecars report 38–237 requested map units, 133–1,041
component records, and 713–3,828 horizon records. All report restrictive-layer,
fragment, and texture records, plus nonzero negative-cache counts. These are
promising candidates for ordinary and missing-record behavior, not verified
coverage of shallow soils, nulls, invalid soils, fallback, or treatment variants.
Sidecar counts can be stale and must be checked against consistent snapshots.
Their August–October 2026 generation timestamps do not identify USDA release dates.

Thirty of the first 31 database files were only 4 KiB while WAL files were present.
Database-file size alone therefore understates the available cache data. Preserve
committed WAL contents through the planned SQLite backup procedure; do not copy
only the database file or use immutable mode against a live source.

## Method and retained evidence

Commands used: `ssh -o BatchMode=yes -o ConnectTimeout=10 wepp1` with `hostname`,
`pwd`, `date -u`, and directory checks; then scripts streamed into
`nice -n 15 python3 -`. Scripts used directory listings, file metadata, and three
bounded Markdown sidecar reads. No SQLite connections, checkpoints, snapshots,
run changes, service actions, or upstream requests were performed.

A first scan exceeded its 90-second budget and produced no usable inventory.
The replacement checked cache filenames before listing artifacts and retained
partial results after 45 seconds. A second pass used SHA256-sorted prefixes/runs,
at most three runs per prefix, also with a 45-second budget. This is a candidate
sample, not a statistically representative sample. Direct run directories only:
nested scenarios and symlink runs were excluded. File presence does not prove
artifact correctness. Host files were not intentionally written; ordinary read
access can update filesystem access metadata.

[Sanitized evidence](../artifacts/wepppy-parity/wepp1-discovery-summary.json)
contains aggregate counts and hashes of the private evidence. Exact paths, raw
inventories, sidecar text, and the executed scripts remain locally under ignored
`data/parity/discovery/`. No project paths or raw project contents are published.

## Next step

Use the three privately recorded sidecar candidates to implement and test a
consistent read-only-source snapshot procedure. Validate source access semantics,
WAL handling, snapshot integrity, required tables, and negative-key records before
freezing a reference. Capture matching configuration and soil artifacts with
change detection; database consistency alone does not make the whole project an
atomic snapshot. Establish source/code lineage and regenerate the reference with
network fetches disabled.

Continue targeted STATSGO discovery separately; do not label the corpus complete
or infer STATSGO coverage from SSURGO caches. Select additional cases from measured
snapshot contents to fill the release coverage matrix.
