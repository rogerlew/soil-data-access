# Project cache snapshot contract

The operator authorized publishing selected soil cache snapshots through Git LFS
on 2026-11-17 (Pacific). Only sanitized soil data and reviewed soil artifacts may
be published. Private run paths, raw project configuration, and source-to-case
mappings remain under ignored data/parity/. This is an explicit exception to the
default exclusion of downloaded data from Git; it does not authorize publishing
whole projects.

## Acquisition and compatibility

Open source SQLite files with mode=ro and query_only; use the SQLite backup API
into memory so committed WAL data is included. Never set source journal mode,
checkpoint, or invoke WEPPpy initialization. If a WAL exists without its shared
memory file, stop rather than create that file. SQLite may coordinate readers
through existing shared memory; no source database or WAL writes are permitted.
Hash database and WAL before/after, verify metadata stability while hashing, and
reject detected concurrent changes. Capture is bounded by time and byte limits.

Backups are retained privately. Public fixtures are newly constructed SQLite
files containing only the exact expected cache tables/indexes, preserving column
values, storage types, rowids, and negative-key records. This removes unused pages
that could contain deleted private data. Reject unexpected schema or values
containing private paths; do not redact or alter soil values to obtain acceptance.
Compare logical content before/after reconstruction, run integrity_check, and
record both acquisition and publication hashes. No live-source immutable flag.

## Evidence and limitations

Use anonymous sequential case IDs, WEPPpy cache labels, complete table schemas/counts,
selected keys, source-file hashes, known sidecar generation time, and explicit
unknown source release and historical code/configuration. The currently deployed
revision is observation context, not proof of the revision that built old soils.
Include negative records as evidence, not proof all requested keys are complete.
Freeze coverage and reproducible reference builds separately before claiming parity.

LFS stores fixture SQLite files. JSON manifests and provenance stay normal Git.
Validation must test committed WAL capture, source preservation, rejection of
schema drift, rowid/null/type preservation, and removal of deleted-page payloads.
Before pushing, verify LFS pointers and object hashes; after pushing verify remote
object retrieval. These snapshots are test fixtures, not raw USDA export tables.

## Observed historical schema and sidecar handling

The acquired caches recreate negative-key tables without primary keys. The
schema contract explicitly permits both that historical form and the initialized
primary-key form; preserve duplicates and rowids in either case. Do not migrate
reference data to the current initialization schema.

SQLite mode=ro alone can create empty WAL/shared-memory sidecars when a database
header specifies WAL but those files are absent. The first SSURGO acquisition
attempt failed without yielding an accepted snapshot; its exception text was not
retained. Empty sidecars were observed before the successful retry, with creation
time matching that attempt, so the read-only open appears to have created them. The source database retained
its earlier size and modification time. No production cleanup was attempted.
The collector now checks the database header and refuses that condition before
opening SQLite; a regression test verifies it creates neither sidecar. Existing
shared-memory reader coordination is still permitted. The checks are not an OS
filesystem write barrier; before/after fingerprints reject detected source changes.

## Cache labels and source coverage

`cache_label` and case-name prefixes identify the WEPPpy collection/cache path;
they do not classify every contained MUKEY. `--dataset` is the acquisition CLI's
cache-label argument. Both collection paths call the same SDA query helpers,
without a dataset predicate. gNATSGO can supply STATSGO2 MUKEYs through the default
SSURGO path. Classify coverage against source catalogs/releases and retain unknowns;
absence from an old STATSGO catalog does not prove SSURGO provenance.

The paired historical artifacts for ssurgo-004 preserve all model-consumed bytes.
Only the project path in the single `Source File` comment is replaced with
`:<project>/soils/667003.sol` in treated/model files. The base file is unchanged.
Original and published hashes are retained; raw originals remain private. This
specific non-model path field is the only publication redaction for these
historical fixtures. Offline repeatability additionally treats Build Date as a
volatile comment value under docs/offline-reference-contract.md. It does not permit blanket comment removal or numerical normalization.
