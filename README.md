# Unofficial Soil Data Access

An independent soil-data API intended to remain usable during USDA service outages.

## Status

Contract-first assessment. No API, importer, database, or Compose stack is
implemented yet. This repository contains the initial contracts and query inventory.

## Architecture and API direction

Evaluate PostgreSQL/PostGIS and a Rust or Go API, with Docker Compose deployment.
Start with a documented subset of SDA's `/Tabular/post.rest` query behavior and
JSON responses. Coordinate a WEPPpy XML-to-JSON migration with parser and final
soil-file parity tests. XML compatibility remains a separate assessment item.

SSURGO and STATSGO2 coverage, SQL Server translation, public-client compatibility,
and performance require evidence. This is not an official USDA service.

## Developer entry points

- [Behavior contract](docs/contract.md): scope, data, security, and acceptance.
- [Implementation plan](docs/implementation-plan.md): milestones and current state.
- [Current WEPPpy queries](contracts/wepppy-queries.json): five extracted query
  families with provenance; synthetic keys and no captured responses yet.
- [Contributor guidance](AGENTS.md).

Validate the initial inventory from this repository:

```bash
python3 -m json.tool contracts/wepppy-queries.json > /dev/null
```

## Operations and licensing

Portable Compose configuration belongs here; environment-specific deployment
integration belongs in open-wepp-org. The host, route, TLS, and capacity are not
selected. Production infrastructure has not been changed.

Code and documentation are licensed under the [MIT License](LICENSE).
USDA source attribution and data-release metadata are retained independently;
the code license does not relicense third-party datasets.
