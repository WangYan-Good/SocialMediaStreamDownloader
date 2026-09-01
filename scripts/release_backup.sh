#!/usr/bin/env bash
set -euo pipefail
umask 077

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
GIT_BIN="${GIT_BIN:-git}"
RUN_DOCKER_SCRIPT="${RUN_DOCKER_SCRIPT:-$PROJECT_DIR/run-docker.sh}"
BUNDLE_HELPER="$PROJECT_DIR/scripts/release_bundle.py"

output_directory=""
project_name="${COMPOSE_PROJECT_NAME:-socialmediastreamdownloader}"
app_was_running=false

usage() {
  echo "usage: release_backup.sh --output BACKUP_DIRECTORY [--project-name COMPOSE_PROJECT]" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || usage
      output_directory="$2"
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

[[ -n "$output_directory" && -n "$project_name" ]] || usage
"$PYTHON_BIN" "$BUNDLE_HELPER" prepare-output "$output_directory"

app_id="$("$RUN_DOCKER_SCRIPT" -p "$project_name" ps -a -q app)"
mysql_id="$("$RUN_DOCKER_SCRIPT" -p "$project_name" ps -q mysql)"
[[ -n "$app_id" && -n "$mysql_id" ]] || {
  echo "release backup requires an existing app and running MySQL" >&2
  exit 1
}

if [[ "$("$DOCKER_BIN" inspect --format '{{.State.Running}}' "$app_id")" == "true" ]]; then
  app_was_running=true
fi
if [[ "$("$DOCKER_BIN" inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$mysql_id")" != "healthy" ]]; then
  echo "release backup requires healthy MySQL" >&2
  exit 1
fi

restore_app() {
  status=$?
  trap - EXIT
  restart_status=0
  if [[ "$app_was_running" == "true" ]]; then
    "$RUN_DOCKER_SCRIPT" -p "$project_name" up -d app || restart_status=$?
  fi
  if [[ $status -ne 0 ]]; then
    exit "$status"
  fi
  exit "$restart_status"
}
trap restore_app EXIT

if [[ "$app_was_running" == "true" ]]; then
  "$RUN_DOCKER_SCRIPT" -p "$project_name" stop app
fi

schema_status_file="$output_directory/.schema-status.tmp"
"$RUN_DOCKER_SCRIPT" -p "$project_name" run --rm --no-deps -T app \
  python -m backend.src.database.migration_cli status > "$schema_status_file"
"$RUN_DOCKER_SCRIPT" -p "$project_name" run --rm --no-deps -T app \
  python -m backend.src.database.migration_cli check >/dev/null

"$DOCKER_BIN" exec "$mysql_id" sh -c \
  'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysqldump --single-transaction --routines --triggers --events --databases "$MYSQL_DATABASE"' \
  > "$output_directory/database.sql"

"$RUN_DOCKER_SCRIPT" -p "$project_name" run --rm --no-deps -T \
  --entrypoint /bin/tar app --numeric-owner -C /app/downloads -cpf - . \
  > "$output_directory/downloads.tar"

source_git_commit="$("$GIT_BIN" -C "$PROJECT_DIR" rev-parse HEAD)"
source_image="$("$DOCKER_BIN" inspect --format '{{.Image}}' "$app_id")"
database_name="$("$DOCKER_BIN" exec "$mysql_id" printenv MYSQL_DATABASE)"

"$PYTHON_BIN" "$BUNDLE_HELPER" write-manifest "$output_directory" \
  --source-git-commit "$source_git_commit" \
  --source-image "$source_image" \
  --source-project "$project_name" \
  --database-name "$database_name" \
  --schema-status-file "$schema_status_file"
rm -f -- "$schema_status_file"
"$PYTHON_BIN" "$BUNDLE_HELPER" write-checksums "$output_directory"
chmod 600 \
  "$output_directory/database.sql" \
  "$output_directory/downloads.tar" \
  "$output_directory/manifest.json" \
  "$output_directory/SHA256SUMS"
"$PYTHON_BIN" "$BUNDLE_HELPER" verify "$output_directory"

echo "release backup completed: $output_directory"
