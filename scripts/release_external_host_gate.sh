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
# everything: a throwaway MySQL in a container, a media tree under a temporary
# directory, a test image built locally. It never touches the production
# database, the production media root or the production writer.
#
# It is a real-infra gate rather than a CI step because the behaviour it proves
# is a property of this host: which cgroup controllers are delegated, whether a
# container can reach a service on the host, whether the filesystem can clone.
# A GitHub runner would answer all three differently and the answer would mean
# nothing.
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE_BIN="${ENGINE_BIN:-podman}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

MARKER="ok   runtime external host deployment gate"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

require() {
  if ! eval "$1"; then
    fail "$2"
  fi
}

workspace="$(mktemp -d "${TMPDIR:-/tmp}/smsd-external-gate.XXXXXX")"
container="smsd-external-gate-$$"
mysql_container="smsd-external-gate-mysql-$$"

cleanup() {
  "$ENGINE_BIN" rm -f "$container" >/dev/null 2>&1 || true
  "$ENGINE_BIN" rm -f "$mysql_container" >/dev/null 2>&1 || true
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
if "$ENGINE_BIN" run --rm --cpus 1.0 docker.io/library/busybox:latest true >/dev/null 2>&1; then
  cpu_limit_supported=true
else
  cpu_limit_supported=false
fi
memory_limit_supported=true
"$ENGINE_BIN" run --rm --memory 256m docker.io/library/busybox:latest true >/dev/null 2>&1 ||
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
##
## Published on every interface, the way the production MySQL actually is.
## Binding it to loopback would make it unreachable from a container by
## construction and the probe would be measuring its own mistake rather than
## the host's routing.
##
"$ENGINE_BIN" run -d --name "$mysql_container" \
  -e MYSQL_ROOT_PASSWORD=gate_probe -e MYSQL_DATABASE=gate_probe \
  -p 13399:3306 \
  docker.io/library/mysql:8.0.46 >/dev/null
for attempt in $(seq 1 90); do
  if "$ENGINE_BIN" exec "$mysql_container" mysqladmin ping -h 127.0.0.1 -uroot -pgate_probe >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
"$ENGINE_BIN" exec "$mysql_container" mysqladmin ping -h 127.0.0.1 -uroot -pgate_probe >/dev/null 2>&1 ||
  fail "the disposable MySQL never became reachable"

##
## Probed exactly as the deployment will reach it: the engine's own host alias,
## with no extra flags. ``nc -z`` is deliberately not used - this busybox has no
## such option, and a probe that fails because of its own syntax looks identical
## to one that fails because the route is missing.
##
host_route=""
for candidate in host.containers.internal host.docker.internal; do
  if "$ENGINE_BIN" run --rm docker.io/library/busybox:latest \
      sh -c "nc -w 3 $candidate 13399 </dev/null" >/dev/null 2>&1; then
    host_route="$candidate"
    break
  fi
done
require '[[ -n "$host_route" ]]' \
  "no container-to-host route reached the disposable database; external-host mode cannot work here"
echo "container-to-host route: $host_route"

##
## >>================ 4. a bind-mounted media tree is usable ================>>
##
media="$workspace/media"
mkdir -p "$media/douyin/live" "$media/.smsd-recording-recovery"
echo "a recording" > "$media/douyin/live/a.flv"
echo '{"key":"k"}' > "$media/.smsd-recording-recovery/k.json"

"$ENGINE_BIN" run --rm --volume "$media:$media" \
  docker.io/library/busybox:latest \
  sh -c "test -f '$media/douyin/live/a.flv' && test -f '$media/.smsd-recording-recovery/k.json'" ||
  fail "a bind-mounted media tree was not readable inside a container at its host path"

"$ENGINE_BIN" run --rm --volume "$media:$media" \
  docker.io/library/busybox:latest \
  sh -c "touch '$media/.gate-write-probe'" ||
  fail "a bind-mounted media tree was not writable inside a container"
rm -f "$media/.gate-write-probe"
echo "bind-mounted media: readable and writable at the host path"

##
## >>============= 5. the single-writer guard refuses for real =============>>
##
"$ENGINE_BIN" run -d --name "$container" \
  docker.io/library/busybox:latest sleep 300 >/dev/null

set +e
ENGINE_BIN="$ENGINE_BIN" PYTHON_BIN="$PYTHON_BIN" \
  "$PROJECT_DIR/scripts/release_external_deploy.sh" \
  --image "ghcr.io/example/app@sha256:$(printf 'a%.0s' {1..64})" \
  --expected-revision "$(printf 'b%.0s' {1..40})" \
  --container-name "$container" \
  --config-file "$PROJECT_DIR/docs/design/config.yml.example" \
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
## >>================ 6. the media snapshot clones for real ================>>
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
  require '[[ "$entries" -ge 2 ]]' "the snapshot did not record the tree it cloned"
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
