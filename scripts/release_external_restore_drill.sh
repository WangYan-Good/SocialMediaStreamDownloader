#!/usr/bin/env bash
#
# Prove an external-host bundle can actually be restored from, and run against.
#
# A backup nobody has restored is a belief, not a capability. The Compose drill
# already makes this point: it captures, destroys the source, restores from the
# bundle alone, starts the application and postchecks it - so the bundle is
# proven sufficient rather than assumed to be.
#
# The external drill has to make the same point without the safety the Compose
# one gets for free. There, the destination is a project name and a wrong one
# creates a new empty stack. Here the destination is a database on a shared
# server and a directory on a filesystem, and a wrong one imports a backup over
# production or unpacks a snapshot over two terabytes of library. So the guards
# come first and they are refusals, not warnings - and the destination is
# checked by what it resolves to, not by how it is spelled.
#
# Three things this deliberately does not do.
#
# It never drops a database. An existing name is a refusal, because "drop it and
# recreate it" is indistinguishable from "destroy whatever was there" at the
# moment it matters.
#
# It never falls back to copying. The media is restored by reflink or not at
# all; a byte copy of a tree this size is not a slower success, it is a failure
# that takes hours to arrive.
#
# And it never consumes the snapshot. That snapshot is the rollback authority
# for the release that produced it, and a drill that spent it would have spent
# the thing it exists to prove - so it is cloned, and it is re-verified at the
# end to show the drill did not disturb it.
#
set -euo pipefail
umask 077

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ENGINE_BIN="${ENGINE_BIN:-podman}"
MYSQL_BIN="${MYSQL_BIN:-mysql}"
BUNDLE_HELPER="${BUNDLE_HELPER:-$PROJECT_DIR/scripts/release_bundle.py}"
SNAPSHOT_HELPER="${SNAPSHOT_HELPER:-$PROJECT_DIR/scripts/release_media_snapshot.py}"
INVARIANT_HELPER="${INVARIANT_HELPER:-$PROJECT_DIR/scripts/release_db_invariants.py}"
RUNTIME_CONFIG="${RUNTIME_CONFIG:-$PROJECT_DIR/scripts/runtime_config.py}"
EXTERNAL_POSTCHECK_SCRIPT="${EXTERNAL_POSTCHECK_SCRIPT:-$PROJECT_DIR/scripts/release_external_postcheck.sh}"
IMAGE_IDENTITY="${IMAGE_IDENTITY:-$PROJECT_DIR/scripts/release_image_identity.py}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-$PROJECT_DIR/requirements.txt}"
APPLICATION_USER="${APPLICATION_USER:-appuser}"

MARKER="ok   runtime external host restore drill"

backup_directory=""
restore_database=""
restore_media_root=""
config_file=""
image_ref=""
db_host=""
port=""
container_name=""

