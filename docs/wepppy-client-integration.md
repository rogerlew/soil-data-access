# WEPPpy JSON client integration

The coordinated WEPPpy change uses explicit operator selection of endpoint,
wepppy-json-v1 profile, and immutable release ID. Its canonical contract is
[soil-data-source-provenance-contract.md](https://github.com/rogerlew/wepppy/blob/task/ssurgo-json-provenance/docs/schemas/soil-data-source-provenance-contract.md),
with an [operator guide](https://github.com/rogerlew/wepppy/blob/task/ssurgo-json-provenance/docs/dev-notes/soil-json-source.md).
XML remains the default; there is no automatic failover. JSON project caches have
separate source identities and additive retrieval evidence. Generated base soils
have hash-verified provenance sidecars; scientific .sol bytes remain unchanged.

## Acceptance procedure

scripts/run_wepppy_json_parity.py reuses the real reference builder with an explicit
source identity and absent candidate cache. It does not replace HTTP, query helpers,
model code, or writers. Activate one previously validated test replay release in
the local Compose database, then run the matching case through the actual API.
Use scripts/replay_cache.py to create a disposable replay database if needed;
these caches are processed test projections, never a production import.

Attach the candidate container only to the Compose internal database network. The
runner requires external connect errno 101, validates its imported checkout, and
records source hashes and numerical environment. Run each of the six frozen cases
with --case, --endpoint, --wepppy-root, --wepppy-revision, and a new --output directory.
The host must verify the supplied revision against the clean checkout; the runner
records actual source hashes because worktree Git metadata is outside the container.
Select the matching replay-CASE-CACHEHASH12 release before each complete case.

Require identical decision records, positive-cache row multisets, negative-key sets,
and all canonical soil artifact hashes. Negative-key sets intentionally disregard
repeated historical negative markers; they represent the same absence. Separately
verify every base-soil sidecar against the output bytes and expected source identity.
Only Build Date and Source File comment values are excluded, as frozen before this
implementation. The incomplete statsgo-002 case remains excluded, never backfilled.
The empty statsgo-001 case provides no positive STATSGO coverage; ssurgo-004 does.

## Numerical environment

The existing development image is not the frozen reference environment: Python,
libc, and Rosetta code differ. Its first paired-case run failed two diagnostic
comment comparisons by roughly 2e-15, although treated/model files matched. That
failure is retained; exclusions and tolerances were not widened. The matched run
uses read-only host interpreter/library/virtualenv mounts in the same externally
isolated client container, with the candidate checkout and existing native modules.
This checks transport parity under matching inputs and numerical dependencies.
It does not certify numerical equivalence of an eventual deployment image.

Full NoDb/RQ/raster orchestration, fallback/assignment coverage, official-source
import, capacity targets, intended-host recovery and rollout remain the service
release gates. A bounded replay pass does not authorize public deployment.

## Retained result

The [validation receipt](../artifacts/wepppy-parity/json-client/validation.json)
identifies WEPPpy 39f24ce92, runtime 9dc2264 and harness 60a699f. All 24,049 positive
cache rows match; 34 successful HTTP events establish fresh retrievals. The complete
cases retain 499 valid soils, six non-valid outcomes, 501 matching canonical files,
and 499 verified base-soil sidecars. The known null-texture worker rejection was
also reproduced directly from the candidate cache with the reference defaults.
The empty and incomplete cases remain distinct. Reports retain the initial image
failure, matched environment, source hashes, selections, cache counts and sidecar hashes.
