#!/usr/bin/env bash
#
# Start the production application against the production that already exists.
#
# The Compose deployment in release_deploy.sh brings its own database and its
# own volume, so it may create what it needs. This one may create nothing: the
# MySQL has the live rows in it, the media tree is terabytes at a path the
# database refers to by name, and the application being replaced is still
# running and still writing.
#
# So this is a sequence of refusals before it is an action. Every check below
# runs before the engine is asked to start anything, because the failure this
# must never produce is two writers against one database.
#
# And once it has started something, it owns it. A deployment that fails after
# the container is up must leave nothing running, or it has produced the exact
# outcome its refusals were written to prevent - while reporting failure, which
# is worse than reporting nothing.
#
# Deliberately not Compose. Production's engine is rootless Podman, the bundled
# MySQL and named volume are not what production uses, and the Compose CPU
# reservations cannot be satisfied on a user slice with no cpu controller.
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE_BIN="${ENGINE_BIN:-podman}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-$PROJECT_DIR/requirements.txt}"
EXTERNAL_POSTCHECK_SCRIPT="${EXTERNAL_POSTCHECK_SCRIPT:-$PROJECT_DIR/scripts/release_external_postcheck.sh}"
RUNTIME_CONFIG="${RUNTIME_CONFIG:-$PROJECT_DIR/scripts/runtime_config.py}"
IMAGE_IDENTITY="${IMAGE_IDENTITY:-$PROJECT_DIR/scripts/release_image_identity.py}"

##
## The account the image drops to. Its numeric identity is read from the image
## rather than written here, because a mapping built from a guessed number is a
## mapping that silently stops being correct.
##
APPLICATION_USER="${APPLICATION_USER:-appuser}"

image_ref=""
expected_revision=""
container_name=""
config_file=""
media_root=""
db_host=""
port=""
health_url=""
memory_limit=""
publish_address=""

usage() {
  cat >&2 <<'USAGE'
usage: release_external_deploy.sh
  --image ghcr.io/OWNER/REPOSITORY@sha256:DIGEST
  --expected-revision COMMIT_SHA
  --container-name NAME
  --config-file PATH
  --media-root PATH
  --db-host HOST
  --port PORT
  --publish-address ADDRESS
  --health-url URL
  [--memory SIZE]
USAGE
  exit 2
}

##
## >>================== what this invocation has done so far ==================>>
##
## Two facts, and every failure path below reads them.
##
## ``started`` is true once the engine has been asked to run a container and has
## answered with an identifier, which is the instant this script becomes
## responsible for a writer. ``committed`` is true only once that writer has
## been proved to be the reviewed image and to have passed the external
## postcheck - the point at which leaving it running is the correct outcome
## rather than the dangerous one.
##
## Between the two, any exit must take the container with it.
##
started_by_this_invocation=false
committed=false
container_id=""

##
## The one outcome that must never be reported quietly.
##
## Reached only when the engine cannot be made to prove the container this
## invocation started is gone. An operator reading a plain failure would
## reasonably assume nothing is running; here something may be, against the
## production database, and the next thing anybody does must account for it.
##
incomplete() {
  ##
  ## Terminal. The worst outcome has already been reported, so the exit trap
  ## must not follow it with a removal aimed at whatever is left - in
  ## particular not at an identifier the engine never gave us.
  ##
  started_by_this_invocation=false
  echo "DEPLOYMENT INCOMPLETE" >&2
  echo "WRITER STATE UNKNOWN" >&2
  echo "external deploy started a container and could not prove it is stopped: $*" >&2
  echo "container id: ${container_id:-unknown}" >&2
  exit 1
}