usage() {
  cat >&2 <<'USAGE'
usage: release_external_restore_drill.sh
  --backup BACKUP_DIRECTORY
  --restore-database smsd_restore_test_NAME
  --restore-media-root PATH
  --config-file PATH
  --image IMAGE
  --db-host HOST
  [--port PORT]
  [--container-name NAME]
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
    --image) [[ $# -ge 2 ]] || usage; image_ref="$2"; shift 2 ;;
    --db-host) [[ $# -ge 2 ]] || usage; db_host="$2"; shift 2 ;;
    --port) [[ $# -ge 2 ]] || usage; port="$2"; shift 2 ;;
    --container-name) [[ $# -ge 2 ]] || usage; container_name="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$backup_directory" && -n "$restore_database" ]] || usage
[[ -n "$restore_media_root" && -n "$config_file" ]] || usage
[[ -n "$image_ref" && -n "$db_host" ]] || usage

##
## Disposable by construction. Never the production port, never the production
## container name - a drill that borrowed either would be aiming at the writer
## it exists to avoid.
##
container_name="${container_name:-smsd-restore-drill-$$}"
if [[ -z "$port" ]]; then
  port="$("$PYTHON_BIN" -c "
import socket
probe = socket.socket()
probe.bind(('127.0.0.1', 0))
print(probe.getsockname()[1])
probe.close()
")"
fi
[[ "$port" =~ ^[0-9]{1,5}$ ]] || fail "port must be an integer"
[[ "$container_name" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$ ]] ||
  fail "container name must be a plain identifier"

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

##
## >>=========== the image, settled before the credential is staged ===========>>
##
## This drill stages the operator's database credential and hands a
## configuration built from it to whatever image it was given. So the image is
## settled first, by digest, and against an authority outside the image.
##
## That last part is the subtle one. Reading the revision out of the image and
## then asking the postcheck to confirm the image matches it proves only that
## the image agrees with itself. The authority here is the bundle: its manifest
## was written by the backup and its checksums were verified above, before any
## of this ran. The image must be the one that produced the bundle, built from
## the commit the manifest records.
##
## A consequence worth stating: this drill restores a bundle with the image that
## made it. It is not a way to test a newer release against an older bundle -
## that would need its own explicit expected-target arguments, and does not
## exist here.
##
"$PYTHON_BIN" "$IMAGE_IDENTITY" require-canonical "$image_ref" 2>/dev/null ||
  fail "image must be a canonical digest of this project's GHCR repository"

bundle_image="$("$PYTHON_BIN" "$BUNDLE_HELPER" field "$backup_directory" source_image)"
[[ "$image_ref" == "$bundle_image" ]] ||
  fail "this drill restores a bundle with the image that produced it; that is not the image the manifest names"

bundle_revision="$("$PYTHON_BIN" "$BUNDLE_HELPER" field "$backup_directory" source_git_commit)"
[[ -f "$REQUIREMENTS_FILE" ]] || fail "requirements lock is absent"
requirements_sha="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"

"$ENGINE_BIN" pull "$image_ref" >/dev/null 2>&1 ||
  fail "the release image could not be pulled by digest"
image_revision="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref" 2>/dev/null)" ||
  fail "the release image could not be inspected"
image_requirements="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "io.smsd.requirements.sha256"}}' "$image_ref" 2>/dev/null)" ||
  fail "the release image could not be inspected"
[[ "$image_revision" == "$bundle_revision" ]] ||
  fail "the image was not built from the commit the bundle records"
[[ "$image_requirements" == "$requirements_sha" ]] ||
  fail "the image was not built against this dependency lock"

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
## >>=============== will a clone even work between these two? ===============>>
##
## Asked before the database is touched, because the alternative is discovering
## it after the import and either leaving a half-restored drill behind or
## quietly degrading to a copy. Reflink cannot cross a filesystem, so the
## destination and the snapshot have to be on the same one - checked by device
## rather than by path, since a bind mount makes two paths of one filesystem and
## a separate mount makes two filesystems of one path prefix.
##
"$PYTHON_BIN" -c "
import os, sys
from pathlib import Path
snapshot = Path(sys.argv[1])
destination = Path(sys.argv[2])
anchor = destination
while not anchor.exists():
  parent = anchor.parent
  if parent == anchor:
    break
  anchor = parent
if os.stat(snapshot).st_dev != os.stat(anchor).st_dev:
  sys.exit(1)
" "$snapshot_path" "$restore_media_root" ||
  fail "the restore destination is not on the snapshot's filesystem; reflink cannot cross one and a byte copy of the media tree is not a supported fallback"

##
## >>============================== restore ==============================>>
##

credential_directory="$(mktemp -d "${TMPDIR:-/tmp}/smsd-drill-credential.XXXXXX")"
chmod 700 "$credential_directory"

##
## What this invocation created, and therefore what it may take away. Nothing
## that was already there is ever in this list.
##
created_restore_database=false
created_restore_media=false
started_container=false

##
## >>=================== taking the disposable state away ===================>>
##
## This used to be a warning. The drill printed its success marker and then, on
## the way out, tried to remove what it had made; a failure there produced a
## line on stderr and an exit status of zero. So "the bundle is restorable" and
## "there is now an orphaned database, a running container and a cloned media
## tree on this host" were the same result.
##
## They are not the same result. The next run of this drill meets that leftover
## as a refusal, and an operator reading a green line has no reason to look.
##
## So removal is part of the work, each step is *proved* rather than attempted,
## and the marker comes after. Only what this invocation created is ever
## touched, and a failure here never widens the blast radius: it reports and
## fails, it does not go looking for something else to delete.
##
## Returns non-zero if any piece could not be proved gone.
##
remove_disposable_state() {
  local outcome=0

  if [[ "$started_container" == "true" ]]; then
    if ! "$ENGINE_BIN" rm --force "$container_id" >/dev/null 2>&1; then
      echo "external restore drill: the disposable container was not removed" >&2
      outcome=1
    else
      ##
      ## Removed is not the same as gone, and stopped is not gone either. Asked
      ## of the whole list by exact identifier, exactly as the deployment does.
      ##
      local listing
      if ! listing="$("$ENGINE_BIN" ps --all --no-trunc --quiet --filter "id=${container_id}" 2>/dev/null)"; then
        echo "external restore drill: the engine could not confirm the container is gone" >&2
        outcome=1
      elif printf '%s\n' "$listing" | grep -qxF "$container_id"; then
        echo "external restore drill: the disposable container still exists" >&2
        outcome=1
      else
        started_container=false
      fi
    fi
  fi

  if [[ "$created_restore_database" == "true" ]]; then
    ##
    ## Only ever the database this invocation created, and only after proving
    ## the name was free before it took it.
    ##
    if ! "$MYSQL_BIN" "--defaults-extra-file=${option_file}" \
        --execute "DROP DATABASE \`${restore_database}\`;" >/dev/null 2>&1; then
      echo "external restore drill: the disposable database was not dropped" >&2
      outcome=1
    else
      local remaining
      if ! remaining="$("$MYSQL_BIN" "--defaults-extra-file=${option_file}" --skip-column-names --batch \
          --execute "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = '${restore_database}';" 2>/dev/null)"; then
        echo "external restore drill: the server could not confirm the database is gone" >&2
        outcome=1
      elif [[ "$remaining" != "0" ]]; then
        echo "external restore drill: the disposable database still exists" >&2
        outcome=1
      else
        created_restore_database=false
      fi
    fi
  fi

  if [[ "$created_restore_media" == "true" ]]; then
    ##
    ## ``cp -a`` reproduces modes that forbid traversal, so the tree may need to
    ## be made removable first - on paths this invocation itself created.
    ##
    ##
    ## Attempted, not asserted: what decides the outcome is whether the tree is
    ## gone afterwards, not whether these two commands reported success. Written
    ## as guarded blocks rather than ``|| true`` so the rule that no step in this
    ## script may be short-circuited stays absolute and needs no exception.
    ##
    if ! chmod -R u+rwX "$restore_media_root" >/dev/null 2>&1; then
      :
    fi
    if ! rm -rf -- "$restore_media_root" >/dev/null 2>&1; then
      :
    fi
    if [[ -e "$restore_media_root" ]]; then
      echo "external restore drill: the restored media tree still exists" >&2
      outcome=1
    else
      created_restore_media=false
    fi
  fi

  if ! rm -rf -- "$credential_directory" >/dev/null 2>&1; then
    :
  fi
  if [[ -e "$credential_directory" ]]; then
    echo "external restore drill: the credential directory still exists" >&2
    outcome=1
  fi

  return "$outcome"
}

##
## The exit trap covers early failures and signals. On the success path the
## removal has already been done and proved, and each step clears its own flag,
## so this finds nothing left to do rather than doing it twice.
##
cleanup() {
  ##
  ## The exit status here belongs to whatever brought us to the exit, so this
  ## reports and returns rather than replacing it.
  ##
  if ! remove_disposable_state >/dev/null 2>&1; then
    echo "external restore drill: disposable state may remain on this host" >&2
  fi
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
## >>================ a database that is not already there ================>>
##
## Asked before anything destructive, and answered by the server rather than by
## the drill's own confidence. ``DROP DATABASE IF EXISTS`` followed by a create
## is the shape this replaces: it reads as isolation and behaves as destruction,
## because at the moment it runs nobody knows whether the name was free.
##
existing_schema="$(
  "$MYSQL_BIN" "--defaults-extra-file=${option_file}" --skip-column-names --batch \
    --execute "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = '${restore_database}';"
)" || fail "the server could not be asked whether the restore database exists"
[[ "$existing_schema" == "0" ]] ||
  fail "the restore database already exists; this drill will not destroy a database it did not create"

##
## A plain create, so a second actor taking the name between the question and
## the answer makes this fail rather than silently share a destination.
##
"$MYSQL_BIN" "--defaults-extra-file=${option_file}" \
  --execute "CREATE DATABASE \`${restore_database}\`;" ||
  fail "the disposable restore database could not be created; another actor may have taken the name"
created_restore_database=true

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
## And that it landed with rows in it. A schema-only restore satisfies every
## check above and would restore nothing anybody wanted back.
##
"$PYTHON_BIN" "$INVARIANT_HELPER" collect \
  --option-file "$option_file" \
  --database "$restore_database" \
  --mysql-bin "$MYSQL_BIN" \
  --output "$credential_directory/restored-invariants.json" ||
  fail "the restored database could not be described"
restored_rows="$(
  "$PYTHON_BIN" -c "
import json, sys
document = json.load(open(sys.argv[1], encoding='utf-8'))
print(sum(entry['rows'] for entry in document['tables'].values()))
" "$credential_directory/restored-invariants.json"
)"
(( restored_rows > 0 )) ||
  fail "the restored database holds no rows; the bundle restores a schema and nothing else"
echo "restored database: tables=$restored_table_count rows=$restored_rows"

##
## Media restored by cloning the snapshot, never by moving it, and never by
## copying it. ``--reflink=always`` makes the command fail rather than silently
## spend hours filling a disk.
##
mkdir -p "$restore_media_root"
created_restore_media=true
cp -a --reflink=always "$snapshot_path/." "$restore_media_root/" ||
  fail "the media snapshot could not be cloned into the restore destination"

##
## >>======================== verify what was restored ========================>>
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

##
## >>================= and now run the application against it =================>>
##
## Everything above proves the bundle contains what it claims. None of it proves
## the application can start on the result, which is the only question an
## operator restoring at three in the morning actually has.
##
## The application gets a configuration of its own, naming the restored database
## and the restored media root. The operator's file is read and never written.
##
drill_config="$credential_directory/config.yml"
"$PYTHON_BIN" - "$config_file" "$drill_config" "$restore_database" "$restore_media_root" "$port" <<'PYEOF' ||
import sys
from pathlib import Path

import yaml

source = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
source["database"]["name"] = sys.argv[3]
source["download"]["save_path"] = sys.argv[4]
source["server"]["port"] = int(sys.argv[5])
##
## A restored copy must not start doing the real thing.
##
## Everything this drill proves - that the application starts, reaches the
## restored database, has the restored library under it and answers - is proved
## without the application fetching anything. Left live, a second instance of
## production would begin working through whatever the restored rows describe:
## duplicate requests to a platform that rate-limits by cumulative volume, and
## new writes into a tree whose whole purpose here is to be compared against the
## snapshot it came from.
##
## So the drill's copy is inert by construction, and says so rather than relying
## on the restored data happening to be idle.
##
## Two things make that hold, and both were checked against the application
## rather than assumed. The startup path runs one bounded, local journal replay
## - it reads the restored recovery directory and writes rows, which is exactly
## the recovery this drill wants to prove, and it reaches no platform. And
## nothing else starts on its own: the application has no scheduler, no
## background thread, no timer and no auto-resume, so a recording begins only
## when an HTTP request asks for one. The drill sends one request, to the health
## endpoint.
##
source["download"]["test_mode"] = True
source["download"]["save_response"] = False
source["download"]["save_error_response"] = False
Path(sys.argv[2]).write_text(
    yaml.safe_dump(source, allow_unicode=True, sort_keys=False), encoding="utf-8"
)
PYEOF
  fail "the drill configuration could not be staged"
chmod 600 "$drill_config"

##
## The same identity the deployment establishes, for the same reason: under a
## rootless engine the account the entrypoint drops to is not the account the
## mount was created by, and a restored library the application cannot write is
## a restore that has not been proved.
##
if ! application_identity="$("$ENGINE_BIN" run --rm --entrypoint="" "$image_ref" \
    sh -c "id -u $APPLICATION_USER; id -g $APPLICATION_USER" 2>/dev/null)"; then
  fail "the image does not resolve its application account $APPLICATION_USER"
fi
application_uid="$(printf '%s\n' "$application_identity" | sed -n 1p | tr -d '[:space:]')"
application_gid="$(printf '%s\n' "$application_identity" | sed -n 2p | tr -d '[:space:]')"
[[ "$application_uid" =~ ^[0-9]{1,10}$ && "$application_gid" =~ ^[0-9]{1,10}$ ]] ||
  fail "the image reported a malformed identity for $APPLICATION_USER"

if ! container_id="$("$ENGINE_BIN" run --detach \
  --name "$container_name" \
  --publish "127.0.0.1:${port}:${port}" \
  --userns "keep-id:uid=${application_uid},gid=${application_gid}" \
  --env "SMSD_DB_HOST=${db_host}" \
  --volume "${drill_config}:/run/secrets/config.yml:ro" \
  --volume "${restore_media_root}:${restore_media_root}" \
  "$image_ref")"; then
  fail "the disposable application could not be started against the restored state"
fi
started_container=true
##
## By identifier, like the deployment: a name is a label the engine will happily
## attach to something else.
##
container_id="$(printf '%s\n' "$container_id" | tail -1 | tr -d '[:space:]')"
[[ "$container_id" =~ ^[0-9a-f]{12,64}$ ]] ||
  fail "the engine did not return a usable container identifier"

##
## Startup recovery runs while the application comes up, so the postcheck's
## health probe is also the evidence that it survived the restored journal.
##
for attempt in $(seq 1 60); do
  if "$ENGINE_BIN" exec "$container_name" true >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

##
## The real postcheck, not a reimplementation of it. It proves the running image
## is the one that was asked for, the media is mounted at its path, the
## application account can write it, the schema is at this build's head, and the
## health endpoint answers.
##
"$EXTERNAL_POSTCHECK_SCRIPT" \
  --health-url "http://127.0.0.1:${port}/" \
  --container-name "$container_name" \
  --expected-image "$image_ref" \
  --expected-revision "$bundle_revision" \
  --expected-requirements-sha "$requirements_sha" \
  --media-root "$restore_media_root" \
  --application-user "$APPLICATION_USER" \
  --application-uid "$application_uid" \
  --application-gid "$application_gid" ||
  fail "the application did not pass the external postcheck against the restored state"

##
## >>=============== the source is exactly as it was found ===============>>
##
## Last, because everything above had the opportunity to disturb it. A drill
## that proved a restore by consuming the snapshot would have spent the rollback
## authority for the release that produced it.
##
"$PYTHON_BIN" "$SNAPSHOT_HELPER" verify \
  --snapshot-path "$snapshot_path" \
  --document "$backup_directory/media-snapshot.json" ||
  fail "the drill disturbed the snapshot it restored from"
"$PYTHON_BIN" "$BUNDLE_HELPER" verify "$backup_directory" ||
  fail "the drill disturbed the bundle it restored from"

##
## >>============ and the host is left as it was found ============>>
##
## Before the marker, not after it. A drill that proves a bundle restorable and
## leaves a database, a container and a cloned tree behind has not finished; the
## marker says it has.
##
remove_disposable_state ||
  fail "the drill could not prove it removed the disposable state it created"

echo "$MARKER"
