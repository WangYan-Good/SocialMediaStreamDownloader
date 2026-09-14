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
      "CREATE DATABASE",
      "$backup_directory/database.sql",
      "cp -a --reflink=auto",
    ]
    positions = [self.drill.index(anchor) for anchor in anchors]
    self.assertEqual(
      positions, sorted(positions), "the drill's guards are out of order"
    )

  def test_the_drill_refuses_a_bundle_from_the_other_topology(self):
    self.assertIn('[[ "$topology" == "external-host" ]]', self.drill)

  ##
  ## The snapshot is the rollback authority for the release that produced it.
  ## A drill that moved it would have spent the thing it exists to prove.
  ##
  def test_the_snapshot_is_cloned_and_never_moved_or_removed(self):
    self.assertIn("cp -a --reflink=auto", self.drill)
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
      for escape in ("--force", "--no-verify", "--skip-verify", "|| true"):
        self.assertNotIn(escape, source)

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