##
## Remove the container this invocation created, and nothing else.
##
## By identifier, never by name. A name is a label the engine will happily
## attach to a different container, and the container this script must not
## touch under any circumstance is a pre-existing writer - so the thing removed
## here is the exact object the engine handed back from ``run``.
##
abandon_started_container() {
  local reason="$1"
  if [[ "$started_by_this_invocation" != "true" || "$committed" == "true" ]]; then
    return 0
  fi
  ##
  ## Cleared first, so a failure inside the cleanup cannot re-enter it.
  ##
  started_by_this_invocation=false

  if ! "$ENGINE_BIN" rm --force "$container_id" >/dev/null 2>&1; then
    incomplete "the engine refused to remove it ($reason)"
  fi

  ##
  ## Removal reported success; that is not the same as the container being gone.
  ##
  ## The previous spelling asked ``inspect`` for ``.State.Running`` and treated
  ## two different answers as success. ``false`` means the container is still
  ## there and merely stopped - it still holds the name, and the next deployment
  ## would refuse because of it. And a failed ``inspect`` returned no value at
  ## all, which the check read as "not running" and therefore as gone: the one
  ## case where the engine could not answer became the case where it answered
  ## reassuringly.
  ##
  ## So the question is existence, not state, and it is asked of the whole
  ## container list including stopped ones. Three outcomes, kept apart:
  ##
  ##   the query itself fails            -> unknown, and unknown is not absent
  ##   the exact identifier comes back   -> still there, running or not
  ##   the query succeeds with nothing   -> gone, and only now is this a rollback
  ##
  ## Distinguished by exit status and returned identifier rather than by reading
  ## the engine's error text, which is a message and not a contract.
  ##
  local listing
  if ! listing="$("$ENGINE_BIN" ps --all --no-trunc --quiet --filter "id=${container_id}" 2>/dev/null)"; then
    incomplete "the engine could not be asked whether it is gone ($reason)"
  fi
  ##
  ## The filter matches on a prefix, so what comes back is compared against the
  ## identifier this invocation was given rather than assumed to be it.
  ##
  local listed
  while IFS= read -r listed; do
    [[ -n "$listed" ]] || continue
    if [[ "$listed" == "$container_id" ]]; then
      incomplete "the container still exists after removal ($reason)"
    fi
  done <<< "$listing"

  echo "external deploy rolled back: removed the container it started ($reason)" >&2
}

fail() {
  echo "external deploy refused: $*" >&2
  abandon_started_container "$*"
  exit 1
}

