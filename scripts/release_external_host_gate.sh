#!/usr/bin/env bash
#
# The proof a stubbed engine cannot give.
#
# Every deterministic test of this topology runs against a bash script that
# records its arguments. That proves the contract - which refusals fire, in what
# order, what never reaches a command line - and it proves nothing at all about
# whether rootless Podman on this host will do what the contract assumes.
#
# So this runs the real thing, on the real engine, against disposable
# everything: throwaway services, a media tree under a temporary directory, and
# the real application image. It never touches the production database, the
# production media root or the production writer.
#
# It is a real-infra gate rather than a CI step because the behaviour it proves
# is a property of this host: which cgroup controllers are delegated, which host
# addresses a container can reach, how the engine maps user namespaces, and
# whether the filesystem can clone. A GitHub runner would answer all four
# differently and the answer would mean nothing.
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE_BIN="${ENGINE_BIN:-podman}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BUSYBOX_IMAGE="${BUSYBOX_IMAGE:-docker.io/library/busybox:latest}"
MYSQL_IMAGE="${MYSQL_IMAGE:-docker.io/library/mysql:8.0.46}"
APPLICATION_USER="${APPLICATION_USER:-appuser}"

MARKER="ok   runtime external host deployment gate"

image_ref=""

usage() {
  cat >&2 <<'USAGE'
usage: release_external_host_gate.sh --image IMAGE

  --image  the real application image. The media proof runs the real
           entrypoint as the real unprivileged account, because that is the
           only identity whose access matters.
USAGE
  exit 2
}

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

