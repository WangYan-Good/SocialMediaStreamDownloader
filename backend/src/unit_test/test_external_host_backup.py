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
import sys
import tempfile
import textwrap
import unittest

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKUP_SCRIPT = PROJECT_ROOT / "scripts" / "release_external_backup.sh"
##
## The interpreter running these tests, not a checked-in virtualenv path.
## A hard-coded ``venv/bin/python`` exists on a developer machine and on no
## CI runner, where it fails as "the configuration file must be a 0600
## regular file" - the inner check never ran, and the script reported the
## refusal it falls back to.
##
PYTHON_BIN = sys.executable

SECRET_PASSWORD = "SECRET_BACKUP_DB_PASSWORD_P19"
CANONICAL_IMAGE = "ghcr.io/wangyan-good/socialmediastreamdownloader@sha256:" + "a" * 64
SOURCE_COMMIT = "c" * 40
##
## What the shared fixture's configuration names. The backup resolves the
## database from that file and from nowhere else, so this is what every
## artefact in a correct bundle has to say.
##
CONFIGURED_DATABASE = unified_config()["database"]["name"]


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
          ##
          ## The release image's own labels, which the backup now checks before
          ## it reads the operator's configuration.
          ##
          *"org.opencontainers.image.revision"*) printf '%s\\n' "$IMAGE_REVISION" ;;
          *"io.smsd.requirements.sha256"*) printf '%s\\n' "$LOCK_LABEL" ;;
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

    ##
    ## A lock of its own, so the label the image claims can be compared against
    ## something this test controls rather than against the repository's.
    ##
    requirements = root / "requirements.txt"
    requirements.write_text(
      "example==1.0 --hash=sha256:" + "d" * 64 + "\n", encoding="utf-8"
    )
    lock_sha = hashlib.sha256(requirements.read_bytes()).hexdigest()

    environment = dict(os.environ)
    environment.update({
      "CALL_LOG": str(calls),
      "ENGINE_BIN": str(engine),
      "MYSQLDUMP_BIN": str(mysqldump),
      "PYTHON_BIN": str(PYTHON_BIN),
      "REQUIREMENTS_FILE": str(requirements),
      "RUNNING_CONTAINER": overrides.pop("running_container", ""),
      "IMAGE_REVISION": overrides.pop("image_revision", SOURCE_COMMIT),
      "LOCK_LABEL": overrides.pop("lock_label", lock_sha),
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
      "--media-root", str(media),
      "--snapshot-root", str(snapshot_root),
      "--container-name", "smsd-app",
      "--port", str(overrides.pop("port", self.free_port())),
      "--image", str(overrides.pop("image", CANONICAL_IMAGE)),
      "--db-host", "host.containers.internal",
      "--source-git-commit", SOURCE_COMMIT,
    ]
    ##
    ## The configuration is the authority. ``--database`` is written only when a
    ## test is about what happens when an operator names one.
    ##
    declared = overrides.pop("declared_database", CONFIGURED_DATABASE)
    if declared is not None:
      argv += ["--database", declared]
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


##
## >>=============== one database, named by one authority ===============>>
##
## The schema status comes from the migration CLI, which reads the canonical
## configuration. The dump used to take whatever an operator typed. Those are
## two different questions that looked like one answer, and a bundle built from
## both carries a manifest describing one database and rows from another -
## internally consistent, and wrong in a way nothing downstream can detect.
##
class ExternalBackupDatabaseIdentityTest(ExternalBackupTestCase):
  def test_the_configured_database_is_what_gets_dumped(self):
    completed, log, bundle = self.run_backup(declared_database=None)

    self.assertEqual(0, completed.returncode, completed.stderr)
    dumps = [line for line in log.splitlines() if line.startswith("mysqldump")]
    self.assertEqual(1, len(dumps))
    self.assertTrue(dumps[0].endswith(" " + CONFIGURED_DATABASE), dumps[0])

  def test_a_database_the_configuration_does_not_name_is_refused(self):
    completed, log, bundle = self.run_backup(
      declared_database="social_media_stream_downloader_v2"
    )

    self.assertNotEqual(0, completed.returncode)
    ##
    ## Refused before the capture: no credential staged, no dump, no clone.
    ## Grants are irrelevant here precisely because no connection is ever opened
    ## - an account with ``*.*`` cannot talk its way past a check that happens
    ## before the client runs.
    ##
    ## The engine has been used by this point, and only for the image: its
    ## identity is settled before the configuration is read at all, which is a
    ## stricter ordering than this test originally described.
    ##
    self.assertNotIn("mysqldump", log)
    self.assertNotIn("/run/secrets/config.yml", log)
    for line in log.splitlines():
      self.assertIn("image inspect", line.replace("engine pull", "image inspect"))
    self.assertFalse(bundle.exists())

  def test_the_manifest_cannot_name_a_database_the_dump_did_not_capture(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    dumps = [line for line in log.splitlines() if line.startswith("mysqldump")]
    self.assertEqual(CONFIGURED_DATABASE, manifest["database_name"])
    self.assertTrue(dumps[0].endswith(" " + manifest["database_name"]))

  ##
  ## And the schema status is read about that same database, because the only
  ## thing the status container is given is the same configuration file.
  ##
  def test_the_schema_status_is_read_from_the_same_configuration(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    status = [line for line in log.splitlines() if "migration_cli" in line]
    self.assertEqual(1, len(status))
    self.assertIn("/run/secrets/config.yml:ro", status[0])
    ##
    ## Nothing may redirect it at another database on the way in.
    ##
    self.assertNotIn("SMSD_DB_NAME", status[0])
    self.assertNotIn("--database", status[0])

  def test_a_configuration_naming_no_database_is_refused(self):
    temporary = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, temporary, True)
    nameless = Path(temporary) / "config.yml"
    document = unified_config()
    document["database"]["name"] = ""
    nameless.write_text(yaml.safe_dump(document), encoding="utf-8")
    nameless.chmod(0o600)

    completed, log, bundle = self.run_backup(
      config_file=nameless, declared_database=None
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("mysqldump", log)


##
## >>=============== the image is settled before the secret moves ===============>>
##
## The backup mounts the operator's configuration - the file holding the
## production database password - into the image, and then runs the image's own
## code against the production database. So which image it is has to be decided
## first, and by digest: a tag is a name whoever controls the registry can
## repoint after the review, and repointing it hands over the credential.
##
class ExternalBackupImageTrustTest(ExternalBackupTestCase):
  def test_a_mutable_tag_is_refused(self):
    for reference in (
      "ghcr.io/wangyan-good/socialmediastreamdownloader:latest",
      "ghcr.io/wangyan-good/socialmediastreamdownloader:sha-abcdef",
    ):
      with self.subTest(image=reference):
        completed, log, bundle = self.run_backup(image=reference)

        self.assertNotEqual(0, completed.returncode)
        self.assertEqual("", log, "the engine was used before the image was settled")
        self.assertFalse(bundle.exists())

  def test_another_repositorys_digest_is_refused(self):
    completed, log, bundle = self.run_backup(
      image="ghcr.io/example/socialmediastreamdownloader@sha256:" + "a" * 64
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertEqual("", log)

  def test_a_malformed_digest_is_refused(self):
    completed, log, bundle = self.run_backup(
      image="ghcr.io/wangyan-good/socialmediastreamdownloader@sha256:deadbeef"
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertEqual("", log)

  ##
  ## The commit the bundle records must be the commit the image was built from,
  ## or the manifest names a revision nothing in the bundle came from.
  ##
  def test_a_revision_label_that_is_not_the_recorded_commit_is_refused(self):
    completed, log, bundle = self.run_backup(image_revision="f" * 40)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("mysqldump", log)
    self.assertFalse(bundle.exists())

  def test_a_requirements_label_mismatch_is_refused(self):
    completed, log, bundle = self.run_backup(lock_label="e" * 64)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("mysqldump", log)

  ##
  ## And all of it happens before the configuration is even read, let alone
  ## mounted into the image.
  ##
  def test_the_image_is_settled_before_the_configuration_is_touched(self):
    completed, log, bundle = self.run_backup()

    self.assertEqual(0, completed.returncode, completed.stderr)
    lines = log.splitlines()
    first_label = next(
      i for i, line in enumerate(lines) if "image inspect" in line
    )
    first_mount = next(
      i for i, line in enumerate(lines) if "/run/secrets/config.yml" in line
    )
    self.assertLess(first_label, first_mount)


if __name__ == "__main__":
  unittest.main()
