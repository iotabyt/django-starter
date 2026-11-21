# Shared helpers for bin/setup and bin/dev. POSIX sh; sourced, not executed.
# shellcheck shell=sh

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  _bold=$(printf '\033[1m') _dim=$(printf '\033[2m') _reset=$(printf '\033[0m')
  _green=$(printf '\033[32m') _red=$(printf '\033[31m') _yellow=$(printf '\033[33m')
else
  _bold='' _dim='' _reset='' _green='' _red='' _yellow=''
fi

header() { printf '\n%s%s%s\n' "$_bold" "$1" "$_reset"; }
ok() { printf '  %s✓%s %s\n' "$_green" "$_reset" "$1"; }
fail() { printf '  %s✗%s %s\n' "$_red" "$_reset" "$1" >&2; }
tip() { printf '  %s→%s %s\n' "$_yellow" "$_reset" "$1"; }
hint() { printf '    %s\n' "$1" >&2; }

# run LABEL COMMAND...: run quietly; print ✓ LABEL, or ✗ LABEL plus the output's tail and exit.
run() {
  _label=$1
  shift
  _log=$(mktemp "${TMPDIR:-/tmp}/bin-setup.XXXXXX")
  if "$@" >"$_log" 2>&1; then
    rm -f "$_log"
    ok "$_label"
  else
    _rc=$?
    fail "$_label"
    tail -n 40 "$_log" | sed 's/^/    /' >&2
    rm -f "$_log"
    exit "$_rc"
  fi
}

# Python for small helper scripts: the project's venv if it exists, else a uv-managed one.
_py() {
  if [ -x .venv/bin/python ]; then
    .venv/bin/python "$@"
  else
    uv run --no-project --quiet python "$@"
  fi
}

# Prints "HOST PORT" from DATABASE_URL, looked up like Django does (environment first, then
# .env), falling back to .env.example.
db_target() {
  _py - <<'PY'
import os
from urllib.parse import urlsplit


def from_file(path):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return None


url = (
    os.environ.get("DATABASE_URL")
    or from_file(".env")
    or from_file(".env.example")
    or "postgres://localhost:5432/postgres"
)
parts = urlsplit(url)
print(parts.hostname or "localhost", parts.port or 5432)
PY
}

db_reachable() {
  _py - "$1" "$2" <<'PY'
import socket
import sys

try:
    socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=2).close()
except OSError:
    sys.exit(1)
PY
}

docker_available() {
  command -v docker >/dev/null 2>&1 \
    && docker info >/dev/null 2>&1 \
    && docker compose version >/dev/null 2>&1
}

# Use the Postgres in DATABASE_URL if something is listening there; otherwise start the
# Docker Compose one on the same port. Exits with advice if neither is possible.
ensure_postgres() {
  _target=$(db_target)
  _host=${_target% *}
  _port=${_target#* }

  if db_reachable "$_host" "$_port"; then
    ok "Using existing Postgres at $_host:$_port"
    return 0
  fi

  case $_host in
    localhost | 127.0.0.1 | ::1) ;;
    *)
      fail "Can't reach Postgres at $_host:$_port (from DATABASE_URL)"
      hint "Start that server, or change DATABASE_URL in .env."
      exit 1
      ;;
  esac

  if ! docker_available; then
    fail "No Postgres at $_host:$_port, and Docker isn't available to start one"
    hint "Either install Docker (https://docs.docker.com/get-docker/) and re-run,"
    hint "or point DATABASE_URL in .env at an existing Postgres."
    exit 1
  fi

  _log=$(mktemp "${TMPDIR:-/tmp}/bin-setup.XXXXXX")
  if DB_PORT=$_port docker compose up -d --wait db >"$_log" 2>&1; then
    rm -f "$_log"
    ok "Started Postgres in Docker on port $_port"
  else
    fail "Couldn't start Postgres in Docker on port $_port"
    # Show Docker's error lines, not its progress output (or the tail if there are none).
    { grep -i 'error' "$_log" || tail -n 15 "$_log"; } | sed 's/^/    /' >&2
    rm -f "$_log"
    hint "If port $_port is taken, change the port in DATABASE_URL in .env and re-run."
    exit 1
  fi
}

# Creates the database named in Django's settings if the server doesn't have it yet.
ensure_database() {
  uv run python - <<'PY'
import psycopg
from psycopg import sql

from config.settings.base import DATABASES

db = DATABASES["default"]
name = db["NAME"]
params = {
    "host": db.get("HOST") or None,
    "port": db.get("PORT") or None,
    "user": db.get("USER") or None,
    "password": db.get("PASSWORD") or None,
    "connect_timeout": 5,
    **db.get("OPTIONS", {}),
}
try:
    psycopg.connect(dbname=name, **params).close()
    print(f"Database {name} exists")
except psycopg.OperationalError as exc:
    if "does not exist" not in str(exc):
        raise
    with psycopg.connect(dbname="postgres", autocommit=True, **params) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    print(f"Created database {name}")
PY
}
