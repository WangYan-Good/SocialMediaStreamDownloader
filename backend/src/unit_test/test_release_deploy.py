import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "release_deploy.sh"
CANONICAL_IMAGE = "ghcr.io/example/socialmediastreamdownloader@sha256:" + "a" * 64
EXPECTED_REVISION = "b" * 40
EXPECTED_IMAGE_ID = "sha256:" + "c" * 64


class ReleaseDeployTest(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8")
    command.chmod(0o700)
    return command

  def run_deploy(
    self,
    *,
    image=CANONICAL_IMAGE,
    revision=EXPECTED_REVISION,
    image_revision=EXPECTED_REVISION,
    lock_label=None,
    running_image_id=EXPECTED_IMAGE_ID,
  ):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      calls = root / "calls.log"
      requirements = root / "requirements.txt"
      requirements.write_text(
        "example==1.0 --hash=sha256:" + "d" * 64 + "\n", encoding="utf-8"
      )
      lock_sha = hashlib.sha256(requirements.read_bytes()).hexdigest()
      docker = self.make_command(
        root,
        "docker",
        textwrap.dedent(
          """\
          echo "docker $*" >> "$CALL_LOG"
          case "$*" in
            "pull "*) exit 0 ;;
            *"org.opencontainers.image.revision"*) printf '%s\n' "$IMAGE_REVISION" ;;
            *"io.smsd.requirements.sha256"*) printf '%s\n' "$LOCK_LABEL" ;;
            "image inspect "*) printf '%s\n' "$EXPECTED_IMAGE_ID" ;;
            *"app-id") printf '%s\n' "$RUNNING_IMAGE_ID" ;;
            *) exit 91 ;;
          esac
          """
        ),
      )
      run_docker = self.make_command(
        root,
        "run-docker",
        textwrap.dedent(
          """\
          echo "compose $* image=${SMSD_IMAGE:-}" >> "$CALL_LOG"
          case "$*" in
            *"up -d --no-build") exit 0 ;;
            *"ps -q app") printf '%s\n' app-id ;;
            *) exit 92 ;;
          esac
          """
        ),
      )
      postcheck = self.make_command(
        root,
        "postcheck",
        'echo "postcheck $*" >> "$CALL_LOG"\n',
      )
      environment = os.environ.copy()
      environment.update(
        {
          "CALL_LOG": str(calls),
          "DOCKER_BIN": str(docker),
          "RUN_DOCKER_SCRIPT": str(run_docker),
          "POSTCHECK_SCRIPT": str(postcheck),
          "REQUIREMENTS_FILE": str(requirements),
          "IMAGE_REVISION": image_revision,
          "LOCK_LABEL": lock_label or lock_sha,
          "EXPECTED_IMAGE_ID": EXPECTED_IMAGE_ID,
          "RUNNING_IMAGE_ID": running_image_id,
        }
      )
      result = subprocess.run(
        [
          "bash",
          str(DEPLOY_SCRIPT),
          "--image",
          image,
          "--expected-revision",
          revision,
          "--project-name",
          "smsd-release",
          "--health-url",
          "http://127.0.0.1:5000/",
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        text=True,
        capture_output=True,
      )
      recorded = calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []
      return result, recorded, lock_sha

  def test_r1_canonical_digest_is_pulled_verified_and_deployed(self):
    result, calls, lock_sha = self.run_deploy()

    self.assertEqual(0, result.returncode, result.stderr)
    self.assertEqual(f"docker pull {CANONICAL_IMAGE}", calls[0])
    self.assertTrue(any("compose -p smsd-release up -d --no-build" in call for call in calls))
    self.assertTrue(any(f"image={CANONICAL_IMAGE}" in call for call in calls))
    self.assertTrue(any(f"--expected-revision {EXPECTED_REVISION}" in call for call in calls if call.startswith("postcheck ")))
    self.assertTrue(any(f"--expected-requirements-sha {lock_sha}" in call for call in calls if call.startswith("postcheck ")))

  def test_r2_r3_tag_only_and_local_images_are_rejected_before_transport(self):
    for image in ("ghcr.io/example/smsd:latest", "smsd:local", EXPECTED_IMAGE_ID, ""):
      with self.subTest(image=image):
        result, calls, _ = self.run_deploy(image=image)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("canonical lowercase GHCR digest", result.stderr)
        self.assertEqual([], calls)

  def test_r4_malformed_expected_revision_is_rejected(self):
    result, calls, _ = self.run_deploy(revision="main")
    self.assertNotEqual(0, result.returncode)
    self.assertIn("expected revision must be a 40-character SHA", result.stderr)
    self.assertEqual([], calls)

  def test_r5_revision_label_mismatch_stops_before_compose_up(self):
    result, calls, _ = self.run_deploy(image_revision="e" * 40)
    self.assertNotEqual(0, result.returncode)
    self.assertIn("revision label mismatch", result.stderr)
    self.assertFalse(any(call.startswith("compose ") for call in calls))

  def test_r6_requirements_label_mismatch_stops_before_compose_up(self):
    result, calls, _ = self.run_deploy(lock_label="f" * 64)
    self.assertNotEqual(0, result.returncode)
    self.assertIn("requirements label mismatch", result.stderr)
    self.assertFalse(any(call.startswith("compose ") for call in calls))

  def test_r7_r8_r9_deploy_pulls_exactly_and_never_builds(self):
    result, calls, _ = self.run_deploy()
    self.assertEqual(0, result.returncode, result.stderr)
    self.assertEqual(1, sum(call == f"docker pull {CANONICAL_IMAGE}" for call in calls))
    self.assertTrue(any("up -d --no-build" in call for call in calls))
    self.assertFalse(any(" build" in call or "--build" in call.replace("--no-build", "") for call in calls))

  def test_r10_running_container_image_id_mismatch_is_a_hard_failure(self):
    result, calls, _ = self.run_deploy(running_image_id="sha256:" + "0" * 64)
    self.assertNotEqual(0, result.returncode)
    self.assertIn("running application image ID mismatch", result.stderr)
    self.assertFalse(any(call.startswith("postcheck ") for call in calls))


if __name__ == "__main__":
  unittest.main()
