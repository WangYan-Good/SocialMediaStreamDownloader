##
## Starting the production application against the production that exists.
##
## The Compose deployment brings its own database and its own volume, so it can
## afford to create what it needs. This one cannot create anything: the MySQL is
## already there with two years of rows in it, the media tree is terabytes at a
## path the database refers to by name, and the application it replaces is still
## running and still writing.
##
## Everything below is therefore a refusal before it is an action. The script's
## job is to prove it is allowed to start before it starts anything, because the
## failure it must never produce is two writers.
##
import hashlib
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import textwrap
import unittest

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "release_external_deploy.sh"

CANONICAL_IMAGE = "ghcr.io/example/socialmediastreamdownloader@sha256:" + "a" * 64
EXPECTED_REVISION = "b" * 40
EXPECTED_IMAGE_ID = "sha256:" + "c" * 64


class ExternalDeployTestCase(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text(
      "#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8"
    )
    command.chmod(0o700)
    return command

  ##
  ## One engine stub standing in for rootless Podman. It records every
  ## invocation, so a test can assert on what the script *did not* pass just as
  ## easily as on what it did.
  ##
  def engine_stub(self, root: Path) -> Path:
    return self.make_command(
      root,
      "engine",
      textwrap.dedent(
        """\
        echo "engine $*" >> "$CALL_LOG"
        case "$1 ${2:-}" in
          "pull "*) exit 0 ;;
          "image inspect")
            case "$*" in
              *"org.opencontainers.image.revision"*)
                printf '%s\\n' "$IMAGE_REVISION" ;;
              *"io.smsd.requirements.sha256"*)
                printf '%s\\n' "$LOCK_LABEL" ;;
              *) printf '%s\\n' "$EXPECTED_IMAGE_ID" ;;
            esac ;;
          "ps "*) printf '%s' "${EXISTING_CONTAINER:-}" ;;
          "run "*) printf '%s\\n' container-id ;;
          "inspect"*) printf '%s\\n' "${RUNNING_IMAGE_ID:-$EXPECTED_IMAGE_ID}" ;;
          "rm "*) exit 0 ;;
          *) exit 91 ;;
        esac
        """
      ),
    )

  ##
  ## A port nothing is listening on. The default must never be 5000: that is
  ## the real production port on the host these tests run on, and borrowing it
  ## would make the happy path fail for the right reason at the wrong time.
  ##
  def free_port(self) -> int:
    with socket.socket() as probe:
      probe.bind(("127.0.0.1", 0))
      return probe.getsockname()[1]

  def run_deploy(self, **overrides):
    overrides.setdefault("port", self.free_port())
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      calls = root / "calls.log"
      calls.touch()

      requirements = root / "requirements.txt"
      requirements.write_text(
        "example==1.0 --hash=sha256:" + "d" * 64 + "\n", encoding="utf-8"
      )
      lock_sha = hashlib.sha256(requirements.read_bytes()).hexdigest()

      config = root / "config.yml"
      document = unified_config()
      document["database"]["host"] = "localhost"
      document["download"]["save_path"] = str(root / "media")
      config.write_text(yaml.safe_dump(document), encoding="utf-8")
      config.chmod(overrides.pop("config_mode", 0o600))

      media = root / "media"
      media.mkdir(exist_ok=True)

      postcheck = self.make_command(
        root, "postcheck", 'echo "postcheck $*" >> "$CALL_LOG"\nexit 0\n'
      )
      engine = self.engine_stub(root)

      environment = dict(os.environ)
      environment.update({
        "CALL_LOG": str(calls),
        "ENGINE_BIN": str(engine),
        "REQUIREMENTS_FILE": str(requirements),
        "EXTERNAL_POSTCHECK_SCRIPT": str(postcheck),
        "EXPECTED_IMAGE_ID": EXPECTED_IMAGE_ID,
        "IMAGE_REVISION": overrides.pop("image_revision", EXPECTED_REVISION),
        "LOCK_LABEL": overrides.pop("lock_label", lock_sha),
        "EXISTING_CONTAINER": overrides.pop("existing_container", ""),
        "RUNNING_IMAGE_ID": overrides.pop(
          "running_image_id", EXPECTED_IMAGE_ID
        ),
      })

      argv = [
        str(DEPLOY_SCRIPT),
        "--image", overrides.pop("image", CANONICAL_IMAGE),
        "--expected-revision", overrides.pop("revision", EXPECTED_REVISION),
        "--container-name", overrides.pop("container_name", "smsd-app"),
        "--config-file", str(overrides.pop("config_file", config)),
        "--media-root", str(overrides.pop("media_root", media)),
        "--db-host", overrides.pop("db_host", "host.containers.internal"),
        "--port", str(overrides.pop("port", 5000)),
        "--health-url", "http://127.0.0.1:5000/",
      ]
      for extra in overrides.pop("extra", []):
        argv.append(extra)
      self.assertEqual({}, overrides, "unused override")

      completed = subprocess.run(
        argv, capture_output=True, text=True, env=environment
      )
      return completed, calls.read_text(encoding="utf-8")


class ExternalDeployIdentityTest(ExternalDeployTestCase):
  def test_a_correct_invocation_starts_the_container_and_postchecks(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("engine run", log)
    self.assertIn("postcheck", log)

  def test_a_tag_is_refused_as_release_authority(self):
    for reference in (
      "ghcr.io/example/socialmediastreamdownloader:latest",
      "ghcr.io/example/socialmediastreamdownloader:sha-abcdef",
      "socialmediastreamdownloader@sha256:" + "a" * 64,
    ):
      with self.subTest(image=reference):
        completed, log = self.run_deploy(image=reference)

        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn("engine run", log, "a container was started anyway")

  def test_a_revision_label_mismatch_refuses_before_starting(self):
    completed, log = self.run_deploy(image_revision="f" * 40)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_a_requirements_label_mismatch_refuses_before_starting(self):
    completed, log = self.run_deploy(lock_label="e" * 64)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_a_running_image_that_is_not_the_pulled_one_fails(self):
    completed, log = self.run_deploy(running_image_id="sha256:" + "9" * 64)

    self.assertNotEqual(0, completed.returncode)


class ExternalDeploySingleWriterTest(ExternalDeployTestCase):
  ##
  ## The invariant the whole phase exists to protect. Two writers against one
  ## database and one media tree is the one outcome from which there is no
  ## clean rollback.
  ##
  def test_an_existing_container_of_the_same_name_refuses(self):
    completed, log = self.run_deploy(existing_container="already-running")

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log, "a second writer was started")

  def test_an_occupied_production_port_refuses(self):
    ##
    ## A real listener rather than a stubbed answer: the old bare-metal writer
    ## holding the port is precisely the condition this must detect, and it
    ## holds a real socket.
    ##
    with socket.socket() as listener:
      listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      listener.bind(("127.0.0.1", 0))
      listener.listen(1)
      occupied = listener.getsockname()[1]

      completed, log = self.run_deploy(port=occupied)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log, "a second writer was started")


