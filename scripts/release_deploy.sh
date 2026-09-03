#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
RUN_DOCKER_SCRIPT="${RUN_DOCKER_SCRIPT:-$PROJECT_DIR/run-docker.sh}"
POSTCHECK_SCRIPT="${POSTCHECK_SCRIPT:-$PROJECT_DIR/scripts/release_postcheck.sh}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-$PROJECT_DIR/requirements.txt}"
MYSQL_IMAGE_REF="mysql:8.0.46@sha256:7dcddc01f13bab2f15cde676d44d01f61fc9f99fe7785e86196dfc07d358ae2b"

image_ref=""
expected_revision=""
project_name=""
health_url=""

usage() {
  echo "usage: release_deploy.sh --image ghcr.io/OWNER/REPOSITORY@sha256:DIGEST --expected-revision COMMIT_SHA --project-name COMPOSE_PROJECT --health-url URL" >&2
  exit 2
}

fail() {
  echo "release deploy failed: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      [[ $# -ge 2 ]] || usage
      image_ref="$2"
      shift 2
      ;;
    --expected-revision)
      [[ $# -ge 2 ]] || usage
      expected_revision="$2"
      shift 2
      ;;
    --project-name)
      [[ $# -ge 2 ]] || usage
      project_name="$2"
      shift 2
      ;;
    --health-url)
      [[ $# -ge 2 ]] || usage
      health_url="$2"
      shift 2
      ;;
    *) usage ;;
  esac
done

[[ "$image_ref" =~ ^ghcr\.io/[a-z0-9][a-z0-9._/-]*@sha256:[0-9a-f]{64}$ ]] ||
  fail "image must be a canonical lowercase GHCR digest"
[[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] ||
  fail "expected revision must be a 40-character SHA"
[[ -n "$project_name" && -n "$health_url" ]] || usage
[[ -f "$REQUIREMENTS_FILE" ]] || fail "requirements lock is absent"

requirements_sha="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"

"$DOCKER_BIN" pull "$image_ref"
expected_image_id="$("$DOCKER_BIN" image inspect --format '{{.Id}}' "$image_ref")"
revision_label="$("$DOCKER_BIN" image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image_ref")"
requirements_label="$("$DOCKER_BIN" image inspect --format '{{index .Config.Labels "io.smsd.requirements.sha256"}}' "$image_ref")"

[[ "$expected_image_id" =~ ^sha256:[0-9a-f]{64}$ ]] ||
  fail "pulled image ID is malformed"
[[ "$revision_label" == "$expected_revision" ]] ||
  fail "revision label mismatch"
[[ "$requirements_label" == "$requirements_sha" ]] ||
  fail "requirements label mismatch"

export SMSD_IMAGE="$image_ref"
"$RUN_DOCKER_SCRIPT" -p "$project_name" up -d --no-build
app_id="$("$RUN_DOCKER_SCRIPT" -p "$project_name" ps -q app)"
[[ -n "$app_id" ]] || fail "application container is absent"
running_image_id="$("$DOCKER_BIN" inspect --format '{{.Image}}' "$app_id")"
[[ "$running_image_id" == "$expected_image_id" ]] ||
  fail "running application image ID mismatch"

"$POSTCHECK_SCRIPT" \
  --health-url "$health_url" \
  --project-name "$project_name" \
  --expected-image "$image_ref" \
  --expected-revision "$expected_revision" \
  --expected-requirements-sha "$requirements_sha" \
  --expected-mysql-image "$MYSQL_IMAGE_REF"

echo "release deployment completed: revision=$expected_revision image=$image_ref"
