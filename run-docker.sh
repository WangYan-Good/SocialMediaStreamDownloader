#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMPOSE_ENV_FILE="$(mktemp "${TMPDIR:-/tmp}/smsd-compose-env.XXXXXX")"

cleanup() {
  rm -f -- "$COMPOSE_ENV_FILE"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

chmod 600 "$COMPOSE_ENV_FILE"
"$PYTHON_BIN" "$PROJECT_DIR/scripts/runtime_config.py" \
  ensure-root-secret "$PROJECT_DIR/config/mysql-root-password"
"$PYTHON_BIN" "$PROJECT_DIR/scripts/runtime_config.py" \
  compose-env "$COMPOSE_ENV_FILE"

# Shell values must not override the canonical YAML-derived interpolation file.
unset SMSD_SERVER_PORT SMSD_DB_PORT SMSD_DB_NAME SMSD_DB_USER SMSD_DB_PASSWORD
unset SMSD_CONFIG_FILE SMSD_MYSQL_ROOT_SECRET_FILE

if [[ $# -eq 0 ]]; then
  set -- up
fi

docker compose \
  --env-file "$COMPOSE_ENV_FILE" \
  -f "$PROJECT_DIR/docker-compose.yml" \
  "$@"
