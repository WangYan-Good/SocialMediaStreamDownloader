##
## The second deployment topology, and why it is a separate contract.
##
## The Compose topology bundles its own MySQL and keeps media in a named
## volume, and ``compose_environment`` enforces that by refusing any
## ``$.database.host`` other than ``mysql``. That rule is correct there and
## wrong everywhere else: the production this project actually runs is a
## bare-metal application against a MySQL on the host and a media tree at a
## real path, and a release tool that can only describe the Compose shape
## cannot describe production at all.
##
## So this is a second, explicit contract rather than a flag on the first. The
## two topologies disagree about where the database is, where media lives, and
## what may be committed - and blurring them behind conditionals is how one
## topology's guard silently stops protecting the other.
##
## What must stay true of *both*:
##
##   - the canonical operator configuration file is never rewritten. The old
##     bare-metal writer keeps reading it until the moment it is stopped, so a
##     deployment that edited it would break the running production before the
##     replacement was proven.
##   - the database password never reaches argv, the process environment or a
##     log. It travels only in the mounted configuration file, which is what
##     the container entrypoint stages.
##
from copy import deepcopy
import importlib.util
from pathlib import Path
import stat
import tempfile
import unittest

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_CONFIG_SCRIPT = PROJECT_ROOT / "scripts" / "runtime_config.py"


