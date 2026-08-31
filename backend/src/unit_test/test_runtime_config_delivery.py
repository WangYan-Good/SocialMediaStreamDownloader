import contextlib
from copy import deepcopy
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
CONFIG_CONTRACT_MODULE = PROJECT_ROOT / "backend" / "src" / "library" / "config_contract.py"
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"
RUN_DOCKER_SCRIPT = PROJECT_ROOT / "run-docker.sh"
RUN_SERVER_SCRIPT = PROJECT_ROOT / "run-server.sh"
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
DOCKERIGNORE_FILE = PROJECT_ROOT / ".dockerignore"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
README_FILE = PROJECT_ROOT / "README.md"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
CI_FILE = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


class RuntimeConfigDeliveryTest(unittest.TestCase):
  def test_example_uses_a_production_safe_debug_default(self):
    config = yaml.safe_load(CONFIG_EXAMPLE_PATH.read_text(encoding="utf-8"))

    self.assertFalse(config["server"]["debug_mode"])

  def test_example_binds_direct_startup_to_loopback(self):
    config = yaml.safe_load(CONFIG_EXAMPLE_PATH.read_text(encoding="utf-8"))

    self.assertEqual(config["server"]["host"], "127.0.0.1")
    self.assertFalse(config["auth"]["cookie_secure"])

  def test_waitress_is_exactly_pinned(self):
    requirements = REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()

    self.assertIn("waitress==3.0.2", requirements)

  def test_documented_production_entry_uses_the_server_launcher_and_waitress(self):
    readme = README_FILE.read_text(encoding="utf-8")

    self.assertIn("run-server.sh", readme)
    self.assertIn("run-docker.sh", readme)
    self.assertIn("Waitress", readme)
    self.assertNotIn("Flask development server", readme)

  def load_runtime_config_module(self):
    if not RUNTIME_CONFIG_SCRIPT.is_file():
      self.fail("runtime configuration helper is not available")
    spec = importlib.util.spec_from_file_location(
      "smsd_runtime_config", RUNTIME_CONFIG_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

  def copy_runtime_artifacts(self, project: Path) -> None:
    artifacts = (
      (RUNTIME_CONFIG_SCRIPT, project / "scripts" / "runtime_config.py"),
      (
        CONFIG_CONTRACT_MODULE,
        project / "backend" / "src" / "library" / "config_contract.py",
      ),
      (
        CONFIG_EXAMPLE_PATH,
        project / "docs" / "design" / "config.yml.example",
      ),
    )
    for source, target in artifacts:
      target.parent.mkdir(parents=True, exist_ok=True)
      shutil.copy2(source, target)

  def config_without_contract_fields(self) -> dict:
    config = deepcopy(unified_config())
    del config["database"]["host"]
    del config["platform"]["douyin"]["live"]["hls_stall_timeout"]
    return config

  def compose_config(self):
    config = unified_config()
    config["server"]["port"] = 5123
    config["database"].update({
      "host": "mysql",
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
      root_secret_path = Path(temp_directory) / "mysql-root-password"
      runtime_config.write_compose_environment(
        self.compose_config(), output_path, root_secret_path
      )
      output = output_path.read_text(encoding="utf-8")
      mode = stat.S_IMODE(output_path.stat().st_mode)

    self.assertEqual(mode, 0o600)
    self.assertEqual(
      output.splitlines(),
      [
        "SMSD_SERVER_PORT=5123",
        "SMSD_DB_NAME='smsd_test'",
        "SMSD_DB_USER='smsd_test_user'",
        "SMSD_DB_PASSWORD='db-pass-for-test'",
        f"SMSD_CONFIG_FILE='{PROJECT_ROOT / 'config' / 'config.yml'}'",
        f"SMSD_MYSQL_ROOT_SECRET_FILE='{root_secret_path}'",
      ],
    )

  def test_compose_environment_requires_internal_mysql_host(self):
    runtime_config = self.load_runtime_config_module()
    config = self.compose_config()
    config["database"]["host"] = "localhost"

    with self.assertRaisesRegex(ValueError, "database.host"):
      runtime_config.compose_environment(config)

  def test_mysql_root_secret_is_generated_once_private_and_distinct(self):
    runtime_config = self.load_runtime_config_module()
    generated = iter(("db-pass-for-test", "root-only-secret"))

    with tempfile.TemporaryDirectory() as temp_directory:
      secret_path = Path(temp_directory) / "mysql-root-password"
      first = runtime_config.ensure_mysql_root_secret(
        secret_path,
        "db-pass-for-test",
        token_factory=lambda: next(generated),
      )
      mode = stat.S_IMODE(secret_path.stat().st_mode)
      second = runtime_config.ensure_mysql_root_secret(
        secret_path,
        "db-pass-for-test",
        token_factory=lambda: self.fail("existing secret was regenerated"),
      )

    self.assertEqual(first, "root-only-secret")
    self.assertEqual(second, "root-only-secret")
    self.assertEqual(mode, 0o600)

  def test_mysql_root_secret_rejects_application_password_reuse(self):
    runtime_config = self.load_runtime_config_module()

    with tempfile.TemporaryDirectory() as temp_directory:
      secret_path = Path(temp_directory) / "mysql-root-password"
      secret_path.write_text("db-pass-for-test\n", encoding="utf-8")
      secret_path.chmod(0o600)

      with self.assertRaisesRegex(ValueError, "distinct"):
        runtime_config.ensure_mysql_root_secret(
          secret_path,
          "db-pass-for-test",
        )

  def test_runtime_validation_reports_missing_fields_in_canonical_order(self):
    runtime_config = self.load_runtime_config_module()

    with self.assertRaises(runtime_config.ConfigContractError) as raised:
      runtime_config.validate_runtime_config(self.config_without_contract_fields())

    self.assertEqual(
      (
        "$.database.host",
        "$.platform.douyin.live.hls_stall_timeout",
      ),
      raised.exception.issues,
    )

  def test_runtime_validation_allows_actual_only_keys_and_null_leaves(self):
    runtime_config = self.load_runtime_config_module()
    config = self.compose_config()
    config["extra_top_level"] = "allowed"
    config["platform"]["douyin"]["extra_nested"] = "allowed"
    config["platform"]["douyin"]["login"]["msToken"] = None

    self.assertIs(config, runtime_config.validate_runtime_config(config))

  def test_cli_validate_reports_every_missing_path_without_secret_values(self):
    runtime_config = self.load_runtime_config_module()
    secret_marker = "CLI_CONTRACT_SECRET_MUST_NOT_PRINT"
    config = self.config_without_contract_fields()
    config["database"]["password"] = secret_marker

    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config_path.write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
      )
      stdout = io.StringIO()
      stderr = io.StringIO()
      with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        status = runtime_config.main(["validate"], config_path=config_path)

    visible_output = stdout.getvalue() + stderr.getvalue()
    self.assertEqual(status, 1)
    self.assertIn("config/config.yml is missing or invalid", visible_output)
    self.assertIn("$.database.host", visible_output)
    self.assertIn(
      "$.platform.douyin.live.hls_stall_timeout", visible_output
    )
    self.assertNotIn(secret_marker, visible_output)

  def test_cli_server_port_rejects_missing_deep_field_without_output(self):
    runtime_config = self.load_runtime_config_module()
    config = self.config_without_contract_fields()

    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      config_path.write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
      )
      stdout = io.StringIO()
      stderr = io.StringIO()
      with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        status = runtime_config.main(["server-port"], config_path=config_path)

    self.assertEqual(status, 1)
    self.assertEqual("", stdout.getvalue())
    self.assertIn("$.platform.douyin.live.hls_stall_timeout", stderr.getvalue())

  def test_compose_env_rejects_missing_contract_field_without_creating_target(self):
    runtime_config = self.load_runtime_config_module()
    config = self.config_without_contract_fields()

    with tempfile.TemporaryDirectory() as temp_directory:
      config_path = Path(temp_directory) / "config.yml"
      output_path = Path(temp_directory) / "compose.env"
      config_path.write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
      )
      with contextlib.redirect_stderr(io.StringIO()):
        status = runtime_config.main(
          ["compose-env", str(output_path)], config_path=config_path
        )

      self.assertEqual(status, 1)
      self.assertFalse(output_path.exists())

  def test_container_staging_rejects_missing_contract_field_without_replacing_target(self):
    runtime_config = self.load_runtime_config_module()
    config = self.config_without_contract_fields()

    with tempfile.TemporaryDirectory() as temp_directory:
      temporary_root = Path(temp_directory)
      source_path = temporary_root / "source.yml"
      target_path = temporary_root / "config" / "config.yml"
      target_path.parent.mkdir()
      source_path.write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
      )
      target_path.write_text("existing canonical configuration", encoding="utf-8")

      with self.assertRaises(runtime_config.ConfigContractError):
        runtime_config.stage_container_config(
          source_path,
          target_path,
          os.getuid(),
          os.getgid(),
        )

      self.assertEqual(
        "existing canonical configuration",
        target_path.read_text(encoding="utf-8"),
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

      self.copy_runtime_artifacts(project)
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
      self.assertIn("SMSD_MYSQL_ROOT_SECRET_FILE=", record["env_content"])
      root_secret_path = project / "config" / "mysql-root-password"
      root_secret = root_secret_path.read_text(encoding="utf-8").strip()
      self.assertTrue(root_secret)
      self.assertNotEqual(root_secret, "db-pass-for-test")
      self.assertEqual(stat.S_IMODE(root_secret_path.stat().st_mode), 0o600)
      self.assertNotIn(root_secret, record["env_content"])
      self.assertNotIn(root_secret, result.stdout + result.stderr)
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

      staged_config = yaml.safe_load(target_path.read_text(encoding="utf-8"))
      source_config = yaml.safe_load(source_path.read_text(encoding="utf-8"))
      self.assertEqual(source_config["server"]["host"], "127.0.0.1")
      self.assertEqual(staged_config["server"]["host"], "0.0.0.0")
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

  def test_container_entrypoint_always_drops_privileges_before_server_exec(self):
    runtime_config = self.load_runtime_config_module()
    account = pwd.struct_passwd(
      ("appuser", "x", 2345, 3456, "", "/app", "/sbin/nologin")
    )
    source_path = Path("/run/secrets/config.yml")
    command = ["python", "./server.py"]

    with (
      patch.object(runtime_config.pwd, "getpwnam", return_value=account),
      patch.object(runtime_config, "stage_container_config") as stage,
      patch.object(runtime_config, "drop_privileges_and_exec") as drop,
      patch.object(runtime_config.os, "execvp") as direct_exec,
    ):
      runtime_config.run_container_entrypoint(
        source_path, "appuser", command
      )

    stage.assert_called_once_with(
      source_path,
      runtime_config.CANONICAL_CONFIG_PATH,
      2345,
      3456,
    )
    drop.assert_called_once_with("appuser", command)
    direct_exec.assert_not_called()

  def test_compose_mounts_only_the_read_only_container_secret(self):
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    app = compose["services"]["app"]

    self.assertNotIn("environment", app)
    self.assertIn(
      "${SMSD_CONFIG_FILE:?run ./run-docker.sh}:/run/secrets/config.yml:ro",
      app["volumes"],
    )
    self.assertIn("log_data:/app/logs", app["volumes"])
    self.assertNotIn("./logs:/app/logs", app["volumes"])
    self.assertIn("log_data", compose["volumes"])
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
      "127.0.0.1:${SMSD_SERVER_PORT:?run ./run-docker.sh}:"
      "${SMSD_SERVER_PORT:?run ./run-docker.sh}",
    ])
    self.assertEqual(
      app["healthcheck"]["test"],
      [
        "CMD", "curl", "-f",
        "http://localhost:${SMSD_SERVER_PORT:?run ./run-docker.sh}/",
      ],
    )
    self.assertNotIn("container_name", app)
    self.assertEqual(app["image"], "${SMSD_IMAGE:-smsd:local}")

  def test_container_staging_adapts_loopback_source_to_internal_bind_only(self):
    runtime_config = self.load_runtime_config_module()
    config = self.compose_config()
    config["server"]["host"] = "127.0.0.1"

    with tempfile.TemporaryDirectory() as temp_directory:
      temporary_root = Path(temp_directory)
      source_path = temporary_root / "secrets" / "config.yml"
      target_path = temporary_root / "app" / "config" / "config.yml"
      source_path.parent.mkdir()
      target_path.parent.mkdir(parents=True)
      source_path.write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
      )

      runtime_config.stage_container_config(
        source_path,
        target_path,
        os.getuid(),
        os.getgid(),
      )

      source = yaml.safe_load(source_path.read_text(encoding="utf-8"))
      staged = yaml.safe_load(target_path.read_text(encoding="utf-8"))
      self.assertEqual(source["server"]["host"], "127.0.0.1")
      self.assertEqual(staged["server"]["host"], "0.0.0.0")

  def test_security_docs_define_local_and_external_transport_profiles(self):
    readme = README_FILE.read_text(encoding="utf-8")
    security = (PROJECT_ROOT / "docs" / "security.md").read_text(
      encoding="utf-8"
    )
    documentation = readme + "\n" + security

    self.assertIn("127.0.0.1", documentation)
    self.assertIn("HTTPS reverse proxy", documentation)
    self.assertIn("cookie_secure: true", documentation)
    self.assertIn("cookie_secure: false", documentation)
    self.assertIn("0.0.0.0", documentation)
    self.assertIn("不得直接对外暴露", security)
    self.assertIn("cookie_secure: true", security)

  def test_compose_mysql_bootstrap_uses_only_yaml_derived_values(self):
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    mysql = compose["services"]["mysql"]

    self.assertEqual(mysql["environment"], {
      "MYSQL_ROOT_PASSWORD_FILE": "/run/secrets/mysql_root_password",
      "MYSQL_DATABASE": "${SMSD_DB_NAME:?run ./run-docker.sh}",
      "MYSQL_USER": "${SMSD_DB_USER:?run ./run-docker.sh}",
      "MYSQL_PASSWORD": "${SMSD_DB_PASSWORD:?run ./run-docker.sh}",
    })
    self.assertNotIn("ports", mysql)
    self.assertEqual(mysql["secrets"], ["mysql_root_password"])
    self.assertEqual(
      compose["secrets"]["mysql_root_password"]["file"],
      "${SMSD_MYSQL_ROOT_SECRET_FILE:?run ./run-docker.sh}",
    )
    self.assertNotIn("secrets", compose["services"]["app"])
    self.assertNotIn("container_name", mysql)
    self.assertEqual(mysql["healthcheck"]["test"][0], "CMD-SHELL")
    readiness = mysql["healthcheck"]["test"][1]
    self.assertIn("mysql --protocol=TCP", readiness)
    self.assertIn("127.0.0.1", readiness)
    self.assertIn("-P 3306", readiness)
    self.assertIn("$${MYSQL_USER}", readiness)
    self.assertIn("$${MYSQL_PASSWORD}", readiness)
    self.assertIn("$${MYSQL_DATABASE}", readiness)
    self.assertIn("SELECT 1", readiness)
    self.assertNotIn("mysqladmin ping", readiness)
    self.assertEqual(
      compose["services"]["app"]["depends_on"]["mysql"]["condition"],
      "service_healthy",
    )

  def test_ci_runs_real_compose_baseline_with_independent_marker_guard(self):
    workflow = CI_FILE.read_text(encoding="utf-8")
    marker = "ok   runtime secure compose deployment baseline"

    self.assertIn("./run-docker.sh -p", workflow)
    self.assertIn("/run/secrets/mysql_root_password", workflow)
    self.assertIn("docker cp", workflow)
    self.assertIn("docker exec --user appuser", workflow)
    self.assertIn("--force-recreate", workflow)
    self.assertIn(marker, workflow)
    self.assertIn(f"grep -Fxq '{marker}'", workflow)
    self.assertNotIn("docker exec smsd-ci-compose-app python -", workflow)

  def test_docker_build_context_excludes_runtime_config_and_root_secret(self):
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

      results = {
        path: subprocess.run(
          ["git", "check-ignore", "--no-index", path],
          cwd=test_repository,
          check=False,
          capture_output=True,
          text=True,
        ).returncode
        for path in (
          "config/config.yml",
          "config/mysql-root-password",
        )
      }

    self.assertEqual(results, {
      "config/config.yml": 0,
      "config/mysql-root-password": 0,
    })

  def test_local_startup_check_rejects_invalid_yaml_without_echoing_values(self):
    secret_marker = "LOCAL_STARTUP_MUST_NOT_PRINT"
    with tempfile.TemporaryDirectory() as temp_directory:
      project = Path(temp_directory) / "project"
      (project / "config").mkdir(parents=True)
      shutil.copy2(RUN_SERVER_SCRIPT, project / "run-server.sh")
      self.copy_runtime_artifacts(project)
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
      (project / "config").mkdir(parents=True)
      shutil.copy2(RUN_SERVER_SCRIPT, project / "run-server.sh")
      self.copy_runtime_artifacts(project)
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

  def test_image_prepares_runtime_volumes_without_recursive_chown(self):
    instructions = self.dockerfile_instructions()
    combined = "\n".join(instructions)

    self.assertNotIn("chown -R", combined)
    self.assertIn("install -d", combined)
    self.assertIn("/app/logs", combined)
    self.assertIn("/app/downloads", combined)
    self.assertIn("appuser", combined)

  def test_deployment_docs_define_private_root_secret_and_named_logs(self):
    documentation = (
      README_FILE.read_text(encoding="utf-8")
      + "\n"
      + (PROJECT_ROOT / "docs" / "security.md").read_text(encoding="utf-8")
    )

    self.assertIn("MYSQL_ROOT_PASSWORD_FILE", documentation)
    self.assertIn("mysql-root-password", documentation)
    self.assertIn("0600", documentation)
    self.assertIn("log_data", documentation)
    self.assertIn("MySQL", documentation)


if __name__ == "__main__":
  unittest.main()
