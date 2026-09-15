#!/usr/bin/env bash
#
# Back up a production that is not Compose.
#
# The Compose backup can stop the writer because it owns it: stop the app
# service, dump, tar the volume, restart. None of that exists here. The writer
# is a bare-metal process nobody wrote a unit for, the database belongs to the
# host, and the media is terabytes that cannot be tarred anywhere.
#
# What survives the move is the ordering, which was the only load-bearing part:
#
#   stop the writer -> prove it stopped -> dump -> snapshot -> manifest ->
#   checksums -> verify
#
# The proof step is new. Compose stopped the writer itself and therefore knew it
# was stopped; here an operator stops it beforehand, so this has to establish
# that rather than assume it. A dump taken beside a live writer describes a
# moment that never existed, and a reflink snapshot taken beside one is worse:
# it clones each file at a slightly different instant, so the tree it captures
# never existed either - in a way no single file reveals.
#
# Every capture failure must leave a bundle that cannot be restored from. A
# half-written bundle that still verifies is the one outcome worse than no
# bundle, because it will be trusted.
#
set -euo pipefail
umask 077

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ENGINE_BIN="${ENGINE_BIN:-podman}"
MYSQLDUMP_BIN="${MYSQLDUMP_BIN:-mysqldump}"
BUNDLE_HELPER="${BUNDLE_HELPER:-$PROJECT_DIR/scripts/release_bundle.py}"
SNAPSHOT_HELPER="${SNAPSHOT_HELPER:-$PROJECT_DIR/scripts/release_media_snapshot.py}"
RUNTIME_CONFIG="${RUNTIME_CONFIG:-$PROJECT_DIR/scripts/runtime_config.py}"
IMAGE_IDENTITY="${IMAGE_IDENTITY:-$PROJECT_DIR/scripts/release_image_identity.py}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-$PROJECT_DIR/requirements.txt}"

output_directory=""
config_file=""
database_name=""
media_root=""
snapshot_root=""
container_name=""
port=""
image_ref=""
db_host=""
source_git_commit=""

usage() {
  cat >&2 <<'USAGE'
usage: release_external_backup.sh
  --output BACKUP_DIRECTORY
  --config-file PATH
  [--database NAME]       must equal $.database.name in the configuration
  --media-root PATH
  --snapshot-root PATH
  --container-name NAME
  --port PORT
  --image ghcr.io/OWNER/REPOSITORY@sha256:DIGEST
  --db-host HOST
  --source-git-commit SHA
USAGE
  exit 2
}

