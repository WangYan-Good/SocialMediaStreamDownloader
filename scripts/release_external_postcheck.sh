#!/usr/bin/env bash
#
# Prove the application that started is the one that was reviewed.
#
# The Compose postcheck asks for an app container and a MySQL container and
# pins the MySQL image, because there the database is part of the release. Here
# it is not: the MySQL belongs to the host, it predates this release and will
# outlive it, so requiring a container for it would fail a correct deployment.
#
# What replaces that is a stricter account of the one thing this release does
# place - the application - plus evidence that it really reached the database
# and really can write the media tree under it.
#
# "Can write" rather than "is mounted", because those are different questions
# and only one of them matters. The mount is established by the engine and the
# write is performed by an unprivileged account the entrypoint drops to, whose
# host identity under rootless Podman is not the one the mount was checked with.
# So the write is proved by that account, doing what the application does.
#
set -euo pipefail

ENGINE_BIN="${ENGINE_BIN:-podman}"
CURL_BIN="${CURL_BIN:-curl}"

##
## Where the probe lives inside the image. The application image carries the
## repository, so this is the same file the deterministic suites exercise.
##
MEDIA_WRITE_PROBE="${MEDIA_WRITE_PROBE:-/app/scripts/release_media_write_probe.py}"

health_url=""
container_name=""
expected_image=""
expected_revision=""
expected_requirements_sha=""
media_root=""
application_user=""
application_uid=""
application_gid=""

usage() {
  cat >&2 <<'USAGE'
usage: release_external_postcheck.sh
  --health-url URL
  --container-name NAME
  --expected-image DIGEST
  --expected-revision SHA
  --expected-requirements-sha SHA256
  --media-root PATH
  --application-user NAME
  --application-uid UID
  --application-gid GID
USAGE
  exit 2
}

