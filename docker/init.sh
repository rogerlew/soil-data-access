#!/bin/sh
set -eu
if [ -n "${SOIL_SERVE_PASSWORD_FILE:-}" ]; then
    [ -z "${SOIL_SERVE_PASSWORD:-}" ] || { echo "Set one serving password source" >&2; exit 1; }
    SOIL_SERVE_PASSWORD=$(cat "$SOIL_SERVE_PASSWORD_FILE")
fi
[ -n "${SOIL_SERVE_PASSWORD:-}" ] || { echo "Missing serving password" >&2; exit 1; }
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 --set=serve_password="$SOIL_SERVE_PASSWORD" <<'SQL'
CREATE ROLE soil_serve LOGIN PASSWORD :'serve_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
ALTER ROLE soil_serve SET default_transaction_read_only=on;
ALTER ROLE soil_serve SET statement_timeout='5s';
ALTER ROLE soil_serve SET idle_in_transaction_session_timeout='5s';
REVOKE ALL ON DATABASE soil FROM PUBLIC;
GRANT CONNECT ON DATABASE soil TO soil_serve;
SQL
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 --file=/opt/soil/001_replay.sql
