#!/usr/bin/env python3
"""Describe what is in a database, in terms a migration must not change.

A rehearsal that restores a production-shaped database, runs nine migrations and
reports "21 tables present" has proved that the migrations complete. It has not
proved that the rows survived them, and that is the question worth asking: the
expensive failure is a migration that finishes cleanly against two years of real
data and takes some of it with it.

``information_schema.tables.table_rows`` cannot answer it. For InnoDB that
column is an estimate the optimiser keeps, derived from sampled index pages; it
drifts from the truth by large fractions on ordinary tables and is recomputed at
times nobody controls. Comparing it before and after would produce differences
where nothing changed and agreement where rows were lost. So every count here is
an exact ``COUNT(*)``.

Beyond counts, identity. A table whose row count is unchanged can still have had
its rows replaced, so each table's primary key is reduced to an order-independent
checksum - ``BIT_XOR`` over ``CRC32`` of the key - which changes if any key
changes and does not depend on the order rows come back in. Structure that the
data depends on is recorded too: foreign keys and unique indexes.

Nothing here reads a non-key column's contents. The output is written into
release records and pasted into tickets, and a media library's rows are
somebody's broadcasts.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys


INVARIANT_DOCUMENT_VERSION = 1

##
## Differences that mean data was lost, as opposed to differences that mean a
## migration did its job. Only the first kind fails.
##
FAILURE_MISSING_TABLE = "table absent after the upgrade"
FAILURE_ROWS_LOST = "row count decreased"
FAILURE_IDENTITY_CHANGED = "rows were replaced at an unchanged count"


def fail(message: str) -> None:
  print("database invariants refused: " + message, file=sys.stderr)
  raise SystemExit(1)


##
## One query, through the client, with the credential in an option file.
##
## ``--defaults-extra-file`` must be the first argument or the client reads it
## as an unknown option and falls back to whatever other configuration it finds.
##
def _query(mysql_bin: str, option_file: Path, database: str, sql: str) -> list:
  completed = subprocess.run(
    [
      mysql_bin,
      "--defaults-extra-file={}".format(option_file),
      "--batch",
      "--skip-column-names",
      "--raw",
      database,
      "--execute", sql,
    ],
    capture_output=True,
    text=True,
  )
  if completed.returncode != 0:
    ##
    ## Deliberately without the client's message, which quotes the statement and
    ## can quote values out of it.
    ##
    fail("a query against the database did not succeed")
  return [
    line.split("\t")
    for line in completed.stdout.splitlines()
    if line != ""
  ]


def _quote(identifier: str) -> str:
  return "`" + identifier.replace("`", "``") + "`"


##
## One unambiguous string per row's primary key.
##
## The fingerprint exists to answer a question the count cannot: whether a table
## whose row count is unchanged still holds the same rows. That only works if
## two different keys can never serialise to the same string, and the obvious
## spelling - ``CONCAT_WS(',', a, b)`` - fails exactly that test: the keys
## ``('x,y', 'z')`` and ``('x', 'y,z')`` both become ``x,y,z``.
##
## So each component is hexed first. ``HEX`` emits only ``0-9A-F``, so a ``:``
## between components cannot occur inside one and the boundaries are exact.
## Hexing also settles the other two awkward cases at the same time: binary and
## string keys serialise by their bytes rather than through a character set, so
## no collation decides whether two distinct keys look equal, and a trailing
## space survives.
##
## ``IFNULL`` is belt and braces - a primary key column cannot be NULL - but
## ``CONCAT_WS`` *skips* NULLs rather than propagating them, which would silently
## shorten the serialisation rather than fail. ``N`` is not a hex digit, so a
## NULL and an empty value stay distinguishable.
##
def key_expression(columns) -> str:
  parts = ", ".join(
    "IFNULL(HEX(CAST({} AS BINARY)), 'N')".format(_quote(column))
    for column in columns
  )
  return "CONCAT_WS(':', {})".format(parts)


##
## Which tables get a fingerprint at all.
##
## Every table with a primary key does, composite ones included - the whole
## reason the serialisation above is careful is so that a multi-column key can
## be fingerprinted rather than skipped. A table with no primary key has nothing
## to fingerprint and is carried by its exact count alone.
##
## Separated from the collection so the rule can be proven without a database.
##
def table_plan(key_columns):
  if not key_columns:
    return None
  return key_expression(key_columns)


def collect(arguments) -> int:
  option_file = Path(arguments.option_file)
  database = arguments.database

  tables = [
    row[0] for row in _query(
      arguments.mysql_bin, option_file, database,
      "SELECT table_name FROM information_schema.tables "
      "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE' "
      "ORDER BY table_name;",
    )
  ]
  if not tables:
    fail("the database holds no base tables")

  ##
  ## The single-column primary keys, which is what an identity checksum can be
  ## built from. A composite or absent key simply has no checksum; the count
  ## still carries.
  ##
  key_columns = {}
  for table, column, position in _query(
    arguments.mysql_bin, option_file, database,
    "SELECT table_name, column_name, ordinal_position "
    "FROM information_schema.key_column_usage "
    "WHERE table_schema = DATABASE() AND constraint_name = 'PRIMARY' "
    "ORDER BY table_name, ordinal_position;",
  ):
    key_columns.setdefault(table, []).append(column)

  foreign_keys = sorted(
    "{}.{} -> {}.{}".format(*row) for row in _query(
      arguments.mysql_bin, option_file, database,
      "SELECT table_name, column_name, referenced_table_name, "
      "referenced_column_name FROM information_schema.key_column_usage "
      "WHERE table_schema = DATABASE() AND referenced_table_name IS NOT NULL;",
    )
  )
  unique_indexes = sorted(
    "{}.{}".format(row[0], row[1]) for row in _query(
      arguments.mysql_bin, option_file, database,
      "SELECT DISTINCT table_name, index_name FROM information_schema.statistics "
      "WHERE table_schema = DATABASE() AND non_unique = 0;",
    )
  )

  observed = {}
  for table in tables:
    entry = {"rows": None, "identity": None}
    count = _query(
      arguments.mysql_bin, option_file, database,
      "SELECT COUNT(*) FROM {};".format(_quote(table)),
    )
    entry["rows"] = int(count[0][0])

    key = key_columns.get(table) or []
    expression = table_plan(key)
    if expression is not None:
      ##
      ## Order-independent on purpose: the rows come back in whatever order the
      ## storage engine chooses, and an order-sensitive digest would report a
      ## difference every time the optimiser changed its mind.
      ##
      ## The fingerprint never stands in for the count. It answers a different
      ## question - are these the same rows - and it answers it only where the
      ## count already agrees. A CRC32 is small enough to collide if it were
      ## asked to carry the whole claim on its own, and it is not.
      ##
      digest = _query(
        arguments.mysql_bin, option_file, database,
        "SELECT COALESCE(BIT_XOR(CRC32({})), 0), COUNT(DISTINCT {}) "
        "FROM {};".format(expression, expression, _quote(table)),
      )
      entry["identity"] = digest[0][0]
      entry["distinct_keys"] = int(digest[0][1])
      entry["key_columns"] = list(key)
      if len(key) == 1:
        ##
        ## Only meaningful for a single column, and recorded for the record
        ## rather than compared: a migration may legitimately renumber.
        ##
        bounds = _query(
          arguments.mysql_bin, option_file, database,
          "SELECT COALESCE(MIN({}), 0), COALESCE(MAX({}), 0) FROM {};".format(
            _quote(key[0]), _quote(key[0]), _quote(table)
          ),
        )
        entry["key_minimum"] = bounds[0][0]
        entry["key_maximum"] = bounds[0][1]
    observed[table] = entry

  document = {
    "format_version": INVARIANT_DOCUMENT_VERSION,
    "database": database,
    "tables": observed,
    "foreign_keys": foreign_keys,
    "unique_indexes": unique_indexes,
  }
  output = Path(arguments.output)
  output.write_text(
    json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
  )
  output.chmod(0o600)
  print("database invariants collected: tables={} rows={}".format(
    len(observed), sum(entry["rows"] for entry in observed.values())
  ))
  return 0


##
## Kept separate from the collection so it can be exercised without a database.
##
## The asymmetry is the point. A migration that adds rows, adds tables or adds
## constraints is doing its job; a migration that removes any of the first two,
## or that leaves a count alone while changing which rows produced it, has taken
## data with it. Only the second kind is a failure.
##
def compare_invariants(baseline: dict, observed: dict):
  failures = []
  notes = []

  before = baseline.get("tables", {})
  after = observed.get("tables", {})

  for table in sorted(before):
    if table not in after:
      failures.append("{}: {}".format(table, FAILURE_MISSING_TABLE))
      continue
    was, now = before[table], after[table]
    if now["rows"] < was["rows"]:
      failures.append("{}: {} ({} -> {})".format(
        table, FAILURE_ROWS_LOST, was["rows"], now["rows"]
      ))
      continue
    if now["rows"] > was["rows"]:
      notes.append("{}: rows added by the upgrade ({} -> {})".format(
        table, was["rows"], now["rows"]
      ))
      continue
    ##
    ## Equal counts. The only way this is still wrong is if the rows are not the
    ## same rows, which the key checksum is here to catch.
    ##
    if (
      was.get("identity") is not None
      and now.get("identity") is not None
      and was["identity"] != now["identity"]
    ):
      failures.append("{}: {}".format(table, FAILURE_IDENTITY_CHANGED))

  for table in sorted(set(after) - set(before)):
    notes.append("{}: table added by the upgrade".format(table))

  for relationship in baseline.get("foreign_keys", []):
    if relationship not in observed.get("foreign_keys", []):
      notes.append("foreign key no longer present: {}".format(relationship))
  for index in baseline.get("unique_indexes", []):
    if index not in observed.get("unique_indexes", []):
      notes.append("unique index no longer present: {}".format(index))

  return failures, notes


def compare(arguments) -> int:
  try:
    baseline = json.loads(Path(arguments.baseline).read_text(encoding="utf-8"))
    observed = json.loads(Path(arguments.observed).read_text(encoding="utf-8"))
  except (OSError, UnicodeDecodeError, json.JSONDecodeError):
    fail("an invariant document could not be read")

  failures, notes = compare_invariants(baseline, observed)
  for note in notes:
    print("note: " + note)
  if failures:
    for failure in failures:
      print("data invariant violated: " + failure, file=sys.stderr)
    return 1
  print("database invariants held: tables={}".format(
    len(baseline.get("tables", {}))
  ))
  return 0


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  subparsers = parser.add_subparsers(dest="command", required=True)

  collector = subparsers.add_parser("collect")
  collector.add_argument("--option-file", required=True)
  collector.add_argument("--database", required=True)
  collector.add_argument("--output", required=True)
  collector.add_argument("--mysql-bin", default="mysql")

  comparator = subparsers.add_parser("compare")
  comparator.add_argument("--baseline", required=True)
  comparator.add_argument("--observed", required=True)
  return parser


def main(argv=None) -> int:
  arguments = build_parser().parse_args(argv)
  if arguments.command == "collect":
    return collect(arguments)
  return compare(arguments)


if __name__ == "__main__":
  raise SystemExit(main())
