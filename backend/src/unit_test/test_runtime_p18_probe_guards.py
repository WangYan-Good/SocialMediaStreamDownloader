##
## The proof that the proofs actually run.
##
## A runtime marker is only worth something if three things hold: the script
## really is copied into the production image and executed there, the workflow
## checks for the marker with an exact match, and the marker is printed only
## after the script has proved something. Drop any one and the job still goes
## green while proving nothing - which is the specific false-green this file
## exists to prevent.
##
## ``grep -Fxq`` rather than ``grep -q``: a substring match would accept
## "ok   runtime recording orphan inventory quarantine was skipped", and a
## pattern match would accept whatever a regular expression happened to allow.
##
## The heredoc check is here for the same reason it is in the work-admission
## guard: a marker produced by ``docker exec ... python - <<PY`` is produced by
## a script that is not in the repository, so nothing reviews it and nothing
## stops it from being an ``echo``.
##
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = PROJECT_ROOT / ".github/workflows/ci.yml"

PROBES = (
  (
    "scripts/runtime_recording_orphan_probe.py",
    "ok   runtime recording orphan inventory quarantine",
  ),
  (
    "scripts/runtime_persistence_diagnostic_probe.py",
    "ok   runtime persistence diagnostic redaction",
  ),
)


class RuntimeProbeGuardTest(unittest.TestCase):
  def setUp(self):
    self.workflow = WORKFLOW.read_text(encoding="utf-8")

  def test_each_probe_is_tracked_copied_executed_and_exactly_matched(self):
    for relative, marker in PROBES:
      with self.subTest(probe=relative):
        script = PROJECT_ROOT / relative
        self.assertTrue(script.is_file(), "the probe must be tracked in the repo")
        source = script.read_text(encoding="utf-8")

        ##
        ## Printed once. A second print would let a later edit move the marker
        ## above the checks and still satisfy every grep below.
        ##
        self.assertEqual(1, source.count(marker))
        self.assertIn("docker cp {}".format(relative), self.workflow)
        self.assertIn(
          "python /tmp/{}".format(Path(relative).name), self.workflow
        )
        self.assertIn("grep -Fxq '{}'".format(marker), self.workflow)

  def test_no_marker_is_produced_by_an_untracked_heredoc(self):
    self.assertNotIn("docker exec smsd-ci-smoke python -", self.workflow)

  def test_the_marker_is_the_last_thing_each_probe_prints(self):
    for relative, marker in PROBES:
      with self.subTest(probe=relative):
        source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        ##
        ## Everything the probe asserts runs before the marker line. A marker
        ## printed early would survive a later failure and report success for a
        ## run that raised.
        ##
        tail = source[source.index(marker):]
        self.assertNotIn("require(", tail, "a check runs after the marker")
        self.assertNotIn("assert ", tail, "a check runs after the marker")

  def test_each_probe_actually_validates_rather_than_only_printing(self):
    for relative, unused in PROBES:
      with self.subTest(probe=relative):
        source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        ##
        ## A crude but load-bearing floor: a probe reduced to an echo would
        ## have no assertions left at all. The count understates the real
        ## coverage - both probes assert inside loops over levels, sentinels
        ## and planted filesystem shapes - which is fine for a floor.
        ##
        self.assertGreaterEqual(
          source.count("require("),
          5,
          "the probe must prove properties, not merely print a marker",
        )
        self.assertIn("FAIL: ", source)
        ##
        ## And it must be able to fail. A probe with no failure path is a probe
        ## whose marker means nothing.
        ##
        self.assertIn("SystemExit", source)

  def test_no_probe_step_is_allowed_to_fail_silently(self):
    ##
    ## The proof path must not be softened. Log collection elsewhere in this
    ## workflow legitimately uses ``|| true``; a marker check never may.
    ##
    for unused, marker in PROBES:
      guard = "grep -Fxq '{}'".format(marker)
      index = self.workflow.index(guard)
      window = self.workflow[index:index + 400]
      self.assertNotIn("|| true", window)
      self.assertNotIn("continue-on-error", window)
      self.assertIn("exit 1", window)

  def test_the_probes_reach_the_production_modules_rather_than_copies(self):
    for relative, unused in PROBES:
      with self.subTest(probe=relative):
        source = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        self.assertIn("from backend.src.", source)
        ##
        ## The image installs the application at /app; a probe that could not
        ## find it there would silently exercise nothing inside the container.
        ##
        self.assertIn('Path("/app")', source)


if __name__ == "__main__":
  unittest.main()
