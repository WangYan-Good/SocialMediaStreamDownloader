##
## What has to be true before anybody stops production.
##
## The cutover sequence is: stop the old writer, back up, migrate, start the new
## one. Every step after the first assumes the operator can put the old writer
## back if the new one does not work - and on this host that assumption is
## currently false. The production application is a bare-metal process with no
## service manager: PPID 1, started by hand from a conda interpreter, restarted
## by hand when it dies. Nothing records how to start it again.
##
## A rollback plan that ends in "and then somehow restart the old application"
## is not a rollback plan. So this refuses to proceed until the operator has
## written down what the old writer *is* and asserted they can stop and start
## it - which is a decision they make, not a fact this can discover.
##
## It deliberately creates no service manager. Installing a unit would be
## modifying the host, and the host is not P19's to modify.
##
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PREFLIGHT = PROJECT_ROOT / "scripts" / "release_external_preflight.sh"
PYTHON_BIN = PROJECT_ROOT / "venv" / "bin" / "python"


class ExternalPreflightTestCase(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text(
      "#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8"
    )
    command.chmod(0o700)
    return command

  def run_preflight(self, **overrides):
    temporary = tempfile.mkdtemp()
    root = Path(temporary)
    authority = root / "writer-authority.json"
    if "authority" in overrides:
      document = overrides.pop("authority")
      if document is not None:
        authority.write_text(json.dumps(document), encoding="utf-8")
    else:
      authority.write_text(
        json.dumps({
          "revision": "f" * 40,
          "start_command": "python ./server.py",
          "working_directory": "/mnt/main/Service/SocialMediaStreamDownloader",
          "interpreter": "/home/operator/miniconda3/envs/smsd/bin/python3.12",
          "stop_procedure": "documented elsewhere",
          "start_procedure": "documented elsewhere",
          "operator_confirmed_stop_start_authority": True,
        }),
        encoding="utf-8",
      )

    environment = dict(os.environ)
    environment["PYTHON_BIN"] = str(PYTHON_BIN)
    argv = [
      "bash", str(PREFLIGHT),
      "--writer-authority", str(authority),
    ]
    completed = subprocess.run(
      argv, capture_output=True, text=True, env=environment
    )
    return completed


class WriterAuthorityGateTest(ExternalPreflightTestCase):
  def test_a_complete_confirmed_authority_passes(self):
    completed = self.run_preflight()

    self.assertEqual(0, completed.returncode, completed.stderr)

  def test_a_missing_authority_record_refuses(self):
    completed = self.run_preflight(authority=None)

    self.assertNotEqual(0, completed.returncode)

  ##
  ## Each field is something an operator needs in order to put the old writer
  ## back. A record missing one describes a rollback nobody can perform.
  ##
  def test_every_field_needed_to_restart_the_old_writer_is_required(self):
    complete = {
      "revision": "f" * 40,
      "start_command": "python ./server.py",
      "working_directory": "/mnt/main/Service/SocialMediaStreamDownloader",
      "interpreter": "/home/operator/miniconda3/envs/smsd/bin/python3.12",
      "stop_procedure": "documented elsewhere",
      "start_procedure": "documented elsewhere",
      "operator_confirmed_stop_start_authority": True,
    }
    for field in sorted(complete):
      if field == "operator_confirmed_stop_start_authority":
        continue
      with self.subTest(missing=field):
        partial = dict(complete)
        del partial[field]

        completed = self.run_preflight(authority=partial)

        self.assertNotEqual(0, completed.returncode)

  ##
  ## The confirmation is the whole point. A record that lists the commands but
  ## does not assert the operator can run them is a description, not authority.
  ##
  def test_an_unconfirmed_authority_refuses(self):
    for value in (False, "yes", 1, None):
      with self.subTest(confirmation=value):
        document = {
          "revision": "f" * 40,
          "start_command": "python ./server.py",
          "working_directory": "/mnt/main/Service/SocialMediaStreamDownloader",
          "interpreter": "/home/operator/miniconda3/envs/smsd/bin/python3.12",
          "stop_procedure": "documented elsewhere",
          "start_procedure": "documented elsewhere",
          "operator_confirmed_stop_start_authority": value,
        }

        completed = self.run_preflight(authority=document)

        self.assertNotEqual(0, completed.returncode)

  def test_the_preflight_never_prints_a_secret_shaped_field(self):
    completed = self.run_preflight()

    self.assertEqual(0, completed.returncode, completed.stderr)
    combined = (completed.stdout + completed.stderr).lower()
    for forbidden in ("password", "cookie", "token", "secret"):
      self.assertNotIn(forbidden, combined)


class PreflightContractTest(unittest.TestCase):
  ##
  ## The preflight must not become a thing that fixes the host. Its job is to
  ## refuse until somebody else has.
  ##
  def test_it_modifies_no_host_state(self):
    source = PREFLIGHT.read_text(encoding="utf-8")

    for forbidden in (
      "systemctl", "chmod ", "chown ", "mkdir ", "rm -", "kill ", "pkill",
    ):
      self.assertNotIn(
        forbidden, source, "the preflight changes host state: {}".format(forbidden)
      )

  def test_it_fails_closed(self):
    source = PREFLIGHT.read_text(encoding="utf-8")

    self.assertIn("set -euo pipefail", source)
    self.assertNotIn("|| true", source)


if __name__ == "__main__":
  unittest.main()
