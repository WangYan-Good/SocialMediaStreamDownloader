##
## The external restore drill, as a contract rather than as a run.
##
## The drill itself needs a real MySQL and a real filesystem, so it runs as a
## real-infra gate. What can be pinned deterministically is the *shape*: that
## the guards come before the restore, that the destination can never be the
## live one, and that the marker is only printed after something was proven.
##
## This mirrors ``ReleaseScriptContractTest``, which pins the Compose scripts
## the same way and for the same reason - an ordering bug in a release script is
## not the kind of thing anybody notices by reading it once.
##
from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DRILL = PROJECT_ROOT / "scripts" / "release_external_restore_drill.sh"
BACKUP = PROJECT_ROOT / "scripts" / "release_external_backup.sh"
MARKER = "ok   runtime external host restore drill"


class ExternalRestoreDrillContractTest(unittest.TestCase):
  def setUp(self):
    self.drill = DRILL.read_text(encoding="utf-8")
    self.backup = BACKUP.read_text(encoding="utf-8")

  def test_the_drill_fails_fast_and_loudly(self):
    self.assertIn("set -euo pipefail", self.drill)
    self.assertIn("umask 077", self.drill)

  ##
  ## Order is the whole argument. Each of these must precede the one after it,
  ## or the drill would be acting on something it had not yet checked.
  ##
  def test_the_guards_run_before_anything_is_restored(self):
    anchors = [
      "verify \"$backup_directory\"",
      "validate-external-restore-target",
      "require-empty-restore-destination",
      "$SNAPSHOT_HELPER\" verify",
      "information_schema.schemata",
      "CREATE DATABASE",
      "$backup_directory/database.sql",
      "cp -a --reflink=always",
      "$EXTERNAL_POSTCHECK_SCRIPT",
    ]
    positions = [self.drill.index(anchor) for anchor in anchors]
    self.assertEqual(
      positions, sorted(positions), "the drill's guards are out of order"
    )

  ##
  ## >>================= a database it did not create =================>>
  ##
  ## ``DROP DATABASE IF EXISTS`` followed by a create reads as isolation and
  ## behaves as destruction: at the moment it runs, nobody has established that
  ## the name was free. Against a shared server that is one typo from a
  ## production database.
  ##
  def test_the_drill_never_drops_a_database(self):
    ##
    ## Asserted against the executable lines rather than the whole file, because
    ## the comment explaining what this replaces necessarily quotes it.
    ##
    statements = [
      line for line in self.drill.splitlines()
      if "DROP DATABASE" in line and not line.strip().startswith("#")
    ]
    for line in statements:
      self.assertNotIn("IF EXISTS", line, line)
    ##
    ## The one drop that remains is the cleanup of what this invocation itself
    ## created, and it is gated on having created it.
    ##
    self.assertEqual(1, len(statements), statements)
    cleanup = self.drill[self.drill.index("cleanup() {"):]
    cleanup = cleanup[:cleanup.index('trap cleanup EXIT')]
    self.assertIn("DROP DATABASE", cleanup)
    self.assertIn('created_restore_database" == "true"', cleanup)

  def test_the_existing_database_check_precedes_the_create(self):
    self.assertLess(
      self.drill.index("information_schema.schemata"),
      self.drill.index("CREATE DATABASE"),
    )
    self.assertIn("will not destroy a database it did not create", self.drill)
    ##
    ## The condition, not the message beside it. Deleting the test and keeping
    ## the refusal text leaves a script that still describes a guard it no
    ## longer has.
    ##
    self.assertIn('[[ "$existing_schema" == "0" ]]', self.drill)

  def test_the_restore_is_required_to_land_rows_and_not_just_a_schema(self):
    self.assertIn("(( restored_table_count > 0 ))", self.drill)
    self.assertIn("(( restored_rows > 0 ))", self.drill)

  ##
  ## Every step this drill claims to perform is actually reached.
  ##
  ## ``true || <command>`` and ``<command> || true`` both leave the command
  ## written in the file, so any test that greps for its name keeps passing
  ## while the step stops happening.
  ##
  def test_no_step_can_be_short_circuited_out_of_the_drill(self):
    for line in self.drill.splitlines():
      stripped = line.strip()
      if stripped.startswith("#"):
        continue
      self.assertFalse(
        stripped.startswith("true ||"), "a step is skipped: " + stripped
      )
      self.assertNotIn("|| true", stripped, "a step is skipped: " + stripped)

  def test_the_application_start_and_postcheck_are_real_invocations(self):
    started = [
      line for line in self.drill.splitlines() if "run --detach" in line
    ]
    self.assertEqual(1, len(started))
    self.assertTrue(started[0].startswith('"$ENGINE_BIN"'), started[0])

    postchecks = [
      line for line in self.drill.splitlines()
      if line.startswith('"$EXTERNAL_POSTCHECK_SCRIPT"')
    ]
    self.assertEqual(1, len(postchecks), self.drill.count("EXTERNAL_POSTCHECK_SCRIPT"))

  ##
  ## >>================ reflink or refuse, never a copy ================>>
  ##
  ## ``--reflink=auto`` silently becomes a byte copy when cloning is not
  ## available. On a tree this size that is not a slower success - it is a
  ## failure that takes hours to arrive and fills a disk on the way.
  ##
  def test_the_media_is_cloned_or_the_drill_refuses(self):
    self.assertIn("cp -a --reflink=always", self.drill)
    self.assertNotIn("--reflink=auto", self.drill)
    ##
    ## And whether a clone can work at all is settled before the database is
    ## touched, rather than discovered afterwards.
    ##
    self.assertLess(
      self.drill.index("st_dev"), self.drill.index("CREATE DATABASE")
    )

  ##
  ## >>============== the application, not just the artefacts ==============>>
  ##
  ## Everything before this proves the bundle contains what it claims. None of
  ## it proves an operator can start the application on the result, which is the
  ## only question they actually have at three in the morning.
  ##
  def test_the_drill_starts_the_application_and_postchecks_it(self):
    self.assertIn("run --detach", self.drill)
    self.assertIn("$EXTERNAL_POSTCHECK_SCRIPT", self.drill)
    ##
    ## The real postcheck rather than a reimplementation of it, so the drill
    ## cannot drift into proving less than a deployment does.
    ##
    self.assertNotIn("migration_cli status", self.drill)

  ##
  ## The restored copy proves it runs; it must not prove it works, because
  ## "works" here means a second production making real requests and real
  ## writes against a tree that is about to be compared with its own snapshot.
  ##
  def test_the_restored_application_is_inert(self):
    staging = self.drill[self.drill.index("drill_config="):]
    staging = staging[:staging.index("chmod 600")]
    self.assertIn('source["download"]["test_mode"] = True', staging)
    self.assertIn('source["download"]["save_response"] = False', staging)
    self.assertIn('source["download"]["save_error_response"] = False', staging)

  def test_the_application_runs_under_the_same_identity_mapping(self):
    self.assertIn('--userns "keep-id:uid=${application_uid}', self.drill)

  def test_the_drill_never_uses_production_names(self):
    self.assertIn("smsd-restore-drill-", self.drill)
    self.assertIn("127.0.0.1:${port}:${port}", self.drill)
    for forbidden in ("/mnt/video", ":5000:", "--restart"):
      self.assertNotIn(forbidden, self.drill)

  ##
  ## The snapshot and the bundle are re-verified after everything else, so a
  ## drill that disturbed either of them fails rather than reports success.
  ##
  def test_the_source_is_proven_untouched_at_the_end(self):
    tail = self.drill[self.drill.index("$EXTERNAL_POSTCHECK_SCRIPT"):]
    self.assertIn("$SNAPSHOT_HELPER\" verify", tail)
    self.assertIn("$BUNDLE_HELPER\" verify", tail)
    self.assertIn("disturbed the snapshot", tail)
    self.assertIn("disturbed the bundle", tail)

  def test_the_drill_refuses_a_bundle_from_the_other_topology(self):
    self.assertIn('[[ "$topology" == "external-host" ]]', self.drill)

  ##
  ## The snapshot is the rollback authority for the release that produced it.
  ## A drill that moved it would have spent the thing it exists to prove.
  ##
  def test_the_snapshot_is_cloned_and_never_moved_or_removed(self):
    self.assertIn("cp -a --reflink=always", self.drill)
    for destructive in ("mv \"$snapshot_path", "rm -rf -- \"$snapshot_path"):
      self.assertNotIn(destructive, self.drill)

  def test_the_marker_is_printed_once_and_only_at_the_end(self):
    self.assertEqual(1, self.drill.count(MARKER))
    tail = self.drill[self.drill.index('echo "$MARKER"'):]
    self.assertNotIn("fail ", tail, "a check runs after the marker")

  ##
  ## The existing Compose marker is asserted elsewhere to appear exactly once in
  ## its own script and once in the workflow, so this one has to be different.
  ##
  def test_the_marker_is_distinct_from_the_compose_drill_marker(self):
    self.assertNotEqual(MARKER, "ok   runtime release backup restore drill")
    self.assertNotIn("ok   runtime release backup restore drill", self.drill)

  ##
  ## Neither script may carry a flag that turns a refusal into a warning. The
  ## Compose restore is pinned the same way.
  ##
  def test_neither_script_offers_a_way_past_its_own_guards(self):
    for source in (self.drill, self.backup):
      ##
      ## Flags that would turn a refusal into a warning. ``--skip-column-names``
      ## is deliberately not here: it shapes output, it does not skip a check.
      ##
      for escape in ("--no-verify", "--skip-verify", "|| true"):
        self.assertNotIn(escape, source)
      ##
      ## ``--force`` is allowed in exactly one place: removing a disposable
      ## container this script started. Anywhere else - on the bundle helper, on
      ## the snapshot helper, on the client - it would be a way past a check.
      ##
      for line in source.splitlines():
        if "--force" in line:
          self.assertIn("$ENGINE_BIN", line, line)

  def test_the_backup_proves_the_writer_stopped_before_it_captures(self):
    anchors = [
      "stop the writer before backing up",
      "$MYSQLDUMP_BIN",
      "$SNAPSHOT_HELPER\" create",
      "write-manifest",
      "write-checksums",
      ##
      ## The final verification, anchored on the call rather than on the bare
      ## word: "verify" appears in this file's own prose long before the step
      ## that does it.
      ##
      "$BUNDLE_HELPER\" verify",
    ]
    positions = [self.backup.index(anchor) for anchor in anchors]
    self.assertEqual(
      positions, sorted(positions), "the backup's ordering is not the contract"
    )

  ##
  ## The dump must not name its own database.
  ##
  ## ``mysqldump --databases X`` emits ``CREATE DATABASE X`` and ``USE X``, so
  ## the SQL selects its own destination and the client's ``--database`` is
  ## ignored. A drill "restoring" such a dump writes into the source database
  ## instead - which on the production server means importing a backup over
  ## production while the disposable-name guard reports success. The guard is
  ## inert against a dump that chooses for itself, so the dump must not.
  ##
  ## The Compose path keeps ``--databases`` because there the destination is a
  ## whole disposable stack and the name is meant to be preserved.
  ##
  def test_the_external_dump_does_not_embed_its_database_name(self):
    ##
    ## Asserted against the invocation rather than the file, because the comment
    ## above it necessarily names the flag it is explaining.
    ##
    invocation = self.backup[self.backup.index('"$MYSQLDUMP_BIN"'):]
    invocation = invocation[:invocation.index("fail \"the database could not be dumped\"")]
    self.assertNotIn("--databases", invocation)
    self.assertIn('"$database_name"', invocation)

  ##
  ## And the drill proves the data actually landed where it was aimed, so a
  ## future change to the dump format cannot quietly reopen the same hole.
  ##
  def test_the_drill_verifies_the_restore_landed_in_the_target(self):
    self.assertIn("restored_table_count", self.drill)
    index = self.drill.index("restored_table_count")
    self.assertLess(
      index,
      self.drill.index('echo "$MARKER"'),
      "the landing check must run before the marker",
    )

  ##
  ## The credential never survives the script, on any path.
  ##
  def test_both_scripts_remove_the_credential_on_every_exit(self):
    for source in (self.drill, self.backup):
      self.assertIn("trap cleanup EXIT", source)
      self.assertIn('rm -rf -- "$credential_directory"', source)
      self.assertNotIn("MYSQL_PWD", source)
      self.assertNotIn("-p$", source)


if __name__ == "__main__":
  unittest.main()
