#!/usr/bin/env bash
#
# Prove an external-host bundle can actually be restored from.
#
# A backup nobody has restored is a belief, not a capability. The Compose drill
# already makes this point: it captures, destroys the source, restores from the
# bundle alone and then verifies the restored data - so the bundle is proven
# sufficient rather than assumed to be.
#
# The external drill has to make the same point without the safety the Compose
# one gets for free. There, the destination is a project name and a wrong one
# creates a new empty stack. Here the destination is a database on a host and a
# directory on a filesystem, and a wrong one imports a backup over production or
# unpacks a snapshot over two terabytes of library. So the guards come first and
# they are refusals, not warnings.
#
# The drill restores media by cloning the snapshot rather than moving it. The
# snapshot stays where it is: it is the rollback authority for the release that
# produced it, and a drill that consumed it would have spent the thing it was
# meant to prove.
#
set -euo pipefail
umask 077

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ENGINE_BIN="${ENGINE_BIN:-podman}"
MYSQL_BIN="${MYSQL_BIN:-mysql}"
BUNDLE_HELPER="${BUNDLE_HELPER:-$PROJECT_DIR/scripts/release_bundle.py}"
SNAPSHOT_HELPER="${SNAPSHOT_HELPER:-$PROJECT_DIR/scripts/release_media_snapshot.py}"
RUNTIME_CONFIG="${RUNTIME_CONFIG:-$PROJECT_DIR/scripts/runtime_config.py}"

MARKER="ok   runtime external host restore drill"

backup_directory=""
restore_database=""
restore_media_root=""
config_file=""

usage() {
  cat >&2 <<'USAGE'
usage: release_external_restore_drill.sh
  --backup BACKUP_DIRECTORY
  --restore-database smsd_restore_test_NAME
  --restore-media-root PATH
  --config-file PATH
USAGE
  exit 2
}

