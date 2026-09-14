##
## The runbook has to keep saying the things the tooling actually enforces.
##
## Documentation drifts in one direction: a guard gets added and the runbook
## keeps describing the world before it, or a boundary gets documented once and
## then quietly widened in code. The existing docs test pins the Compose
## contract for that reason; this pins the external one.
##
## Two of these are about what the runbook must *not* claim. A document that
## implies the cutover already happened, or that the media snapshot protects
## against device loss, is worse than no document - somebody will plan around it.
##
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RELEASE = PROJECT_ROOT / "docs" / "operations" / "release.md"
MIGRATIONS = PROJECT_ROOT / "docs" / "operations" / "migrations.md"
RECORD = PROJECT_ROOT / "docs" / "operations" / "release-record-template.md"


class ExternalRunbookTest(unittest.TestCase):
  def setUp(self):
    self.release = RELEASE.read_text(encoding="utf-8")
    self.migrations = MIGRATIONS.read_text(encoding="utf-8")
    self.record = RECORD.read_text(encoding="utf-8")

  def test_both_topologies_are_named_and_kept_apart(self):
    self.assertIn("Compose deployment", self.release)
    self.assertIn("External-host deployment", self.release)

  ##
  ## The two boundaries an operator must not have to discover.
  ##
  def test_the_snapshot_rollback_scope_is_stated_including_what_it_excludes(self):
    self.assertIn("reflink", self.release)
    self.assertIn("设备损失", self.release)
    self.assertIn("off-host backup", self.release)

  def test_nothing_implies_the_cutover_has_happened(self):
    self.assertIn("不**表示生产 cutover 已经发生", self.release)
    for claim in ("cutover 已完成", "已切换到容器", "生产已迁移"):
      self.assertNotIn(claim, self.release)

  ##
  ## Each precondition that fails closed has to be findable by an operator who
  ## hit it, which means the runbook has to name the thing they saw.
  ##
  def test_every_failing_precondition_is_documented(self):
    for topic in (
      "release_external_preflight.sh",
      "operator_confirmed_stop_start_authority",
      "release_db_privileges.py",
      "SECURITY HARDENING REQUIRED",
      "0600",
      "single writer",
    ):
      with self.subTest(topic=topic):
        self.assertIn(topic, self.release.replace("Single writer", "single writer"))

  def test_the_publication_and_networking_decisions_are_explained(self):
    self.assertIn("--publish-address", self.release)
    self.assertIn("--network=host", self.release)
    self.assertIn("--cpus", self.release)

  def test_the_canonical_config_is_documented_as_never_rewritten(self):
    self.assertIn("canonical config 不被改写", self.release)
    self.assertIn("SMSD_DB_HOST", self.release)

  ##
  ## The hidden state is the part somebody restoring in a hurry forgets.
  ##
  def test_the_hidden_state_is_named_in_recoverable_state(self):
    self.assertIn(".smsd-recording-recovery/", self.release)
    self.assertIn(".smsd-recording-orphan-quarantine/", self.release)

  def test_the_dump_destination_hazard_is_recorded(self):
    self.assertIn("--databases", self.release)
    self.assertIn("USE", self.release)

  def test_the_migration_doc_explains_how_to_reach_a_host_database(self):
    self.assertIn("SMSD_DB_HOST", self.migrations)
    self.assertIn("state=ready", self.migrations)
    self.assertIn("disposable", self.migrations)

  def test_the_release_record_captures_the_external_facts(self):
    for field in (
      "topology: external-host",
      "publish_address",
      "media_snapshot_path",
      "writer_authority_confirmed",
      "db_privilege_verdict",
      "restore_drill_result",
    ):
      with self.subTest(field=field):
        self.assertIn(field, self.record)

  ##
  ## The record is pasted into tickets, so its template must not invite a
  ## secret into one.
  ##
  def test_the_release_record_still_forbids_secrets(self):
    self.assertIn("禁止保存", self.record)
    for forbidden in ("password: ", "db_password", "cookie:"):
      self.assertNotIn(forbidden, self.record)


if __name__ == "__main__":
  unittest.main()
