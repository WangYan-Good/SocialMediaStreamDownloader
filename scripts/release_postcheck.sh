#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CURL_BIN="${CURL_BIN:-curl}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
RUN_DOCKER_SCRIPT="${RUN_DOCKER_SCRIPT:-$PROJECT_DIR/run-docker.sh}"

health_url=""
project_name=""
expected_image=""
expected_revision=""
expected_requirements_sha=""
expected_mysql_image=""

usage() {
  echo "usage: release_postcheck.sh --health-url URL [--project-name COMPOSE_PROJECT] [--expected-image DIGEST --expected-revision SHA --expected-requirements-sha SHA256 --expected-mysql-image DIGEST]" >&2
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
    --expected-image)
      [[ $# -ge 2 ]] || usage
      expected_image="$2"
      shift 2
      ;;
    --expected-revision)
      [[ $# -ge 2 ]] || usage
      expected_revision="$2"
      shift 2
      ;;
    --expected-requirements-sha)
      [[ $# -ge 2 ]] || usage
      expected_requirements_sha="$2"
      shift 2
      ;;
    --expected-mysql-image)
      [[ $# -ge 2 ]] || usage
      expected_mysql_image="$2"
      shift 2
      ;;
    *) usage ;;
  esac
done

[[ -n "$health_url" ]] || usage

identity_values=(
  "$expected_image"
  "$expected_revision"
  "$expected_requirements_sha"
  "$expected_mysql_image"
)
identity_count=0
for identity_value in "${identity_values[@]}"; do
  [[ -n "$identity_value" ]] && identity_count=$((identity_count + 1))
done
if [[ $identity_count -ne 0 && $identity_count -ne 4 ]]; then
  usage
fi
if [[ $identity_count -eq 4 ]]; then
  [[ -n "$project_name" ]] || usage
  [[ "$expected_image" =~ ^ghcr\.io/[a-z0-9][a-z0-9._/-]*@sha256:[0-9a-f]{64}$ ]] || usage
  [[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] || usage
  [[ "$expected_requirements_sha" =~ ^[0-9a-f]{64}$ ]] || usage
  [[ "$expected_mysql_image" =~ ^mysql:[0-9]+\.[0-9]+\.[0-9]+@sha256:[0-9a-f]{64}$ ]] || usage
fi

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

  if [[ $identity_count -eq 4 ]]; then
    expected_image_id="$($DOCKER_BIN image inspect --format '{{.Id}}' "$expected_image")"
    running_image_id="$($DOCKER_BIN inspect --format '{{.Image}}' "$app_id")"
    revision_label="$($DOCKER_BIN inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$app_id")"
    requirements_label="$($DOCKER_BIN inspect --format '{{index .Config.Labels "io.smsd.requirements.sha256"}}' "$app_id")"
    mysql_config_image="$($DOCKER_BIN inspect --format '{{.Config.Image}}' "$mysql_id")"
    [[ "$running_image_id" == "$expected_image_id" ]] || {
      echo "release identity failed: running application image differs" >&2
      exit 1
    }
    [[ "$revision_label" == "$expected_revision" ]] || {
      echo "release identity failed: revision label differs" >&2
      exit 1
    }
    [[ "$requirements_label" == "$expected_requirements_sha" ]] || {
      echo "release identity failed: requirements label differs" >&2
      exit 1
    }
    [[ "$mysql_config_image" == "$expected_mysql_image" ]] || {
      echo "release identity failed: MySQL image reference differs" >&2
      exit 1
    }
    echo "release identity: revision=$expected_revision image=$expected_image mysql=$expected_mysql_image"
  fi
fi

echo "ok   release post-upgrade verification"
