#!/usr/bin/env bash
#
# Rehearse the production migration against a production-shaped database, twice.
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
# Two things this used to get wrong, both now fixed here.
#
# It proved that tables existed afterwards and called that data preservation.
# What it printed was ``information_schema.tables.table_rows``, which for InnoDB
# is an estimate the optimiser keeps from sampled index pages - it drifts by
# large fractions and is recomputed at times nobody controls. Every count in
# this rehearsal is now an exact ``COUNT(*)``, taken before the upgrade and
# again after it, alongside an order-independent checksum of each table's
# primary key so that a table whose count is unchanged cannot have had its rows
# quietly replaced.
#
# And it ran the upgrade once and then ran it again, which proves idempotency
# and not reproducibility. Those are different claims: "applying head twice is a
# no-op" says nothing about whether 0002 -> head behaves the same way the second
# time it is attempted. So the whole thing is done twice, each time from the same
# verified immutable snapshot onto a *fresh* server, and the invariants are
# compared across both.
#
# Touches nothing in production: not the database, not the application, not the
# media, and - unlike its first version - not the working repository's own
# configuration either. The migration CLI reads one fixed path, so the rehearsal
# gets a private copy of the project to read it from.
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE_BIN="${ENGINE_BIN:-podman}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MYSQL_BIN="${MYSQL_BIN:-mysql}"
MYSQL_IMAGE="${MYSQL_IMAGE:-docker.io/library/mysql:8.0.46}"
INVARIANT_HELPER="${INVARIANT_HELPER:-$PROJECT_DIR/scripts/release_db_invariants.py}"

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
## The snapshot is evidence, so its identity is checked before it is used and
## again after each run. A rehearsal against a file that is not the one taken
## from production proves something about a different database, and a rehearsal
## whose second run read a different file than its first proves nothing at all.
##
[[ -f "$snapshot" ]] || fail "the snapshot is absent"
require_snapshot_identity() {
  local actual
  actual="$(sha256sum "$snapshot" | awk '{print $1}')"
  [[ "$actual" == "$expected_sha" ]] ||
    fail "the snapshot is not the file this rehearsal was authorised against ($1)"
}
require_snapshot_identity "before the first run"

workspace="$(mktemp -d "${TMPDIR:-/tmp}/smsd-rehearsal.XXXXXX")"
chmod 700 "$workspace"
containers=()

cleanup() {
  for name in "${containers[@]:-}"; do
    [[ -n "$name" ]] || continue
    if ! "$ENGINE_BIN" rm -f "$name" >/dev/null 2>&1; then
      echo "rehearsal warning: a disposable database container was not removed: $name" >&2
    fi
  done
  rm -rf -- "$workspace"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

log="$workspace/rehearsal.log"
record() {
  echo "$*" | tee -a "$log"
}

record "rehearsal snapshot sha256=$expected_sha"
record "rehearsal expected source revision=$expected_source_revision"

##
## >>=============== a project of its own to read from ===============>>
##
## The migration CLI resolves its configuration from its own module's location,
## so pointing it at another database means giving it another project. The first
## version of this script did that by overwriting the working repository's
## ``config/config.yml`` and restoring it afterwards - which works until it
## does not, and whose failure mode is a developer's checkout left holding a
## rehearsal's credentials.
##
## A copy costs about twenty megabytes and removes the question. Nothing here
## ever writes inside the repository.
##
isolated="$workspace/project"
"$PYTHON_BIN" - "$PROJECT_DIR" "$isolated" <<'PYEOF' || fail "the isolated project could not be staged"
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])

IGNORED = {
    "venv", ".venv", ".git", "node_modules", "__pycache__",
    "logs", "downloads", "config", ".pytest_cache", "dist",
}


def ignore(directory, names):
    return [name for name in names if name in IGNORED]


target.mkdir(parents=True)
for name in ("backend", "scripts", "docs"):
    shutil.copytree(source / name, target / name, ignore=ignore, symlinks=False)
(target / "config").mkdir(mode=0o700)
PYEOF