fail() {
  echo "external restore drill refused: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup) [[ $# -ge 2 ]] || usage; backup_directory="$2"; shift 2 ;;
    --restore-database) [[ $# -ge 2 ]] || usage; restore_database="$2"; shift 2 ;;
    --restore-media-root) [[ $# -ge 2 ]] || usage; restore_media_root="$2"; shift 2 ;;
    --config-file) [[ $# -ge 2 ]] || usage; config_file="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$backup_directory" && -n "$restore_database" ]] || usage
[[ -n "$restore_media_root" && -n "$config_file" ]] || usage

##
## >>=================== the bundle, before anything else ===================>>
##
## Verified first so every value the guards are about to compare against comes
## from a bundle whose checksums already hold.
##
"$PYTHON_BIN" "$BUNDLE_HELPER" verify "$backup_directory" ||
  fail "the backup bundle does not verify"

topology="$("$PYTHON_BIN" "$BUNDLE_HELPER" field "$backup_directory" topology)"
[[ "$topology" == "external-host" ]] ||
  fail "this drill restores external-host bundles; that bundle is $topology"

source_database="$("$PYTHON_BIN" "$BUNDLE_HELPER" field "$backup_directory" database_name)"
source_media_root="$(
  "$PYTHON_BIN" -c "
import json, sys
document = json.load(open(sys.argv[1], encoding='utf-8'))
sys.stdout.write(document['media_root'])
" "$backup_directory/media-snapshot.json"
)"
snapshot_path="$(
  "$PYTHON_BIN" -c "
import json, sys
document = json.load(open(sys.argv[1], encoding='utf-8'))
sys.stdout.write(document['snapshot_path'])
" "$backup_directory/media-snapshot.json"
)"

##
## >>========================= the destination guards =========================>>
##
"$PYTHON_BIN" "$BUNDLE_HELPER" validate-external-restore-target \
  --database "$restore_database" \
  --media-root "$restore_media_root" \
  --source-database "$source_database" \
  --source-media-root "$source_media_root" ||
  fail "the restore target is not an explicit disposable destination"

"$PYTHON_BIN" "$BUNDLE_HELPER" require-empty-restore-destination \
  "$restore_media_root" ||
  fail "the restore media root already has content"

##
## The snapshot this drill reads from must still be the one that was taken. If
## it is not, the drill would prove a restore of something else.
##
"$PYTHON_BIN" "$SNAPSHOT_HELPER" verify \
  --snapshot-path "$snapshot_path" \
  --document "$backup_directory/media-snapshot.json" ||
  fail "the media snapshot is not the one the bundle describes"

##
## >>============================== restore ==============================>>
##

credential_directory="$(mktemp -d "${TMPDIR:-/tmp}/smsd-drill-credential.XXXXXX")"
chmod 700 "$credential_directory"
cleanup() {
  rm -rf -- "$credential_directory"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

option_file="$credential_directory/my.cnf"
"$PYTHON_BIN" -c "
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('rc', '$RUNTIME_CONFIG')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.load_runtime_config(Path(sys.argv[1]))
module.write_mysql_option_file(config, Path(sys.argv[2]))
" "$config_file" "$option_file" || fail "the restore credential could not be staged"

##
## The dump names its own database, so the target is created and selected here
## rather than trusted to match.
##
"$MYSQL_BIN" "--defaults-extra-file=${option_file}" \
  --execute "DROP DATABASE IF EXISTS \`${restore_database}\`; CREATE DATABASE \`${restore_database}\`;" ||
  fail "the disposable restore database could not be created"

"$MYSQL_BIN" "--defaults-extra-file=${option_file}" \
  --database "$restore_database" < "$backup_directory/database.sql" ||
  fail "the database could not be restored"

##
## Prove the import landed where it was aimed.
##
## The dump is written so that it cannot select its own destination, and this is
## the check that keeps that true: if a future change reintroduced an embedded
## ``USE``, the data would land in the source database and this target would be
## empty. Refusing here turns that from a silent success into a failure.
##
restored_table_count="$(
  "$MYSQL_BIN" "--defaults-extra-file=${option_file}" --skip-column-names --batch \
    --execute "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${restore_database}';"
)"
[[ "$restored_table_count" =~ ^[0-9]+$ ]] ||
  fail "the restored table count could not be read"
(( restored_table_count > 0 )) ||
  fail "the restore produced no tables in the target database; the dump may have selected its own destination"

##
## Media restored by cloning the snapshot, never by moving it. The snapshot is
## the rollback authority for the release that produced it, and a drill that
## consumed it would have spent the thing it exists to prove.
##
mkdir -p "$restore_media_root"
cp -a --reflink=auto "$snapshot_path/." "$restore_media_root/" ||
  fail "the media snapshot could not be restored"

##
## >>============================== verify ==============================>>
##
## Judged against what the restore produced, not against the snapshot's inode
## numbers: cloning makes new inodes by definition, so comparing those would
## fail on a correct restore.
##
"$PYTHON_BIN" - "$backup_directory/media-snapshot.json" "$restore_media_root" <<'PYEOF' ||
import json
import os
from pathlib import Path
import sys

document = json.load(open(sys.argv[1], encoding="utf-8"))
root = Path(sys.argv[2])

expected = {entry["relative_path"]: entry for entry in document["entries"]}
observed = {}
for current, directories, files in os.walk(root):
    for name in files:
        path = Path(current) / name
        info = os.lstat(path)
        observed[str(path.relative_to(root))] = info.st_size

missing = sorted(set(expected) - set(observed))
extra = sorted(set(observed) - set(expected))
if missing or extra:
    print("restored media does not match the snapshot", file=sys.stderr)
    raise SystemExit(1)
for name, entry in expected.items():
    if observed[name] != entry["size"]:
        print("a restored file has the wrong size", file=sys.stderr)
        raise SystemExit(1)

##
## The hidden state has to be there too. A library restored without its recovery
## journal and its quarantine has bookkeeping from another moment.
##
for prefix in (".smsd-recording-recovery/", ".smsd-recording-orphan-quarantine/"):
    if any(name.startswith(prefix) for name in expected):
        if not any(name.startswith(prefix) for name in observed):
            print("hidden recovery state was not restored", file=sys.stderr)
            raise SystemExit(1)
print("restored entries={}".format(len(observed)))
PYEOF
  fail "the restored media does not match the snapshot"

echo "$MARKER"
