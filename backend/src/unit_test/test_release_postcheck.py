import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / "scripts" / "release_postcheck.sh"


class ReleasePostcheckTest(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text("#!/usr/bin/env bash\nset -eu\n" + body, encoding="utf-8")
    command.chmod(0o700)
    return command

  def run_postcheck(
    self,
    *,
    status=None,
    check=None,
    curl_code=0,
    compose=False,
    identity=False,
    running_image_id="sha256:" + "a" * 64,
    revision_label="b" * 40,
    requirements_label="c" * 64,
    mysql_config_image="mysql:8.0.46@sha256:" + "d" * 64,
  ):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      log = root / "calls.log"
      python = self.make_command(
        root,
        "python",
        textwrap.dedent(
          f"""\
          echo "python $*" >> "$CALL_LOG"
          case "$*" in
            *"migration_cli status") printf '%s\\n' "${{STATUS_OUTPUT}}" ;;
            *"migration_cli check") printf '%s\\n' "${{CHECK_OUTPUT}}" ;;
            *) exit 91 ;;
          esac
          """
        ),
      )
      curl = self.make_command(
        root,
        "curl",
        'echo "curl $*" >> "$CALL_LOG"\nexit "${CURL_CODE}"\n',
      )
      run_docker = self.make_command(
        root,
        "run-docker",
        textwrap.dedent(
          """\
          echo "compose $*" >> "$CALL_LOG"
          case "$*" in
            *"exec -T app python -m backend.src.database.migration_cli status")
              printf '%s\n' "$STATUS_OUTPUT" ;;
            *"exec -T app python -m backend.src.database.migration_cli check")
              printf '%s\n' "$CHECK_OUTPUT" ;;
            *"ps -q app") printf '%s\n' app-id ;;
            *"ps -q mysql") printf '%s\n' mysql-id ;;
            *) exit 92 ;;
          esac
          """
        ),
      )
      docker = self.make_command(
        root,
        "docker",
        textwrap.dedent(
          """\
          echo "docker $*" >> "$CALL_LOG"
          case "$*" in
            *"org.opencontainers.image.revision"*) printf '%s\n' "$REVISION_LABEL" ;;
            *"io.smsd.requirements.sha256"*) printf '%s\n' "$REQUIREMENTS_LABEL" ;;
            "image inspect "*) printf '%s\n' "$EXPECTED_IMAGE_ID" ;;
            *".Image"*"app-id") printf '%s\n' "$RUNNING_IMAGE_ID" ;;
            *".Config.Image"*"mysql-id") printf '%s\n' "$MYSQL_CONFIG_IMAGE" ;;
            *"app-id") printf '%s\n' "${APP_RUNNING:-true}" ;;
            *"mysql-id") printf '%s\n' "${MYSQL_HEALTH:-healthy}" ;;
            *) exit 93 ;;
          esac
          """
        ),
      )
      environment = os.environ.copy()
      environment.update(
        {
          "CALL_LOG": str(log),
          "STATUS_OUTPUT": status
          or "state=ready current=head-revision heads=head-revision",
          "CHECK_OUTPUT": check or "managed schema is compatible",
          "CURL_CODE": str(curl_code),
          "PYTHON_BIN": str(python),
          "CURL_BIN": str(curl),
          "DOCKER_BIN": str(docker),
          "RUN_DOCKER_SCRIPT": str(run_docker),
          "EXPECTED_IMAGE_ID": "sha256:" + "a" * 64,
          "RUNNING_IMAGE_ID": running_image_id,
          "REVISION_LABEL": revision_label,
          "REQUIREMENTS_LABEL": requirements_label,
          "MYSQL_CONFIG_IMAGE": mysql_config_image,
        }
      )
      arguments = ["bash", str(SCRIPT), "--health-url", "http://127.0.0.1/health"]
      if compose:
        arguments.extend(["--project-name", "smsd-release-test"])
      if identity:
        arguments.extend(
          [
            "--expected-image",
            "ghcr.io/example/smsd@sha256:" + "e" * 64,
            "--expected-revision",
            "b" * 40,
            "--expected-requirements-sha",
            "c" * 64,
            "--expected-mysql-image",
            "mysql:8.0.46@sha256:" + "d" * 64,
          ]
        )
      result = subprocess.run(
        arguments,
        cwd=PROJECT_ROOT,
        env=environment,
        text=True,
        capture_output=True,
      )
      calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
      return result, calls

  def test_host_postcheck_orders_schema_status_check_then_http(self):
    result, calls = self.run_postcheck()

    self.assertEqual(0, result.returncode, result.stderr)
    self.assertIn("ok   release post-upgrade verification", result.stdout)
    self.assertEqual(
      [
        "python -m backend.src.database.migration_cli status",
        "python -m backend.src.database.migration_cli check",
        "curl -fsS http://127.0.0.1/health",
      ],
      calls,
    )

  def test_schema_not_ready_is_a_hard_failure_before_http(self):
    result, calls = self.run_postcheck(
      status="state=behind current=old heads=head-revision"
    )

    self.assertNotEqual(0, result.returncode)
    self.assertFalse(any(call.startswith("curl ") for call in calls))

  def test_schema_check_or_http_failure_is_nonzero(self):
    incompatible, _ = self.run_postcheck(check="missing managed column")
    unavailable, _ = self.run_postcheck(curl_code=22)

    self.assertNotEqual(0, incompatible.returncode)
    self.assertNotEqual(0, unavailable.returncode)

  def test_compose_postcheck_requires_running_app_and_healthy_mysql(self):
    success, calls = self.run_postcheck(compose=True)

    self.assertEqual(0, success.returncode, success.stderr)
    self.assertTrue(any("ps -q app" in call for call in calls))
    self.assertTrue(any("ps -q mysql" in call for call in calls))
    self.assertTrue(any("app-id" in call for call in calls))
    self.assertTrue(any("mysql-id" in call for call in calls))

  def test_release_identity_checks_exact_app_labels_and_mysql_reference(self):
    result, calls = self.run_postcheck(compose=True, identity=True)

    self.assertEqual(0, result.returncode, result.stderr)
    self.assertTrue(any(call.startswith("docker image inspect ") for call in calls))
    self.assertTrue(any(".Image" in call and "app-id" in call for call in calls))
    self.assertTrue(any("org.opencontainers.image.revision" in call for call in calls))
    self.assertTrue(any("io.smsd.requirements.sha256" in call for call in calls))
    self.assertTrue(any(".Config.Image" in call and "mysql-id" in call for call in calls))

  def test_release_identity_mismatch_is_a_hard_failure(self):
    cases = (
      {"running_image_id": "sha256:" + "f" * 64},
      {"revision_label": "0" * 40},
      {"requirements_label": "1" * 64},
      {"mysql_config_image": "mysql:8.0.45@sha256:" + "2" * 64},
    )
    for mismatch in cases:
      with self.subTest(mismatch=mismatch):
        result, _ = self.run_postcheck(compose=True, identity=True, **mismatch)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("release identity", result.stderr)


if __name__ == "__main__":
  unittest.main()
