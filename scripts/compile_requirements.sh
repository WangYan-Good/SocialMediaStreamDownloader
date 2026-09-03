#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_BIN="${DOCKER_BIN:-docker}"
PYTHON_BASE="python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea"
PIP_TOOLS_VERSION="7.6.1"
temporary_lock="$(mktemp "$PROJECT_DIR/.requirements.txt.XXXXXX")"
cleanup() {
  rm -f -- "$temporary_lock"
}
trap cleanup EXIT

"$DOCKER_BIN" run --rm \
  --env CUSTOM_COMPILE_COMMAND=./scripts/compile_requirements.sh \
  --volume "$PROJECT_DIR:/workspace:ro" \
  --workdir /workspace \
  "$PYTHON_BASE" \
  sh -c "python -m pip install --disable-pip-version-check --no-cache-dir pip-tools==$PIP_TOOLS_VERSION >/dev/null && python -m piptools compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file=- requirements.in" \
  > "$temporary_lock"
chmod 0644 "$temporary_lock"
mv -f -- "$temporary_lock" "$PROJECT_DIR/requirements.txt"
trap - EXIT