##
## Which database the snapshot will actually land in.
##
## A dump taken with ``--databases`` carries ``CREATE DATABASE X`` and ``USE X``
## and therefore selects its own destination; the restoring client's choice is
## ignored. This snapshot is one of those - it predates the release tooling - so
## the rehearsal reads the name out of it rather than assuming its own.
##
## Guessing wrong here does not fail loudly, which is what makes it worth
## handling: the import succeeds, the intended database stays empty, and the
## rehearsal reports ``unversioned`` as though production had no schema at all.
##
embedded_database="$(
  head -c 200000 "$snapshot" |
    grep -aoE '^USE `[^`]+`;' |
    head -1 |
    sed -E 's/^USE `//; s/`;$//'
)"
if [[ -n "$embedded_database" ]]; then
  rehearsal_database="$embedded_database"
  record "the snapshot selects its own database: using $rehearsal_database"
else
  rehearsal_database="smsd_rehearsal"
  record "the snapshot names no database: using $rehearsal_database"
fi

migration() {
  ( cd "$isolated" && PYTHONPATH="$isolated" "$PYTHON_BIN" -m backend.src.database.migration_cli "$@" )
}

##
## Parsed rather than matched, so "ready" cannot be satisfied by a line naming
## no revision, and a build that grew a second head cannot pass.
##
require_ready_at_head() {
  local status="$1" label="$2" state current heads
  state="$(printf '%s\n' "$status" | sed -n 's/.*state=\([^ ]*\).*/\1/p' | head -1)"
  current="$(printf '%s\n' "$status" | sed -n 's/.*current=\([^ ]*\).*/\1/p' | head -1)"
  heads="$(printf '%s\n' "$status" | sed -n 's/.*heads=\([^ ]*\).*/\1/p' | head -1)"
  [[ "$state" == "ready" ]] || fail "$label: the database is not ready"
  [[ -n "$current" && "$current" != "none" ]] || fail "$label: no applied revision"
  [[ "$heads" != *","* ]] || fail "$label: the build has more than one head"
  [[ "$current" == "$heads" ]] || fail "$label: the database is not at the head"
  printf '%s' "$current"
}

