#!/usr/bin/env python3
"""Emit transactional COPY SQL for a scoped SSURGO GeoPackage + STATSGO2 ZIP release.

No source files are modified. Execute the output with psql ON_ERROR_STOP=1 and
import credentials; serving credentials cannot import or activate releases.
"""
import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sqlite3

from audit_sources import digest, identifier, inspect, load_legacy
from replay_cache import TYPES, literal

PARENTS = {'mapunit': 'mukey', 'component': 'cokey', 'chorizon': 'chkey'}


def exact_key(value):
    raw = str(value)
    if not re.fullmatch(r'[0-9]+', raw) or len(raw.lstrip('0')) > 19:
        raise ValueError('Invalid source key')
    key = int(raw)
    if key > 9223372036854775807:
        raise ValueError('Source key exceeds signed bigint')
    return key


def validate_source(conn):
    evidence = inspect(conn)
    if any(evidence['orphan_counts'].values()):
        raise ValueError('Source contains orphan relationships')
    keys = {}
    for table, column in PARENTS.items():
        rows = conn.execute(f'SELECT {column} FROM {table}')
        values = [exact_key(row[0]) for row in rows]
        if len(set(values)) != len(values):
            raise ValueError('Duplicate source parent keys: ' + table)
        keys[table] = set(values)
    for table, columns in TYPES.items():
        present = {row[1] for row in conn.execute(f'PRAGMA table_info({identifier(table)})')}
        if not set(columns) <= present:
            raise ValueError('Missing required source columns: ' + table)
    aggregates = [exact_key(row[0]) for row in conn.execute('SELECT mukey FROM muaggatt')]
    if len(set(aggregates)) != len(aggregates):
        raise ValueError('Duplicate aggregate keys')
    component_mukeys = {exact_key(row[0]) for row in conn.execute('SELECT DISTINCT mukey FROM component')}
    if not component_mukeys <= set(aggregates):
        raise ValueError('Components lack aggregate records')
    evidence['parent_key_counts'] = {table: len(values) for table, values in keys.items()}
    return evidence, keys


def copy_cell(value, kind):
    if value is None:
        return ''  # CSV NULL: an unquoted empty field; real empty text is quoted.
    if kind == 'bigint':
        text = str(exact_key(value))
    elif kind == 'numeric':
        try:
            number = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError('Invalid source numeric value') from exc
        if not number.is_finite():
            raise ValueError('Nonfinite source numeric value')
        text = str(number)
    else:
        text = str(value)
    if '\x00' in text:
        raise ValueError('Source text contains NUL')
    return '"' + text.replace('"', '""') + '"'


