#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
RUN_DOCKER_SCRIPT="${RUN_DOCKER_SCRIPT:-$PROJECT_DIR/run-docker.sh}"
BUNDLE_HELPER="$PROJECT_DIR/scripts/release_bundle.py"

backup_directory=""
project_name=""
health_url=""

usage() {
  echo "usage: release_restore.sh --backup BACKUP_DIRECTORY --project-name smsd-restore-test-UNIQUE --health-url URL" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup)
      [[ $# -ge 2 ]] || usage
      backup_directory="$2"
      shift 2
      ;;
    --project-name)
      [[ $# -ge 2 ]] || usage
      project_name="$2"
      shift 2
      ;;
    --health-url)
      [[ $# -ge 2 ]] || usage
      health_url="$2"
      shift 2
      ;;
    *) usage ;;
  esac
done

[[ -n "$backup_directory" && -n "$project_name" && -n "$health_url" ]] || usage

"$PYTHON_BIN" "$BUNDLE_HELPER" verify "$backup_directory"
source_project="$(
  "$PYTHON_BIN" "$BUNDLE_HELPER" field "$backup_directory" source_project
)"
source_database="$(
  "$PYTHON_BIN" "$BUNDLE_HELPER" field "$backup_directory" database_name
)"
"$PYTHON_BIN" "$BUNDLE_HELPER" validate-restore-project "$project_name" \
  --source-project "$source_project"

if [[ -n "$("$RUN_DOCKER_SCRIPT" -p "$project_name" ps -a -q)" ]]; then
  echo "destination project already has recoverable state" >&2
  exit 1
fi
for volume in mysql_data download_data; do
  if "$DOCKER_BIN" volume inspect "${project_name}_${volume}" >/dev/null 2>&1; then
    echo "destination project already has recoverable state" >&2
    exit 1
  fi
done

"$RUN_DOCKER_SCRIPT" -p "$project_name" up -d mysql
mysql_id="$("$RUN_DOCKER_SCRIPT" -p "$project_name" ps -q mysql)"
[[ -n "$mysql_id" ]] || {
  echo "restore failed: MySQL container is absent" >&2
  exit 1
}

mysql_health=""
for _ in $(seq 1 60); do
  mysql_health="$(
    "$DOCKER_BIN" inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' \
      "$mysql_id"
  )"
  [[ "$mysql_health" == "healthy" ]] && break
  sleep 1
done
[[ "$mysql_health" == "healthy" ]] || {
  echo "restore failed: MySQL did not become healthy" >&2
  exit 1
}

destination_database="$("$DOCKER_BIN" exec "$mysql_id" printenv MYSQL_DATABASE)"
[[ "$destination_database" == "$source_database" ]] || {
  echo "restore database name differs from backup manifest" >&2
  exit 1
}

"$DOCKER_BIN" exec -i "$mysql_id" sh -c \
  'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql --protocol=TCP -h 127.0.0.1 -uroot' \
  < "$backup_directory/database.sql"

"$RUN_DOCKER_SCRIPT" -p "$project_name" create app
"$RUN_DOCKER_SCRIPT" -p "$project_name" run --rm --no-deps -T \
  --entrypoint /bin/tar app --numeric-owner -C /app/downloads -xpf - \
  < "$backup_directory/downloads.tar"

"$RUN_DOCKER_SCRIPT" -p "$project_name" up -d app
"$PROJECT_DIR/scripts/release_postcheck.sh" \
  --health-url "$health_url" --project-name "$project_name"

echo "release restore completed: $project_name"
