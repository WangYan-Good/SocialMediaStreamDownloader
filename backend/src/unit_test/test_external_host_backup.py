##
## Backing up a production that is not Compose.
##
## The Compose backup can stop the writer because it owns it: ``run-docker stop
## app``, dump, tar the volume, restart. None of that is available here. The
## writer is a bare-metal process nobody wrote a unit for, the database belongs
## to the host, and the media is two terabytes that cannot be tarred.
##
## What survives the move is the *ordering*, which is the only part that was
## ever load-bearing:
##
##   stop the writer -> prove it stopped -> dump -> snapshot -> manifest ->
##   checksums -> verify
##
## The proof step is new and is the one this file cares most about. Compose
## could stop the writer itself and therefore knew; here the writer is stopped
## by an operator beforehand, so the backup has to establish that it really is
## stopped rather than assume the operator did it. A dump taken beside a live
## writer is a dump of a moment that never existed, and a reflink snapshot taken
## beside one is worse: it clones each file at a slightly different instant.
##
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import textwrap
import unittest

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKUP_SCRIPT = PROJECT_ROOT / "scripts" / "release_external_backup.sh"
PYTHON_BIN = PROJECT_ROOT / "venv" / "bin" / "python"

SECRET_PASSWORD = "SECRET_BACKUP_DB_PASSWORD_P19"
CANONICAL_IMAGE = "ghcr.io/example/socialmediastreamdownloader@sha256:" + "a" * 64
SOURCE_COMMIT = "c" * 40


def reflink_supported(directory: Path) -> bool:
  source = directory / ".probe-src"
  target = directory / ".probe-dst"
  try:
    source.write_bytes(b"probe")
    return subprocess.run(
      ["cp", "--reflink=always", str(source), str(target)], capture_output=True
    ).returncode == 0
  finally:
    for path in (source, target):
      try:
        path.unlink()
      except FileNotFoundError:
        pass


