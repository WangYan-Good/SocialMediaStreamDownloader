##
## What a migration is allowed to change, and what it is not.
##
## The rehearsal used to prove that tables existed after the upgrade and call
## that data preservation. What it printed was
## ``information_schema.tables.table_rows``, which for InnoDB is an estimate the
## optimiser keeps from sampled index pages - it drifts by large fractions on
## ordinary tables and is recomputed at times nobody controls. Comparing it
## across an upgrade produces differences where nothing changed and agreement
## where rows were lost, which is the worst of both.
##
## The comparison below is deliberately asymmetric. A migration that adds rows,
## adds tables or adds constraints is doing its job. A migration that removes a
## table, removes rows, or leaves a count alone while changing which rows
## produced it has taken data with it. Only the second kind is a failure, and
## the difference is the whole point of collecting a key checksum alongside the
## count.
##
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HELPER = PROJECT_ROOT / "scripts" / "release_db_invariants.py"
REHEARSAL = PROJECT_ROOT / "scripts" / "release_migration_rehearsal.sh"


def helper_module():
  specification = importlib.util.spec_from_file_location(
    "release_db_invariants", HELPER
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


def snapshot(**tables) -> dict:
  return {
    "format_version": 1,
    "database": "smsd",
    "tables": {
      name: {"rows": rows, "identity": identity}
      for name, (rows, identity) in tables.items()
    },
    "foreign_keys": [],
    "unique_indexes": [],
  }


class InvariantComparisonTest(unittest.TestCase):
  def setUp(self):
    self.module = helper_module()

  def compare(self, baseline, observed):
    return self.module.compare_invariants(baseline, observed)

  def test_an_unchanged_database_holds(self):
    before = snapshot(live=(1200, "7f3a"), task=(40, "0011"))

    failures, notes = self.compare(before, before)

    self.assertEqual([], failures)
    self.assertEqual([], notes)

  ##
  ## The failure this exists to catch.
  ##
  def test_a_table_that_lost_rows_is_a_failure(self):
    before = snapshot(live=(1200, "7f3a"))
    after = snapshot(live=(1199, "7f3a"))

    failures, notes = self.compare(before, after)

    self.assertEqual(1, len(failures))
    self.assertIn("row count decreased", failures[0])

  def test_a_table_that_disappeared_is_a_failure(self):
    before = snapshot(live=(1200, "7f3a"), task=(40, "0011"))
    after = snapshot(live=(1200, "7f3a"))

    failures, notes = self.compare(before, after)

    self.assertEqual(1, len(failures))
    self.assertIn("absent after the upgrade", failures[0])

  ##
  ## The subtle one. A count is not an identity: a migration that rewrote every
  ## row would leave the count exactly where it was.
  ##
  def test_rows_replaced_at_an_unchanged_count_is_a_failure(self):
    before = snapshot(live=(1200, "7f3a"))
    after = snapshot(live=(1200, "b19c"))

    failures, notes = self.compare(before, after)

    self.assertEqual(1, len(failures))
    self.assertIn("replaced", failures[0])

  ##
  ## And the things a migration is supposed to do.
  ##
  def test_rows_and_tables_added_by_the_upgrade_are_reported_not_failed(self):
    before = snapshot(live=(1200, "7f3a"))
    after = snapshot(live=(1400, "b19c"), recovery=(3, "aa"))

    failures, notes = self.compare(before, after)

    self.assertEqual([], failures)
    self.assertEqual(2, len(notes))

  def test_a_table_without_a_single_column_key_is_still_counted(self):
    before = {"tables": {"joins": {"rows": 10, "identity": None}}}
    after = {"tables": {"joins": {"rows": 9, "identity": None}}}

    failures, notes = self.compare(before, after)

    self.assertEqual(1, len(failures))

  def test_a_dropped_constraint_is_reported(self):
    before = dict(snapshot(live=(1, "a")), unique_indexes=["live.by_url"])
    after = dict(snapshot(live=(1, "a")), unique_indexes=[])

    failures, notes = self.compare(before, after)

    self.assertEqual([], failures)
    self.assertIn("unique index no longer present", notes[0])


##
## >>============ a fingerprint that two different keys cannot share ============>>
##
## The fingerprint answers the question the count cannot: whether a table whose
## row count is unchanged still holds the same rows. That only works if two
## different keys can never serialise to the same string - and the obvious
## spelling fails exactly that test.
##
class KeySerialisationTest(unittest.TestCase):
  def setUp(self):
    self.module = helper_module()

  def test_a_single_column_key_serialises_through_its_bytes(self):
    expression = self.module.key_expression(["id"])

    self.assertIn("HEX(CAST(`id` AS BINARY))", expression)

  ##
  ## The collision this design exists to avoid. With a plain separator,
  ## ``('x,y', 'z')`` and ``('x', 'y,z')`` both become ``x,y,z``.
  ##
  def test_a_composite_key_cannot_be_confused_with_another_one(self):
    expression = self.module.key_expression(["left", "right"])

    self.assertIn("HEX(CAST(`left` AS BINARY))", expression)
    self.assertIn("HEX(CAST(`right` AS BINARY))", expression)
    self.assertIn("CONCAT_WS(':'", expression)
    ##
    ## Hex emits only 0-9A-F, so the separator cannot occur inside a component
    ## and the boundaries are exact. That is the whole argument, and it stops
    ## holding the moment a component stops being hexed.
    ##
    self.assertNotIn("CAST(`left` AS CHAR)", expression)

  ##
  ## Composite keys get a fingerprint rather than being skipped. Skipping them
  ## would leave exactly the tables whose rows are hardest to reason about
  ## carried by a row count alone.
  ##
  def test_every_key_gets_a_fingerprint_including_composite_ones(self):
    self.assertIsNotNone(self.module.table_plan(["id"]))
    self.assertIsNotNone(self.module.table_plan(["left", "right"]))
    self.assertIsNotNone(self.module.table_plan(["a", "b", "c"]))

  def test_a_table_without_a_primary_key_has_nothing_to_fingerprint(self):
    self.assertIsNone(self.module.table_plan([]))

  def test_a_null_component_stays_distinguishable_from_an_empty_one(self):
    ##
    ## A primary key column cannot be NULL, but ``CONCAT_WS`` skips NULLs rather
    ## than propagating them - which would silently shorten the serialisation
    ## instead of failing. ``N`` is not a hex digit.
    ##
    expression = self.module.key_expression(["id"])

    self.assertIn("IFNULL(", expression)
    self.assertIn("'N'", expression)

  def test_an_identifier_containing_a_backtick_cannot_escape_the_expression(self):
    expression = self.module.key_expression(["we`ird"])

    self.assertIn("`we``ird`", expression)

  ##
  ## And the fingerprint never carries the claim on its own. A CRC32 is small
  ## enough to collide; it is only ever consulted where the exact count already
  ## agrees, which is what makes that acceptable.
  ##
  def test_the_fingerprint_is_only_consulted_at_an_unchanged_count(self):
    module = self.module
    before = {"tables": {"t": {"rows": 10, "identity": "aaaa"}}}
    after = {"tables": {"t": {"rows": 11, "identity": "bbbb"}}}

    failures, notes = module.compare_invariants(before, after)

    self.assertEqual([], failures)
    self.assertIn("rows added", notes[0])

  def test_the_exact_count_is_what_decides_loss(self):
    module = self.module
    ##
    ## Identical fingerprints do not excuse a missing row.
    ##
    before = {"tables": {"t": {"rows": 10, "identity": "aaaa"}}}
    after = {"tables": {"t": {"rows": 9, "identity": "aaaa"}}}

    failures, notes = module.compare_invariants(before, after)

    self.assertEqual(1, len(failures))
    self.assertIn("row count decreased", failures[0])


class InvariantCommandTest(unittest.TestCase):
  ##
  ## The comparison is also reachable as a command, because the rehearsal is a
  ## shell script and its exit status is how it decides whether to continue.
  ##
  def run_compare(self, baseline: dict, observed: dict):
    directory = Path(tempfile.mkdtemp())
    self.addCleanup(__import__("shutil").rmtree, directory, True)
    first = directory / "baseline.json"
    second = directory / "observed.json"
    first.write_text(json.dumps(baseline), encoding="utf-8")
    second.write_text(json.dumps(observed), encoding="utf-8")
    return subprocess.run(
      [
        sys.executable, str(HELPER), "compare",
        "--baseline", str(first), "--observed", str(second),
      ],
      capture_output=True,
      text=True,
    )

  def test_a_preserved_database_exits_zero(self):
    before = snapshot(live=(5, "aa"))

    completed = self.run_compare(before, before)

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("invariants held", completed.stdout)

  def test_a_database_that_lost_rows_exits_non_zero(self):
    completed = self.run_compare(snapshot(live=(5, "aa")), snapshot(live=(4, "aa")))

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("data invariant violated", completed.stderr)

  ##
  ## Row contents are never read and never printed. The output of this goes into
  ## release records and tickets, and a media library's rows are somebody's
  ## broadcasts.
  ##
  def test_it_reads_no_row_contents(self):
    source = HELPER.read_text(encoding="utf-8")
    self.assertNotIn("SELECT *", source)
    self.assertIn("COUNT(*)", source)

  ##
  ## The estimate must not come back through this file either.
  ##
  ## The rehearsal is pinned against ``table_rows`` separately, but the query
  ## that produces the number lives here - and asserting on the whole file was
  ## satisfied by the prose explaining why the estimate is wrong. Checked
  ## against the statements, so the explanation can stay.
  ##
  def test_the_counts_are_exact_rather_than_the_optimisers_estimate(self):
    source = HELPER.read_text(encoding="utf-8")
    ##
    ## Checked against the queries, so the module docstring can go on explaining
    ## why the estimate is the wrong number to use.
    ##
    queries = [line for line in source.splitlines() if "SELECT" in line]
    self.assertTrue(queries)
    for line in queries:
      self.assertNotIn("table_rows", line, line.strip())
    self.assertIn('"SELECT COUNT(*) FROM {};"', source)


##
## >>=============== what the database is actually asked ===============>>
##
## A stub client that answers canned rows and records every statement. The point
## is the record: information_schema.tables.table_rows and an exact COUNT(*)
## read identically in a diff and differ by large fractions in production, so
## the only assertion worth making is about the SQL that was issued.
##
class InvariantCollectionTest(unittest.TestCase):
  def setUp(self):
    self.module = helper_module()
    self.root = Path(tempfile.mkdtemp())
    self.addCleanup(__import__("shutil").rmtree, self.root, True)
    self.log = self.root / "sql.log"
    self.client = self.root / "mysql"
    self.client.write_text(
      "#!/usr/bin/env bash\n"
      "set -euo pipefail\n"
      'sql="${!#}"\n'
      'printf \'%s\\n\' "$sql" >> "$SQL_LOG"\n'
      'case "$sql" in\n'
      "  *\"table_type = 'BASE TABLE'\"*) printf 'live\\ntask\\n' ;;\n"
      "  *\"constraint_name = 'PRIMARY'\"*)\n"
      "    printf 'live\\tid\\t1\\ntask\\ta\\t1\\ntask\\tb\\t2\\n' ;;\n"
      '  *"referenced_table_name IS NOT NULL"*) : ;;\n'
      "  *\"non_unique = 0\"*) printf 'live\\tPRIMARY\\n' ;;\n"
      '  *"COUNT(*) FROM "*) printf \'5\\n\' ;;\n'
      '  *"BIT_XOR"*) printf \'4242\\t5\\n\' ;;\n'
      '  *"MIN("*) printf \'1\\t99\\n\' ;;\n'
      '  *) : ;;\n'
      'esac\n',
      encoding="utf-8",
    )
    self.client.chmod(0o700)
    self.option_file = self.root / "my.cnf"
    self.option_file.write_text("[client]\n", encoding="utf-8")
    self.option_file.chmod(0o600)

  def collect(self):
    output = self.root / "invariants.json"
    completed = subprocess.run(
      [
        sys.executable, str(HELPER), "collect",
        "--option-file", str(self.option_file),
        "--database", "smsd",
        "--mysql-bin", str(self.client),
        "--output", str(output),
      ],
      capture_output=True,
      text=True,
      env={**__import__("os").environ, "SQL_LOG": str(self.log)},
    )
    statements = (
      self.log.read_text(encoding="utf-8").splitlines()
      if self.log.exists() else []
    )
    document = (
      json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
    )
    return completed, statements, document

  ##
  ## The defect this whole file exists to prevent.
  ##
  def test_the_row_count_is_an_exact_count_and_never_the_estimate(self):
    completed, statements, document = self.collect()

    self.assertEqual(0, completed.returncode, completed.stderr)
    counts = [line for line in statements if line.startswith("SELECT COUNT(*)")]
    self.assertEqual(2, len(counts), statements)
    for line in statements:
      self.assertNotIn("table_rows", line, line)
    self.assertEqual(5, document["tables"]["live"]["rows"])

  ##
  ## Composite keys are fingerprinted rather than skipped, and the statement
  ## that does it hexes each component so two different keys cannot serialise
  ## to one string.
  ##
  def test_a_composite_key_is_fingerprinted_through_hexed_components(self):
    completed, statements, document = self.collect()

    self.assertEqual(0, completed.returncode, completed.stderr)
    digests = [line for line in statements if "BIT_XOR" in line]
    self.assertEqual(2, len(digests), statements)
    composite = [line for line in digests if "`a`" in line and "`b`" in line]
    self.assertEqual(1, len(composite), digests)
    self.assertIn("HEX(CAST(`a` AS BINARY))", composite[0])
    self.assertIn("HEX(CAST(`b` AS BINARY))", composite[0])
    self.assertIn("CONCAT_WS(':'", composite[0])
    self.assertIsNotNone(document["tables"]["task"]["identity"])

  ##
  ## Bounds are only meaningful for a single column, and are recorded rather
  ## than compared.
  ##
  def test_only_a_single_column_key_gets_bounds(self):
    completed, statements, document = self.collect()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("key_minimum", document["tables"]["live"])
    self.assertNotIn("key_minimum", document["tables"]["task"])

  def test_no_statement_reads_a_row_of_data(self):
    completed, statements, document = self.collect()

    self.assertEqual(0, completed.returncode, completed.stderr)
    for line in statements:
      self.assertNotIn("SELECT *", line, line)


class RehearsalContractTest(unittest.TestCase):
  def setUp(self):
    self.rehearsal = REHEARSAL.read_text(encoding="utf-8")
    self.statements = [
      line for line in self.rehearsal.splitlines()
      if line.strip() and not line.strip().startswith("#")
    ]

  ##
  ## The estimate must not come back. It is one identifier away at all times and
  ## it reads exactly like the real thing.
  ##
  def test_the_row_estimate_is_never_used_as_evidence(self):
    for line in self.statements:
      self.assertNotIn("table_rows", line, line.strip())

  def test_the_baseline_is_taken_before_the_upgrade(self):
    body = self.rehearsal[self.rehearsal.index("rehearse() {"):]
    self.assertLess(
      body.index("$baseline_output"),
      body.index("migration upgrade"),
      "the baseline must be collected before anything migrates",
    )

  def test_the_comparison_runs_and_its_failure_stops_the_rehearsal(self):
    self.assertIn("$INVARIANT_HELPER\" compare", self.rehearsal)
    self.assertIn("did not preserve the data it was given", self.rehearsal)

  ##
  ## Every step this rehearsal claims to perform is actually reached.
  ##
  ## ``<command> || true`` leaves the command written in the file, so a test
  ## that greps for its name keeps passing while the step stops happening. The
  ## drill is pinned the same way and for the same reason.
  ##
  def test_no_step_can_be_short_circuited_out_of_the_rehearsal(self):
    for line in self.statements:
      stripped = line.strip()
      self.assertFalse(
        stripped.startswith("true ||"), "a step is skipped: " + stripped
      )
      self.assertNotIn("|| true", stripped, "a step is skipped: " + stripped)

  ##
  ## Two independent runs, each from the same immutable snapshot onto a fresh
  ## server. Running the upgrade twice against one database is a different claim
  ## - idempotency - and it is kept, but it does not stand in for this.
  ##
  def test_the_whole_rehearsal_is_performed_twice_from_a_fresh_server(self):
    invocations = [
      line for line in self.statements if line.startswith("rehearse ")
    ]
    self.assertEqual(2, len(invocations), invocations)
    self.assertIn("independent, fresh server", invocations[1])
    self.assertIn("the disposable server could not be destroyed", self.rehearsal)

  def test_each_run_proves_the_source_revision_for_itself(self):
    body = self.rehearsal[self.rehearsal.index("rehearse() {"):]
    self.assertIn("expected_source_revision", body)
    self.assertIn("not at the expected production revision", body)

  def test_each_run_checks_the_schema_after_its_own_upgrade(self):
    body = self.rehearsal[self.rehearsal.index("rehearse() {"):]
    self.assertIn("migration check", body)
    self.assertIn("require_ready_at_head", body)

  def test_the_snapshot_identity_is_proven_around_both_runs(self):
    self.assertGreaterEqual(
      self.rehearsal.count("require_snapshot_identity"), 4
    )
    self.assertIn("byte-identical", self.rehearsal)

  ##
  ## And the repository's own configuration is never written. The first version
  ## overwrote it and restored it afterwards, which works until a signal arrives
  ## at the wrong moment.
  ##
  def test_the_working_repository_configuration_is_never_rewritten(self):
    for line in self.statements:
      self.assertNotIn('"$PROJECT_DIR/config/config.yml"', line, line.strip())
    self.assertIn("isolated", self.rehearsal)


if __name__ == "__main__":
  unittest.main()
