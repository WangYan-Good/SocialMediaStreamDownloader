##
## Proving the thing that started is the thing that was reviewed.
##
## The Compose postcheck asks for two containers and pins the MySQL image,
## because in that topology the database is part of the release. Here it is not:
## the MySQL is the host's, it predates this release and it will outlive it, so
## demanding a container for it would make the check fail on a correct
## deployment.
##
## What replaces it is stricter about the application, since the application is
## the only thing this release actually places: exact image identity, the
## revision it was built from, the dependency lock it was built against, the
## media root it is really serving, and a database it can really reach.
##
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
POSTCHECK_SCRIPT = PROJECT_ROOT / "scripts" / "release_external_postcheck.sh"

CANONICAL_IMAGE = "ghcr.io/example/socialmediastreamdownloader@sha256:" + "a" * 64
EXPECTED_REVISION = "b" * 40
EXPECTED_IMAGE_ID = "sha256:" + "c" * 64
EXPECTED_LOCK = "d" * 64


class ExternalPostcheckTest(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text(
      "#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8"
    )
    command.chmod(0o700)
    return command

  def run_postcheck(self, **overrides):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      calls = root / "calls.log"
      calls.touch()
      media = root / "media"
      media.mkdir()

      engine = self.make_command(
        root,
        "engine",
        textwrap.dedent(
          """\
          echo "engine $*" >> "$CALL_LOG"
          case "$*" in
            *".State.Running"*) printf '%s\\n' "${RUNNING:-true}" ;;
            *".Image}}"*) printf '%s\\n' "${RUNNING_IMAGE_ID:-$EXPECTED_IMAGE_ID}" ;;
            *".Id}}"*) printf '%s\\n' "$EXPECTED_IMAGE_ID" ;;
            *"org.opencontainers.image.revision"*) printf '%s\\n' "${IMAGE_REVISION:-$EXPECTED_REVISION}" ;;
            *"io.smsd.requirements.sha256"*) printf '%s\\n' "${LOCK_LABEL:-$EXPECTED_LOCK}" ;;
            *"Destination"*) printf '%s\\n' "${MEDIA_MOUNT:-$MEDIA_ROOT}" ;;
            *"test -f"*"release_media_write_probe"*)
              exit "${PROBE_PRESENT_STATUS:-0}" ;;
            *"release_media_write_probe"*)
              printf '%s\\n' "${PROBE_OUTPUT:-media write probe passed: uid=999 gid=999 read=3}"
              exit "${PROBE_STATUS:-0}" ;;
            *"migration_cli status"*) printf '%s\\n' "${MIGRATION:-state=ready current=0011_x heads=0011_x}" ;;
            *"migration_cli check"*)
              printf '%s\\n' "${CHECK_OUTPUT:-managed schema is compatible}"
              exit "${CHECK_STATUS:-0}" ;;
            "exec "*) exit "${EXEC_STATUS:-0}" ;;
            *) exit 91 ;;
          esac
          """
        ),
      )
      curl = self.make_command(
        root,
        "curl",
        'echo "curl $*" >> "$CALL_LOG"\nexit "${HEALTH_STATUS:-0}"\n',
      )

      environment = dict(os.environ)
      environment.update({
        "CALL_LOG": str(calls),
        "ENGINE_BIN": str(engine),
        "CURL_BIN": str(curl),
        "EXPECTED_IMAGE_ID": str(
          overrides.pop("expected_image_id", EXPECTED_IMAGE_ID)
        ),
        "EXPECTED_REVISION": EXPECTED_REVISION,
        "EXPECTED_LOCK": EXPECTED_LOCK,
        "MEDIA_ROOT": str(media),
      })
      for key in (
        "RUNNING", "RUNNING_IMAGE_ID", "IMAGE_REVISION", "LOCK_LABEL",
        "MEDIA_MOUNT", "MIGRATION", "HEALTH_STATUS", "EXEC_STATUS",
        "PROBE_OUTPUT", "PROBE_STATUS", "CHECK_OUTPUT", "CHECK_STATUS",
        "PROBE_PRESENT_STATUS",
      ):
        if key in overrides:
          environment[key] = str(overrides.pop(key))

      argv = [
        str(POSTCHECK_SCRIPT),
        "--health-url", "http://127.0.0.1:5000/",
        "--container-name", "smsd-app",
        "--expected-image", CANONICAL_IMAGE,
        "--expected-revision", EXPECTED_REVISION,
        "--expected-requirements-sha", EXPECTED_LOCK,
        "--media-root", str(media),
        "--application-user", str(overrides.pop("application_user", "appuser")),
        "--application-uid", str(overrides.pop("application_uid", 999)),
        "--application-gid", str(overrides.pop("application_gid", 999)),
      ]
      self.assertEqual({}, overrides, "unused override")
      completed = subprocess.run(
        argv, capture_output=True, text=True, env=environment
      )
      return completed, calls.read_text(encoding="utf-8")

  def test_a_correct_deployment_passes(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)

  ##
  ## The point of the split: an external deployment has no MySQL container and
  ## must not be asked for one.
  ##
  def test_it_never_requires_a_database_container(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertNotIn("name=^mysql", log)
    self.assertNotIn("mysql:8.0", log)
    ##
    ## And every engine call is about the application container it was given.
    ## Without this the check passes even if the postcheck were quietly asking
    ## about a container named ``mysql`` instead - which is exactly the Compose
    ## assumption this topology has to drop.
    ##
    inspected = [
      line for line in log.splitlines()
      if line.startswith("engine inspect") or line.startswith("engine exec")
    ]
    self.assertTrue(inspected)
    for line in inspected:
      self.assertIn("smsd-app", line)

  def test_a_stopped_container_fails(self):
    completed, unused = self.run_postcheck(RUNNING="false")

    self.assertNotEqual(0, completed.returncode)

  ##
  ## Podman reports a bare digest where Docker reports ``sha256:<digest>``.
  ## Comparing the running container's spelling against the image's must not
  ## depend on which engine is answering.
  ##
  def test_either_engines_spelling_of_the_same_image_is_accepted(self):
    for label, image_id in (
      ("docker", "sha256:" + "c" * 64),
      ("podman", "c" * 64),
    ):
      with self.subTest(engine=label):
        completed, unused = self.run_postcheck(
          expected_image_id=image_id, RUNNING_IMAGE_ID=image_id
        )

        self.assertEqual(0, completed.returncode, completed.stderr)

  def test_an_image_identity_mismatch_fails(self):
    completed, unused = self.run_postcheck(
      RUNNING_IMAGE_ID="sha256:" + "9" * 64
    )

    self.assertNotEqual(0, completed.returncode)

  def test_a_revision_mismatch_fails(self):
    completed, unused = self.run_postcheck(IMAGE_REVISION="f" * 40)

    self.assertNotEqual(0, completed.returncode)

  def test_a_requirements_mismatch_fails(self):
    completed, unused = self.run_postcheck(LOCK_LABEL="e" * 64)

    self.assertNotEqual(0, completed.returncode)

  def test_a_media_mount_pointing_somewhere_else_fails(self):
    completed, unused = self.run_postcheck(MEDIA_MOUNT="/somewhere/else")

    self.assertNotEqual(0, completed.returncode)

  def test_a_migration_state_that_is_not_ready_fails(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=behind current=0002_x heads=0011_x"
    )

    self.assertNotEqual(0, completed.returncode)

  ##
  ## The same clause, isolated.
  ##
  ## Every other case here is refused by more than one of the four checks, so
  ## deleting any single one left the postcheck still refusing and the suite
  ## still green. This line satisfies the other three - a real revision, one
  ## head, and the database sitting on it - and is wrong in exactly one way, so
  ## only the state check can catch it.
  ##
  def test_a_state_that_is_not_ready_fails_even_when_the_revision_is_the_head(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=schema_drift current=0011_x heads=0011_x"
    )

    self.assertNotEqual(0, completed.returncode)

  def test_a_failing_health_endpoint_fails(self):
    completed, unused = self.run_postcheck(HEALTH_STATUS=7)

    self.assertNotEqual(0, completed.returncode)

  def test_it_checks_the_database_is_reachable_from_the_container(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("migration_cli", log)


##
## >>================ the application account, not the entrypoint ================>>
##
## The container starts as root to stage the mounted configuration and then
## drops to an unprivileged account. Under a rootless engine those are different
## host identities, so a mount the entrypoint can write is not necessarily a
## mount the application can write - and the failure appears on the first
## recording, long after a health endpoint has answered.
##
class ExternalPostcheckMediaWriteTest(ExternalPostcheckTest):
  def test_the_write_proof_runs_as_the_application_account(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)
    ##
    ## Two calls, and they are different questions: is the probe there at all,
    ## and can the application account use it.
    ##
    presence = [
      line for line in log.splitlines()
      if "release_media_write_probe" in line and "test -f" in line
    ]
    run = [
      line for line in log.splitlines()
      if "release_media_write_probe" in line and "--expect-uid" in line
    ]
    self.assertEqual(1, len(presence), log)
    self.assertEqual(1, len(run), log)
    self.assertIn("exec --user appuser", run[0])
    self.assertIn("--expect-uid 999", run[0])
    self.assertIn("--expect-gid 999", run[0])
    ##
    ## Presence first, so a missing probe is never reported as a denied write.
    ##
    self.assertLess(log.index(presence[0]), log.index(run[0]))

  def test_a_media_tree_the_application_cannot_write_fails(self):
    completed, unused = self.run_postcheck(PROBE_STATUS=1)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("cannot write the media tree", completed.stderr)

  ##
  ## A missing capability and a denied write are different failures and they
  ## send an operator to different places. An image built before this contract
  ## has no probe in it; reporting that as "cannot write" sends somebody to look
  ## at uids, mappings and mount options for a check that never ran.
  ##
  def test_an_image_without_the_probe_says_so_rather_than_blaming_permissions(self):
    completed, unused = self.run_postcheck(PROBE_PRESENT_STATUS=1)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("predates the media-write contract", completed.stderr)
    self.assertIn("not a permission failure", completed.stderr)
    self.assertNotIn("cannot write the media tree", completed.stderr)

  ##
  ## A probe that exits zero without saying it passed is a probe that did not
  ## run. Exit status alone would accept that.
  ##
  def test_a_probe_that_does_not_report_success_fails(self):
    completed, unused = self.run_postcheck(PROBE_OUTPUT="nothing to report")

    self.assertNotEqual(0, completed.returncode)


##
## >>=================== the release contract, kept explicit ===================>>
##
## ``status`` now classifies schema compatibility as part of its own answer, so
## ``check`` could be argued to be redundant. It is kept because the release
## contract names both, and a contract that quietly became implicit is one that
## can quietly stop being enforced.
##
class ExternalPostcheckMigrationParityTest(ExternalPostcheckTest):
  def test_both_status_and_check_are_run(self):
    completed, log = self.run_postcheck()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("migration_cli status", log)
    self.assertIn("migration_cli check", log)

  def test_a_database_at_no_revision_fails(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=ready current=none heads=0011_x"
    )

    self.assertNotEqual(0, completed.returncode)

  ##
  ## Isolated: an unversioned database agrees with a build that has no head, so
  ## every other check passes and only "there must be an applied revision" can
  ## refuse it. Without this, deleting that clause changed nothing.
  ##
  def test_a_database_at_no_revision_fails_even_when_it_matches_the_heads(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=ready current=none heads=none"
    )

    self.assertNotEqual(0, completed.returncode)

  def test_more_than_one_head_fails(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=ready current=0011_x heads=0011_x,0012_y"
    )

    self.assertNotEqual(0, completed.returncode)

  ##
  ## Isolated: the database is at the heads, whatever the heads are. Only the
  ## single-head rule objects to there being two of them.
  ##
  def test_more_than_one_head_fails_even_when_the_database_is_at_both(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=ready current=0011_x,0012_y heads=0011_x,0012_y"
    )

    self.assertNotEqual(0, completed.returncode)

  def test_a_current_revision_behind_the_head_fails(self):
    completed, unused = self.run_postcheck(
      MIGRATION="state=ready current=0009_x heads=0011_x"
    )

    self.assertNotEqual(0, completed.returncode)

  def test_an_incompatible_managed_schema_fails(self):
    completed, unused = self.run_postcheck(CHECK_STATUS=3)

    self.assertNotEqual(0, completed.returncode)

  def test_a_check_that_does_not_report_compatibility_fails(self):
    completed, unused = self.run_postcheck(
      CHECK_OUTPUT="column live_status is missing"
    )

    self.assertNotEqual(0, completed.returncode)


if __name__ == "__main__":
  unittest.main()
