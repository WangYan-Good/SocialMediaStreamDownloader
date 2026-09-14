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

image_ref=""
expected_revision=""
container_name=""
config_file=""
media_root=""
db_host=""
port=""
health_url=""
memory_limit=""

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
  --health-url URL
  [--memory SIZE]
USAGE
  exit 2
}

fail() {
  echo "external deploy refused: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) [[ $# -ge 2 ]] || usage; image_ref="$2"; shift 2 ;;
    --expected-revision) [[ $# -ge 2 ]] || usage; expected_revision="$2"; shift 2 ;;
    --container-name) [[ $# -ge 2 ]] || usage; container_name="$2"; shift 2 ;;
    --config-file) [[ $# -ge 2 ]] || usage; config_file="$2"; shift 2 ;;
    --media-root) [[ $# -ge 2 ]] || usage; media_root="$2"; shift 2 ;;
    --db-host) [[ $# -ge 2 ]] || usage; db_host="$2"; shift 2 ;;
    --port) [[ $# -ge 2 ]] || usage; port="$2"; shift 2 ;;
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
[[ -n "$port" && -n "$health_url" ]] || usage

##
## >>===================== identity, before anything runs =====================>>
##
## Only a canonical digest is release authority. A tag - `latest`, `sha-...` -
## is a name somebody can repoint after it was reviewed, so it names an
## intention rather than an artifact.
##
[[ "$image_ref" =~ ^ghcr\.io/[a-z0-9][a-z0-9._/-]*@sha256:[0-9a-f]{64}$ ]] ||
  fail "image must be a canonical lowercase GHCR digest"
[[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] ||
  fail "expected revision must be a 40-character SHA"
[[ "$container_name" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$ ]] ||
  fail "container name must be a plain identifier"
[[ "$port" =~ ^[0-9]{1,5}$ ]] && (( port >= 1 && port <= 65535 )) ||
  fail "port must be an integer from 1 to 65535"
[[ "$db_host" =~ ^[A-Za-z0-9]([A-Za-z0-9._-]{0,251}[A-Za-z0-9])?$ ]] ||
  fail "database host must be a hostname or address"
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
[[ -w "$media_resolved" ]] || fail "media root is not writable"

##
## >>======================== the single-writer gate ========================>>
##
## Two writers against one database and one media tree is the outcome with no
## clean rollback, so both ways it can happen are refused here.
##
existing="$("$ENGINE_BIN" ps --all --quiet --filter "name=^${container_name}$" 2>/dev/null || true)"
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
requirements_sha="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"

"$ENGINE_BIN" pull "$image_ref" >/dev/null
expected_image_id="$("$ENGINE_BIN" image inspect --format '{{.Id}}' "$image_ref")"
revision_label="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref")"
requirements_label="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "io.smsd.requirements.sha256"}}' "$image_ref")"

[[ "$expected_image_id" =~ ^sha256:[0-9a-f]{64}$ ]] ||
  fail "pulled image ID is malformed"
[[ "$revision_label" == "$expected_revision" ]] ||
  fail "revision label mismatch"
[[ "$requirements_label" == "$requirements_sha" ]] ||
  fail "requirements label mismatch"

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
  --publish "127.0.0.1:${port}:${port}"
  --env "SMSD_DB_HOST=${db_host}"
  --volume "${config_file}:/run/secrets/config.yml:ro"
  --volume "${media_resolved}:${media_resolved}"
)
if [[ -n "$memory_limit" ]]; then
  run_arguments+=(--memory "$memory_limit")
fi
run_arguments+=("$image_ref")

"$ENGINE_BIN" "${run_arguments[@]}" >/dev/null

running_image_id="$("$ENGINE_BIN" inspect --format '{{.Image}}' "$container_name")"
[[ "$running_image_id" == "$expected_image_id" ]] ||
  fail "running application image ID mismatch"

"$EXTERNAL_POSTCHECK_SCRIPT" \
  --health-url "$health_url" \
  --container-name "$container_name" \
  --expected-image "$image_ref" \
  --expected-revision "$expected_revision" \
  --expected-requirements-sha "$requirements_sha" \
  --media-root "$media_resolved"

echo "external deployment completed: revision=$expected_revision container=$container_name"
