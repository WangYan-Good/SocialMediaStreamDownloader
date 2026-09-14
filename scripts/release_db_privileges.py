#!/usr/bin/env python3
"""Report what the application's database account can do, and change nothing.

A read-only preflight. A deployment script that widened a grant would be
handing itself privileges; one that narrowed a grant mid-release would break the
writer it is about to start. Both are decisions an operator makes with the
release in front of them, so this only reports.

The direction of the comparison is the part worth stating. *Missing* privileges
are a release blocker: the application will fail at runtime, usually partway
through a migration. *Extra* privileges are not a blocker - a working deployment
with a too-powerful account still works - so they are a hardening finding.
Collapsing the two would either block a release for a condition that predates
it, or wave through an account that cannot run the application at all.
"""

import argparse
import re
import sys


##
## What the application genuinely needs on its own schema.
##
## CREATE/DROP/ALTER/INDEX/REFERENCES are here because migrations run as this
## account: the schema is managed by Alembic at startup, not applied by hand.
##
REQUIRED_PRIVILEGES = (
  "SELECT",
  "INSERT",
  "UPDATE",
  "DELETE",
  "CREATE",
  "DROP",
  "ALTER",
  "INDEX",
  "REFERENCES",
)

##
## MySQL's own umbrella. Reported rather than expanded: what it covers varies by
## server version, and the finding is "this account has everything", which does
## not need enumerating to be actionable.
##
ALL_PRIVILEGES = "ALL PRIVILEGES"

_GRANT = re.compile(
  r"^GRANT\s+(?P<privileges>.+?)\s+ON\s+(?P<scope>\S+)\s+TO\s",
  re.IGNORECASE | re.DOTALL,
)


def _normalise_scope(scope: str) -> str:
  return scope.replace("`", "").strip()


def _split_privileges(text: str) -> list[str]:
  ##
  ## Column-level grants read as ``SELECT (a, b)``; the parenthesised part is
  ## not a separator, so commas inside it must not split the list.
  ##
  items = []
  depth = 0
  current = []
  for character in text:
    if character == "(":
      depth += 1
    elif character == ")":
      depth -= 1
    if character == "," and depth == 0:
      items.append("".join(current).strip())
      current = []
      continue
    current.append(character)
  if current:
    items.append("".join(current).strip())
  return [item.upper() for item in items if item]


def classify_grants(grants, database: str) -> dict:
  """Compare the account's grants against what the application needs."""
  held = set()
  excessive = []
  for line in grants:
    match = _GRANT.match(line.strip())
    if match is None:
      continue
    scope = _normalise_scope(match.group("scope"))
    privileges = _split_privileges(match.group("privileges"))

    global_scope = scope in ("*.*",)
    own_scope = scope in (f"{database}.*", f"{database}.`*`")
    if global_scope:
      ##
      ## Reaches every schema on the server, including ones this application
      ## has no business in. Always a finding, whatever it grants.
      ##
      excessive.append("privileges granted on *.* rather than on the database")
    if not (global_scope or own_scope):
      continue

    if any(item.startswith(ALL_PRIVILEGES) for item in privileges):
      held.update(REQUIRED_PRIVILEGES)
      excessive.append("the account holds ALL PRIVILEGES on its scope")
    else:
      for item in privileges:
        held.add(item.split("(")[0].strip())

    if "WITH GRANT OPTION" in line.upper():
      ##
      ## Named literally, because an operator searching for "GRANT OPTION" in a
      ## report should find it rather than a paraphrase of it.
      ##
      excessive.append(
        "the account holds WITH GRANT OPTION and can grant its privileges to others"
      )

  missing = [name for name in REQUIRED_PRIVILEGES if name not in held]
  return {
    "database": database,
    "missing": missing,
    ##
    ## Ordered and de-duplicated so the report reads the same way twice.
    ##
    "excessive": sorted(set(excessive)),
    "verdict": "insufficient" if missing else "sufficient",
  }


def render_report(report: dict) -> str:
  """Render the finding, and nothing that identifies the account.

  Never the user, never the host it connects from, never anything after
  ``IDENTIFIED BY``. This runs on a release path whose output is pasted into
  tickets, and an account name plus a source address is most of a credential.
  """
  lines = [
    "database privilege preflight: verdict={} database={}".format(
      report["verdict"], report["database"]
    )
  ]
  if report["missing"]:
    lines.append(
      "RELEASE BLOCKER: the account lacks {}".format(
        ", ".join(report["missing"])
      )
    )
  for finding in report["excessive"]:
    lines.append("SECURITY HARDENING REQUIRED: {}".format(finding))
  if not report["missing"] and not report["excessive"]:
    lines.append("the account holds exactly what the application needs")
  return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  parser.add_argument("--database", required=True)
  parser.add_argument(
    "--grants-file",
    required=True,
    help="output of SHOW GRANTS, one statement per line",
  )
  return parser


def main(argv=None) -> int:
  arguments = build_parser().parse_args(argv)
  with open(arguments.grants_file, encoding="utf-8") as stream:
    grants = [line for line in stream if line.strip()]
  report = classify_grants(grants, database=arguments.database)
  print(render_report(report))
  ##
  ## Only a missing privilege fails. A hardening finding is reported and does
  ## not block: it describes a condition that predates this release.
  ##
  return 1 if report["missing"] else 0


if __name__ == "__main__":
  raise SystemExit(main())
