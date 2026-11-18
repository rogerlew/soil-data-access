"""Inspect official sample downloads; emit source-data evidence, not SDA responses.

Usage: python3 scripts/audit_sources.py --gpkg PATH --statsgo-zip PATH --output DIR
Only the six WEPPpy source tables and mapunit are loaded from the legacy ZIP.
Legacy values remain text; this intentionally does not implement a production import.
"""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import zipfile

TABLES = ("mapunit", "component", "muaggatt", "chorizon", "chfrags",
          "chtexturegrp", "corestrictions", "sacatalog")
ROOT = Path(__file__).resolve().parents[1]


def identifier(value):
    return '"' + value.replace('"', '""') + '"'


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def zip_rows(archive, stem):
    matches = [n for n in archive.namelist()
               if n.replace("\\", "/").endswith("/tabular/" + stem + ".txt")]
    if len(matches) != 1:
        raise ValueError(f"Expected one tabular {stem}.txt, found {len(matches)}")
    with archive.open(matches[0]) as stream:
        return list(csv.reader(io.TextIOWrapper(stream, encoding="utf-8-sig"), delimiter="|"))


def load_legacy(path):
    connection = sqlite3.connect(":memory:")
    with zipfile.ZipFile(path) as archive:
        columns = zip_rows(archive, "mstabcol")
        names = {r[0]: r[4] for r in zip_rows(archive, "mstab")}
        metadata = {}
        for table in TABLES:
            definitions = sorted((r for r in columns if r[0] == table), key=lambda r: int(r[1]))
            if not definitions:
                raise ValueError(f"Missing column metadata: {table}")
            metadata[table] = [{"name": r[2], "logical_type": r[5], "required": r[6],
                                "field_size": r[7], "precision": r[8]} for r in definitions]
            connection.execute(f"CREATE TABLE {identifier(table)} (" +
                               ",".join(identifier(r[2]) + " TEXT" for r in definitions) + ")")
            rows = zip_rows(archive, names[table])
            if any(len(row) != len(definitions) for row in rows):
                raise ValueError(f"Row width differs from metadata: {table}")
            connection.executemany(f"INSERT INTO {identifier(table)} VALUES (" +
                                   ",".join("?" for _ in definitions) + ")",
                                   ([value if value != "" else None for value in row] for row in rows))
    return connection, metadata


def inspect(connection):
    result = {}
    for table in TABLES:
        cols = connection.execute(f"PRAGMA table_info({identifier(table)})").fetchall()
        result[table] = {
            "rows": connection.execute(f"SELECT COUNT(*) FROM {identifier(table)}").fetchone()[0],
            "columns": [{"name": r[1], "storage_type": r[2], "not_null": bool(r[3]),
                         "primary_key_position": r[5]} for r in cols],
        }
    relations = [("component", "mukey", "mapunit", "mukey"),
                 ("muaggatt", "mukey", "mapunit", "mukey"),
                 ("chorizon", "cokey", "component", "cokey"),
                 ("chfrags", "chkey", "chorizon", "chkey"),
                 ("chtexturegrp", "chkey", "chorizon", "chkey"),
                 ("corestrictions", "cokey", "component", "cokey")]
    orphans = {}
    for child, foreign, parent, primary in relations:
        sql = (f"SELECT COUNT(*) FROM {child} c LEFT JOIN {parent} p ON c.{foreign}=p.{primary} "
               f"WHERE c.{foreign} IS NOT NULL AND p.{primary} IS NULL")
        orphans[f"{child}.{foreign}->{parent}.{primary}"] = connection.execute(sql).fetchone()[0]
    catalog = connection.execute("SELECT areasymbol,saversion,saverest FROM sacatalog").fetchall()
    return {"tables": result, "orphan_counts": orphans, "survey_catalog": catalog}


def examples(connection, label):
    # Prefer a real map unit with populated horizon data rather than a water-only key.
    mukey = connection.execute("SELECT c.mukey FROM component c JOIN chorizon h ON c.cokey=h.cokey "
                               "GROUP BY c.mukey ORDER BY COUNT(*) DESC,c.mukey LIMIT 1").fetchone()[0]
    cokeys = [r[0] for r in connection.execute("SELECT cokey FROM component WHERE mukey=? ORDER BY cokey", (mukey,))]
    chkeys = [r[0] for r in connection.execute("SELECT h.chkey FROM chorizon h JOIN component c "
                                             "ON h.cokey=c.cokey WHERE c.mukey=? ORDER BY h.chkey", (mukey,))]
    keys = {"_fetch_components": [mukey], "_fetch_chorizon": cokeys,
            "_fetch_corestrictions": cokeys, "_fetch_chfrags": chkeys, "_fetch_chtexturegrp": chkeys}
    definitions = json.loads((ROOT / "contracts/wepppy-queries.json").read_text())["queries"]
    output = []
    for definition in definitions:
        values = keys[definition["id"]]
        # The baseline consumer queries use numeric literals. Reject nonnumeric keys here.
        if not values or any(not str(v).isdigit() for v in values):
            raise ValueError("Sample requires nonempty numeric identifiers")
        query = definition["request"]["form"]["query"].replace("1001,1002", ",".join(map(str, values)))
        execution_query = query
        adaptation = None
        if definition["id"] == "_fetch_components":
            execution_query = query.replace("ORDER BY mukey", "ORDER BY component.mukey")
            adaptation = "Qualify ambiguous joined ORDER BY mukey for SQLite; original SQL retained."
        cursor = connection.execute(execution_query)
        output.append({"id": label + definition["id"], "sql": query,
                       "audit_execution_sql": execution_query, "audit_adaptation": adaptation,
                       "columns": [d[0] for d in cursor.description], "rows": cursor.fetchall()})
    return {"evidence_kind": "official_download_query_results_not_sda_wire_fixture",
            "mukey": str(mukey), "cokeys": list(map(str, cokeys)), "chkeys": list(map(str, chkeys)),
            "queries": output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpkg", type=Path, required=True)
    parser.add_argument("--statsgo-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.gpkg.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        ssurgo = inspect(connection)
        ssurgo["geometry_columns"] = connection.execute("SELECT * FROM gpkg_geometry_columns").fetchall()
        ssurgo["query_examples"] = examples(connection, "ssurgo")
    connection, metadata = load_legacy(args.statsgo_zip)
    try:
        statsgo = inspect(connection)
        statsgo["source_column_metadata"] = metadata
        statsgo["query_examples"] = examples(connection, "statsgo2")
    finally:
        connection.close()
    for name, value, path in [("ssurgo-gu", ssurgo, args.gpkg), ("statsgo2-vi", statsgo, args.statsgo_zip)]:
        value["source_file"] = path.name
        value["source_sha256"] = digest(path)
        value["source_bytes"] = path.stat().st_size
        (args.output / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")
        print(name, "query families:", len(value["query_examples"]["queries"]),
              "orphans:", sum(value["orphan_counts"].values()))


if __name__ == "__main__":
    main()
