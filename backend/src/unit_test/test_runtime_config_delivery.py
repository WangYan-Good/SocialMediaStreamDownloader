import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import call, patch

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_CONFIG_SCRIPT = PROJECT_ROOT / "scripts" / "runtime_config.py"
RUN_DOCKER_SCRIPT = PROJECT_ROOT / "run-docker.sh"
RUN_SERVER_SCRIPT = PROJECT_ROOT / "run-server.sh"
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
DOCKERIGNORE_FILE = PROJECT_ROOT / ".dockerignore"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"


class RuntimeConfigDeliveryTest(unittest.TestCase):
  def load_runtime_config_module(self):
    if not RUNTIME_CONFIG_SCRIPT.is_file():
      self.fail("runtime configuration helper is not available")
    spec = importlib.util.spec_from_file_location(
      "smsd_runtime_config", RUNTIME_CONFIG_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

  def compose_config(self):
    config = unified_config()
    config["server"]["port"] = 5123
    config["database"].update({
      "name": "smsd_test",
      "port": 33306,
      "username": "smsd_test_user",
      "password": "db-pass-for-test",
    })
    return config

  def test_compose_environment_is_derived_into_a_private_file(self):
    runtime_config = self.load_runtime_config_module()

    with tempfile.TemporaryDirectory() as temp_directory:
      output_path = Path(temp_directory) / "compose.env"
      runtime_config.write_compose_environment(
        self.compose_config(), output_path
      )
      output = output_path.read_text(encoding="utf-8")
      mode = stat.S_IMODE(output_path.stat().st_mode)

    self.assertEqual(mode, 0o600)
    self.assertEqual(
      output.splitlines(),
      [
        "SMSD_SERVER_PORT=5123",
        "SMSD_DB_PORT=33306",
        "SMSD_DB_NAME='smsd_test'",
        "SMSD_DB_USER='smsd_test_user'",
        "SMSD_DB_PASSWORD='db-pass-for-test'",
      ],
    )

  def test_invalid_yaml_fails_without_echoing_configuration_values(self):
    runtime_config = self.load_runtime_config_module()
    secret_marker = "MUST_NOT_BE_PRINTED"

    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config_path.write_text(
        f"database:\n  password: {secret_marker}\nserver: [invalid\n",
        encoding="utf-8",
      )
      stdout = io.StringIO()
      stderr = io.StringIO()
      with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        status = runtime_config.main(["validate"], config_path=config_path)

    visible_output = stdout.getvalue() + stderr.getvalue()
    self.assertEqual(status, 1)
    self.assertIn("config/config.yml is missing or invalid", visible_output)
    self.assertNotIn(secret_marker, visible_output)

  def test_docker_wrapper_cleans_its_private_derived_environment(self):
    missing_artifacts = [
      path for path in (RUNTIME_CONFIG_SCRIPT, RUN_DOCKER_SCRIPT)
      if not path.is_file()
    ]
    if missing_artifacts:
      self.fail(f"Docker wrapper artifacts are unavailable: {missing_artifacts}")

    with tempfile.TemporaryDirectory() as temp_directory:
      project = Path(temp_directory) / "project"
      scripts = project / "scripts"
      config_directory = project / "config"
      fake_bin = project / "fake-bin"
      temp_files = project / "tmp"
      for directory in (scripts, config_directory, fake_bin, temp_files):
        directory.mkdir(parents=True, exist_ok=True)

      shutil.copy2(RUNTIME_CONFIG_SCRIPT, scripts / "runtime_config.py")
      shutil.copy2(RUN_DOCKER_SCRIPT, project / "run-docker.sh")
      (project / "docker-compose.yml").write_text(
        "services:\n  app:\n    image: scratch\n",
        encoding="utf-8",
      )
      (config_directory / "config.yml").write_text(
        yaml.safe_dump(self.compose_config(), sort_keys=False),
        encoding="utf-8",
      )

      record_path = project / "docker-record.json"
      fake_docker = fake_bin / "docker"
      fake_docker.write_text(
        """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import stat
import sys

arguments = sys.argv[1:]
env_index = arguments.index("--env-file") + 1
env_path = Path(arguments[env_index])
record = {
  "arguments": arguments,
  "env_path": str(env_path),
  "env_mode": stat.S_IMODE(env_path.stat().st_mode),
  "env_content": env_path.read_text(encoding="utf-8"),
  "inherited_server_port": os.environ.get("SMSD_SERVER_PORT"),
}
Path(os.environ["FAKE_DOCKER_RECORD"]).write_text(
  json.dumps(record), encoding="utf-8"
)
""",
        encoding="utf-8",
      )
      fake_docker.chmod(0o755)

      environment = os.environ.copy()
      environment.update({
        "PATH": f"{fake_bin}{os.pathsep}{environment['PATH']}",
        "PYTHON_BIN": sys.executable,
        "TMPDIR": str(temp_files),
        "FAKE_DOCKER_RECORD": str(record_path),
        "SMSD_SERVER_PORT": "9999",
      })
      try:
        result = subprocess.run(
          [str(project / "run-docker.sh"), "config"],
          cwd=project,
          env=environment,
          capture_output=True,
          text=True,
          check=False,
        )
      except OSError as error:
        self.fail(f"Docker wrapper is not executable: {error}")
      if result.returncode != 0:
        self.fail(
          f"Docker wrapper failed: stdout={result.stdout!r}, "
          f"stderr={result.stderr!r}"
        )
      record = json.loads(record_path.read_text(encoding="utf-8"))

      self.assertEqual(record["env_mode"], 0o600)
      self.assertIn("SMSD_SERVER_PORT=5123", record["env_content"])
      self.assertIsNone(record["inherited_server_port"])
      self.assertEqual(record["arguments"][0:2], ["compose", "--env-file"])
      self.assertEqual(record["arguments"][-1], "config")
      self.assertFalse(Path(record["env_path"]).exists())

  def test_container_config_is_staged_privately_from_the_read_only_mount(self):
    runtime_config = self.load_runtime_config_module()
    self.assertTrue(
      hasattr(runtime_config, "stage_container_config"),
      "container configuration staging is not implemented",
    )

    with tempfile.TemporaryDirectory() as temp_directory:
      temporary_root = Path(temp_directory)
      source_path = temporary_root / "secrets" / "config.yml"
      target_path = temporary_root / "app" / "config" / "config.yml"
      source_path.parent.mkdir()
      target_path.parent.mkdir(parents=True)
      config_text = yaml.safe_dump(self.compose_config(), sort_keys=False)
      source_path.write_text(config_text, encoding="utf-8")
      source_path.chmod(0o600)

      runtime_config.stage_container_config(
        source_path,
        target_path,
        os.getuid(),
        os.getgid(),
      )

      self.assertEqual(target_path.read_text(encoding="utf-8"), config_text)
      self.assertEqual(stat.S_IMODE(target_path.stat().st_mode), 0o600)
      self.assertEqual(target_path.stat().st_uid, os.getuid())
      self.assertEqual(target_path.stat().st_gid, os.getgid())

  def test_container_entrypoint_rejects_bad_sources_without_echoing_values(self):
    runtime_config = self.load_runtime_config_module()
    secret_marker = "STAGING_MUST_NOT_PRINT_THIS_VALUE"

    with tempfile.TemporaryDirectory() as temp_directory:
      temporary_root = Path(temp_directory)
      malformed_path = temporary_root / "malformed.yml"
      malformed_path.write_text(
        f"database:\n  password: {secret_marker}\nserver: [invalid\n",
        encoding="utf-8",
      )
      unreadable_path = temporary_root / "unreadable.yml"
      unreadable_path.write_text(secret_marker, encoding="utf-8")
      unreadable_path.chmod(0o000)
      bad_sources = [
        malformed_path,
        temporary_root / "missing.yml",
        unreadable_path,
      ]
      for source_path in bad_sources:
        with self.subTest(source_path=source_path.name):
          stdout = io.StringIO()
          stderr = io.StringIO()
          with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
          ):
            status = runtime_config.main([
              "container-entrypoint",
              str(source_path),
              pwd.getpwuid(os.getuid()).pw_name,
              sys.executable,
              "-c",
              "raise SystemExit('server must not start')",
            ])

          visible_output = stdout.getvalue() + stderr.getvalue()
          self.assertEqual(status, 1)
          self.assertIn("config/config.yml is missing or invalid", visible_output)
          self.assertNotIn(secret_marker, visible_output)

  def test_privilege_drop_initializes_groups_before_exec(self):
    runtime_config = self.load_runtime_config_module()
    self.assertTrue(
      hasattr(runtime_config, "drop_privileges_and_exec"),
      "container privilege drop is not implemented",
    )
    account = pwd.struct_passwd(
      ("appuser", "x", 2345, 3456, "", "/app", "/sbin/nologin")
    )

    with (
      patch.object(runtime_config.pwd, "getpwnam", return_value=account),
      patch.object(runtime_config.os, "initgroups") as initgroups,
      patch.object(runtime_config.os, "setgid") as setgid,
      patch.object(runtime_config.os, "setuid") as setuid,
      patch.object(runtime_config.os, "execvp") as execvp,
    ):
      manager = unittest.mock.Mock()
      manager.attach_mock(initgroups, "initgroups")
      manager.attach_mock(setgid, "setgid")
      manager.attach_mock(setuid, "setuid")
      manager.attach_mock(execvp, "execvp")

      runtime_config.drop_privileges_and_exec(
        "appuser", ["python", "./server.py"]
      )

    self.assertEqual(manager.mock_calls, [
      call.initgroups("appuser", 3456),
      call.setgid(3456),
      call.setuid(2345),
      call.execvp("python", ["python", "./server.py"]),
    ])

  def test_compose_mounts_only_the_read_only_container_secret(self):
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    app = compose["services"]["app"]

    self.assertNotIn("environment", app)
    self.assertIn(
      "./config/config.yml:/run/secrets/config.yml:ro",
      app["volumes"],
    )
    self.assertFalse(
      any(
        str(volume).startswith("./config/config.yml:/app/config/")
        for volume in app["volumes"]
      )
    )
    self.assertFalse(
      any(".env" in str(volume) for volume in app["volumes"])
    )
    self.assertEqual(app["ports"], [
      "${SMSD_SERVER_PORT:?run ./run-docker.sh}:"
      "${SMSD_SERVER_PORT:?run ./run-docker.sh}",
    ])
    self.assertEqual(
      app["healthcheck"]["test"],
      [
        "CMD", "curl", "-f",
        "http://localhost:${SMSD_SERVER_PORT:?run ./run-docker.sh}/",
      ],
    )

  def test_compose_mysql_bootstrap_uses_only_yaml_derived_values(self):
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    mysql = compose["services"]["mysql"]

    self.assertEqual(mysql["environment"], {
      "MYSQL_ROOT_PASSWORD": "${SMSD_DB_PASSWORD:?run ./run-docker.sh}",
      "MYSQL_DATABASE": "${SMSD_DB_NAME:?run ./run-docker.sh}",
      "MYSQL_USER": "${SMSD_DB_USER:?run ./run-docker.sh}",
      "MYSQL_PASSWORD": "${SMSD_DB_PASSWORD:?run ./run-docker.sh}",
    })
    self.assertEqual(
      mysql["ports"],
      ["${SMSD_DB_PORT:?run ./run-docker.sh}:3306"],
    )

  def test_docker_build_context_excludes_the_canonical_config(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      test_repository = Path(temp_directory) / "repository"
      test_repository.mkdir()
      subprocess.run(
        ["git", "init", "--quiet"],
        cwd=test_repository,
        check=True,
        capture_output=True,
        text=True,
      )
      shutil.copy2(DOCKERIGNORE_FILE, test_repository / ".gitignore")

      ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "config/config.yml"],
        cwd=test_repository,
        check=False,
        capture_output=True,
        text=True,
      )

    self.assertEqual(
      ignored.returncode,
      0,
      "config/config.yml would enter the Docker build context",
    )

  def test_local_startup_check_rejects_invalid_yaml_without_echoing_values(self):
    secret_marker = "LOCAL_STARTUP_MUST_NOT_PRINT"
    with tempfile.TemporaryDirectory() as temp_directory:
      project = Path(temp_directory) / "project"
      (project / "scripts").mkdir(parents=True)
      (project / "config").mkdir()
      shutil.copy2(RUN_SERVER_SCRIPT, project / "run-server.sh")
      shutil.copy2(RUNTIME_CONFIG_SCRIPT, project / "scripts/runtime_config.py")
      (project / "config" / "config.yml").write_text(
        f"database:\n  password: {secret_marker}\nserver: [invalid\n",
        encoding="utf-8",
      )
      environment = os.environ.copy()
      environment["PYTHON_BIN"] = sys.executable
      result = subprocess.run(
        ["bash", str(project / "run-server.sh"), "--check-config"],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
      )

    visible_output = result.stdout + result.stderr
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("config/config.yml is missing or invalid", visible_output)
    self.assertNotIn(secret_marker, visible_output)

  def test_local_startup_check_uses_yaml_even_when_env_disagrees(self):
    with tempfile.TemporaryDirectory() as temp_directory:
      project = Path(temp_directory) / "project"
      (project / "scripts").mkdir(parents=True)
      (project / "config").mkdir()
      shutil.copy2(RUN_SERVER_SCRIPT, project / "run-server.sh")
      shutil.copy2(RUNTIME_CONFIG_SCRIPT, project / "scripts/runtime_config.py")
      (project / "config" / "config.yml").write_text(
        yaml.safe_dump(self.compose_config(), sort_keys=False),
        encoding="utf-8",
      )
      (project / ".env").write_text(
        "SERVER_PORT=9999\nFLASK_DEBUG=true\n",
        encoding="utf-8",
      )
      environment = os.environ.copy()
      environment.update({
        "PYTHON_BIN": sys.executable,
        "SERVER_PORT": "9998",
        "FLASK_DEBUG": "true",
      })
      result = subprocess.run(
        ["bash", str(project / "run-server.sh"), "--check-config"],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
      )

    self.assertEqual(
      result.returncode,
      0,
      f"stdout={result.stdout!r}, stderr={result.stderr!r}",
    )

  def dockerfile_instructions(self):
    instructions = []
    pending = ""
    for raw_line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
      line = raw_line.strip()
      if not line or line.startswith("#"):
        continue
      pending = f"{pending} {line}".strip()
      if pending.endswith("\\"):
        pending = pending[:-1].rstrip()
        continue
      instructions.append(pending)
      pending = ""

    return instructions

  def test_image_defers_port_and_health_configuration_to_compose(self):
    instructions = self.dockerfile_instructions()

    instruction_names = [line.split(maxsplit=1)[0] for line in instructions]
    self.assertNotIn("EXPOSE", instruction_names)
    self.assertNotIn("HEALTHCHECK", instruction_names)

  def test_image_stages_config_as_root_then_executes_server_as_appuser(self):
    instructions = self.dockerfile_instructions()
    instruction_map = {
      line.split(maxsplit=1)[0]: line.split(maxsplit=1)[1]
      for line in instructions
      if " " in line and line.split(maxsplit=1)[0] in {
        "USER", "ENTRYPOINT", "CMD",
      }
    }

    self.assertEqual(instruction_map["USER"], "root")
    self.assertEqual(json.loads(instruction_map["ENTRYPOINT"]), [
      "python",
      "./scripts/runtime_config.py",
      "container-entrypoint",
      "/run/secrets/config.yml",
      "appuser",
    ])
    self.assertEqual(
      json.loads(instruction_map["CMD"]),
      ["python", "./server.py"],
    )

  def test_root_entrypoint_code_is_not_owned_by_appuser(self):
    instructions = self.dockerfile_instructions()
    runtime_copies = [
      instruction for instruction in instructions
      if instruction.startswith("COPY ") and instruction.endswith(" . .")
    ]

    self.assertEqual(runtime_copies, ["COPY . ."])


if __name__ == "__main__":
  unittest.main()
