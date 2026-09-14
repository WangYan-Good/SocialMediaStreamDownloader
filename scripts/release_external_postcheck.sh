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
# and really has the media tree under it.
#
set -euo pipefail

ENGINE_BIN="${ENGINE_BIN:-podman}"
CURL_BIN="${CURL_BIN:-curl}"

health_url=""
container_name=""
expected_image=""
expected_revision=""
expected_requirements_sha=""
media_root=""

usage() {
  echo "usage: release_external_postcheck.sh --health-url URL --container-name NAME --expected-image DIGEST --expected-revision SHA --expected-requirements-sha SHA256 --media-root PATH" >&2
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
    *) usage ;;
  esac
done

[[ -n "$health_url" && -n "$container_name" && -n "$expected_image" ]] || usage
[[ -n "$expected_revision" && -n "$expected_requirements_sha" ]] || usage
[[ -n "$media_root" ]] || usage

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
running_image_id="$("$ENGINE_BIN" inspect --format '{{.Image}}' "$container_name")"
expected_image_id="$("$ENGINE_BIN" image inspect --format '{{.Id}}' "$expected_image")"
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
## The database, reached from inside the container.
##
## This is the external topology's replacement for "is the MySQL container
## healthy". It proves more than a ping would: the schema the application will
## actually use is the schema this build expects.
##
migration_state="$(
  "$ENGINE_BIN" exec "$container_name" \
    python -m backend.src.database.migration_cli status 2>/dev/null || true
)"
[[ -n "$migration_state" ]] ||
  fail "the database could not be reached from the container"
[[ "$migration_state" == *"state=ready"* ]] ||
  fail "the database schema is not the one this build expects"

##
## And finally that it answers.
##
"$CURL_BIN" -fsS --max-time 10 "$health_url" >/dev/null ||
  fail "the application did not answer its health endpoint"

echo "external postcheck passed: revision=$expected_revision container=$container_name"
