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

  def run_postcheck(self, *, status=None, check=None, curl_code=0, compose=False):
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
        }
      )
      arguments = ["bash", str(SCRIPT), "--health-url", "http://127.0.0.1/health"]
      if compose:
        arguments.extend(["--project-name", "smsd-release-test"])
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


if __name__ == "__main__":
  unittest.main()
