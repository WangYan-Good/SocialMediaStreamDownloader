##
## Proving the application can write the media tree, in the application's name.
##
## The external topology bind-mounts a host directory that predates the release.
## Whether that works is a question about exactly one identity - the one the
## application process has - and under rootless Podman that is not the identity
## the container starts with. The entrypoint runs as root, which maps to the
## operator and can write anything the operator can; the application runs as an
## unprivileged account, which maps into the subordinate range and cannot.
##
## A probe that does not insist on being the second of those measures the first
## and reports a capability the application does not have. That was the defect.
## Everything below is about making that impossible to reintroduce.
##
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROBE_SCRIPT = PROJECT_ROOT / "scripts" / "release_media_write_probe.py"
PYTHON_BIN = sys.executable


def load_probe():
  specification = importlib.util.spec_from_file_location(
    "release_media_write_probe", PROBE_SCRIPT
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


class MediaWriteProbeTestCase(unittest.TestCase):
  def media_root(self, populated: bool = True) -> Path:
    root = Path(tempfile.mkdtemp())
    self.addCleanup(shutil.rmtree, root, True)
    media = root / "media"
    (media / "douyin" / "live").mkdir(parents=True)
    if populated:
      (media / "douyin" / "live" / "a.flv").write_bytes(b"a recording")
    return media

  def run_probe(self, media: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run(
      [
        PYTHON_BIN, str(PROBE_SCRIPT),
        "--media-root", str(media),
        "--expect-uid", str(os.geteuid()),
        "--expect-gid", str(os.getegid()),
        *extra,
      ],
      capture_output=True,
      text=True,
    )


class MediaWriteProbeIdentityTest(MediaWriteProbeTestCase):
  ##
  ## The guard the whole file exists for. A root probe writes a bind mount
  ## successfully whatever the mapping is, so accepting one would turn this
  ## proof into a restatement of the entrypoint's privileges.
  ##
  def test_it_refuses_to_run_as_root(self):
    module = load_probe()
    media = self.media_root()
    with mock.patch.object(os, "geteuid", return_value=0), \
         mock.patch.object(os, "getegid", return_value=0):
      with self.assertRaises(SystemExit) as raised:
        module.main([
          "--media-root", str(media), "--expect-uid", "0", "--expect-gid", "0",
        ])
    self.assertNotEqual(0, raised.exception.code)

  def test_a_uid_other_than_the_application_account_is_refused(self):
    media = self.media_root()
    completed = subprocess.run(
      [
        PYTHON_BIN, str(PROBE_SCRIPT),
        "--media-root", str(media),
        "--expect-uid", str(os.geteuid() + 1),
        "--expect-gid", str(os.getegid()),
      ],
      capture_output=True,
      text=True,
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("rather than the application", completed.stderr)

  def test_a_gid_other_than_the_application_account_is_refused(self):
    media = self.media_root()
    completed = subprocess.run(
      [
        PYTHON_BIN, str(PROBE_SCRIPT),
        "--media-root", str(media),
        "--expect-uid", str(os.geteuid()),
        "--expect-gid", str(os.getegid() + 1),
      ],
      capture_output=True,
      text=True,
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("rather than the application", completed.stderr)


class MediaWriteProbeCapabilityTest(MediaWriteProbeTestCase):
  def test_a_writable_media_tree_passes_and_reports_what_it_read(self):
    media = self.media_root()

    completed = self.run_probe(media, "--require-existing")

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("media write probe passed", completed.stdout)
    self.assertIn("read=1", completed.stdout)

  def test_a_media_root_that_cannot_be_written_fails(self):
    media = self.media_root()
    media.chmod(0o555)
    self.addCleanup(media.chmod, 0o755)

    completed = self.run_probe(media)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("could not be captured", completed.stderr)

  def test_existing_media_that_cannot_be_read_fails(self):
    media = self.media_root()
    recording = media / "douyin" / "live" / "a.flv"
    recording.chmod(0o000)
    self.addCleanup(recording.chmod, 0o644)

    completed = self.run_probe(media)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("could not be read", completed.stderr)

  ##
  ## An application that can write recordings but not its bookkeeping loses the
  ## bookkeeping on the next restart, silently.
  ##
  def test_a_recovery_journal_that_cannot_be_created_fails(self):
    media = self.media_root()
    (media / ".smsd-recording-recovery").write_text("not a directory")

    completed = self.run_probe(media)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("recovery journal", completed.stderr)

  def test_a_quarantine_that_cannot_be_created_fails(self):
    media = self.media_root()
    (media / ".smsd-recording-orphan-quarantine").write_text("not a directory")

    completed = self.run_probe(media)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("orphan quarantine", completed.stderr)

  def test_a_recovery_journal_that_cannot_be_written_fails(self):
    media = self.media_root()
    journal = media / ".smsd-recording-recovery"
    journal.mkdir()
    journal.chmod(0o555)
    self.addCleanup(journal.chmod, 0o700)

    completed = self.run_probe(media)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("recovery journal", completed.stderr)

  def test_an_empty_tree_cannot_stand_in_for_read_access(self):
    media = self.media_root(populated=False)

    completed = self.run_probe(media, "--require-existing")

    self.assertNotEqual(0, completed.returncode)

  def test_an_absent_media_root_fails(self):
    media = self.media_root() / "absent"

    completed = self.run_probe(media)

    self.assertNotEqual(0, completed.returncode)

  ##
  ## It runs against production. Everything it creates is hidden, is its own,
  ## and is gone when it returns.
  ##
  def test_it_leaves_nothing_of_its_own_behind(self):
    media = self.media_root()

    completed = self.run_probe(media)
    self.assertEqual(0, completed.returncode, completed.stderr)

    residue = [
      str(Path(current).relative_to(media) / name)
      for current, unused, files in os.walk(media)
      for name in files
      if "write-probe" in name
    ]
    self.assertEqual([], residue)
    self.assertTrue((media / "douyin" / "live" / "a.flv").exists())


##
## >>=========== one identity contract, in every place it matters ===========>>
##
## The mapping is only worth anything if the deployment, the postcheck, the
## restore drill and the real-host gate all mean the same thing by it. A gate
## that maps the application and a deployment that forgets to would leave the
## gate proving a topology nobody runs; a drill that starts its application
## under a different identity would be exercising a second runtime and calling
## it a rehearsal of the first.
##
class ApplicationIdentityContractTest(unittest.TestCase):
  SCRIPTS = (
    "release_external_deploy.sh",
    "release_external_restore_drill.sh",
    "release_external_host_gate.sh",
  )

  def source(self, name: str) -> str:
    return (PROJECT_ROOT / "scripts" / name).read_text(encoding="utf-8")

  ##
  ## Every script that starts the application maps it, and maps it the same way.
  ##
  def test_every_script_that_starts_the_application_maps_it(self):
    for name in self.SCRIPTS:
      with self.subTest(script=name):
        self.assertIn(
          '--userns "keep-id:uid=${application_uid},gid=${application_gid}"',
          self.source(name),
        )

  ##
  ## Read from the image, never written down. A hard-coded pair keeps working
  ## right up until the image changes one, and then maps the operator onto the
  ## wrong account in silence.
  ##
  def test_the_identity_is_read_from_the_image_in_every_script(self):
    for name in self.SCRIPTS:
      source = self.source(name)
      with self.subTest(script=name):
        self.assertIn('id -u $APPLICATION_USER', source)
        self.assertIn('id -g $APPLICATION_USER', source)
        self.assertIn("APPLICATION_USER", source)

  def test_no_script_hard_codes_the_application_identity(self):
    for name in self.SCRIPTS + ("release_external_postcheck.sh",):
      source = self.source(name)
      with self.subTest(script=name):
        for line in source.splitlines():
          stripped = line.strip()
          if stripped.startswith("#") or stripped.startswith('"'):
            continue
          self.assertNotIn("uid=999", stripped, stripped)
          self.assertNotIn("gid=999", stripped, stripped)

  ##
  ## And a malformed or root identity stops each of them, rather than being
  ## mapped anyway.
  ##
  def test_every_script_validates_what_the_image_reported(self):
    for name in self.SCRIPTS:
      source = self.source(name)
      with self.subTest(script=name):
        self.assertIn('=~ ^[0-9]{1,10}$ ]]', source)
    for name in ("release_external_deploy.sh", "release_external_host_gate.sh"):
      with self.subTest(script=name):
        self.assertIn("application_uid != 0", self.source(name))

  ##
  ## The postcheck is told which identity to prove and proves that one, so a
  ## stale pair passed to it fails rather than being accepted.
  ##
  def test_the_postcheck_is_given_the_identity_and_holds_the_probe_to_it(self):
    postcheck = self.source("release_external_postcheck.sh")
    self.assertIn("--expect-uid", postcheck)
    self.assertIn("--expect-gid", postcheck)
    for name in ("release_external_deploy.sh", "release_external_restore_drill.sh"):
      with self.subTest(script=name):
        source = self.source(name)
        self.assertIn('--application-uid "$application_uid"', source)
        self.assertIn('--application-gid "$application_gid"', source)


class MediaWriteProbeContractTest(unittest.TestCase):
  ##
  ## The postcheck runs this file inside the image, so the two names have to
  ## agree, and the hidden directories have to be the ones the application
  ## actually keeps.
  ##
  def test_the_postcheck_runs_this_probe(self):
    postcheck = (PROJECT_ROOT / "scripts" / "release_external_postcheck.sh").read_text(
      encoding="utf-8"
    )
    self.assertIn("release_media_write_probe.py", postcheck)
    self.assertIn("exec --user", postcheck)

  def test_the_hidden_directories_are_the_applications_own(self):
    module = load_probe()
    from backend.src.service.recording_orphan import QUARANTINE_DIRECTORY_NAME
    from backend.src.service.recording_recovery_journal import (
      JOURNAL_DIRECTORY_NAME,
    )

    self.assertEqual(JOURNAL_DIRECTORY_NAME, module.JOURNAL_DIRECTORY_NAME)
    self.assertEqual(
      QUARANTINE_DIRECTORY_NAME, module.QUARANTINE_DIRECTORY_NAME
    )


if __name__ == "__main__":
  unittest.main()