def runtime_config_module():
  specification = importlib.util.spec_from_file_location(
    "smsd_runtime_config_external", RUNTIME_CONFIG_SCRIPT
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


def external_config():
  ##
  ## Shaped like the deployment this exists for: a database on the host and a
  ## media root that is a real path rather than a volume name.
  ##
  config = deepcopy(unified_config())
  config["database"]["host"] = "localhost"
  config["download"]["save_path"] = "/mnt/video/"
  return config


class ExternalHostEnvironmentTest(unittest.TestCase):
  def setUp(self):
    self.module = runtime_config_module()

  ##
  ## >>=============== the two contracts stay separate ===============>>
  ##

  def test_the_compose_contract_still_refuses_an_external_database(self):
    ##
    ## The guard that makes Compose coherent must survive this phase. A
    ## deployment that reached the bundled MySQL by any name other than the
    ## service name would be talking to something nobody nominated.
    ##
    with self.assertRaises(ValueError):
      self.module.compose_environment(external_config())

  def test_the_external_contract_refuses_the_compose_database_name(self):
    ##
    ## And the reverse. ``mysql`` is a Compose service name, not a host: an
    ## external deployment pointed at it would resolve nothing, or worse,
    ## something else entirely.
    ##
    config = external_config()
    config["database"]["host"] = "mysql"

    with self.assertRaises(ValueError):
      self.module.external_environment(config)

  ##
  ## >>================== what the external contract yields ==================>>
  ##

  def test_it_reports_the_port_media_root_and_database_host(self):
    values = self.module.external_environment(external_config())

    self.assertEqual(unified_config()["server"]["port"], values["SMSD_SERVER_PORT"])
    self.assertEqual("/mnt/video", values["SMSD_MEDIA_ROOT"])
    self.assertEqual("localhost", values["SMSD_DB_HOST"])

  def test_it_never_yields_the_database_password(self):
    ##
    ## The whole point of the split. Compose needs the password in its
    ## interpolation file because it creates the database user; an external
    ## deployment connects to a user somebody else already created, so the
    ## password has no reason to leave the configuration file at all.
    ##
    config = external_config()
    config["database"]["password"] = "SECRET_EXTERNAL_DB_PASSWORD"

    values = self.module.external_environment(config)

    for key, value in values.items():
      self.assertNotIn(
        "SECRET_EXTERNAL_DB_PASSWORD",
        str(value),
        "{} carries the database password".format(key),
      )
    self.assertNotIn("SMSD_DB_PASSWORD", values)

  def test_a_media_root_that_is_not_absolute_is_refused(self):
    config = external_config()
    config["download"]["save_path"] = "relative/media"

    with self.assertRaises(ValueError):
      self.module.external_environment(config)

  ##
  ## >>================== the configuration file's mode ==================>>
  ##
  ## Production's canonical file is group- and world-readable today and holds
  ## the database password. A deployment tool that read it anyway would be
  ## treating "somebody already made this mistake" as permission to keep
  ## making it.
  ##

  def test_a_group_readable_configuration_is_refused(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "config.yml"
      path.write_text(yaml.safe_dump(external_config()), encoding="utf-8")
      path.chmod(0o644)

      with self.assertRaises(ValueError):
        self.module.require_private_config(path)

  def test_an_owner_only_configuration_is_accepted(self):
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "config.yml"
      path.write_text(yaml.safe_dump(external_config()), encoding="utf-8")
      path.chmod(0o600)

      self.assertEqual(path, self.module.require_private_config(path))

  def test_a_symlinked_configuration_is_refused(self):
    ##
    ## The mode of a link says nothing about the mode of what it points at.
    ##
    with tempfile.TemporaryDirectory() as directory:
      real = Path(directory) / "real.yml"
      real.write_text(yaml.safe_dump(external_config()), encoding="utf-8")
      real.chmod(0o600)
      link = Path(directory) / "config.yml"
      link.symlink_to(real)

      with self.assertRaises(ValueError):
        self.module.require_private_config(link)


class ExternalConfigStagingTest(unittest.TestCase):
  ##
  ## The container cannot use production's ``$.database.host`` as written.
  ## Inside a container ``localhost`` is the container, so the application
  ## would look for MySQL in its own namespace and find nothing.
  ##
  ## The address is not a secret, so it may travel as an environment value; the
  ## password is, so it stays in the mounted file and is never re-emitted.
  ##
  def setUp(self):
    self.module = runtime_config_module()

  ##
  ## Returns the staged document *and* its mode, read while the directory is
  ## still there - a path handed back out of the context manager describes a
  ## file that no longer exists.
  ##
  def stage(self, config, **options):
    import os

    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "source.yml"
      source.write_text(yaml.safe_dump(config), encoding="utf-8")
      target = Path(directory) / "staged.yml"
      self.module.stage_container_config(
        source, target, os.getuid(), os.getgid(), **options
      )
      return (
        yaml.safe_load(target.read_text(encoding="utf-8")),
        stat.S_IMODE(target.stat().st_mode),
      )

  def test_the_staged_configuration_takes_the_database_host_override(self):
    staged, unused = self.stage(
      external_config(), database_host="host.containers.internal"
    )

    self.assertEqual("host.containers.internal", staged["database"]["host"])

  def test_staging_without_an_override_leaves_the_database_host_alone(self):
    ##
    ## The Compose path stages the same file and must keep behaving exactly as
    ## it did.
    ##
    staged, unused = self.stage(unified_config())

    self.assertEqual(
      unified_config()["database"]["host"], staged["database"]["host"]
    )

  def test_staging_still_rewrites_the_server_host_for_the_container(self):
    staged, unused = self.stage(external_config(), database_host="10.0.0.1")

    self.assertEqual(
      self.module.CONTAINER_INTERNAL_SERVER_HOST, staged["server"]["host"]
    )

  def test_the_staged_file_is_owner_only(self):
    unused, mode = self.stage(external_config(), database_host="10.0.0.1")

    self.assertEqual(0o600, mode)

  def test_an_override_that_is_not_a_hostname_is_refused(self):
    ##
    ## The override reaches this from an environment value, so it is exactly
    ## the kind of input that must not become a YAML document of its own.
    ##
    for hostile in ("", "not a host", "10.0.0.1\nserver: {}", "a" * 300):
      with self.subTest(value=hostile):
        with self.assertRaises(ValueError):
          self.stage(external_config(), database_host=hostile)


##
## >>=============== the entrypoint that applies the override ===============>>
##
##
## The container is started with the canonical file mounted read-only and, in
## external-host mode, one non-secret environment value naming the database
## address. The entrypoint is where those two meet: it stages a private copy,
## applies the address, drops to ``appuser`` and execs.
##
## What must never appear in that environment is the password, which is why the
## variable below is the *host* and there is no companion for the credential.
##
class ExternalEntrypointTest(unittest.TestCase):
  def setUp(self):
    self.module = runtime_config_module()

  def run_entrypoint(self, environment):
    import os
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as directory:
      source = Path(directory) / "source.yml"
      source.write_text(yaml.safe_dump(external_config()), encoding="utf-8")
      target = Path(directory) / "staged.yml"

      captured = {}
      ##
      ## Bound before the patch, or the wrapper would call itself.
      ##
      real_stage = self.module.stage_container_config

      def fake_stage(source_path, target_path, uid, gid, database_host=None):
        captured["database_host"] = database_host
        real_stage(
          source_path, target_path, uid, gid, database_host=database_host
        )

      account = type(
        "Account", (), {"pw_uid": os.getuid(), "pw_gid": os.getgid(),
                        "pw_name": "appuser"}
      )()
      with patch.object(self.module, "CANONICAL_CONFIG_PATH", target), \
           patch.object(self.module, "stage_container_config", fake_stage), \
           patch.object(self.module.pwd, "getpwnam", lambda name: account), \
           patch.object(self.module, "drop_privileges_and_exec", lambda *a: None), \
           patch.dict(os.environ, environment, clear=False):
        self.module.run_container_entrypoint(source, "appuser", ["true"])
      return captured, yaml.safe_load(target.read_text(encoding="utf-8"))

  def test_the_environment_override_reaches_the_staged_configuration(self):
    captured, staged = self.run_entrypoint(
      {"SMSD_DB_HOST": "host.containers.internal"}
    )

    self.assertEqual("host.containers.internal", captured["database_host"])
    self.assertEqual("host.containers.internal", staged["database"]["host"])

  def test_without_the_variable_the_compose_behaviour_is_unchanged(self):
    import os
    from unittest.mock import patch

    with patch.dict(os.environ, {}, clear=False):
      os.environ.pop("SMSD_DB_HOST", None)
      captured, staged = self.run_entrypoint({})

    self.assertIsNone(captured["database_host"])
    self.assertEqual("localhost", staged["database"]["host"])

  def test_a_hostile_override_stops_the_container_rather_than_staging_it(self):
    with self.assertRaises(ValueError):
      self.run_entrypoint({"SMSD_DB_HOST": "10.0.0.1\ndatabase: {}"})


if __name__ == "__main__":
  unittest.main()
