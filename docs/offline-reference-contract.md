# Offline WEPPpy reference contract

This stage establishes a reproducible legacy reference from frozen cache fixtures.
It does not exercise the new service or certify an entire project replay. Use a
clean, pinned WEPPpy checkout, record the interpreter and numerical dependencies,
and run in a fresh Linux network namespace with no external interfaces/routes.
Import real WEPPpy code; do not stub fetchers, soil models, Rosetta, or soil writers.
Missing required dependencies fail explicitly.

## Inputs and scope

Copy each hashed frozen SQLite fixture into a new writable scratch directory.
Prove that requested component keys and their horizon/restriction/fragment/texture
lookups are represented by rows or explicit negative-cache markers before calling
SurgoSoilCollection. Missing coverage fails as an incomplete reference; never fetch
or synthesize missing upstream rows. Require zero cache synchronization misses.
Keep every valid/invalid result and component/horizon selection in the report.

For ssurgo-004, capture an allowlisted scientific configuration and assignment
projection from raw JSON NoDb state, without constructing live NoDb objects or
publishing raw configuration. Retain state-file hashes and unknown historical
commit values. Read and hash the actual project treatment lookup. Capture inputs
with before/after stability checks; do not claim an atomic historical project
snapshot. The selected project has initial_sat=0.75, ksflag=False, forest treatment,
9002 treated soils, and no clipping/kslast override. Confirm these in saved inputs.

Other cache fixtures use an explicitly authored reference profile (initial_sat=0.75,
ksflag=True, no experimental retention policy), not an assertion about historical
project settings. Build all cached MUKEYs, plus explicitly recorded negative keys.
Report content/behavior coverage and gaps; the reference suite is not complete
merely because ordinary profiles succeed.

Exercise the real base-soil builder and writer. For the paired project, exercise
its soil utility conversion and model-input preparation with captured values.
Retain historical comparisons separately from two-run repeatability. Differences
must remain visible; never copy expected soil contents into newly generated output.
Full NoDb/RQ workflow, raster assignment computation, and migrated API execution
remain later acceptance gates.

## Comparison and publication

Require exact output bytes after replacing only two named non-model comment values:
Build Date and Source File. Preserve the comment prefixes, line endings, every
other comment, and all model-consumed bytes. Build Date is a new declared exclusion
because legacy builders insert the wall-clock time on each build; Source File
contains scratch/project paths. These exclusions are fixed before comparison and
must not expand automatically after a mismatch. Keep raw and canonical hashes.

Generated references may be published through Git LFS with sanitized reports and
input manifests. A historical mismatch is not waived by repeatability; classify
its cause and retain both artifacts. No rounding, line-ending normalization, row
sorting that affects selection, or blanket removal of comments is allowed.

## Reproduce and verify

The retained builds use WEPPpy revision
917708c90dce46bbab920ecf9ce5f315e8611290, Python 3.12.3, NumPy 1.26.0,
SciPy 1.13.1, and DuckDB 1.1.1. Exact native/model hashes are in the reports.
Use a clean checkout at that revision and a compatible WEPPpy environment with
Rosetta's local model database. Linux unprivileged user/network namespaces and
`unshare` are required. The runner rejects dirty tracked files, another revision,
network access, missing cache closure, and existing output directories.

From this repository, with that checkout at data/parity/wepppy-reference:

```bash
/workdir/wepppy/.venv/bin/python scripts/run_wepppy_parity.py \
  --wepppy-root data/parity/wepppy-reference --output data/parity/reference-new-a
/workdir/wepppy/.venv/bin/python scripts/run_wepppy_parity.py \
  --wepppy-root data/parity/wepppy-reference --output data/parity/reference-new-b
python3 scripts/verify_wepppy_reference.py \
  data/parity/reference-new-a data/parity/reference-new-b \
  --receipt data/parity/reference-new-comparison.json
```

Use new directories after a failed run; retain diagnostics instead of overwriting
partial evidence. `--publish fixtures/wepppy/<new-name>.tar.gz` additionally creates
a deterministic canonical archive without overwriting an existing file. Review
privacy and deviations before adding a new artifact or changing the baseline.

For a normal checkout, fetch LFS objects and verify the published reference:

```bash
git lfs pull
python3 scripts/verify_corpus.py
python3 scripts/verify_wepppy_reference.py --verify-published
python3 -m unittest discover -s tests -v
```

The published checker verifies report, input, archive, and individual member
hashes without extracting files or rebuilding models. It is an integrity check,
not a fresh numerical replay. [Findings and limitations](reference-deviations.md)
record 499 valid soils, six non-valid outcomes, 501 repeatable files, historical
comparison results, and remaining workflow coverage.
