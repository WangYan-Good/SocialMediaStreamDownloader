#!/usr/bin/env bash
#
# What has to be true before anybody stops production.
#
# The cutover is: stop the old writer, back up, migrate, start the new one.
# Every step after the first assumes the operator can put the old writer back if
# the new one does not work - and on this host that assumption is false today.
# The production application is a bare-metal process with no service manager:
# reparented to init, started by hand from a conda interpreter, restarted by
# hand when it dies. Nothing records how to start it again.
#
# A rollback plan that ends in "and then somehow restart the old application" is
# not a rollback plan. So this refuses until an operator has written down what
# the old writer is and asserted they can stop and start it. That assertion is a
# decision, not a fact this can discover: the process being visible in a process
# table says nothing about whether anybody knows how to bring it back.
#
# It deliberately creates no service manager and changes nothing on the host.
# Installing a unit would be modifying the host, and the host is not this
# phase's to modify - that is a separate, explicitly authorised piece of work.
#
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

writer_authority=""

usage() {
  echo "usage: release_external_preflight.sh --writer-authority PATH" >&2
  exit 2
}

fail() {
  echo "external preflight refused: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --writer-authority) [[ $# -ge 2 ]] || usage; writer_authority="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$writer_authority" ]] || usage
[[ -f "$writer_authority" ]] ||
  fail "no writer authority record; the old writer cannot be proven restartable"

##
## Every field is something an operator needs in order to put the old writer
## back. A record missing one describes a rollback nobody can perform.
##
## Nothing here is a secret, and nothing here is echoed: the record names a
## command, a directory and an interpreter, and the diagnostic says only which
## field was absent.
##
"$PYTHON_BIN" - "$writer_authority" <<'PYEOF' || fail "the writer authority record is incomplete or unconfirmed"
import json
import sys

REQUIRED = (
    "revision",
    "start_command",
    "working_directory",
    "interpreter",
    "stop_procedure",
    "start_procedure",
)

try:
    document = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, UnicodeDecodeError, ValueError):
    print("the writer authority record could not be read", file=sys.stderr)
    raise SystemExit(1)

if not isinstance(document, dict):
    print("the writer authority record is not an object", file=sys.stderr)
    raise SystemExit(1)

for field in REQUIRED:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        print("the writer authority record is missing " + field, file=sys.stderr)
        raise SystemExit(1)

##
## Exactly ``True``. A string "yes" or a 1 is somebody filling in a form, not an
## operator asserting a capability - and Python would treat both as truthy.
##
if document.get("operator_confirmed_stop_start_authority") is not True:
    print(
        "the operator has not confirmed stop/start authority over the old writer",
        file=sys.stderr,
    )
    raise SystemExit(1)
PYEOF

echo "external preflight passed: the old writer is documented and restartable"
