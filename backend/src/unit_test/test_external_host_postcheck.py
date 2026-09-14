##
## Proving the thing that started is the thing that was reviewed.
##
## The Compose postcheck asks for two containers and pins the MySQL image,
## because in that topology the database is part of the release. Here it is not:
## the MySQL is the host's, it predates this release and it will outlive it, so
## demanding a container for it would make the check fail on a correct
## deployment.
##
## What replaces it is stricter about the application, since the application is
## the only thing this release actually places: exact image identity, the
## revision it was built from, the dependency lock it was built against, the
## media root it is really serving, and a database it can really reach.
##
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
POSTCHECK_SCRIPT = PROJECT_ROOT / "scripts" / "release_external_postcheck.sh"

CANONICAL_IMAGE = "ghcr.io/example/socialmediastreamdownloader@sha256:" + "a" * 64
EXPECTED_REVISION = "b" * 40
EXPECTED_IMAGE_ID = "sha256:" + "c" * 64
EXPECTED_LOCK = "d" * 64


class ExternalPostcheckTest(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text(
      "#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8"
    )
    command.chmod(0o700)
    return command

  def run_postcheck(self, **overrides):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      calls = root / "calls.log"
      calls.touch()
      media = root / "media"
      media.mkdir()

      engine = self.make_command(
        root,
        "engine",
        textwrap.dedent(
          """\
          echo "engine $*" >> "$CALL_LOG"
          case "$*" in
            *".State.Running"*) printf '%s\\n' "${RUNNING:-true}" ;;
            *".Image}}"*) printf '%s\\n' "${RUNNING_IMAGE_ID:-$EXPECTED_IMAGE_ID}" ;;
            *".Id}}"*) printf '%s\\n' "$EXPECTED_IMAGE_ID" ;;
            *"org.opencontainers.image.revision"*) printf '%s\\n' "${IMAGE_REVISION:-$EXPECTED_REVISION}" ;;
            *"io.smsd.requirements.sha256"*) printf '%s\\n' "${LOCK_LABEL:-$EXPECTED_LOCK}" ;;
            *"Destination"*) printf '%s\\n' "${MEDIA_MOUNT:-$MEDIA_ROOT}" ;;
            "exec "*"migration_cli"*) printf '%s\\n' "${MIGRATION:-state=ready current=0011_x heads=0011_x}" ;;
            "exec "*) exit "${EXEC_STATUS:-0}" ;;
            *) exit 91 ;;
          esac
          """
        ),
      )
      curl = self.make_command(
        root,
        "curl",
        'echo "curl $*" >> "$CALL_LOG"\nexit "${HEALTH_STATUS:-0}"\n',
      )

      environment = dict(os.environ)
      environment.update({
        "CALL_LOG": str(calls),
        "ENGINE_BIN": str(engine),
        "CURL_BIN": str(curl),
        "EXPECTED_IMAGE_ID": EXPECTED_IMAGE_ID,
        "EXPECTED_REVISION": EXPECTED_REVISION,
        "EXPECTED_LOCK": EXPECTED_LOCK,
        "MEDIA_ROOT": str(media),
      })
      for key in (
        "RUNNING", "RUNNING_IMAGE_ID", "IMAGE_REVISION", "LOCK_LABEL",
        "MEDIA_MOUNT", "MIGRATION", "HEALTH_STATUS", "EXEC_STATUS",
      ):
        if key in overrides:
          environment[key] = str(overrides.pop(key))

      argv = [
        str(POSTCHECK_SCRIPT),
        "--health-url", "http://127.0.0.1:5000/",
        "--container-name", "smsd-app",
        "--expected-image", CANONICAL_IMAGE,
        "--expected-revision", EXPECTED_REVISION,
        "--expected-requirements-sha", EXPECTED_LOCK,
        "--media-root", str(media),
      ]
      self.assertEqual({}, overrides, "unused override")
      completed = subprocess.run(
        argv, capture_output=True, text=True, env=environment
      )
      return completed, calls.read_text(encoding="utf-8")

  def test_a_correct_deployment_passes(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)

  ##
  ## The point of the split: an external deployment has no MySQL container and
  ## must not be asked for one.
  ##
  def test_it_never_requires_a_database_container(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertNotIn("name=^mysql", log)
    self.assertNotIn("mysql:8.0", log)
    ##
    ## And every engine call is about the application container it was given.
    ## Without this the check passes even if the postcheck were quietly asking
    ## about a container named ``mysql`` instead - which is exactly the Compose
    ## assumption this topology has to drop.
    ##
    inspected = [
      line for line in log.splitlines()
      if line.startswith("engine inspect") or line.startswith("engine exec")
    ]
    self.assertTrue(inspected)
    for line in inspected:
      self.assertIn("smsd-app", line)

  def test_a_stopped_container_fails(self):
    completed, unused = self.run_postcheck(RUNNING="false")

    self.assertNotEqual(0, completed.returncode)

  def test_an_image_identity_mismatch_fails(self):
    completed, unused = self.run_postcheck(
      RUNNING_IMAGE_ID="sha256:" + "9" * 64
    )

    self.assertNotEqual(0, completed.returncode)

  def test_a_revision_mismatch_fails(self):
    completed, unused = self.run_postcheck(IMAGE_REVISION="f" * 40)

    self.assertNotEqual(0, completed.returncode)

  def test_a_requirements_mismatch_fails(self):
    completed, unused = self.run_postcheck(LOCK_LABEL="e" * 64)

    self.assertNotEqual(0, completed.returncode)

  def test_a_media_mount_pointing_somewhere_else_fails(self):
    completed, unused = self.run_postcheck(MEDIA_MOUNT="/somewhere/else")

    self.assertNotEqual(0, completed.returncode)

  def test_a_migration_state_that_is_not_ready_fails(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=behind current=0002_x heads=0011_x"
    )

    self.assertNotEqual(0, completed.returncode)

  def test_a_failing_health_endpoint_fails(self):
    completed, unused = self.run_postcheck(HEALTH_STATUS=7)

    self.assertNotEqual(0, completed.returncode)

  def test_it_checks_the_database_is_reachable_from_the_container(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("migration_cli", log)


if __name__ == "__main__":
  unittest.main()
