##
## Handing a password to mysqldump without writing it down anywhere it survives.
##
## The Compose backup never has this problem: the credential lives in a Docker
## secret and is read inside the container by a shell that already has it
## mounted. An external backup runs against a MySQL on the host, so the password
## has to get from the canonical configuration file to the client somehow, and
## every obvious route is wrong.
##
##   - ``-pSECRET`` puts it in argv, which is world-readable in ``/proc`` for as
##     long as the dump runs - and a dump of this database runs for a while.
##   - ``MYSQL_PWD`` puts it in the environment, which is readable by anything
##     that can read the process and is inherited by every child.
##   - a heredoc or a pipe puts it in whatever the shell was traced into.
##
## What is left is an option file: the *path* travels in argv and the secret
## stays in a 0600 file that this writes and removes. That only works if the
## file is written correctly, which is the whole subject here - MySQL's option
## file format has quoting rules, and a password containing ``#`` silently
## becomes a comment if they are ignored.
##
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_CONFIG_SCRIPT = PROJECT_ROOT / "scripts" / "runtime_config.py"


def runtime_config_module():
  specification = importlib.util.spec_from_file_location(
    "smsd_runtime_config_credential", RUNTIME_CONFIG_SCRIPT
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


##
## Passwords that break a naive writer. Each one is a real thing a generator can
## emit, and each one means something to some layer that reads the file.
##
HOSTILE_PASSWORDS = (
  "plain-ascii-password",
  "has#hash-which-starts-a-comment",
  'has"double-quote',
  "has'single-quote",
  "has\\backslash",
  "has spaces and\ttab",
  "has=equals",
  "trailing-space ",
  "有中文密码",
  "#leading-hash",
  ";semicolon",
)


class MySQLOptionFileTest(unittest.TestCase):
  def setUp(self):
    self.module = runtime_config_module()

  def write_option_file(self, password, directory: Path) -> Path:
    config = unified_config()
    config["database"]["host"] = "localhost"
    config["database"]["password"] = password
    target = directory / "my.cnf"
    self.module.write_mysql_option_file(config, target)
    return target

  ##
  ## >>==================== what ends up on disk ====================>>
  ##

  def test_the_option_file_is_owner_only(self):
    with tempfile.TemporaryDirectory() as directory:
      target = self.write_option_file("secret", Path(directory))

      self.assertEqual(0o600, stat.S_IMODE(target.stat().st_mode))

  def test_the_option_file_is_written_atomically_and_privately(self):
    ##
    ## Created through a private temporary and renamed, so there is never an
    ## instant where the final name exists with a wider mode - which is exactly
    ## the window a 0644-then-chmod would leave.
    ##
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      observed = []
      real_chmod = os.chmod

      def watching_chmod(path, mode, *arguments, **options):
        observed.append((str(path), mode))
        return real_chmod(path, mode, *arguments, **options)

      os.chmod = watching_chmod
      try:
        self.write_option_file("secret", root)
      finally:
        os.chmod = real_chmod

      for path, mode in observed:
        self.assertEqual(
          0, mode & 0o077, "{} was made group or world readable".format(path)
        )

  ##
  ## >>============== the client must read back what we wrote ==============>>
  ##

  def test_every_hostile_password_round_trips_through_the_client_parser(self):
    ##
    ## Parsed by the real client rather than by a reimplementation of its rules.
    ## ``my_print_defaults`` is the same option-file parser mysqldump uses, so
    ## agreeing with it is the only thing that matters.
    ##
    parser = None
    for candidate in ("my_print_defaults", "/usr/bin/my_print_defaults"):
      if subprocess.run(
        ["sh", "-c", "command -v " + candidate], capture_output=True
      ).returncode == 0:
        parser = candidate
        break
    if parser is None:
      self.skipTest("my_print_defaults is unavailable")

    for password in HOSTILE_PASSWORDS:
      with self.subTest(password=password):
        with tempfile.TemporaryDirectory() as directory:
          target = self.write_option_file(password, Path(directory))
          ##
          ## ``--show`` because the tool masks passwords by default - which is
          ## the right default, and exactly why it has to be asked to stop.
          ##
          completed = subprocess.run(
            [parser, "--show", "--defaults-file=" + str(target), "mysqldump"],
            capture_output=True,
            text=True,
          )
          self.assertEqual(0, completed.returncode, completed.stderr)
          recovered = None
          for line in completed.stdout.splitlines():
            if line.startswith("--password="):
              recovered = line[len("--password="):]
          self.assertEqual(
            password,
            recovered,
            "the client parsed a different password than was written",
          )

  ##
  ## >>================== and never anywhere else ==================>>
  ##

  def test_the_password_is_not_in_the_process_table_or_the_environment(self):
    ##
    ## The point of the whole mechanism: what travels in argv is the path.
    ##
    with tempfile.TemporaryDirectory() as directory:
      target = self.write_option_file("SECRET_MYSQL_PASSWORD_P19", Path(directory))
      arguments = self.module.mysql_credential_arguments(target)

      self.assertEqual(["--defaults-extra-file=" + str(target)], arguments)
      for argument in arguments:
        self.assertNotIn("SECRET_MYSQL_PASSWORD_P19", argument)

  ##
  ## MySQL only honours ``--defaults-extra-file`` when it is the first argument.
  ## Placed anywhere else it is read as an unknown option and the client falls
  ## back to whatever other configuration it can find - which is how a backup
  ## silently connects as the wrong user.
  ##
  def test_the_option_file_argument_must_come_first(self):
    with tempfile.TemporaryDirectory() as directory:
      target = self.write_option_file("secret", Path(directory))
      arguments = self.module.mysql_credential_arguments(target)

      self.assertTrue(arguments[0].startswith("--defaults-extra-file="))


class MySQLOptionFileRefusalTest(unittest.TestCase):
  def setUp(self):
    self.module = runtime_config_module()

  def test_a_group_readable_option_file_is_refused(self):
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "my.cnf"
      target.write_text("[mysqldump]\npassword=secret\n", encoding="utf-8")
      target.chmod(0o644)

      with self.assertRaises(ValueError):
        self.module.require_private_option_file(target)

  def test_a_symlinked_option_file_is_refused(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      real = root / "real.cnf"
      real.write_text("[mysqldump]\npassword=secret\n", encoding="utf-8")
      real.chmod(0o600)
      link = root / "my.cnf"
      link.symlink_to(real)

      with self.assertRaises(ValueError):
        self.module.require_private_option_file(link)

  def test_an_oversized_option_file_is_refused(self):
    ##
    ## An option file is a few lines. Anything larger is not one, and reading it
    ## unbounded is how a single planted file becomes an outage.
    ##
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "my.cnf"
      target.write_text("#" + "a" * 100000 + "\n", encoding="utf-8")
      target.chmod(0o600)

      with self.assertRaises(ValueError):
        self.module.require_private_option_file(target)

  def test_a_directory_is_refused(self):
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "my.cnf"
      target.mkdir(mode=0o700)

      with self.assertRaises(ValueError):
        self.module.require_private_option_file(target)

  def test_an_owner_only_option_file_is_accepted(self):
    with tempfile.TemporaryDirectory() as directory:
      target = Path(directory) / "my.cnf"
      target.write_text("[mysqldump]\npassword=secret\n", encoding="utf-8")
      target.chmod(0o600)

      self.assertEqual(target, self.module.require_private_option_file(target))


if __name__ == "__main__":
  unittest.main()
