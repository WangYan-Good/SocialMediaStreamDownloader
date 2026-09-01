#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
RUN_DOCKER_SCRIPT="${RUN_DOCKER_SCRIPT:-$PROJECT_DIR/run-docker.sh}"

source_project=""
restore_project=""
backup_directory=""
health_url=""

usage() {
  echo "usage: release_restore_drill.sh --source-project NAME --restore-project smsd-restore-test-NAME --backup BACKUP_DIR --health-url URL" >&2
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-project)
      [[ $# -ge 2 ]] || usage
      source_project="$2"
      shift 2
      ;;
    --restore-project)
      [[ $# -ge 2 ]] || usage
      restore_project="$2"
      shift 2
      ;;
    --backup)
      [[ $# -ge 2 ]] || usage
      backup_directory="$2"
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

[[ -n "$source_project" && -n "$restore_project" ]] || usage
[[ -n "$backup_directory" && -n "$health_url" ]] || usage

cleanup() {
  "$RUN_DOCKER_SCRIPT" -p "$source_project" down -v --remove-orphans \
    >/dev/null 2>&1 || true
  "$RUN_DOCKER_SCRIPT" -p "$restore_project" down -v --remove-orphans \
    >/dev/null 2>&1 || true
}
trap cleanup EXIT

"$RUN_DOCKER_SCRIPT" -p "$source_project" up -d mysql
source_mysql_id="$("$RUN_DOCKER_SCRIPT" -p "$source_project" ps -q mysql)"
[[ -n "$source_mysql_id" ]] || {
  echo "release drill failed: source MySQL is absent" >&2
  exit 1
}
source_mysql_health=""
for _ in $(seq 1 60); do
  source_mysql_health="$(
    "$DOCKER_BIN" inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' \
      "$source_mysql_id"
  )"
  [[ "$source_mysql_health" == "healthy" ]] && break
  sleep 1
done
[[ "$source_mysql_health" == "healthy" ]] || {
  echo "release drill failed: source MySQL did not become healthy" >&2
  exit 1
}
"$RUN_DOCKER_SCRIPT" -p "$source_project" run --rm --no-deps -T app \
  python -m backend.src.database.migration_cli upgrade
"$RUN_DOCKER_SCRIPT" -p "$source_project" up -d app

source_app_id="$("$RUN_DOCKER_SCRIPT" -p "$source_project" ps -q app)"
[[ -n "$source_app_id" ]] || {
  echo "release drill failed: source app is absent" >&2
  exit 1
}

cat > /tmp/release-drill-seed.py <<'PY'
from datetime import datetime, timedelta
import hashlib
import os
from pathlib import Path
import secrets
import sys

sys.path.insert(0, "/app")

from backend.src.database.schema_guard import initialize_schema_guard
from backend.src.library.configlib import load_config
from backend.src.service.recording_recovery_journal import RecordingRecoveryJournal
from backend.src.service.recording_resource import RecordingPersistenceIntent
from backend.src.web.auth_routes import build_auth_runtime


RECOVERY_KEY = "c" * 32
ORDINARY_BYTES = b"release-drill-ordinary-media\n"
RECOVERY_BYTES = b"release-drill-recovery-media\n"

settings = load_config()
initialize_schema_guard(settings)
runtime = build_auth_runtime(lambda: settings)
service = runtime.service()
user = service.create_user(
  "release-drill-account", secrets.token_urlsafe(24), role="admin"
)
service.create_session(user.user_id)

database = service._repository._database
with database.get_connection() as connection:
  with connection.cursor() as cursor:
    cursor.execute(
      "INSERT INTO share_url (owner_user_id, nickname) VALUES (%s, %s)",
      ("release-drill-owner", "release-drill-seed"),
    )
  connection.commit()

root = Path("/app/downloads")
media = root / "release-drill"
media.mkdir(parents=True, exist_ok=True)
ordinary_path = media / "ordinary.bin"
recovery_path = media / "recovery.flv"
for path, payload in (
  (ordinary_path, ORDINARY_BYTES),
  (recovery_path, RECOVERY_BYTES),
):
  with path.open("wb") as stream:
    stream.write(payload)
    stream.flush()
    os.fsync(stream.fileno())
directory = os.open(str(media), os.O_RDONLY | os.O_DIRECTORY)
try:
  os.fsync(directory)
finally:
  os.close(directory)

now = datetime.utcnow()
intent = RecordingPersistenceIntent(
  app_user_id=user.user_id,
  platform="douyin",
  room_id="release-drill-room",
  owner_user_id="release-drill-owner",
  title="release drill",
  protocol="flv",
  output_path=str(recovery_path),
  started_at=now - timedelta(seconds=5),
  finished_at=now,
  source="live",
)
RecordingRecoveryJournal(config_loader=lambda: settings).publish(intent, RECOVERY_KEY)

proof = media / "proof.txt"
proof.write_text(
  "ordinary_sha256={}\nrecovery_sha256={}\n".format(
    hashlib.sha256(ORDINARY_BYTES).hexdigest(),
    hashlib.sha256(RECOVERY_BYTES).hexdigest(),
  ),
  encoding="utf-8",
)
PY
"$DOCKER_BIN" cp /tmp/release-drill-seed.py \
  "$source_app_id:/tmp/release-drill-seed.py"
"$DOCKER_BIN" exec --user appuser "$source_app_id" \
  python /tmp/release-drill-seed.py

"$PROJECT_DIR/scripts/release_backup.sh" \
  --output "$backup_directory" --project-name "$source_project"
[[ "$(stat -c '%a' "$backup_directory")" == "700" ]] || {
  echo "release drill failed: backup directory is not mode 0700" >&2
  exit 1
}
for backup_asset in database.sql downloads.tar manifest.json SHA256SUMS; do
  [[ "$(stat -c '%a' "$backup_directory/$backup_asset")" == "600" ]] || {
    echo "release drill failed: backup asset is not mode 0600" >&2
    exit 1
  }
done
tar -tf "$backup_directory/downloads.tar" | \
  grep -Fq './.smsd-recording-recovery/' || {
    echo "release drill failed: hidden recovery journal was not archived" >&2
    exit 1
  }

"$RUN_DOCKER_SCRIPT" -p "$source_project" down -v --remove-orphans

"$PROJECT_DIR/scripts/release_restore.sh" \
  --backup "$backup_directory" \
  --project-name "$restore_project" \
  --health-url "$health_url"

restored_app_id="$("$RUN_DOCKER_SCRIPT" -p "$restore_project" ps -q app)"
[[ -n "$restored_app_id" ]] || {
  echo "release drill failed: restored app is absent" >&2
  exit 1
}

cat > /tmp/release-drill-verify.py <<'PY'
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, "/app")

from backend.src.database.schema_guard import initialize_schema_guard
from backend.src.library.configlib import load_config
from backend.src.web.auth_routes import build_auth_runtime


RECOVERY_KEY = "c" * 32
settings = load_config()
initialize_schema_guard(settings)
service = build_auth_runtime(lambda: settings).service()
database = service._repository._database


def scalar(row):
  if isinstance(row, dict):
    return next(iter(row.values()))
  return row[0]


with database.get_connection() as connection:
  with connection.cursor() as cursor:
    cursor.execute(
      "SELECT COUNT(*) FROM share_url WHERE owner_user_id = %s",
      ("release-drill-owner",),
    )
    ordinary_rows = int(scalar(cursor.fetchone()))
    cursor.execute(
      "SELECT COUNT(*) FROM app_user WHERE username = %s",
      ("release-drill-account",),
    )
    account_rows = int(scalar(cursor.fetchone()))
    cursor.execute(
      "SELECT COUNT(*) FROM auth_session s JOIN app_user u ON u.user_id = s.user_id "
      "WHERE u.username = %s",
      ("release-drill-account",),
    )
    session_rows = int(scalar(cursor.fetchone()))
    cursor.execute(
      "SELECT COUNT(*) FROM recording_record WHERE recovery_key = %s",
      (RECOVERY_KEY,),
    )
    recording_rows = int(scalar(cursor.fetchone()))

if (ordinary_rows, account_rows, session_rows, recording_rows) != (1, 1, 1, 1):
  raise SystemExit("release drill failed: restored database seed is incomplete")

media = Path("/app/downloads/release-drill")
proof = dict(
  line.split("=", 1)
  for line in (media / "proof.txt").read_text(encoding="utf-8").splitlines()
)
ordinary = hashlib.sha256((media / "ordinary.bin").read_bytes()).hexdigest()
recovery = hashlib.sha256((media / "recovery.flv").read_bytes()).hexdigest()
if ordinary != proof["ordinary_sha256"] or recovery != proof["recovery_sha256"]:
  raise SystemExit("release drill failed: restored media checksum differs")

journal = Path("/app/downloads/.smsd-recording-recovery") / f"{RECOVERY_KEY}.json"
if journal.exists():
  raise SystemExit("release drill failed: recovery journal was not acknowledged")
PY
"$DOCKER_BIN" cp /tmp/release-drill-verify.py \
  "$restored_app_id:/tmp/release-drill-verify.py"
"$DOCKER_BIN" exec --user appuser "$restored_app_id" \
  python /tmp/release-drill-verify.py

echo "ok   runtime release backup restore drill"