fail() {
  echo "external backup refused: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) [[ $# -ge 2 ]] || usage; output_directory="$2"; shift 2 ;;
    --config-file) [[ $# -ge 2 ]] || usage; config_file="$2"; shift 2 ;;
    --database) [[ $# -ge 2 ]] || usage; database_name="$2"; shift 2 ;;
    --media-root) [[ $# -ge 2 ]] || usage; media_root="$2"; shift 2 ;;
    --snapshot-root) [[ $# -ge 2 ]] || usage; snapshot_root="$2"; shift 2 ;;
    --container-name) [[ $# -ge 2 ]] || usage; container_name="$2"; shift 2 ;;
    --port) [[ $# -ge 2 ]] || usage; port="$2"; shift 2 ;;
    --image) [[ $# -ge 2 ]] || usage; image_ref="$2"; shift 2 ;;
    --db-host) [[ $# -ge 2 ]] || usage; db_host="$2"; shift 2 ;;
    --source-git-commit) [[ $# -ge 2 ]] || usage; source_git_commit="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$output_directory" && -n "$config_file" ]] || usage
[[ -n "$media_root" && -n "$snapshot_root" && -n "$container_name" ]] || usage
[[ -n "$port" && -n "$image_ref" && -n "$db_host" && -n "$source_git_commit" ]] || usage

[[ "$source_git_commit" =~ ^[0-9a-f]{40}$ ]] ||
  fail "source commit must be a 40-character SHA"
[[ "$port" =~ ^[0-9]{1,5}$ ]] || fail "port must be an integer"

##
## >>=========== the image, settled before the configuration is read ===========>>
##
## This backup mounts the operator's configuration - the file holding the
## production database password - into the image, and then runs the image's own
## code against the production database to read schema state. So which image it
## is has to be decided before any of that, and decided by digest: a tag is a
## name whoever controls the registry can repoint after the review, and
## repointing it hands over the credential.
##
## Every check here precedes the 0600 gate below, which is the first thing that
## even reads the file.
##
"$PYTHON_BIN" "$IMAGE_IDENTITY" require-canonical "$image_ref" 2>/dev/null ||
  fail "image must be a canonical digest of this project's GHCR repository"

[[ -f "$REQUIREMENTS_FILE" ]] || fail "requirements lock is absent"
requirements_sha="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"

"$ENGINE_BIN" pull "$image_ref" >/dev/null 2>&1 ||
  fail "the release image could not be pulled by digest"
image_revision="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref" 2>/dev/null)" ||
  fail "the release image could not be inspected"
image_requirements="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "io.smsd.requirements.sha256"}}' "$image_ref" 2>/dev/null)" ||
  fail "the release image could not be inspected"

##
## The commit recorded in the bundle must be the commit the image was built
## from. Otherwise the manifest names a revision nothing in the bundle came
## from, and a restore drill would be proving the wrong thing.
##
[[ "$image_revision" == "$source_git_commit" ]] ||
  fail "the image was not built from the commit this backup records"
[[ "$image_requirements" == "$requirements_sha" ]] ||
  fail "the image was not built against this dependency lock"

##
## The operator's file, refused rather than repaired. It holds the password this
## backup is about to use, and a deployment tool that widened or narrowed an
## operator's file as a side effect of a check would be changing production
## state without being asked.
##
"$PYTHON_BIN" -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('rc', '$RUNTIME_CONFIG')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.require_private_config('$config_file')
" 2>/dev/null || fail "the configuration file must be a 0600 regular file"

##
## >>=============== which database this backup is actually about ===============>>
##
## One authority, resolved once, used by everything downstream.
##
## Before this, two different questions looked like one answer. The schema
## status came from the migration CLI, which reads the canonical configuration
## and therefore reports on the configured database; the dump took whatever an
## operator typed after ``--database``. A single typo produced a bundle whose
## manifest and schema status describe one database and whose rows come from
## another - and nothing downstream can tell, because every artefact in the
## bundle is internally consistent with itself.
##
## So the configuration decides. ``--database`` may still be written, because
## naming the target out loud is worth something on a path that ends in a
## restore, but it decides nothing: it either equals the configured name or this
## refuses, before the credential is staged and long before anything is dumped
## or cloned.
##
if ! database_name="$("$PYTHON_BIN" -c "
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('rc', '$RUNTIME_CONFIG')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.load_runtime_config(Path(sys.argv[1]))
declared = sys.argv[2] or None
sys.stdout.write(module.require_configured_database_name(config, declared))
" "$config_file" "$database_name" 2>/dev/null)"; then
  fail "the database this backup would capture is not the one the configuration names"
fi
[[ -n "$database_name" ]] ||
  fail "the configuration does not name a database"

##
## >>================= prove the writer is actually stopped =================>>
##
## Both ways it can still be running, because they fail independently: a
## container can be up with nothing listening while it starts, and a bare-metal
## writer can hold the port with no container anywhere.
##
##
## An engine that cannot be queried is not an engine reporting "stopped".
## Swallowing its failure here would turn a broken Podman into a silent pass on
## the one check that stands between this and a dump beside a live writer.
##
if ! running="$("$ENGINE_BIN" ps --quiet --filter "name=^${container_name}$" 2>/dev/null)"; then
  fail "the container engine could not be queried; the writer state is unknown"
fi
[[ -z "$running" ]] ||
  fail "the application container is still running; stop the writer before backing up"

if "$PYTHON_BIN" -c "
import socket, sys
probe = socket.socket()
probe.settimeout(2)
sys.exit(0 if probe.connect_ex(('127.0.0.1', int(sys.argv[1]))) == 0 else 1)
" "$port"; then
  fail "port $port is still serving; the writer must be stopped before backing up"
fi

##
## >>========================= capture =========================>>
##

"$PYTHON_BIN" "$BUNDLE_HELPER" prepare-output "$output_directory"

##
## The credential lives in a private directory of its own for the duration and
## is removed on every exit path, successful or not.
##
credential_directory="$(mktemp -d "${TMPDIR:-/tmp}/smsd-backup-credential.XXXXXX")"
chmod 700 "$credential_directory"
option_file="$credential_directory/my.cnf"

cleanup() {
  rm -rf -- "$credential_directory"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

"$PYTHON_BIN" -c "
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('rc', '$RUNTIME_CONFIG')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
config = module.load_runtime_config(Path(sys.argv[1]))
module.write_mysql_option_file(config, Path(sys.argv[2]))
" "$config_file" "$option_file" || fail "the database credential could not be staged"

##
## Schema state, read through the application's own migration CLI in a
## disposable container. The CLI takes no DSN and always reads the staged
## configuration, so this is the only way to ask it about the host database.
##
schema_status_file="$credential_directory/schema-status"
"$ENGINE_BIN" run --rm \
  --env "SMSD_DB_HOST=${db_host}" \
  --volume "${config_file}:/run/secrets/config.yml:ro" \
  "$image_ref" \
  python -m backend.src.database.migration_cli status \
  > "$schema_status_file" 2>/dev/null ||
  fail "the database schema state could not be read"
grep -q "state=ready" "$schema_status_file" ||
  fail "the database schema is not the one this build expects"

##
## The dump. Two things about this invocation are deliberate.
##
## ``--defaults-extra-file`` must be the first argument or the client treats it
## as an unknown option and falls back to whatever other configuration it finds,
## which is how a backup silently connects as the wrong user.
##
## And the database is named positionally rather than with ``--databases``.
## ``--databases X`` emits ``CREATE DATABASE X`` and ``USE X`` into the dump, so
## the SQL selects its own destination and any ``--database`` the restoring
## client passes is ignored. A restore of such a dump lands in the source
## database whatever it was aimed at - which against the production server means
## importing a backup over production while the disposable-target guard reports
## success. The Compose path keeps ``--databases`` because there the destination
## is a whole disposable stack and preserving the name is the point; here the
## destination is a name on a shared server, so the dump must not choose it.
##
## The name itself came from the configuration and not from the command line,
## so the rows in this file, the schema status read above and the manifest
## written below all describe the same database by construction.
##
"$MYSQLDUMP_BIN" \
  "--defaults-extra-file=${option_file}" \
  --single-transaction --routines --triggers --events \
  "$database_name" \
  > "$output_directory/database.sql" ||
  fail "the database could not be dumped"

##
## The media, cloned rather than copied. A failure here aborts the backup: a
## bundle whose media half is missing must never reach the point of having a
## manifest.
##
"$PYTHON_BIN" "$SNAPSHOT_HELPER" create \
  --media-root "$media_root" \
  --snapshot-root "$snapshot_root" \
  --output "$output_directory/media-snapshot.json" ||
  fail "the media tree could not be snapshotted"

##
## >>===================== only now, describe it =====================>>
##
## The manifest and the checksums are written last on purpose. Until they exist
## the bundle does not verify, so every failure above leaves something that
## cannot be restored from rather than something that looks complete.
##
"$PYTHON_BIN" "$BUNDLE_HELPER" write-manifest "$output_directory" \
  --source-git-commit "$source_git_commit" \
  --source-image "$image_ref" \
  --source-project "$container_name" \
  --database-name "$database_name" \
  --schema-status-file "$schema_status_file" \
  --topology external-host

"$PYTHON_BIN" "$BUNDLE_HELPER" write-checksums "$output_directory" \
  --topology external-host

chmod 600 \
  "$output_directory/database.sql" \
  "$output_directory/media-snapshot.json" \
  "$output_directory/manifest.json" \
  "$output_directory/SHA256SUMS"

"$PYTHON_BIN" "$BUNDLE_HELPER" verify "$output_directory"

echo "external backup completed: $output_directory"
