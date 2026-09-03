##
## The operator surface, and what it is not allowed to do or say.
##
## Two properties matter more than the argument parsing. First, quarantine never
## acts without being told to twice - once by naming the subcommand and once by
## ``--confirm`` - because a command that moves media when run bare will
## eventually be run bare. Second, nothing this prints describes the host: an
## operator's output ends up in tickets and pastes, and a deployment's absolute
## paths, database location and credentials have no reason to travel with it.
##
import io
from pathlib import Path
import tempfile
import unittest

from backend.src.service.recording_orphan import (
  OrphanInventoryUnavailable,
  OrphanQuarantineRefused,
  RecordingOrphanInventory,
)
from backend.src.service.recording_orphan_cli import (
  EXIT_OK,
  EXIT_REFUSED,
  EXIT_UNAVAILABLE,
  EXIT_USAGE,
  main,
)
from backend.src.service.recording_recovery_journal import RecordingRecoveryJournal

from backend.src.unit_test.test_recording_orphan_inventory import (
  FakeReferences,
  settings_for,
)


class OrphanCliTestCase(unittest.TestCase):
  def setUp(self):
    self._temporary = tempfile.TemporaryDirectory()
    self.root = Path(self._temporary.name)
    self.media_root = self.root / "douyin" / "live"
    self.media_root.mkdir(parents=True)
    self.settings = settings_for(self.root)
    self.references = FakeReferences()
    self.out = io.StringIO()
    self.addCleanup(self._temporary.cleanup)

  def inventory(self):
    return RecordingOrphanInventory(
      journal=RecordingRecoveryJournal(config_loader=lambda: self.settings),
      references=self.references,
      config_loader=lambda: self.settings,
    )

  def run_cli(self, *argv, factory=None):
    return main(
      list(argv),
      inventory_factory=factory or self.inventory,
      out=self.out,
    )

  def orphan(self, name="orphan.flv"):
    directory = self.media_root / "broadcaster"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(b"a whole broadcast")
    return path

  def relative(self, path):
    return str(path.relative_to(self.root))


class OrphanCliScanTest(OrphanCliTestCase):
  def test_scan_reports_a_candidate_by_its_root_relative_path(self):
    source = self.orphan()

    code = self.run_cli("scan")

    self.assertEqual(EXIT_OK, code)
    printed = self.out.getvalue()
    self.assertIn(self.relative(source), printed)
    self.assertIn("candidates=1", printed)

  def test_scan_never_prints_an_absolute_path(self):
    self.orphan()

    self.run_cli("scan")

    self.assertNotIn(str(self.root), self.out.getvalue())

  def test_scan_changes_nothing(self):
    source = self.orphan()

    self.run_cli("scan")

    self.assertTrue(source.exists())

  def test_scan_reports_an_unavailable_authority_rather_than_an_empty_result(self):
    self.orphan()
    self.references.error = RuntimeError("database is down")

    code = self.run_cli("scan")

    self.assertEqual(EXIT_UNAVAILABLE, code)
    self.assertIn("unavailable", self.out.getvalue())

  def test_an_unavailable_deployment_never_prints_the_underlying_reason(self):
    def failing():
      raise OrphanInventoryUnavailable(
        "connect to 10.1.2.3 as root failed: SECRET_DB_PASSWORD"
      )

    self.run_cli("scan", factory=failing)

    self.assertNotIn("SECRET_DB_PASSWORD", self.out.getvalue())
    self.assertNotIn("10.1.2.3", self.out.getvalue())