class ExternalBackupTestCase(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text(
      "#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8"
    )
    command.chmod(0o700)
    return command

  def free_port(self) -> int:
    with socket.socket() as probe:
      probe.bind(("127.0.0.1", 0))
      return probe.getsockname()[1]

  ##
  ## The directory outlives the call on purpose. The assertions are about what
  ## the backup *left behind*, and a context manager would delete the bundle
  ## before anything could look at it.
  ##
  def run_backup(self, **overrides):
    temporary = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, temporary, True)
    root = Path(temporary)
    if not reflink_supported(root):
      self.skipTest("the scratch filesystem cannot reflink")
    calls = root / "calls.log"
    calls.touch()

    config = root / "config.yml"
    document = unified_config()
    document["database"]["host"] = "localhost"
    document["database"]["password"] = SECRET_PASSWORD
    document["download"]["save_path"] = str(root / "media")
    config.write_text(yaml.safe_dump(document), encoding="utf-8")
    config.chmod(overrides.pop("config_mode", 0o600))

    media = root / "media"
    (media / "douyin" / "live").mkdir(parents=True)
    (media / "douyin" / "live" / "a.flv").write_bytes(b"recording")
    (media / ".smsd-recording-recovery").mkdir()
    (media / ".smsd-recording-recovery" / "k.json").write_text("{}", encoding="utf-8")

    ##
    ## The engine stub answers the two questions the writer-stop proof asks,
    ## and stands in for the disposable container that reads schema state.
    ##
    engine = self.make_command(
      root,
      "engine",
      textwrap.dedent(
        """\
        echo "engine $*" >> "$CALL_LOG"
        case "$*" in
          *"ps "*) printf '%s' "${RUNNING_CONTAINER:-}" ;;
          *"migration_cli"*) printf '%s\\n' "${MIGRATION:-state=ready current=0011_x heads=0011_x}" ;;
          *) exit 0 ;;
        esac
        """
      ),
    )
    mysqldump = self.make_command(
      root,
      "mysqldump",
      textwrap.dedent(
        """\
        echo "mysqldump $*" >> "$CALL_LOG"
        exit "${DUMP_STATUS:-0}"
        printf -- '-- dump\\n'
        """
      ),
    )
    ##
    ## Written by the stub rather than by the real client, but through the
    ## real argument list, so the credential assertions are about what the
    ## script actually passes.
    ##
    mysqldump.write_text(
      "#!/usr/bin/env bash\nset -euo pipefail\n"
      'echo "mysqldump $*" >> "$CALL_LOG"\n'
      'if [[ "${DUMP_STATUS:-0}" != "0" ]]; then exit "${DUMP_STATUS}"; fi\n'
      "printf -- '-- dump\\n'\n",
      encoding="utf-8",
    )
    mysqldump.chmod(0o700)

    environment = dict(os.environ)
    environment.update({
      "CALL_LOG": str(calls),
      "ENGINE_BIN": str(engine),
      "MYSQLDUMP_BIN": str(mysqldump),
      "PYTHON_BIN": str(PYTHON_BIN),
      "RUNNING_CONTAINER": overrides.pop("running_container", ""),
    })
    for key in ("MIGRATION", "DUMP_STATUS"):
      if key.lower() in overrides:
        environment[key] = str(overrides.pop(key.lower()))
    if "snapshot_root" in overrides:
      snapshot_root = overrides.pop("snapshot_root")
    else:
      snapshot_root = media / ".smsd-release-snapshot"

    argv = [
      "bash", str(BACKUP_SCRIPT),
      "--output", str(root / "bundle"),
      "--config-file", str(overrides.pop("config_file", config)),
      "--database", "social_media_stream_downloader_v2",
      "--media-root", str(media),
      "--snapshot-root", str(snapshot_root),
      "--container-name", "smsd-app",
      "--port", str(overrides.pop("port", self.free_port())),
      "--image", CANONICAL_IMAGE,
      "--db-host", "host.containers.internal",
      "--source-git-commit", SOURCE_COMMIT,
    ]
    self.assertEqual({}, overrides, "unused override")

    completed = subprocess.run(
      argv, capture_output=True, text=True, env=environment
    )
    return completed, calls.read_text(encoding="utf-8"), root / "bundle"