fail() {
  echo "external postcheck failed: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --health-url) [[ $# -ge 2 ]] || usage; health_url="$2"; shift 2 ;;
    --container-name) [[ $# -ge 2 ]] || usage; container_name="$2"; shift 2 ;;
    --expected-image) [[ $# -ge 2 ]] || usage; expected_image="$2"; shift 2 ;;
    --expected-revision) [[ $# -ge 2 ]] || usage; expected_revision="$2"; shift 2 ;;
    --expected-requirements-sha) [[ $# -ge 2 ]] || usage; expected_requirements_sha="$2"; shift 2 ;;
    --media-root) [[ $# -ge 2 ]] || usage; media_root="$2"; shift 2 ;;
    --application-user) [[ $# -ge 2 ]] || usage; application_user="$2"; shift 2 ;;
    --application-uid) [[ $# -ge 2 ]] || usage; application_uid="$2"; shift 2 ;;
    --application-gid) [[ $# -ge 2 ]] || usage; application_gid="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$health_url" && -n "$container_name" && -n "$expected_image" ]] || usage
[[ -n "$expected_revision" && -n "$expected_requirements_sha" ]] || usage
[[ -n "$media_root" ]] || usage
[[ -n "$application_user" && -n "$application_uid" && -n "$application_gid" ]] || usage
[[ "$application_uid" =~ ^[0-9]{1,10}$ && "$application_gid" =~ ^[0-9]{1,10}$ ]] ||
  fail "the application identity must be numeric"

##
## Running at all.
##
running="$("$ENGINE_BIN" inspect --format '{{.State.Running}}' "$container_name" 2>/dev/null || true)"
[[ "$running" == "true" ]] || fail "the application container is not running"

##
## The exact artifact. The digest was the release authority at deploy time and
## it stays the release authority here: what is running must be the image that
## digest resolved to, not merely something built from the same source.
##
##
## Normalised on both sides for the same reason the deployment does it: Docker
## spells an image ID with a ``sha256:`` prefix and Podman without one, and a
## comparison between the two spellings of the same image would fail on the
## engine production actually runs.
##
normalise_image_id() {
  printf '%s' "${1#sha256:}"
}

running_image_id="$(normalise_image_id "$("$ENGINE_BIN" inspect --format '{{.Image}}' "$container_name")")"
expected_image_id="$(normalise_image_id "$("$ENGINE_BIN" image inspect --format '{{.Id}}' "$expected_image")")"
[[ "$running_image_id" == "$expected_image_id" ]] ||
  fail "the running image is not the promoted image"

revision_label="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$expected_image")"
[[ "$revision_label" == "$expected_revision" ]] ||
  fail "revision label mismatch"

requirements_label="$("$ENGINE_BIN" image inspect --format '{{index .Config.Labels "io.smsd.requirements.sha256"}}' "$expected_image")"
[[ "$requirements_label" == "$expected_requirements_sha" ]] ||
  fail "requirements label mismatch"

##
## The media tree, by destination rather than by intention.
##
## The database stores paths, so a container serving a different directory than
## the one the rows describe would look healthy and answer for nothing. Asking
## the engine where the mount actually lands is the only form of this check
## worth making.
##
mount_destination="$(
  "$ENGINE_BIN" inspect \
    --format '{{range .Mounts}}{{if eq .Destination "'"$media_root"'"}}{{.Destination}}{{end}}{{end}}' \
    "$container_name" 2>/dev/null || true
)"
[[ "$mount_destination" == "$media_root" ]] ||
  fail "the media root is not mounted at its host path"

##
## >>=========== and that the application itself can write to it ===========>>
##
## Run as the account the entrypoint drops to, not as the container's default
## user. Those are different host identities under a rootless engine, and a
## deployment whose entrypoint can write the media while its application cannot
## starts cleanly, answers its health endpoint and fails on the first recording.
##
## The probe creates only hidden paths of its own and removes them.
##
##
## Whether the probe is *there* is asked first, and separately.
##
## An image built before this contract has no probe in it, and running it
## produces an exec failure that looks exactly like a denied write. Reporting
## that as "the application cannot write the media tree" sends an operator to
## look at uids, mappings and mount options for a problem that is none of those:
## the check could not run at all. Those are different sentences because they
## lead to different next steps.
##
if ! "$ENGINE_BIN" exec "$container_name" test -f "$MEDIA_WRITE_PROBE" >/dev/null 2>&1; then
  fail "this image predates the media-write contract: $MEDIA_WRITE_PROBE is absent, so the application's access to the media tree could not be proven - this is a missing capability, not a permission failure"
fi

if ! probe_output="$(
  "$ENGINE_BIN" exec --user "$application_user" "$container_name" \
    python "$MEDIA_WRITE_PROBE" \
    --media-root "$media_root" \
    --expect-uid "$application_uid" \
    --expect-gid "$application_gid" 2>&1
)"; then
  fail "the application account $application_user cannot write the media tree"
fi
[[ "$probe_output" == *"media write probe passed"* ]] ||
  fail "the media write proof did not report success"

##
## >>================= the database, from inside the container =================>>
##
## This is the external topology's replacement for "is the MySQL container
## healthy", and it keeps the release contract's two separate questions
## separate: ``status`` is about revision state and ``check`` is about whether
## the schema the application will issue queries against matches the models.
## ``status`` now subsumes a compatibility classification, which is exactly why
## the explicit ``check`` stays - a contract that quietly became implicit is a
## contract that can quietly stop being enforced.
##
migration_status="$(
  "$ENGINE_BIN" exec "$container_name" \
    python -m backend.src.database.migration_cli status 2>/dev/null || true
)"
[[ -n "$migration_status" ]] ||
  fail "the database could not be reached from the container"

##
## Parsed rather than matched. ``state=ready`` alone would also be satisfied by
## a line that named no revision, and the release contract is about a specific
## one: a database at a real revision, at the single head this build has.
##
migration_state="$(printf '%s\n' "$migration_status" | sed -n 's/.*state=\([^ ]*\).*/\1/p' | head -1)"
migration_current="$(printf '%s\n' "$migration_status" | sed -n 's/.*current=\([^ ]*\).*/\1/p' | head -1)"
migration_heads="$(printf '%s\n' "$migration_status" | sed -n 's/.*heads=\([^ ]*\).*/\1/p' | head -1)"

[[ "$migration_state" == "ready" ]] ||
  fail "the database schema is not the one this build expects"
[[ -n "$migration_current" && "$migration_current" != "none" ]] ||
  fail "the database reports no applied revision"
[[ "$migration_heads" != *","* ]] ||
  fail "the build has more than one migration head"
[[ "$migration_current" == "$migration_heads" ]] ||
  fail "the database is not at this build's migration head"

if ! migration_check="$(
  "$ENGINE_BIN" exec "$container_name" \
    python -m backend.src.database.migration_cli check 2>&1
)"; then
  fail "the managed schema is not compatible with this build"
fi
[[ "$migration_check" == *"managed schema is compatible"* ]] ||
  fail "the schema compatibility check did not report a compatible schema"

##
## And finally that it answers.
##
"$CURL_BIN" -fsS --max-time 10 "$health_url" >/dev/null ||
  fail "the application did not answer its health endpoint"

echo "external postcheck passed: revision=$expected_revision container=$container_name"