class OrphanCliQuarantineTest(OrphanCliTestCase):
  def test_quarantine_refuses_to_act_without_confirmation(self):
    source = self.orphan()

    code = self.run_cli("quarantine", self.relative(source))

    self.assertEqual(EXIT_USAGE, code)
    self.assertTrue(source.exists(), "an unconfirmed quarantine must not act")
    self.assertIn("--confirm", self.out.getvalue())

  def test_a_dry_run_reports_without_confirmation_and_changes_nothing(self):
    source = self.orphan()

    code = self.run_cli("quarantine", self.relative(source), "--dry-run")

    self.assertEqual(EXIT_OK, code)
    self.assertTrue(source.exists())
    self.assertIn("would quarantine", self.out.getvalue())

  def test_a_confirmed_quarantine_moves_exactly_the_named_file(self):
    source = self.orphan()
    bystander = self.orphan("bystander.flv")

    code = self.run_cli("quarantine", self.relative(source), "--confirm")

    self.assertEqual(EXIT_OK, code)
    self.assertFalse(source.exists())
    self.assertTrue(bystander.exists(), "only the named file may move")
    self.assertIn("quarantined", self.out.getvalue())

  def test_a_path_that_is_not_a_current_candidate_is_refused(self):
    self.orphan()

    code = self.run_cli(
      "quarantine", "douyin/live/broadcaster/never-existed.flv", "--confirm"
    )

    self.assertEqual(EXIT_REFUSED, code)

  def test_a_referenced_recording_cannot_be_quarantined_by_naming_it(self):
    source = self.orphan()
    self.references.paths = [str(source)]

    code = self.run_cli("quarantine", self.relative(source), "--confirm")

    self.assertEqual(EXIT_REFUSED, code)
    self.assertTrue(source.exists())

  def test_a_refusal_never_prints_the_underlying_reason(self):
    source = self.orphan()

    class RefusingInventory:
      def scan(self, **unused):
        raise OrphanQuarantineRefused(
          "link /srv/media/SECRET_PATH failed: SECRET_REASON"
        )

    self.run_cli(
      "quarantine", self.relative(source), "--confirm",
      factory=RefusingInventory,
    )

    printed = self.out.getvalue()
    self.assertNotIn("SECRET_PATH", printed)
    self.assertNotIn("SECRET_REASON", printed)
    self.assertIn("refused", printed)


class OrphanCliSurfaceTest(unittest.TestCase):
  def test_p18_adds_no_browser_route_for_orphans(self):
    web = Path(__file__).resolve().parents[1] / "web"
    for source in web.rglob("*.py"):
      text = source.read_text(encoding="utf-8")
      self.assertNotIn("recording_orphan", text)
      self.assertNotIn("quarantine", text)

  def test_the_entry_point_only_delegates(self):
    entry = (
      Path(__file__).resolve().parents[1] / "recording_orphan_cli.py"
    ).read_text(encoding="utf-8")

    self.assertIn("from backend.src.service.recording_orphan_cli import main", entry)
    ##
    ## Nothing decided here. A thin entry point that grew logic would be a
    ## second copy of the command's rules.
    ##
    self.assertNotIn("argparse", entry)
    self.assertNotIn("os.", entry)


if __name__ == "__main__":
  unittest.main()


class OrphanCliReachabilityTest(OrphanCliTestCase):
  ##
  ## A file an operator can list but never quarantine would be a command that
  ## silently does not work for the case it exists for. ``scan``'s default
  ## limit keeps a *report* readable; it must not decide what can be acted on.
  ##
  def test_a_candidate_beyond_the_reporting_limit_can_still_be_named(self):
    for index in range(7):
      self.orphan("orphan-{}.flv".format(index))
    target = self.media_root / "broadcaster" / "orphan-6.flv"
    relative = self.relative(target)

    ##
    ## A limited report genuinely stops short of this file, and says so.
    ##
    limited = self.inventory().scan(limit=2)
    self.assertTrue(limited.truncated)
    self.assertNotIn(
      relative, [candidate.relative_path for candidate in limited.candidates]
    )

    ##
    ## The command still reaches it, because the lookup asks for everything
    ## rather than for a page.
    ##
    code = self.run_cli("quarantine", relative, "--confirm")

    self.assertEqual(EXIT_OK, code)
    self.assertFalse(target.exists())

  def test_the_lookup_walks_the_tree_once(self):
    from backend.src.service.recording_orphan_cli import _find_candidate

    class CountingInventory:
      def __init__(self):
        self.calls = 0

      def scan(self, limit=None, after=None):
        from backend.src.service.recording_orphan import OrphanScan

        self.calls += 1
        return OrphanScan(candidates=[], truncated=False, scanned=0)

    inventory = CountingInventory()
    self.assertIsNone(_find_candidate(inventory, "never-existed.flv"))
    ##
    ## One walk. Paging to reach a later candidate would re-walk the whole
    ## media tree once per page.
    ##
    self.assertEqual(1, inventory.calls)