class ExternalBackupOrderingTest(ExternalBackupTestCase):
  def test_a_correct_run_produces_a_verifiable_external_bundle(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    self.assertEqual("external-host", manifest["topology"])
    self.assertEqual(SOURCE_COMMIT, manifest["source_git_commit"])
    self.assertTrue((bundle / "database.sql").is_file())
    self.assertTrue((bundle / "media-snapshot.json").is_file())
    self.assertTrue((bundle / "SHA256SUMS").is_file())

  def test_the_bundle_verifies_through_the_shared_helper(self):
    completed, log, bundle = self.run_backup()
    self.assertEqual(0, completed.returncode, completed.stderr)

    verified = subprocess.run(
      [str(PYTHON_BIN), str(PROJECT_ROOT / "scripts" / "release_bundle.py"),
       "verify", str(bundle)],
      capture_output=True, text=True,
    )

    self.assertEqual(0, verified.returncode, verified.stderr)

  def test_the_writer_is_proven_stopped_before_anything_is_captured(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    ##
    ## The proof has to precede the capture, or it is proving something about a
    ## moment after the dump already started.
    ##
    self.assertLess(log.index("engine ps"), log.index("mysqldump"))

  def test_the_snapshot_records_the_hidden_recovery_state(self):
    completed, log, bundle = self.run_backup()
    self.assertEqual(0, completed.returncode, completed.stderr)

    document = json.loads(
      (bundle / "media-snapshot.json").read_text(encoding="utf-8")
    )
    paths = {entry["relative_path"] for entry in document["entries"]}

    self.assertIn("douyin/live/a.flv", paths)
    self.assertIn(".smsd-recording-recovery/k.json", paths)


class ExternalBackupWriterProofTest(ExternalBackupTestCase):
  ##
  ## A dump taken beside a live writer is a dump of a moment that never
  ## existed. A reflink snapshot taken beside one is worse: it clones each file
  ## at a slightly different instant, so the tree it captures never existed
  ## either, in a way no single file reveals.
  ##
  def test_a_still_running_writer_container_refuses_the_backup(self):
    completed, log, bundle = self.run_backup(running_container="still-here")

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("mysqldump", log, "a dump was taken beside a live writer")
    self.assertFalse((bundle / "database.sql").exists())

  def test_a_port_still_serving_refuses_the_backup(self):
    with socket.socket() as listener:
      listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      listener.bind(("127.0.0.1", 0))
      listener.listen(1)
      occupied = listener.getsockname()[1]

      completed, log, bundle = self.run_backup(port=occupied)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("mysqldump", log)


class ExternalBackupFailureTest(ExternalBackupTestCase):
  ##
  ## Every capture failure has to leave a bundle that cannot be restored from.
  ## A half-written bundle that still verifies is the one outcome worse than no
  ## bundle at all, because it will be trusted.
  ##
  def test_a_failed_dump_leaves_no_verifiable_bundle(self):
    completed, log, bundle = self.run_backup(dump_status=1)

    self.assertNotEqual(0, completed.returncode)
    self.assertFalse((bundle / "SHA256SUMS").exists())
    self.assertFalse((bundle / "manifest.json").exists())

  def test_a_failed_snapshot_leaves_no_verifiable_bundle(self):
    ##
    ## A snapshot root on a filesystem that cannot clone is refused by the
    ## snapshot helper, which must abort the whole backup rather than produce a
    ## bundle whose media half is missing.
    ##
    shared = Path("/dev/shm")
    if not shared.is_dir() or not os.access(shared, os.W_OK):
      self.skipTest("no second filesystem available")
    with tempfile.TemporaryDirectory(dir=shared) as elsewhere:
      completed, log, bundle = self.run_backup(
        snapshot_root=Path(elsewhere) / ".snapshots"
      )

    self.assertNotEqual(0, completed.returncode)
    self.assertFalse((bundle / "SHA256SUMS").exists())

  def test_a_schema_state_that_is_not_ready_refuses(self):
    completed, log, bundle = self.run_backup(
      migration="state=behind current=0002_x heads=0011_x"
    )

    self.assertNotEqual(0, completed.returncode)


class ExternalBackupSecretTest(ExternalBackupTestCase):
  def test_the_password_never_reaches_the_command_line_or_the_output(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    combined = log + completed.stdout + completed.stderr
    self.assertNotIn(SECRET_PASSWORD, combined)
    self.assertNotIn("MYSQL_PWD", combined)
    ##
    ## What travels is the path to an option file, never the value in it.
    ##
    self.assertIn("--defaults-extra-file=", log)

  def test_the_option_file_argument_is_first(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    for line in log.splitlines():
      if line.startswith("mysqldump "):
        arguments = line.split()[1:]
        self.assertTrue(
          arguments[0].startswith("--defaults-extra-file="),
          "mysqldump only honours the option file as its first argument",
        )

  def test_the_option_file_does_not_survive_the_backup(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    for line in log.splitlines():
      if "--defaults-extra-file=" in line:
        for argument in line.split():
          if argument.startswith("--defaults-extra-file="):
            path = Path(argument.split("=", 1)[1])
            self.assertFalse(
              path.exists(), "the credential file outlived the backup"
            )

  def test_a_group_readable_configuration_refuses(self):
    completed, log, bundle = self.run_backup(config_mode=0o644)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("mysqldump", log)

  def test_the_bundle_never_contains_the_configuration_or_a_credential(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    for path in bundle.iterdir():
      self.assertNotIn(path.name, ("config.yml", "my.cnf"))
      if path.suffix in (".json", ".sql"):
        self.assertNotIn(
          SECRET_PASSWORD, path.read_text(encoding="utf-8", errors="replace")
        )


if __name__ == "__main__":
  unittest.main()
