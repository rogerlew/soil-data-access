# Unofficial Soil Data Access

An independent soil-data API intended to remain usable during USDA service outages.

## Status

Contract-first assessment. No API, importer, database, or Compose stack is
implemented yet. The initial release will be gated by project SQLite cache and
generated-soil parity for declared WEPPpy workflows. Full SDA parity is deferred;
upstream availability does not block this bounded implementation. No release gate
has passed yet.

## Architecture and API direction

The assessment recommends Rust with PostgreSQL/PostGIS and Docker Compose
deployment. The complete runtime stack is not yet adopted.
Start with a documented subset of SDA's `/Tabular/post.rest` query behavior and
JSON responses. Coordinate a WEPPpy XML-to-JSON migration with parser and final
soil-file parity tests. XML compatibility remains a separate assessment item.

SSURGO and STATSGO2 coverage, SQL Server translation, public-client compatibility,
and performance require evidence. This is not an official USDA service.

## Developer entry points

- [Behavior contract](docs/contract.md): scope, data, security, and acceptance.
- [Implementation plan](docs/implementation-plan.md): milestones and current state.
- [WEPPpy release gate](docs/wepppy-release-gate.md): corpus, artifact parity, and deployment requirements.
- [Milestone 1 assessment](docs/milestone-1-assessment.md): source audit and remaining gaps.
- [Rust/Go recommendation](docs/dependency-evaluation.md): reproducible probes and tradeoffs.
- [Current WEPPpy queries](contracts/wepppy-queries.json): five extracted query
  families with provenance; synthetic keys and no captured responses yet.
- [Contributor guidance](AGENTS.md).

Validate the initial inventory from this repository:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_assessment.py
```

## Operations and licensing

Portable Compose configuration belongs here; environment-specific deployment
integration belongs in open-wepp-org. The host, route, TLS, and capacity are not
selected. Production infrastructure has not been changed.

Code and documentation are licensed under the [MIT License](LICENSE).
USDA source attribution and data-release metadata are retained independently;
the code license does not relicense third-party datasets.