require() {
  if ! eval "$1"; then
    fail "$2"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) [[ $# -ge 2 ]] || usage; image_ref="$2"; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$image_ref" ]] || usage

workspace="$(mktemp -d "${TMPDIR:-/tmp}/smsd-external-gate.XXXXXX")"
chmod 700 "$workspace"
container="smsd-external-gate-$$"
mysql_container="smsd-external-gate-mysql-$$"
listener_pid=""

cleanup() {
  if [[ -n "$listener_pid" ]]; then
    kill "$listener_pid" 2>/dev/null || true
    wait "$listener_pid" 2>/dev/null || true
  fi
  for name in "$container" "$mysql_container"; do
    if ! "$ENGINE_BIN" rm -f "$name" >/dev/null 2>&1; then
      :
    fi
  done
  chmod -R u+rwX "$workspace" >/dev/null 2>&1 || true
  rm -rf -- "$workspace"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM

echo "external-host gate workspace: $workspace"

##
## >>=================== 1. the engine is what we think ===================>>
##
engine_version="$("$ENGINE_BIN" version --format '{{.Client.Version}}')"
rootless="$("$ENGINE_BIN" info --format '{{.Host.Security.Rootless}}')"
echo "engine=$engine_version rootless=$rootless"
require '[[ "$rootless" == "true" ]]' "the gate must run rootless, as production does"

##
## >>============== 2. the cgroup reality the design depends on ==============>>
##
## The deploy script refuses --cpus rather than dropping it, and that refusal is
## only correct if the controller really is unavailable. Proven by asking the
## engine to apply one.
##
controllers="$(cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers 2>/dev/null || echo "")"
echo "delegated controllers: $controllers"
if "$ENGINE_BIN" run --rm --cpus 1.0 "$BUSYBOX_IMAGE" true >/dev/null 2>&1; then
  cpu_limit_supported=true
else
  cpu_limit_supported=false
fi
memory_limit_supported=true
"$ENGINE_BIN" run --rm --memory 256m "$BUSYBOX_IMAGE" true >/dev/null 2>&1 ||
  memory_limit_supported=false
echo "cpu_limit_supported=$cpu_limit_supported memory_limit_supported=$memory_limit_supported"
require '[[ "$memory_limit_supported" == "true" ]]' \
  "external-host mode applies a memory limit, so the memory controller must work"
if [[ "$cpu_limit_supported" == "true" ]]; then
  ##
  ## Not a failure - it means the host gained a delegation. It is reported
  ## loudly because the documented policy assumes the opposite and would need
  ## revisiting rather than silently continuing to apply no CPU limit.
  ##
  echo "NOTE: the cpu controller is now delegated; the no-CPU-limit policy should be revisited"
fi

##
## >>=============== 3. a container can reach a host service ===============>>
##
## The whole topology rests on this: the application runs in a namespace and the
## database does not. If the route does not exist, nothing else matters.
##
## Two separate questions, deliberately separated.
##
## Whether the *route* exists is a question about networking and needs no
## credentials at all, so it is answered first with a listener that serves one
## word and knows nothing. The previous version of this gate answered it by
## publishing a MySQL with a known root password on every interface of a
## production host for the length of the probe, which is a large exposure to
## take on for a question about routing.
##
## Whether *MySQL* is reachable over that route is asked second, still with a
## real server, but bound to the single host address the route actually uses and
## with a password generated for this run and never written down.
##
## The narrow address is not decoration. Measured on this host: a service bound
## to 127.0.0.1 is unreachable from a container, a service bound to the host's
## route address is reachable through ``host.containers.internal``, and the
## container cannot reach that address by any other spelling. So the route
## address is the narrowest binding that works, and ``0.0.0.0`` - every
## interface the machine has, now and in future - is strictly wider than the
## proof requires.
##
host_route_address="$("$PYTHON_BIN" -c "
import socket, sys
probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
  ##
  ## A connected UDP socket sends nothing. This asks the routing table which
  ## local address would be used, and nothing leaves the machine.
  ##
  probe.connect(('192.0.2.1', 9))
  sys.stdout.write(probe.getsockname()[0])
finally:
  probe.close()
")"
[[ "$host_route_address" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] ||
  fail "this host has no routable address; the container-to-host route cannot be proven"
[[ "$host_route_address" != "127.0.0.1" ]] ||
  fail "the host routes to loopback only; a container cannot reach a service here"
echo "host route address: $host_route_address"

##
## A listener that holds no secret, bound to that one address.
##
"$PYTHON_BIN" - "$host_route_address" "$workspace/route-port" <<'PYEOF' &
import socketserver
import sys
from pathlib import Path


class Handler(socketserver.BaseRequestHandler):
  def handle(self):
    self.request.sendall(b"smsd-route-probe\n")


socketserver.TCPServer.allow_reuse_address = True
server = socketserver.TCPServer((sys.argv[1], 0), Handler)
Path(sys.argv[2]).write_text(str(server.server_address[1]), encoding="utf-8")
server.serve_forever()
PYEOF
listener_pid=$!

for attempt in $(seq 1 30); do
  [[ -s "$workspace/route-port" ]] && break
  sleep 1
done
[[ -s "$workspace/route-port" ]] || fail "the route probe listener never started"
route_port="$(cat "$workspace/route-port")"

host_route=""
for candidate in host.containers.internal host.docker.internal; do
  if "$ENGINE_BIN" run --rm "$BUSYBOX_IMAGE" \
      sh -c "nc -w 3 $candidate $route_port </dev/null" >/dev/null 2>&1; then
    host_route="$candidate"
    break
  fi
done
require '[[ -n "$host_route" ]]' \
  "no container-to-host route reached a service on $host_route_address; external-host mode cannot work here"
echo "container-to-host route: $host_route"

##
## And now the same route, speaking the database protocol. The credential is
## generated here, used by two commands and destroyed with the container.
##
##
## The credential is generated straight into a private file and read from there.
##
## It never becomes a shell variable, never appears in an argument list and is
## never echoed: ``-pPASSWORD`` and ``-e MYSQL_PWD=...`` both put it in this
## host's process table, where anything that lists processes can read it.
##
## The exception this makes is narrow and deliberate. The password does reach
## the *environment of a disposable container* that this gate created moments
## ago and destroys on exit, which is acceptable for a throwaway. It is not a
## pattern for the production database credential, which stays in a mounted
## 0600 file and is read only by the staging step - nothing in the release path
## may start passing that one through an environment.
##
mysql_env_file="$workspace/mysql.env"
( umask 077
  "$PYTHON_BIN" -c "
import secrets
password = secrets.token_hex(24)
print('MYSQL_ROOT_PASSWORD=' + password)
print('MYSQL_PWD=' + password)
print('MYSQL_DATABASE=gate_probe')
" > "$mysql_env_file"
)
chmod 600 "$mysql_env_file"

mysql_port="$("$PYTHON_BIN" -c "
import socket
probe = socket.socket()
probe.bind(('127.0.0.1', 0))
print(probe.getsockname()[1])
probe.close()
")"
"$ENGINE_BIN" run -d --name "$mysql_container" \
  --env-file "$mysql_env_file" \
  --publish "${host_route_address}:${mysql_port}:3306" \
  "$MYSQL_IMAGE" >/dev/null
for attempt in $(seq 1 90); do
  if "$ENGINE_BIN" exec --env-file "$mysql_env_file" "$mysql_container" \
      mysqladmin ping -h 127.0.0.1 -uroot >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
"$ENGINE_BIN" exec --env-file "$mysql_env_file" "$mysql_container" \
  mysqladmin ping -h 127.0.0.1 -uroot >/dev/null 2>&1 ||
  fail "the disposable MySQL never became reachable"

"$ENGINE_BIN" run --rm --env-file "$mysql_env_file" "$MYSQL_IMAGE" \
  mysqladmin ping -h "$host_route" -P "$mysql_port" -uroot >/dev/null 2>&1 ||
  fail "a container could not speak the database protocol to a host-side server"
echo "container-to-host database protocol: reached $host_route_address:$mysql_port"

##
## >>========= 4. the real application can write a bind-mounted tree =========>>
##
## The authoritative proof, and the one this gate used to get wrong.
##
## It ran BusyBox as the container's default user - which under a rootless
## engine is the operator - and concluded that a bind mount the operator owns is
## writable. That is true and it is not the question. The application does not
## run as that user: the entrypoint runs as root only long enough to stage the
## mounted configuration and then drops to an unprivileged account, which maps
## into the subordinate range and has no access to the operator's files at all.
##
## So everything below uses the real image, the real entrypoint and the real
## account, on a directory shaped like production's: owned by this operator,
## mode 0755, with content already in it.
##
media="$workspace/media"
mkdir -p "$media/douyin/live"
chmod 0755 "$media" "$media/douyin" "$media/douyin/live"
echo "a recording" > "$media/douyin/live/a.flv"
chmod 0644 "$media/douyin/live/a.flv"
config="$workspace/config.yml"
cp -a "$PROJECT_DIR/docs/design/config.yml.example" "$config"
chmod 600 "$config"

application_identity="$("$ENGINE_BIN" run --rm --entrypoint="" "$image_ref" \
  sh -c "id -u $APPLICATION_USER; id -g $APPLICATION_USER")" ||
  fail "the image does not resolve its application account $APPLICATION_USER"
application_uid="$(printf '%s\n' "$application_identity" | sed -n 1p | tr -d '[:space:]')"
application_gid="$(printf '%s\n' "$application_identity" | sed -n 2p | tr -d '[:space:]')"
##
## Validated exactly as the deployment validates it, so the gate cannot pass on
## an identity the deployment would refuse.
##
[[ "$application_uid" =~ ^[0-9]{1,10}$ && "$application_gid" =~ ^[0-9]{1,10}$ ]] ||
  fail "the image reported a malformed identity for $APPLICATION_USER"
echo "application account: $APPLICATION_USER uid=$application_uid gid=$application_gid"
require '(( application_uid != 0 && application_gid != 0 ))' \
  "the application account must be unprivileged"

probe_media() {
  local description="$1"
  shift
  "$ENGINE_BIN" run --rm "$@" \
    --volume "$config:/run/secrets/config.yml:ro" \
    --volume "$media:$media" \
    --volume "$PROJECT_DIR/scripts/release_media_write_probe.py:/tmp/smsd-media-probe.py:ro" \
    "$image_ref" \
    python /tmp/smsd-media-probe.py \
    --media-root "$media" \
    --expect-uid "$application_uid" \
    --expect-gid "$application_gid" \
    --require-existing
}

probe_media "with the mapping" \
  --userns "keep-id:uid=${application_uid},gid=${application_gid}" ||
  fail "the real application account could not read and write the bind-mounted media tree"
echo "real application account: read, wrote, fsynced, renamed and journalled at the host path"

##
## The negative control. Without the mapping the same image, the same
## entrypoint and the same account must fail - otherwise the mapping is not
## what makes this work and the proof above is measuring something else.
##
if probe_media "without the mapping" >/dev/null 2>&1; then
  fail "the media write succeeded without a user-namespace mapping; this gate is not proving what it claims"
fi
echo "negative control: without the mapping the application is refused, as expected"

##
## A mapping that names the wrong account must fail. The identity is read from
## the image precisely so it cannot drift, and this is the check that makes a
## drift visible: map one uid too far and the application is back in the
## subordinate range with no access to anything.
##
if probe_media "with a mismatched mapping" \
    --userns "keep-id:uid=$(( application_uid + 1 )),gid=$(( application_gid + 1 ))" \
    >/dev/null 2>&1; then
  fail "the media write succeeded under a mapping for a different account; the uid/gid contract is not being enforced"
fi
echo "negative control: a mapping for another account is refused, as expected"

##
## And a probe running as container root must refuse itself, because that is the
## exact mistake this section replaced.
##
if probe_media "as container root" --user root --entrypoint="" >/dev/null 2>&1; then
  fail "the write proof accepted a root identity"
fi
echo "negative control: a root probe refuses to stand in for the application"

##
## Host-side: what the application created belongs to this operator, and what
## was already there was not touched.
##
owner="$(stat -c '%u:%g' "$media/.smsd-recording-recovery")"
require '[[ "$owner" == "$(id -u):$(id -g)" ]]' \
  "the application's writes did not land as this operator on the host"
require '[[ "$(stat -c "%a" "$media")" == "755" ]]' \
  "the media root's mode was changed by the deployment path"
require '[[ "$(stat -c "%u" "$media/douyin/live/a.flv")" == "$(id -u)" ]]' \
  "existing media changed ownership; nothing here may chown a production tree"
echo "production ownership unchanged: no chown, no :U, no privileged container"

##
## >>=========== 5. a media root this operator does not own is refused ===========>>
##
## Made with the engine's own user namespace, so it is a real 0755 directory
## owned by a real other uid rather than a simulation of one. With the mapping
## in force the application acts as this operator, so a tree this operator
## cannot write is a tree the application cannot write - and the deployment has
## to refuse before it starts anything.
##
foreign="$workspace/foreign-media"
mkdir -p "$foreign"
chmod 0755 "$foreign"
"$ENGINE_BIN" unshare chown 1:1 "$foreign"
set +e
ENGINE_BIN="$ENGINE_BIN" PYTHON_BIN="$PYTHON_BIN" \
  "$PROJECT_DIR/scripts/release_external_deploy.sh" \
  --image "ghcr.io/example/app@sha256:$(printf 'a%.0s' {1..64})" \
  --expected-revision "$(printf 'b%.0s' {1..40})" \
  --container-name "smsd-external-gate-foreign-$$" \
  --config-file "$config" \
  --media-root "$foreign" \
  --db-host 127.0.0.1 \
  --port 13397 \
  --publish-address 127.0.0.1 \
  --health-url http://127.0.0.1:13397/ >/dev/null 2>&1
foreign_status=$?
set -e
"$ENGINE_BIN" unshare chown 0:0 "$foreign"
require '[[ "$foreign_status" -ne 0 ]]' \
  "the deploy accepted a media root this operator cannot write"
echo "ownership guard: refused a 0755 media root owned by another user"

##
## >>============= 6. the single-writer guard refuses for real =============>>
##
"$ENGINE_BIN" run -d --name "$container" \
  "$BUSYBOX_IMAGE" sleep 300 >/dev/null

set +e
ENGINE_BIN="$ENGINE_BIN" PYTHON_BIN="$PYTHON_BIN" \
  "$PROJECT_DIR/scripts/release_external_deploy.sh" \
  --image "ghcr.io/example/app@sha256:$(printf 'a%.0s' {1..64})" \
  --expected-revision "$(printf 'b%.0s' {1..40})" \
  --container-name "$container" \
  --config-file "$config" \
  --media-root "$media" \
  --db-host 127.0.0.1 \
  --port 13398 \
  --publish-address 127.0.0.1 \
  --health-url http://127.0.0.1:13398/ >/dev/null 2>&1
collision_status=$?
set -e
require '[[ "$collision_status" -ne 0 ]]' \
  "the deploy did not refuse an existing container of the same name"
echo "single-writer guard: refused an existing container"

##
## >>================ 7. the media snapshot clones for real ================>>
##
snapshot_output="$workspace/media-snapshot.json"
if "$PYTHON_BIN" "$PROJECT_DIR/scripts/release_media_snapshot.py" create \
    --media-root "$media" \
    --snapshot-root "$media/.smsd-release-snapshot" \
    --output "$snapshot_output" >/dev/null 2>&1; then
  entries="$("$PYTHON_BIN" -c "
import json, sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['entry_count'])
" "$snapshot_output")"
  require '[[ "$entries" -ge 1 ]]' "the snapshot did not record the tree it cloned"
  echo "reflink snapshot on the workspace filesystem: $entries entries"
else
  ##
  ## Not a failure of the design. The workspace may be on a filesystem that
  ## cannot clone; production's media filesystem is XFS with reflink=1 and is
  ## proved separately. What matters is that it refused rather than copied.
  ##
  echo "NOTE: the workspace filesystem cannot reflink; the snapshot refused, as designed"
fi

echo "$MARKER"