class ExternalDeploySafetyTest(ExternalDeployTestCase):
  def test_a_group_readable_configuration_refuses(self):
    ##
    ## Production's file is 0644 today and holds the database password.
    ##
    completed, log = self.run_deploy(config_mode=0o644)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_a_missing_media_root_refuses(self):
    with tempfile.TemporaryDirectory() as directory:
      completed, log = self.run_deploy(
        media_root=Path(directory) / "absent"
      )

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_the_filesystem_root_is_never_bind_mounted(self):
    completed, log = self.run_deploy(media_root=Path("/"))

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  ##
  ## The cpu controller is not delegated to a rootless user slice on this host,
  ## so a ``--cpus`` request cannot be honoured. Silently dropping it would be
  ## the worst answer: the operator would believe a limit is in force.
  ##
  def test_a_cpu_limit_request_is_refused_rather_than_ignored(self):
    completed, log = self.run_deploy(extra=["--cpus", "4.0"])

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_no_cpu_limit_is_ever_passed_to_the_engine(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertNotIn("--cpus", log)

  def test_a_memory_limit_is_passed_through(self):
    completed, log = self.run_deploy(extra=["--memory", "2g"])

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("--memory", log)

  ##
  ## The address is not a secret and travels as an environment value. The
  ## password is, and has no argument to travel through at all.
  ##
  def test_the_database_address_is_passed_but_never_the_password(self):
    completed, log = self.run_deploy(db_host="10.88.0.1")

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("SMSD_DB_HOST=10.88.0.1", log)
    combined = log + completed.stdout + completed.stderr
    self.assertNotIn(unified_config()["database"]["password"], combined)
    self.assertNotIn("SMSD_DB_PASSWORD", combined)

  def test_the_container_is_never_privileged_and_mounts_no_engine_socket(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    for forbidden in ("--privileged", "docker.sock", "podman.sock", "-v /:"):
      self.assertNotIn(forbidden, log)


if __name__ == "__main__":
  unittest.main()
