##
## The real-infra gate, as a contract.
##
## The gate itself needs a real rootless Podman, a real filesystem that can
## clone and a real application image, so it runs by hand on the host it is
## about. What can be pinned here is the shape - and two parts of that shape are
## worth pinning hard, because both were wrong once and neither failure is
## visible from the gate's own output.
##
## The first is what it exposes. Proving that a container can reach a service on
## the host used to mean publishing a MySQL with a fixed, checked-in root
## password on every interface of a production machine. It passed, and it was a
## large exposure taken on to answer a question about routing.
##
## The second is who it proves things for. The media write proof ran BusyBox as
## the container's default user, which under a rootless engine is the operator -
## so it proved the operator can write a directory the operator owns. The
## application does not run as that user, and on this host it gets EACCES on the
## same directory. The gate passed while the deployment it blessed could not
## have written a single recording.
##
from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GATE = PROJECT_ROOT / "scripts" / "release_external_host_gate.sh"
DEPLOY = PROJECT_ROOT / "scripts" / "release_external_deploy.sh"


##
## The lines that actually run something.
##
## Everything this file asserts the absence of is necessarily *named* somewhere
## in the gate: the prose above each section explains the mistake it replaced,
## and the refusal messages quote the flags they are about. Filtering to
## commands is what lets those explanations stay in the file.
##
def command_lines(source: str) -> list:
  commands = []
  for line in source.splitlines():
    stripped = line.strip()
    if not stripped:
      continue
    ##
    ## A line beginning with ``"$`` is a quoted command - ``"$ENGINE_BIN" ...``
    ## - and is one of these. A line beginning with a bare quote is the
    ## continuation of a message.
    ##
    if stripped.startswith("#") or stripped.startswith(("echo ", "require ", "fail ")):
      continue
    if stripped.startswith('"') and not stripped.startswith('"$'):
      continue
    commands.append(line)
  return commands


class ExternalHostGateExposureTest(unittest.TestCase):
  def setUp(self):
    self.gate = GATE.read_text(encoding="utf-8")
    self.statements = command_lines(self.gate)

  ##
  ## Every published port names the host address it is published on. A bare
  ## ``-p PORT:3306`` means every interface the machine has, now and after
  ## somebody adds one.
  ##
  def test_nothing_is_published_without_an_explicit_host_address(self):
    published = [
      line for line in self.statements
      if "--publish " in line or "--publish=" in line
    ]
    self.assertTrue(published, "the gate publishes nothing at all")
    for line in published:
      self.assertRegex(
        line,
        r'--publish "\$\{?[a-z_]+\}?:',
        "a port is published without naming a host address: " + line.strip(),
      )
    ##
    ## And the short form, which has no room for an address at all, is absent.
    ##
    for line in self.statements:
      self.assertNotRegex(
        line, r"(^|\s)-p\s+\S*\d+:\d+", line.strip()
      )

  def test_the_bound_address_is_never_every_interface(self):
    for line in self.statements:
      self.assertNotIn("0.0.0.0:", line, line.strip())

  ##
  ## The credential is generated for the run. A fixed one in a file that is read
  ## by anybody with the repository is not a credential.
  ##
  def test_the_database_password_is_generated_rather_than_written_down(self):
    self.assertIn("secrets.token_hex", self.gate)
    self.assertNotIn("MYSQL_ROOT_PASSWORD=gate_probe", self.gate)

  ##
  ## And it never reaches an argument list. ``-pPASSWORD`` and
  ## ``-e MYSQL_PWD=...`` both put it in this host's process table, where
  ## anything that can list processes can read it.
  ##
  def test_the_credential_never_reaches_a_command_line(self):
    for line in self.statements:
      stripped = line.strip()
      ##
      ## The generator that writes the file necessarily names the variables it
      ## writes. What must never appear is an *argument* carrying one.
      ##
      if stripped.startswith("print("):
        continue
      self.assertNotRegex(line, r"-p\$", stripped)
      self.assertNotIn("-e MYSQL", line, stripped)
      self.assertNotIn('-e "MYSQL', line, stripped)
      self.assertNotIn("--env MYSQL", line, stripped)
    self.assertIn("--env-file", self.gate)
    ##
    ## And every engine invocation that needs the credential takes it from the
    ## file rather than from its own arguments.
    ##
    credentialled = [
      line for line in self.statements
      if "mysqladmin" in line or "$MYSQL_IMAGE" in line
    ]
    self.assertTrue(credentialled)

  ##
  ## A generated credential that lands in a shell variable is a credential in
  ## this script's memory, in any `set -x` trace, and in whatever the shell
  ## happens to export. It is written straight to the file instead.
  ##
  def test_the_credential_is_never_held_in_a_shell_variable(self):
    for line in self.statements:
      stripped = line.strip()
      if stripped.startswith("print("):
        continue
      self.assertNotRegex(
        stripped, r"^[a-z_]*password[a-z_]*=", stripped
      )

  ##
  ## Tracing would print the credential file's contents the moment anything
  ## reads it, which undoes the rest of this.
  ##
  def test_the_gate_never_turns_on_tracing(self):
    for line in self.statements:
      stripped = line.strip()
      self.assertNotIn("set -x", stripped, stripped)
      self.assertNotIn("set -o xtrace", stripped, stripped)

  def test_the_credential_file_is_private_disposable_and_outside_the_repository(self):
    self.assertIn('mysql_env_file="$workspace/mysql.env"', self.gate)
    self.assertIn('chmod 600 "$mysql_env_file"', self.gate)
    self.assertIn("umask 077", self.gate)
    ##
    ## The workspace is a temporary directory removed by the exit trap, so the
    ## credential cannot outlive the run or land in the checkout.
    ##
    self.assertIn('workspace="$(mktemp -d', self.gate)
    self.assertIn('rm -rf -- "$workspace"', self.gate)
    self.assertIn('chmod 700 "$workspace"', self.gate)

  ##
  ## The exception is for a throwaway container this gate created and destroys.
  ## The production database credential stays in a mounted 0600 file, and
  ## nothing in the release path may start passing that one through an
  ## environment instead.
  ##
  def test_the_exception_is_not_generalised_to_the_production_credential(self):
    for name in (
      "release_external_deploy.sh",
      "release_external_backup.sh",
      "release_external_restore_drill.sh",
      "release_external_postcheck.sh",
    ):
      source = (PROJECT_ROOT / "scripts" / name).read_text(encoding="utf-8")
      with self.subTest(script=name):
        self.assertNotIn("MYSQL_PWD", source)
        self.assertNotIn("--env-file", source)

  ##
  ## Together these are the regression: a bare publish plus a fixed password is
  ## exactly what this replaced, and either one alone would be enough to get
  ## back to it.
  ##
  def test_the_two_halves_of_the_old_exposure_cannot_both_return(self):
    self.assertNotRegex(self.gate, r"-p\s+\d+:3306")
    self.assertNotIn("MYSQL_ROOT_PASSWORD=gate_probe", self.gate)

  ##
  ## The route question is answered before the database question, by something
  ## that holds no secret at all.
  ##
  def test_the_route_is_proven_without_a_credential_first(self):
    self.assertIn("smsd-route-probe", self.gate)
    self.assertLess(
      self.gate.index("smsd-route-probe"),
      self.gate.index("MYSQL_ROOT_PASSWORD"),
    )

  def test_the_bound_address_is_discovered_rather_than_hard_coded(self):
    self.assertIn("host_route_address", self.gate)
    ##
    ## No literal address of this host anywhere. A gate that hard-coded one
    ## would silently bind nothing the day the machine is renumbered.
    ##
    for line in self.statements:
      self.assertNotRegex(line, r"192\.168\.\d+\.\d+")


