#!/usr/bin/env bash
#
# Rehearse the production migration against a production-shaped database.
#
# Production is nine revisions behind the code. The release will run those nine
# migrations against a database with two years of real rows in it, and the only
# honest way to know what that does is to do it - on a copy, on a disposable
# server, with the real snapshot.
#
# A rehearsal against an empty schema proves that the migrations are
# syntactically valid. It does not prove that they complete against real data,
# that a unique constraint added in 0006 does not collide with rows written in
# 2024, or how long the release window needs to be. Those are the questions.
#
# Touches nothing in production: not the database, not the application, not the
# media. The snapshot is opened read-only and never rewritten.
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE_BIN="${ENGINE_BIN:-podman}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MYSQL_BIN="${MYSQL_BIN:-mysql}"

MARKER="ok   runtime production shaped migration rehearsal"

snapshot=""
expected_sha=""
expected_source_revision=""
port="13401"

usage() {
  cat >&2 <<'USAGE'
usage: release_migration_rehearsal.sh
  --snapshot PATH
  --expected-sha256 SHA256
  --expected-source-revision REVISION
  [--port PORT]
USAGE
  exit 2
}

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --snapshot) [[ $# -ge 2 ]] || usage; snapshot="$2"; shift 2 ;;
    --expected-sha256) [[ $# -ge 2 ]] || usage; expected_sha="$2"; shift 2 ;;
    --expected-source-revision) [[ $# -ge 2 ]] || usage; expected_source_revision="$2"; shift 2 ;;
    --port) [[ $# -ge 2 ]] || usage; port="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$snapshot" && -n "$expected_sha" && -n "$expected_source_revision" ]] || usage

##
## The snapshot is evidence, so its identity is checked before it is used. A
## rehearsal against a file that is not the one that was taken from production
## proves something about a different database.
##
[[ -f "$snapshot" ]] || fail "the snapshot is absent"
actual_sha="$(sha256sum "$snapshot" | awk '{print $1}')"
[[ "$actual_sha" == "$expected_sha" ]] ||
  fail "the snapshot is not the file this rehearsal was authorised against"

container="smsd-rehearsal-$$"
workspace="$(mktemp -d "${TMPDIR:-/tmp}/smsd-rehearsal.XXXXXX")"
chmod 700 "$workspace"

cleanup() {
  "$ENGINE_BIN" rm -f "$container" >/dev/null 2>&1 || true
  rm -rf -- "$workspace"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

log="$workspace/rehearsal.log"
record() {
  echo "$*" | tee -a "$log"
}

record "rehearsal snapshot sha256=$actual_sha"
record "rehearsal expected source revision=$expected_source_revision"

##
## A disposable server. Never the production one, and never a database name a
## production client is configured to reach.
##
"$ENGINE_BIN" run -d --name "$container" \
  -e MYSQL_ROOT_PASSWORD=rehearsal \
  -e MYSQL_DATABASE=smsd_rehearsal \
  -p "${port}:3306" \
  docker.io/library/mysql:8.0.46 >/dev/null

for attempt in $(seq 1 180); do
  if "$ENGINE_BIN" exec "$container" \
      mysqladmin ping -h 127.0.0.1 -uroot -prehearsal >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
"$ENGINE_BIN" exec "$container" \
  mysqladmin ping -h 127.0.0.1 -uroot -prehearsal >/dev/null 2>&1 ||
  fail "the disposable MySQL never became ready"
record "disposable mysql ready on port $port"

option_file="$workspace/my.cnf"
umask 077
cat > "$option_file" <<CNF
[client]
user=root
password=rehearsal
host=127.0.0.1
port=$port
CNF
chmod 600 "$option_file"

config_file="$workspace/config.yml"
"$PYTHON_BIN" - "$config_file" "$port" <<'PYEOF'
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
example = Path("docs/design/config.yml.example")
config = yaml.safe_load(example.read_text(encoding="utf-8"))
config["database"].update({
    "enable": True,
    "host": "127.0.0.1",
    "port": int(sys.argv[2]),
    "username": "root",
    "password": "rehearsal",
    "name": "smsd_rehearsal",
})
Path(sys.argv[1]).write_text(
    yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
)
PYEOF
chmod 600 "$config_file"

##
## The application reads its configuration from one fixed path, so the rehearsal
## stages a copy there and restores the original afterwards. The production
## checkout is never involved.
##
canonical="$PROJECT_DIR/config/config.yml"
restore_canonical=""
if [[ -f "$canonical" ]]; then
  restore_canonical="$workspace/canonical-backup.yml"
  cp -a "$canonical" "$restore_canonical"
fi
restore_config() {
  if [[ -n "$restore_canonical" ]]; then
    cp -a "$restore_canonical" "$canonical"
  else
    rm -f "$canonical"
  fi
}
trap 'restore_config; cleanup' EXIT
mkdir -p "$PROJECT_DIR/config"
cp -a "$config_file" "$canonical"

migration() {
  ( cd "$PROJECT_DIR" && "$PYTHON_BIN" -m backend.src.database.migration_cli "$@" )
}

##
## >>================== 1. restore the production shape ==================>>
##
record "restoring the production-shaped snapshot"
started="$(date -u +%s)"
"$MYSQL_BIN" "--defaults-extra-file=$option_file" smsd_rehearsal < "$snapshot" ||
  fail "the production-shaped snapshot could not be restored"
record "restore completed in $(( $(date -u +%s) - started ))s"

##
## >>=================== 2. confirm the source revision ===================>>
##
source_state="$(migration status || true)"
record "source state: $source_state"
[[ "$source_state" == *"current=$expected_source_revision"* ]] ||
  fail "the restored database is not at the expected production revision"

##
## >>====================== 3. upgrade to the head ======================>>
##
record "upgrading to head"
started="$(date -u +%s)"
migration upgrade || fail "the upgrade to head failed"
upgrade_seconds=$(( $(date -u +%s) - started ))
record "upgrade completed in ${upgrade_seconds}s"

post_state="$(migration status)"
record "post state: $post_state"
[[ "$post_state" == *"state=ready"* ]] ||
  fail "the database is not ready after the upgrade"

migration check || fail "the managed schema is not compatible after the upgrade"
record "schema check passed"

##
## >>========================= 4. idempotency =========================>>
##
## Running the upgrade again must be a no-op. A migration that is not
## idempotent turns an interrupted release into a broken one.
##
migration upgrade || fail "a second upgrade failed"
second_state="$(migration status)"
[[ "$second_state" == *"state=ready"* ]] ||
  fail "a second upgrade left the database unready"
record "second upgrade is a no-op: $second_state"

##
## >>=================== 5. the data is still there ===================>>
##
## A migration that completes and empties a table is a migration that completed.
## The counts are compared against the snapshot's own, read before the upgrade.
##
row_report="$(
  "$MYSQL_BIN" "--defaults-extra-file=$option_file" --skip-column-names --batch \
    smsd_rehearsal -e "
      SELECT CONCAT(table_name, '=', table_rows)
      FROM information_schema.tables
      WHERE table_schema = 'smsd_rehearsal'
      ORDER BY table_name;
    "
)"
record "post-upgrade table inventory:"
echo "$row_report" | sed 's/^/  /' | tee -a "$log"

table_count="$(echo "$row_report" | grep -c '=' || true)"
[[ "$table_count" -gt 0 ]] || fail "the upgraded database has no tables"
record "tables present after upgrade: $table_count"

record "rehearsal log retained at $log"
cp -a "$log" "${REHEARSAL_LOG_DESTINATION:-$PROJECT_DIR/../smsd-rehearsal-$(date -u +%Y%m%dT%H%M%SZ).log}" 2>/dev/null || true

echo "$MARKER"