##
## ``set -e`` and a signal both reach here, so a failure nobody wrote a message
## for still cannot leave a writer behind.
##
trap 'abandon_started_container "interrupted"; exit 130' HUP INT TERM
trap 'abandon_started_container "the deployment did not complete"' EXIT

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) [[ $# -ge 2 ]] || usage; image_ref="$2"; shift 2 ;;
    --expected-revision) [[ $# -ge 2 ]] || usage; expected_revision="$2"; shift 2 ;;
    --container-name) [[ $# -ge 2 ]] || usage; container_name="$2"; shift 2 ;;
    --config-file) [[ $# -ge 2 ]] || usage; config_file="$2"; shift 2 ;;
    --media-root) [[ $# -ge 2 ]] || usage; media_root="$2"; shift 2 ;;
    --db-host) [[ $# -ge 2 ]] || usage; db_host="$2"; shift 2 ;;
    --port) [[ $# -ge 2 ]] || usage; port="$2"; shift 2 ;;
    --publish-address) [[ $# -ge 2 ]] || usage; publish_address="$2"; shift 2 ;;
    --health-url) [[ $# -ge 2 ]] || usage; health_url="$2"; shift 2 ;;
    --memory) [[ $# -ge 2 ]] || usage; memory_limit="$2"; shift 2 ;;
    ##
    ## Refused rather than dropped.
    ##
    ## A rootless user slice on this host is delegated `memory` and `pids` and
    ## not `cpu`, so a CPU limit cannot be enforced. Accepting the flag and
    ## quietly omitting it would leave an operator believing a limit is in
    ## force, which is worse than not offering one: the documented production
    ## policy is that external-host mode runs with a memory limit and no CPU
    ## limit, exactly as the bare-metal application it replaces does.
    ##
    --cpus)
      fail "a CPU limit cannot be enforced: the cpu controller is not delegated to a rootless user slice; external-host mode runs with a memory limit only"
      ;;
    *) usage ;;
  esac
done

[[ -n "$image_ref" && -n "$expected_revision" && -n "$container_name" ]] || usage
[[ -n "$config_file" && -n "$media_root" && -n "$db_host" ]] || usage
[[ -n "$port" && -n "$health_url" && -n "$publish_address" ]] || usage

##
## >>===================== identity, before anything runs =====================>>
##
## Only a canonical digest is release authority. A tag - `latest`, `sha-...` -
## is a name somebody can repoint after it was reviewed, so it names an
## intention rather than an artifact.
##
##
## One validator, shared with the backup and the restore drill, because three
## regular expressions agree only until one of them is edited.
##
"$PYTHON_BIN" "$IMAGE_IDENTITY" require-canonical "$image_ref" 2>/dev/null ||
  fail "image must be a canonical digest of this project's GHCR repository"
[[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] ||
  fail "expected revision must be a 40-character SHA"
[[ "$container_name" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$ ]] ||
  fail "container name must be a plain identifier"
[[ "$port" =~ ^[0-9]{1,5}$ ]] && (( port >= 1 && port <= 65535 )) ||
  fail "port must be an integer from 1 to 65535"
[[ "$db_host" =~ ^[A-Za-z0-9]([A-Za-z0-9._-]{0,251}[A-Za-z0-9])?$ ]] ||
  fail "database host must be a hostname or address"
##
## Two different exposures are easy to conflate. Inside the container the
## application listens on 0.0.0.0 or nothing outside its namespace could reach
## it - that is the staged config's job. What the *host* publishes is a separate
## decision and the one that changes who can reach production, so it is stated
## on the command line rather than defaulted to whatever seemed reasonable.
##
## Validated as a bare address, because it is interpolated into the publish
## argument and an unchecked value there is a second flag.
##
[[ "$publish_address" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$|^\[[0-9a-fA-F:]+\]$ ]] ||
  fail "publish address must be a plain IPv4 address or a bracketed IPv6 address"
[[ -f "$REQUIREMENTS_FILE" ]] || fail "requirements lock is absent"

##
## >>========================= the operator's file =========================>>
##
## It holds the database password, and production's copy is world-readable
## today. Refused rather than repaired: silently changing the mode of an
## operator's file as a side effect of a deployment check would be changing
## production state without being asked.
##
"$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
import importlib.util
spec = importlib.util.spec_from_file_location('rc', '$RUNTIME_CONFIG')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.require_private_config('$config_file')
" 2>/dev/null || fail "the configuration file must be a 0600 regular file: it holds the database password"

##
## >>=========================== the media tree ===========================>>
##
## Bind-mounted at the same path it has on the host, so nothing has to
## translate paths and the rows already in the database keep meaning what they
## say. Validated as a real directory rather than accepted as a string: this
## value becomes a mount source, and the one mount that must never happen is
## the filesystem root.
##
[[ "$media_root" = /* ]] || fail "media root must be an absolute path"
media_resolved="$($PYTHON_BIN -c "
import os, sys
path = os.path.realpath(sys.argv[1])
sys.stdout.write(path)
" "$media_root")"
[[ "$media_resolved" != "/" ]] || fail "media root must not be the filesystem root"
[[ -d "$media_resolved" ]] || fail "media root is not an existing directory"
##
## Writable *by the identity running this script*, which - because of the
## mapping established below - is exactly the identity the application process
## will have on this bind mount. Without that mapping this check would be
## meaningless: the operator can write a tree the containerised application
## cannot, and that is the failure this whole section exists to prevent.
##
[[ -w "$media_resolved" ]] ||
  fail "media root is not writable by this operator, and the application will run with this operator's host identity"

##
## >>======================== the single-writer gate ========================>>
##
## Two writers against one database and one media tree is the outcome with no
## clean rollback, so both ways it can happen are refused here.
##
##
## An engine that cannot answer is not an engine answering "nothing there".
## A swallowed failure here would let a second writer start because the check
## that should have stopped it could not run.
##
if ! existing="$("$ENGINE_BIN" ps --all --quiet --filter "name=^${container_name}$" 2>/dev/null)"; then
  fail "the container engine could not be queried; refusing to start blind"
fi
[[ -z "$existing" ]] ||
  fail "a container named $container_name already exists; refusing to start a second writer"

if "$PYTHON_BIN" -c "
import socket, sys
probe = socket.socket()
probe.settimeout(2)
sys.exit(0 if probe.connect_ex(('127.0.0.1', int(sys.argv[1]))) == 0 else 1)
" "$port"; then
  fail "port $port is already serving; the previous writer must be stopped first"
fi

##
## >>=========================== the exact image ===========================>>
##
##
## The two engines disagree about how to spell an image ID: Docker prefixes it
## with ``sha256:`` and Podman returns the bare digest. Production runs Podman,
## and the check below was written against Docker's spelling - so it refused
## every real deployment on the engine it was written for, which only running it
## against that engine revealed.
##
## Both forms are accepted, and every ID is normalised before it is compared, so
## the two engines cannot be made to disagree by spelling alone.
##
normalise_image_id() {
  printf '%s' "${1#sha256:}"
}

requirements_sha="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"

"$ENGINE_BIN" pull "$image_ref" >/dev/null
expected_image_id="$(normalise_image_id "$("$ENGINE_BIN" image inspect --format '{{.Id}}' "$image_ref")")"
revision_label="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref")"
requirements_label="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "io.smsd.requirements.sha256"}}' "$image_ref")"

[[ "$expected_image_id" =~ ^[0-9a-f]{64}$ ]] ||
  fail "pulled image ID is malformed"
[[ "$revision_label" == "$expected_revision" ]] ||
  fail "revision label mismatch"
[[ "$requirements_label" == "$requirements_sha" ]] ||
  fail "requirements label mismatch"

##
## >>============== the identity the application will really have ==============>>
##
## The entrypoint runs as root only long enough to stage the mounted
## configuration, then drops to an unprivileged account. Under rootless Podman
## those two are different *host* users: container root maps to the operator,
## and container ``appuser`` maps into the subordinate range - so a bind mount
## the operator owns is readable by the entrypoint and unwritable by the
## application. Proven on this host: without the mapping below the application
## process gets EACCES on a 0755 directory the operator owns.
##
## The fix is a user-namespace mapping, not an ownership change. ``keep-id``
## with an explicit uid and gid places the *operator's* host identity at the
## application's container identity, so the application acts on the media tree
## as the operator already does. Production's ownership is never touched: no
## recursive chown, no ``:U`` on the mount, no privileged container. Files the
## application creates land owned by the operator, exactly as the bare-metal
## writer's do today.
##
## The numbers are read out of the image because they are a property of the
## image. A hard-coded pair would keep working right up until the image changed
## one, and would then map the operator onto the wrong account in silence.
##
if ! application_identity="$("$ENGINE_BIN" run --rm --entrypoint="" "$image_ref" \
    sh -c "id -u $APPLICATION_USER; id -g $APPLICATION_USER" 2>/dev/null)"; then
  fail "the image does not resolve its application account $APPLICATION_USER; the media mapping cannot be established"
fi
application_uid="$(printf '%s\n' "$application_identity" | sed -n 1p | tr -d '[:space:]')"
application_gid="$(printf '%s\n' "$application_identity" | sed -n 2p | tr -d '[:space:]')"
[[ "$application_uid" =~ ^[0-9]{1,10}$ && "$application_gid" =~ ^[0-9]{1,10}$ ]] ||
  fail "the image reported a malformed identity for $APPLICATION_USER"
##
## Refused rather than mapped. ``keep-id:uid=0`` would place the operator at
## container root, which is both a privilege the application does not need and
## a sign the image stopped dropping privileges at all.
##
(( application_uid != 0 && application_gid != 0 )) ||
  fail "the application account $APPLICATION_USER resolves to root in this image; it must be unprivileged"

##
## >>============================== start it ==============================>>
##
## The address travels as an environment value because an address is a fact
## about the network. The password does not travel at all - it stays in the
## mounted file, which the container entrypoint stages into a private copy and
## then drops privileges to read.
##
run_arguments=(
  run --detach
  --name "$container_name"
  --restart unless-stopped
  ##
  ## Bridge networking with an explicit published address, never
  ## ``--network=host``. Host networking would reach the database by dissolving
  ## the namespace boundary rather than routing across it, and it would publish
  ## every port the container opens instead of the one that was asked for.
  ##
  --publish "${publish_address}:${port}:${port}"
  --userns "keep-id:uid=${application_uid},gid=${application_gid}"
  --env "SMSD_DB_HOST=${db_host}"
  --volume "${config_file}:/run/secrets/config.yml:ro"
  --volume "${media_resolved}:${media_resolved}"
)
if [[ -n "$memory_limit" ]]; then
  run_arguments+=(--memory "$memory_limit")
fi
run_arguments+=("$image_ref")

##
## From here on this invocation owns a writer.
##
if ! container_id="$("$ENGINE_BIN" "${run_arguments[@]}")"; then
  fail "the container could not be started"
fi
started_by_this_invocation=true
container_id="$(printf '%s\n' "$container_id" | tail -1 | tr -d '[:space:]')"
[[ "$container_id" =~ ^[0-9a-f]{12,64}$ ]] ||
  incomplete "the engine did not return a usable container identifier"

running_image_id="$(normalise_image_id "$("$ENGINE_BIN" inspect --format '{{.Image}}' "$container_id")")"
[[ "$running_image_id" == "$expected_image_id" ]] ||
  fail "running application image ID mismatch"

"$EXTERNAL_POSTCHECK_SCRIPT" \
  --health-url "$health_url" \
  --container-name "$container_name" \
  --expected-image "$image_ref" \
  --expected-revision "$expected_revision" \
  --expected-requirements-sha "$requirements_sha" \
  --media-root "$media_resolved" \
  --application-user "$APPLICATION_USER" \
  --application-uid "$application_uid" \
  --application-gid "$application_gid" ||
  fail "the external postcheck did not pass"

##
## Only now is leaving it running the right outcome.
##
committed=true
echo "external deployment completed: revision=$expected_revision container=$container_name"