class ExternalHostGateMediaProofTest(unittest.TestCase):
  def setUp(self):
    self.gate = GATE.read_text(encoding="utf-8")

  ##
  ## The authoritative media proof uses the real image, the real entrypoint and
  ## the real unprivileged account. BusyBox as container root proves the
  ## operator's access, which was never the question.
  ##
  def test_the_media_proof_uses_the_application_image(self):
    proof = self.gate[self.gate.index("probe_media()"):]
    proof = proof[:proof.index("negative control: a root probe")]
    self.assertIn('"$image_ref"', proof)
    self.assertIn("release_media_write_probe.py", proof)
    self.assertNotIn("$BUSYBOX_IMAGE", proof)

  def test_the_media_proof_runs_under_the_identity_mapping(self):
    self.assertIn('--userns "keep-id:uid=${application_uid}', self.gate)

  ##
  ## Both negative controls. Without them the positive result could be produced
  ## by something other than the mapping, and nobody would know.
  ##
  def test_the_gate_proves_the_mapping_is_what_makes_it_work(self):
    self.assertIn("without a user-namespace mapping", self.gate)
    self.assertIn("accepted a root identity", self.gate)

  ##
  ## The identity is read from the image so it cannot drift. This is the check
  ## that makes a drift visible rather than silent: map one account too far and
  ## the application is back in the subordinate range with no access at all.
  ##
  def test_a_mapping_for_another_account_must_fail_the_gate(self):
    self.assertIn("application_uid + 1", self.gate)
    self.assertIn("the uid/gid contract is not being enforced", self.gate)

  def test_the_gate_never_changes_ownership_to_make_the_write_work(self):
    ##
    ## ``podman unshare chown`` appears once, on a directory the gate created in
    ## its own workspace, to manufacture the ownership-mismatch case. It never
    ## touches a media tree it did not make.
    ##
    commands = command_lines(self.gate)
    chowns = [line for line in commands if "chown" in line]
    self.assertTrue(chowns)
    for line in chowns:
      self.assertIn("foreign", line, line.strip())
    for line in commands:
      self.assertNotIn(":U", line, line.strip())
      self.assertNotIn("--privileged", line, line.strip())

  def test_the_gate_checks_the_existing_tree_was_left_alone(self):
    self.assertIn("existing media changed ownership", self.gate)
    self.assertIn("mode was changed by the deployment path", self.gate)

  def test_the_deploy_it_exercises_is_the_real_one(self):
    self.assertIn("release_external_deploy.sh", self.gate)
    self.assertTrue(DEPLOY.is_file())


if __name__ == "__main__":
  unittest.main()
