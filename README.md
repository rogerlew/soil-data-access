# Unofficial Soil Data Access

An independent soil-data API intended to remain usable during USDA service outages.

## Status and architecture

The Rust API, PostgreSQL/PostGIS Compose stack, official-source importer and cache
replay tools implement five bounded WEPPpy query families. Frozen project-cache records
and authored wire cases can be checked through the real API/database. This is an
unofficial service serving national SSURGO and STATSGO2 datasets on forest development.

The [WEPPpy JSON client](docs/wepppy-client-integration.md) now records server,
release, cache retrievals, and base-soil provenance. Fresh-cache replay matches
501 canonical artifacts in the frozen numerical environment. Forest now serves the
official national SSURGO October 2026 and STATSGO2 October 2016 releases. Real queued builds for
two keys outside replay fixtures match direct-file references through the mirror
and warm SDA-cache fallback, including 76 prepared soil files per case.

[Forest evidence](docs/forest-validation.md) covers import, source selection,
readiness, runtime controls and bounded performance. Shared forest WEPPpy client defaults are active following exact-revision approval;
the initial canaries verified 152 prepared soil inputs. The [national recovery](docs/nationwide-recovery-plan.md)
loaded 22,073,263 rows, verified both source datasets, and rebuilt the failed Colorado
project with 32 prepared hillslope soils. Comprehensive live SDA parity, public
hosting and broader workflow coverage remain follow-ups.

## Local setup

Requires Docker Compose, Python 3, and Git LFS. Rust 1.92.0 is needed for native
checks; Docker builds pin the compiler and image digests. From a clean checkout:

```bash
git lfs pull
python3 scripts/init_local_env.py
export COMPOSE_PROJECT_NAME=soil-replay-local
docker compose config --quiet
docker compose up -d --build
curl --fail http://127.0.0.1:18080/v1/metadata
```

The initialization script creates .env once with random local credentials and the
current source revision. Do not overwrite existing credentials or change them for
an initialized volume without a database password migration. Before validating a
new committed build, update CODE_REVISION in .env to that commit. Metadata initially
reports ready=false until an explicit official or replay import activates a release.

To exercise every complete fixture, authored examples, and operational checks on
this new empty database:

```bash
python3 scripts/verify_runtime.py --receipt data/parity/runtime-validation.json
```

This harness mutates only the selected local test stack and refuses an already
populated release table. For another full run, choose a new COMPOSE_PROJECT_NAME
and an unused SOIL_HTTP_PORT, or stop the previous stack first. Keep previous
volumes/evidence; do not delete persistent volumes as routine cleanup.

For a single fixture instead of the full harness:

```bash
python3 scripts/replay_cache.py --case ssurgo-004 --output data/parity/replay.sql
docker compose exec -T db psql -U soil_import -d soil -v ON_ERROR_STOP=1 < data/parity/replay.sql
curl --fail http://127.0.0.1:18080/v1/metadata
```

A duplicate release import fails transactionally. The incomplete shared STATSGO
fixture is deliberately rejected. Stop local containers with `docker compose down`;
the named data volume remains. WEPPcloud environment wiring lives in WEPPpy Compose; public openwepp.org hosting
is separately owned by open-wepp-org.

## API and configuration

| Endpoint | Behavior |
| --- | --- |
| GET /v1/metadata | Unofficial identity, readiness, code revision, active release manifest |
| POST /Tabular/post.rest | Form fields query and format=JSON+COLUMNNAME; five exact parsed shapes |

The [JSON profile](docs/wepppy-json-profile.md) defines ordered headers, string/null
cells and release headers. The [runtime contract](docs/runtime-contract.md) defines
admission, resource bounds and replay assumptions. XML and arbitrary SQL are unsupported.

| Setting | Purpose |
| --- | --- |
| SOIL_IMPORT_PASSWORD | Local database initialization/import credential |
| SOIL_SERVE_PASSWORD | Separate SELECT-only API credential |
| CODE_REVISION | Exact lowercase 40-character source revision |
| SOIL_HTTP_PORT | Localhost published HTTP port; default 18080 |
| COMPOSE_PROJECT_NAME | Isolates test containers, network and volume |
| DATABASE_URL_FILE | API credential file; mutually exclusive with DATABASE_URL |
| SOIL_SERVE_PASSWORD_FILE | Initializer credential file; mutually exclusive with SOIL_SERVE_PASSWORD |
| SOIL_DATA_RELEASE | Expected release for the API --healthcheck command |

PostgreSQL has no published port. API success logs contain request IDs, query family,
release and row count. Use `docker compose logs api` for those records. See the
[security review](docs/runtime-security-review.md) for controls and open public gates.

## Developer checks

```bash
cargo test --locked
cargo clippy --locked --all-targets -- -D warnings
python3 -m unittest discover -s tests -v
python3 scripts/verify_assessment.py
python3 scripts/verify_runtime_evidence.py
python3 scripts/verify_corpus.py
python3 scripts/verify_wepppy_reference.py --verify-published
```

src/planner.rs admits frozen query shapes; src/main.rs executes owned SQL with bound
keys. scripts/replay_cache.py reconstructs test tables from processed caches and
rejects conflicting map-unit attributes. It is not a production importer.
scripts/import_official.py imports original GeoPackage/legacy ZIP data transactionally;
see the [official import contract](docs/official-import-contract.md).

- [Contributor guidance](AGENTS.md) and [implementation plan](docs/implementation-plan.md).
- [Behavior contract](docs/contract.md) and [WEPPpy release gate](docs/wepppy-release-gate.md).
- [Reference findings](docs/reference-deviations.md) and [reproduction](docs/offline-reference-contract.md).
- [Rust/Go assessment](docs/dependency-evaluation.md) and [runtime dependencies](docs/runtime-dependencies.md).

Code and documentation use the [MIT License](LICENSE). USDA data attribution and
third-party component licenses remain independent; MIT does not relicense them.