##
## >>======================== one whole rehearsal ========================>>
##
## Called twice, on two fresh servers, from the same immutable snapshot. The
## second call is not a repetition for its own sake: it is the difference
## between "applying head twice is a no-op" and "0002 -> head behaves the same
## way the second time it is attempted", and only the second is what a release
## window depends on.
##
run_number=0
rehearse() {
  local label="$1" baseline_output="$2" post_output="$3"
  run_number=$(( run_number + 1 ))
  local container="smsd-rehearsal-$$-$run_number"
  local run_port=$(( port + run_number - 1 ))

  require_snapshot_identity "$label"

  record ""
  record ">> $label"
  "$ENGINE_BIN" run -d --name "$container" \
    -e MYSQL_ROOT_PASSWORD=rehearsal \
    -e MYSQL_DATABASE=smsd_rehearsal \
    -p "127.0.0.1:${run_port}:3306" \
    "$MYSQL_IMAGE" >/dev/null
  containers+=("$container")

  for attempt in $(seq 1 180); do
    if "$ENGINE_BIN" exec "$container" \
        mysqladmin ping -h 127.0.0.1 -uroot -prehearsal >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  "$ENGINE_BIN" exec "$container" \
    mysqladmin ping -h 127.0.0.1 -uroot -prehearsal >/dev/null 2>&1 ||
    fail "$label: the disposable MySQL never became ready"
  record "$label: disposable mysql ready on 127.0.0.1:$run_port"

  local option_file="$workspace/my-$run_number.cnf"
  ( umask 077; cat > "$option_file" <<CNF
[client]
user=root
password=rehearsal
host=127.0.0.1
port=$run_port
CNF
  )
  chmod 600 "$option_file"

  ##
  ## The isolated project's configuration, rewritten per run because each run
  ## has its own server. The repository's own file is never involved.
  ##
  "$PYTHON_BIN" - "$isolated/config/config.yml" "$run_port" "$rehearsal_database" "$PROJECT_DIR" <<'PYEOF' ||
import sys
from pathlib import Path
import yaml

example = Path(sys.argv[4]) / "docs" / "design" / "config.yml.example"
config = yaml.safe_load(example.read_text(encoding="utf-8"))
config["database"].update({
    "enable": True,
    "host": "127.0.0.1",
    "port": int(sys.argv[2]),
    "username": "root",
    "password": "rehearsal",
    "name": sys.argv[3],
})
Path(sys.argv[1]).write_text(
    yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
)
PYEOF
    fail "$label: the rehearsal configuration could not be staged"
  chmod 600 "$isolated/config/config.yml"

  ##
  ## 1. restore the production shape
  ##
  local started
  started="$(date -u +%s)"
  "$MYSQL_BIN" "--defaults-extra-file=$option_file" < "$snapshot" ||
    fail "$label: the production-shaped snapshot could not be restored"
  record "$label: restore completed in $(( $(date -u +%s) - started ))s"

  ##
  ## 2. confirm the source revision
  ##
  local source_state
  ##
  ## ``status`` exits non-zero for any state that is not ``ready``, and
  ## before the upgrade the state is deliberately not ready - that is the
  ## whole point of asking. So the exit status is suppressed deliberately
  ## and narrowly, around this one capture, rather than with a trailing
  ## ``|| true`` that reads like every other skipped step.
  ##
  set +e
  source_state="$(migration status)"
  set -e
  record "$label: source state: $source_state"
  [[ "$source_state" == *"current=$expected_source_revision"* ]] ||
    fail "$label: the restored database is not at the expected production revision"

  ##
  ## 3. what is in it, exactly, before anything migrates
  ##
  "$PYTHON_BIN" "$INVARIANT_HELPER" collect \
    --option-file "$option_file" \
    --database "$rehearsal_database" \
    --mysql-bin "$MYSQL_BIN" \
    --output "$baseline_output" ||
    fail "$label: the pre-upgrade invariants could not be collected"
  record "$label: $("$PYTHON_BIN" -c "
import json, sys
document = json.load(open(sys.argv[1], encoding='utf-8'))
print('baseline tables={} rows={}'.format(
  len(document['tables']), sum(e['rows'] for e in document['tables'].values())
))
" "$baseline_output")"

  ##
  ## 4. upgrade to the head
  ##
  started="$(date -u +%s)"
  migration upgrade || fail "$label: the upgrade to head failed"
  record "$label: upgrade completed in $(( $(date -u +%s) - started ))s"

  local head_revision
  head_revision="$(require_ready_at_head "$(migration status)" "$label")"
  record "$label: at head $head_revision"

  migration check || fail "$label: the managed schema is not compatible after the upgrade"
  record "$label: schema check passed"

  ##
  ## 5. and what is in it now
  ##
  "$PYTHON_BIN" "$INVARIANT_HELPER" collect \
    --option-file "$option_file" \
    --database "$rehearsal_database" \
    --mysql-bin "$MYSQL_BIN" \
    --output "$post_output" ||
    fail "$label: the post-upgrade invariants could not be collected"

  "$PYTHON_BIN" "$INVARIANT_HELPER" compare \
    --baseline "$baseline_output" \
    --observed "$post_output" | tee -a "$log" ||
    fail "$label: the upgrade did not preserve the data it was given"
  record "$label: data invariants held across the upgrade"

  ##
  ## 6. idempotency, which is a different claim from either of the above
  ##
  migration upgrade || fail "$label: a second upgrade failed"
  require_ready_at_head "$(migration status)" "$label (second upgrade)" >/dev/null
  record "$label: a second upgrade is a no-op"

  ##
  ## The server goes away with the run, so the next one starts from nothing.
  ##
  "$ENGINE_BIN" rm -f "$container" >/dev/null ||
    fail "$label: the disposable server could not be destroyed"
  record "$label: disposable server destroyed"
}

rehearse "run 1" "$workspace/baseline-1.json" "$workspace/post-1.json"
rehearse "run 2 (independent, fresh server)" \
  "$workspace/baseline-2.json" "$workspace/post-2.json"

##
## >>================== the two runs agree with each other ==================>>
##
## The same snapshot restored onto two fresh servers has to produce the same
## database, or the rehearsal is measuring the servers rather than the data.
##
"$PYTHON_BIN" "$INVARIANT_HELPER" compare \
  --baseline "$workspace/baseline-1.json" \
  --observed "$workspace/baseline-2.json" | tee -a "$log" ||
  fail "the two restores of the same snapshot did not produce the same database"
"$PYTHON_BIN" "$INVARIANT_HELPER" compare \
  --baseline "$workspace/post-1.json" \
  --observed "$workspace/post-2.json" | tee -a "$log" ||
  fail "the two upgrades of the same snapshot did not produce the same database"
record "both runs agree, before and after the upgrade"

require_snapshot_identity "after both runs"
record "the snapshot is byte-identical to the file both runs began from"

record ""
record "rehearsal log retained at $log"
cp -a "$log" "${REHEARSAL_LOG_DESTINATION:-$PROJECT_DIR/../smsd-rehearsal-$(date -u +%Y%m%dT%H%M%SZ).log}"

echo "$MARKER"
