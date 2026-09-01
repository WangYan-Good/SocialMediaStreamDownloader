#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CURL_BIN="${CURL_BIN:-curl}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
RUN_DOCKER_SCRIPT="${RUN_DOCKER_SCRIPT:-$PROJECT_DIR/run-docker.sh}"

health_url=""
project_name=""

usage() {
  echo "usage: release_postcheck.sh --health-url URL [--project-name COMPOSE_PROJECT]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --health-url)
      [[ $# -ge 2 ]] || usage
      health_url="$2"
      shift 2
      ;;
    --project-name)
      [[ $# -ge 2 ]] || usage
      project_name="$2"
      shift 2
      ;;
    *) usage ;;
  esac
done

[[ -n "$health_url" ]] || usage

if [[ -n "$project_name" ]]; then
  status_output="$(
    "$RUN_DOCKER_SCRIPT" -p "$project_name" exec -T app \
      python -m backend.src.database.migration_cli status
  )"
  check_output="$(
    "$RUN_DOCKER_SCRIPT" -p "$project_name" exec -T app \
      python -m backend.src.database.migration_cli check
  )"
else
  status_output="$(
    "$PYTHON_BIN" -m backend.src.database.migration_cli status
  )"
  check_output="$(
    "$PYTHON_BIN" -m backend.src.database.migration_cli check
  )"
fi

state=""
current=""
heads=""
for field in $status_output; do
  case "$field" in
    state=*) state="${field#state=}" ;;
    current=*) current="${field#current=}" ;;
    heads=*) heads="${field#heads=}" ;;
  esac
done

if [[ "$state" != "ready" || -z "$current" || "$current" == "none" || "$current" != "$heads" ]]; then
  echo "release postcheck failed: migration status is not ready at the single code head" >&2
  exit 1
fi

if [[ "$check_output" != *"managed schema is compatible"* ]]; then
  echo "release postcheck failed: managed schema is incompatible" >&2
  exit 1
fi

"$CURL_BIN" -fsS "$health_url" >/dev/null

if [[ -n "$project_name" ]]; then
  app_id="$("$RUN_DOCKER_SCRIPT" -p "$project_name" ps -q app)"
  mysql_id="$("$RUN_DOCKER_SCRIPT" -p "$project_name" ps -q mysql)"
  [[ -n "$app_id" && -n "$mysql_id" ]] || {
    echo "release postcheck failed: required Compose container is absent" >&2
    exit 1
  }
  app_running="$("$DOCKER_BIN" inspect --format '{{.State.Running}}' "$app_id")"
  mysql_health="$(
    "$DOCKER_BIN" inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' \
      "$mysql_id"
  )"
  [[ "$app_running" == "true" ]] || {
    echo "release postcheck failed: app container is not running" >&2
    exit 1
  }
  [[ "$mysql_health" == "healthy" ]] || {
    echo "release postcheck failed: mysql container is not healthy" >&2
    exit 1
  }
fi

echo "ok   release post-upgrade verification"