def generate(gpkg, statsgo_zip, release, ssurgo_url, statsgo_url, output, receipt,
             ssurgo_release, statsgo_release, ssurgo_scope, statsgo_scope, no_activate=False):
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,128}', release):
        raise ValueError('Invalid release ID')
    if output.exists() or receipt.exists():
        raise FileExistsError('Choose new import output and receipt paths')
    # These source hashes are immutable dataset inputs, not inferred retrieval dates.
    specs = [
        {'dataset': 'SSURGO', 'release_id': ssurgo_release, 'scope': ssurgo_scope,
         'source_url': ssurgo_url, 'sha256': digest(gpkg)},
        {'dataset': 'STATSGO2', 'release_id': statsgo_release, 'scope': statsgo_scope,
         'source_url': statsgo_url, 'sha256': digest(statsgo_zip)},
    ]
    from urllib.parse import urlsplit
    for item in specs:
        url = urlsplit(item['source_url'])
        if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
            raise ValueError('Source URL must be public HTTP(S) without credentials')
    first = sqlite3.connect(gpkg.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    second = None
    try:
        second, _ = load_legacy(statsgo_zip)
        connections = (first, second)
        audits, keysets = [], []
        for conn in connections:
            audit, keys = validate_source(conn)
            audits.append(audit)
            keysets.append(keys)
        for table in PARENTS:
            if keysets[0][table] & keysets[1][table]:
                raise ValueError('Overlapping source key domains: ' + table)
        manifest = {'id': release, 'datasets': specs}
        counts = {name: 0 for name in TYPES}
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8', newline='') as stream:
            stream.write("BEGIN;\nSET LOCAL standard_conforming_strings=on;\nSET LOCAL statement_timeout='15min';\n")
            stream.write('INSERT INTO soil.release(id,manifest) VALUES(' + literal(release, 'text') + ',' + literal(json.dumps(manifest), 'text') + '::jsonb);\n')
            for table, columns in TYPES.items():
                names = ['release_id', 'ordinal'] + list(columns)
                stream.write('COPY soil.' + table + '(' + ','.join(names) + ') FROM STDIN WITH (FORMAT csv);\n')
                for conn in connections:
                    projection = ','.join(identifier(name) for name in columns)
                    for row in conn.execute(f'SELECT {projection} FROM {identifier(table)} ORDER BY rowid'):
                        counts[table] += 1
                        values = [copy_cell(release, 'text'), copy_cell(counts[table], 'bigint')]
                        values.extend(copy_cell(value, kind) for value, kind in zip(row, columns.values()))
                        stream.write(','.join(values) + '\n')
                stream.write('\\.\n')
            # COPY does not update planner statistics. Analyze before relationship joins.
            for table in TYPES:
                stream.write('ANALYZE soil.' + table + ';\n')
            for table, count in counts.items():
                stream.write("DO $$ BEGIN IF (SELECT count(*) FROM soil." + table + ' WHERE release_id=' + literal(release, 'text') + ') <> ' + str(count) + " THEN RAISE EXCEPTION 'Imported row count differs'; END IF; END $$;\n")
            for child, foreign, parent, primary in (
                ('component', 'mukey', 'muaggatt', 'mukey'),
                ('chorizon', 'cokey', 'component', 'cokey'),
                ('chfrags', 'chkey', 'chorizon', 'chkey'),
                ('chtexturegrp', 'chkey', 'chorizon', 'chkey'),
                ('corestrictions', 'cokey', 'component', 'cokey'),
            ):
                stream.write("DO $$ BEGIN IF EXISTS (SELECT 1 FROM soil." + child + ' c LEFT JOIN soil.' + parent + ' p ON c.release_id=p.release_id AND c.' + foreign + '=p.' + primary + ' WHERE c.release_id=' + literal(release, 'text') + ' AND p.' + primary + " IS NULL) THEN RAISE EXCEPTION 'Imported relationship differs'; END IF; END $$;\n")
            if not no_activate:
                stream.write('INSERT INTO soil.active_release(singleton,release_id) VALUES(true,' + literal(release, 'text') + ') ON CONFLICT(singleton) DO UPDATE SET release_id=EXCLUDED.release_id;\n')
            stream.write('COMMIT;\n')
        result = {'claim': 'official_source_import_prepared_not_yet_executed', 'manifest': manifest,
                  'source_audits': audits, 'import_row_counts': counts, 'sql_sha256': digest(output),
                  'activation_included': not no_activate,
                  'source_files': [gpkg.name, statsgo_zip.name], 'ordering': 'source rowid; sources in manifest order',
                  'scope': [item['scope'] for item in specs]}
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        first.close()
        if second is not None:
            second.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('gpkg', 'statsgo-zip', 'output', 'receipt'):
        p.add_argument('--' + name, type=Path, required=True)
    for name in ('release', 'ssurgo-url', 'statsgo-url', 'ssurgo-release', 'statsgo-release', 'ssurgo-scope', 'statsgo-scope'):
        p.add_argument('--' + name, required=True)
    p.add_argument("--no-activate", action="store_true", help="Validate and load without switching the active release")
    result = generate(**vars(p.parse_args()))
    print(json.dumps({'release': result['manifest']['id'], 'row_counts': result['import_row_counts']}))


if __name__ == '__main__':
    main()
