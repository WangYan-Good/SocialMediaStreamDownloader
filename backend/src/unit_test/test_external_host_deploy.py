##
## Starting the production application against the production that exists.
##
## The Compose deployment brings its own database and its own volume, so it can
## afford to create what it needs. This one cannot create anything: the MySQL is
## already there with two years of rows in it, the media tree is terabytes at a
## path the database refers to by name, and the application it replaces is still
## running and still writing.
##
## Everything below is therefore a refusal before it is an action. The script's
## job is to prove it is allowed to start before it starts anything, because the
## failure it must never produce is two writers.
##
import hashlib
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import textwrap
import unittest

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "release_external_deploy.sh"

CANONICAL_IMAGE = "ghcr.io/wangyan-good/socialmediastreamdownloader@sha256:" + "a" * 64
EXPECTED_REVISION = "b" * 40
EXPECTED_IMAGE_ID = "sha256:" + "c" * 64
##
## What the engine hands back from ``run --detach``: the identifier the
## cleanup path must use, rather than the name it was asked for.
##
CONTAINER_ID = "0123456789ab" + "cdef" * 13


class ExternalDeployTestCase(unittest.TestCase):
  def make_command(self, directory: Path, name: str, body: str) -> Path:
    command = directory / name
    command.write_text(
      "#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8"
    )
    command.chmod(0o700)
    return command

  ##
  ## One engine stub standing in for rootless Podman. It records every
  ## invocation, so a test can assert on what the script *did not* pass just as
  ## easily as on what it did.
  ##
  def engine_stub(self, root: Path) -> Path:
    return self.make_command(
      root,
      "engine",
      textwrap.dedent(
        """\
        echo "engine $*" >> "$CALL_LOG"
        case "$1 ${2:-}" in
          "pull "*) exit 0 ;;
          "image inspect")
            case "$*" in
              *"org.opencontainers.image.revision"*)
                printf '%s\\n' "$IMAGE_REVISION" ;;
              *"io.smsd.requirements.sha256"*)
                printf '%s\\n' "$LOCK_LABEL" ;;
              *) printf '%s\\n' "$EXPECTED_IMAGE_ID" ;;
            esac ;;
          "ps "*)
            case "$*" in
              ##
              ## The rollback's existence query, which asks about one exact
              ## identifier across all containers including stopped ones.
              ##
              *"--filter id="*)
                [[ "${EXISTENCE_QUERY_FAILS:-}" != "true" ]] || exit 1
                printf '%s' "${EXISTS_AFTER_REMOVAL:-}" ;;
              *) printf '%s' "${EXISTING_CONTAINER:-}" ;;
            esac ;;
          "run "*)
            ##
            ## Two different runs reach this stub. One asks the image what its
            ## application account resolves to; the other starts the writer.
            ##
            case "$*" in
              *"id -u"*)
                [[ "${IDENTITY_QUERY_FAILS:-}" != "true" ]] || exit 1
                printf '%s\\n%s\\n' "${APPLICATION_UID:-999}" "${APPLICATION_GID:-999}" ;;
              *) printf '%s\\n' "$CONTAINER_ID" ;;
            esac ;;
          "inspect"*)
            case "$*" in
              *)
                [[ "${INSPECT_IMAGE_FAILS:-}" != "true" ]] || exit 1
                printf '%s\\n' "${RUNNING_IMAGE_ID:-$EXPECTED_IMAGE_ID}" ;;
            esac ;;
          "rm "*) [[ "${REMOVE_FAILS:-}" != "true" ]] || exit 1 ;;
          *) exit 91 ;;
        esac
        """
      ),
    )

  ##
  ## A port nothing is listening on. The default must never be 5000: that is
  ## the real production port on the host these tests run on, and borrowing it
  ## would make the happy path fail for the right reason at the wrong time.
  ##
  def free_port(self) -> int:
    with socket.socket() as probe:
      probe.bind(("127.0.0.1", 0))
      return probe.getsockname()[1]

  def run_deploy(self, **overrides):
    overrides.setdefault("port", self.free_port())
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      calls = root / "calls.log"
      calls.touch()

      requirements = root / "requirements.txt"
      requirements.write_text(
        "example==1.0 --hash=sha256:" + "d" * 64 + "\n", encoding="utf-8"
      )
      lock_sha = hashlib.sha256(requirements.read_bytes()).hexdigest()

      config = root / "config.yml"
      document = unified_config()
      document["database"]["host"] = "localhost"
      document["download"]["save_path"] = str(root / "media")
      config.write_text(yaml.safe_dump(document), encoding="utf-8")
      config.chmod(overrides.pop("config_mode", 0o600))

      media = root / "media"
      media.mkdir(exist_ok=True)

      postcheck = self.make_command(
        root,
        "postcheck",
        'echo "postcheck $*" >> "$CALL_LOG"\nexit {}\n'.format(
          overrides.pop("postcheck_exit", 0)
        ),
      )
      engine = self.engine_stub(root)

      environment = dict(os.environ)
      environment.update({
        "CALL_LOG": str(calls),
        "ENGINE_BIN": str(engine),
        "REQUIREMENTS_FILE": str(requirements),
        "EXTERNAL_POSTCHECK_SCRIPT": str(postcheck),
        "EXPECTED_IMAGE_ID": overrides.pop(
          "expected_image_id", EXPECTED_IMAGE_ID
        ),
        "IMAGE_REVISION": overrides.pop("image_revision", EXPECTED_REVISION),
        "LOCK_LABEL": overrides.pop("lock_label", lock_sha),
        "EXISTING_CONTAINER": overrides.pop("existing_container", ""),
        "RUNNING_IMAGE_ID": overrides.pop(
          "running_image_id", EXPECTED_IMAGE_ID
        ),
        "CONTAINER_ID": overrides.pop("container_id_value", CONTAINER_ID),
        "APPLICATION_UID": str(overrides.pop("application_uid", 999)),
        "APPLICATION_GID": str(overrides.pop("application_gid", 999)),
        "IDENTITY_QUERY_FAILS": (
          "true" if overrides.pop("identity_query_fails", False) else ""
        ),
        "REMOVE_FAILS": (
          "true" if overrides.pop("remove_fails", False) else ""
        ),
        "INSPECT_IMAGE_FAILS": (
          "true" if overrides.pop("inspect_image_fails", False) else ""
        ),
        "EXISTS_AFTER_REMOVAL": overrides.pop("exists_after_removal", ""),
        "EXISTENCE_QUERY_FAILS": (
          "true" if overrides.pop("existence_query_fails", False) else ""
        ),
      })

      argv = [
        str(DEPLOY_SCRIPT),
        "--image", overrides.pop("image", CANONICAL_IMAGE),
        "--expected-revision", overrides.pop("revision", EXPECTED_REVISION),
        "--container-name", overrides.pop("container_name", "smsd-app"),
        "--config-file", str(overrides.pop("config_file", config)),
        "--media-root", str(overrides.pop("media_root", media)),
        "--db-host", overrides.pop("db_host", "host.containers.internal"),
        "--port", str(overrides.pop("port", 5000)),
        "--health-url", "http://127.0.0.1:5000/",
      ]
      ##
      ## Stated explicitly by every caller, exactly as an operator must. A
      ## default here would hide the one argument that decides who can reach
      ## production.
      ##
      publish_address = overrides.pop("publish_address", "0.0.0.0")
      if publish_address is not None:
        argv += ["--publish-address", publish_address]
      for extra in overrides.pop("extra", []):
        argv.append(extra)
      self.assertEqual({}, overrides, "unused override")

      completed = subprocess.run(
        argv, capture_output=True, text=True, env=environment
      )
      return completed, calls.read_text(encoding="utf-8")


class ExternalDeployIdentityTest(ExternalDeployTestCase):
  def test_a_correct_invocation_starts_the_container_and_postchecks(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("engine run", log)
    self.assertIn("postcheck", log)

  def test_a_tag_is_refused_as_release_authority(self):
    for reference in (
      "ghcr.io/example/socialmediastreamdownloader:latest",
      "ghcr.io/example/socialmediastreamdownloader:sha-abcdef",
      "socialmediastreamdownloader@sha256:" + "a" * 64,
    ):
      with self.subTest(image=reference):
        completed, log = self.run_deploy(image=reference)

        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn("engine run", log, "a container was started anyway")

  def test_a_revision_label_mismatch_refuses_before_starting(self):
    completed, log = self.run_deploy(image_revision="f" * 40)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_a_requirements_label_mismatch_refuses_before_starting(self):
    completed, log = self.run_deploy(lock_label="e" * 64)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  ##
  ## >>================ the two engines spell an ID differently ================>>
  ##
  ## Docker reports an image ID as ``sha256:<64 hex>``; Podman reports the bare
  ## digest. Production runs Podman. This suite's stub modelled Docker, so a
  ## format check written against Docker's spelling passed every test here and
  ## refused every real deployment on the engine it was written for - which only
  ## running it against that engine revealed.
  ##
  def test_the_engines_disagree_about_spelling_and_both_are_accepted(self):
    for label, image_id in (
      ("docker", "sha256:" + "c" * 64),
      ("podman", "c" * 64),
    ):
      with self.subTest(engine=label):
        completed, log = self.run_deploy(
          expected_image_id=image_id, running_image_id=image_id
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("run --detach", log)

  ##
  ## And a mismatch is still a mismatch across the two spellings, so
  ## normalising cannot be used to wave one through.
  ##
  def test_a_mismatch_is_caught_whichever_way_each_side_is_spelled(self):
    completed, log = self.run_deploy(
      expected_image_id="sha256:" + "c" * 64,
      running_image_id="9" * 64,
    )

    self.assertNotEqual(0, completed.returncode)

  def test_an_identifier_that_is_not_a_digest_at_all_is_refused(self):
    completed, log = self.run_deploy(expected_image_id="not-an-image-id")

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("run --detach", log)
    self.assertIn("malformed", completed.stderr)

  def test_a_running_image_that_is_not_the_pulled_one_fails(self):
    completed, log = self.run_deploy(running_image_id="sha256:" + "9" * 64)

    self.assertNotEqual(0, completed.returncode)


class ExternalDeploySingleWriterTest(ExternalDeployTestCase):
  ##
  ## The invariant the whole phase exists to protect. Two writers against one
  ## database and one media tree is the one outcome from which there is no
  ## clean rollback.
  ##
  def test_an_existing_container_of_the_same_name_refuses(self):
    completed, log = self.run_deploy(existing_container="already-running")

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log, "a second writer was started")

  def test_an_occupied_production_port_refuses(self):
    ##
    ## A real listener rather than a stubbed answer: the old bare-metal writer
    ## holding the port is precisely the condition this must detect, and it
    ## holds a real socket.
    ##
    with socket.socket() as listener:
      listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      listener.bind(("127.0.0.1", 0))
      listener.listen(1)
      occupied = listener.getsockname()[1]

      completed, log = self.run_deploy(port=occupied)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log, "a second writer was started")


class ExternalDeploySafetyTest(ExternalDeployTestCase):
  def test_a_group_readable_configuration_refuses(self):
    ##
    ## Production's file is 0644 today and holds the database password.
    ##
    completed, log = self.run_deploy(config_mode=0o644)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_a_missing_media_root_refuses(self):
    with tempfile.TemporaryDirectory() as directory:
      completed, log = self.run_deploy(
        media_root=Path(directory) / "absent"
      )

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_the_filesystem_root_is_never_bind_mounted(self):
    completed, log = self.run_deploy(media_root=Path("/"))

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)
    ##
    ## Asserted on *which* guard fired. Without this the test passes whenever
    ## ``/`` happens not to be writable by the test user, which would leave the
    ## rule that actually matters - never mount the filesystem root - untested
    ## on any host where that happens to be true.
    ##
    self.assertIn("filesystem root", completed.stderr)

  def test_an_ancestor_of_the_media_root_is_not_silently_accepted(self):
    ##
    ## A writable directory that happens to sit above the media tree passes
    ## every other check. What stops it is that the operator has to name the
    ## media root itself, and the deployment mounts exactly what it was given -
    ## so the mount argument is pinned to the resolved value rather than to
    ## anything derived from it.
    ##
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    mounts = [line for line in log.splitlines() if "--volume" in line]
    self.assertTrue(mounts)
    for line in mounts:
      self.assertNotIn("--volume /tmp:", line)
      self.assertNotIn("--volume /:", line)

  ##
  ## The cpu controller is not delegated to a rootless user slice on this host,
  ## so a ``--cpus`` request cannot be honoured. Silently dropping it would be
  ## the worst answer: the operator would believe a limit is in force.
  ##
  def test_a_cpu_limit_request_is_refused_rather_than_ignored(self):
    completed, log = self.run_deploy(extra=["--cpus", "4.0"])

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_no_cpu_limit_is_ever_passed_to_the_engine(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertNotIn("--cpus", log)

  def test_a_memory_limit_is_passed_through(self):
    completed, log = self.run_deploy(extra=["--memory", "2g"])

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("--memory", log)

  ##
  ## The address is not a secret and travels as an environment value. The
  ## password is, and has no argument to travel through at all.
  ##
  def test_the_database_address_is_passed_but_never_the_password(self):
    completed, log = self.run_deploy(db_host="10.88.0.1")

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("SMSD_DB_HOST=10.88.0.1", log)
    combined = log + completed.stdout + completed.stderr
    self.assertNotIn(unified_config()["database"]["password"], combined)
    self.assertNotIn("SMSD_DB_PASSWORD", combined)

  def test_the_container_is_never_privileged_and_mounts_no_engine_socket(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    for forbidden in ("--privileged", "docker.sock", "podman.sock", "-v /:"):
      self.assertNotIn(forbidden, log)

  ##
  ## >>================ the host publication contract ================>>
  ##
  ## Two different things are easy to conflate here. Inside the container the
  ## application must listen on ``0.0.0.0`` or nothing outside its namespace
  ## could ever reach it - that is the staged config's job. What the *host*
  ## exposes is a separate decision, and it is the one that changes who can
  ## reach production.
  ##
  ## Production today serves on ``0.0.0.0:5000``. Narrowing that is a change
  ## worth making deliberately and not one to bundle into a cutover, so the
  ## address is stated on the command line rather than defaulted.
  ##

  def test_the_publication_address_must_be_stated(self):
    completed, log = self.run_deploy(publish_address=None)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("engine run", log)

  def test_the_stated_publication_address_is_what_gets_published(self):
    for address in ("0.0.0.0", "127.0.0.1"):
      with self.subTest(address=address):
        completed, log = self.run_deploy(publish_address=address)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("--publish {}:".format(address), log)

  def test_an_address_that_is_not_an_address_is_refused(self):
    for hostile in ("0.0.0.0 --privileged", "; rm -rf /", "not-an-address!"):
      with self.subTest(value=hostile):
        completed, log = self.run_deploy(publish_address=hostile)

        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn("engine run", log)

  ##
  ## Host networking would reach the host database by dissolving the boundary
  ## rather than by routing across it, and it would silently publish every port
  ## the container opens. The route to the database is explicit instead.
  ##
  def test_host_networking_is_never_used(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertNotIn("--network=host", log)
    self.assertNotIn("--network host", log)


##
## >>================== the identity the application really has ==================>>
##
## Under a rootless engine the entrypoint and the application are different
## *host* users: container root maps to the operator and the unprivileged
## account maps into the subordinate range. A bind mount the operator owns is
## therefore readable by the entrypoint and unwritable by the application, and a
## deployment without an explicit mapping starts cleanly and fails on the first
## recording it tries to write.
##
class ExternalDeployApplicationIdentityTest(ExternalDeployTestCase):
  def test_the_application_account_is_mapped_onto_the_host_operator(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("--userns keep-id:uid=999,gid=999", log)

  def test_the_mapping_follows_the_image_rather_than_a_hard_coded_number(self):
    completed, log = self.run_deploy(application_uid=1500, application_gid=1600)

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertIn("--userns keep-id:uid=1500,gid=1600", log)
    self.assertNotIn("uid=999", log)

  ##
  ## ``keep-id:uid=0`` would put the operator at container root: a privilege the
  ## application does not need, and a sign the image stopped dropping them.
  ##
  def test_an_application_account_that_resolves_to_root_is_refused(self):
    for uid, gid in ((0, 999), (999, 0)):
      with self.subTest(uid=uid, gid=gid):
        completed, log = self.run_deploy(application_uid=uid, application_gid=gid)

        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn("run --detach", log, "a container was started anyway")

  def test_a_malformed_application_identity_is_refused(self):
    completed, log = self.run_deploy(application_uid="nine-nine-nine")

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("run --detach", log)

  def test_an_image_that_cannot_resolve_the_account_is_refused(self):
    completed, log = self.run_deploy(identity_query_fails=True)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("run --detach", log)

  ##
  ## The mapping is the whole mechanism. Changing ownership would be the other
  ## way to make the write work, and it would rewrite two terabytes of somebody
  ## else's library to do it.
  ##
  def test_production_ownership_is_never_rewritten_to_make_the_write_work(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    for forbidden in ("chown", "chmod", ":U", "--privileged"):
      self.assertNotIn(forbidden, log)

  ##
  ## With the mapping in force the application acts on the bind mount as this
  ## operator. So a tree this operator cannot write is a tree the application
  ## cannot write, and the check is only meaningful because of the mapping.
  ##
  def test_a_media_root_this_operator_cannot_write_is_refused(self):
    directory = Path(tempfile.mkdtemp())
    self.addCleanup(shutil.rmtree, directory, True)
    unwritable = directory / "media"
    unwritable.mkdir()
    unwritable.chmod(0o555)
    self.addCleanup(unwritable.chmod, 0o755)

    completed, log = self.run_deploy(media_root=unwritable)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("run --detach", log)
    self.assertIn("writable", completed.stderr)

  def test_the_postcheck_is_told_which_identity_to_prove(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    postcheck = [line for line in log.splitlines() if line.startswith("postcheck")]
    self.assertEqual(1, len(postcheck))
    self.assertIn("--application-user appuser", postcheck[0])
    self.assertIn("--application-uid 999", postcheck[0])
    self.assertIn("--application-gid 999", postcheck[0])


##
## >>===================== the transactional boundary =====================>>
##
## Before the run, every failure is a refusal and nothing exists. After it, a
## writer is up against the production database - so every failure between the
## run and the postcheck passing has to take that writer back down, or the
## script has produced the exact outcome its refusals exist to prevent while
## reporting failure.
##
class ExternalDeployRollbackTest(ExternalDeployTestCase):
  def removals(self, log: str) -> list:
    return [line for line in log.splitlines() if line.startswith("engine rm")]

  def test_a_postcheck_failure_removes_the_container_this_invocation_started(self):
    completed, log = self.run_deploy(postcheck_exit=1)

    self.assertNotEqual(0, completed.returncode)
    self.assertEqual(1, len(self.removals(log)), log)
    self.assertIn("rolled back", completed.stderr)

  def test_an_image_mismatch_after_the_start_removes_the_container(self):
    completed, log = self.run_deploy(running_image_id="sha256:" + "9" * 64)

    self.assertNotEqual(0, completed.returncode)
    self.assertEqual(1, len(self.removals(log)), log)

  ##
  ## By identifier, never by name. The one container this must never touch is a
  ## pre-existing writer, and a name is a label an engine will happily move.
  ##
  def test_the_cleanup_targets_the_identifier_the_engine_returned(self):
    other = "fedcba9876543210" + "0" * 48
    completed, log = self.run_deploy(
      postcheck_exit=1, container_id_value=other
    )

    self.assertNotEqual(0, completed.returncode)
    removals = self.removals(log)
    self.assertEqual(1, len(removals))
    self.assertIn(other, removals[0])
    self.assertNotIn("smsd-app", removals[0])

  def test_a_successful_deployment_removes_nothing(self):
    completed, log = self.run_deploy()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertEqual([], self.removals(log))

  def test_a_failure_before_the_start_removes_nothing(self):
    completed, log = self.run_deploy(existing_container="already-running")

    self.assertNotEqual(0, completed.returncode)
    self.assertEqual([], self.removals(log))
    self.assertNotIn("run --detach", log)

  ##
  ## The one outcome that may not be reported as a plain failure. An operator
  ## reading "refused" would reasonably conclude nothing is running.
  ##
  ##
  ## >>============ removal reported success is not the same as gone ============>>
  ##
  ## The rollback used to ask ``inspect`` for ``.State.Running`` and accept two
  ## different answers as success. ``false`` means the container is still there
  ## and merely stopped - it still holds the name, and the next deployment would
  ## refuse because of it. And a failed inspect produced no value, which read as
  ## "not running" and so as gone: the one case where the engine could not answer
  ## became the case where it answered reassuringly.
  ##
  ## Each of the three outcomes now has a case that only it produces.
  ##
  def test_a_rollback_is_reported_only_once_the_exact_id_is_proven_absent(self):
    completed, log = self.run_deploy(postcheck_exit=1)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("rolled back", completed.stderr)
    self.assertNotIn("DEPLOYMENT INCOMPLETE", completed.stderr)
    ##
    ## Asked of the whole list, by exact identifier, not by name.
    ##
    queries = [
      line for line in log.splitlines()
      if line.startswith("engine ps") and "--filter id=" in line
    ]
    self.assertEqual(1, len(queries), log)
    self.assertIn(CONTAINER_ID, queries[0])
    self.assertIn("--all", queries[0])
    self.assertIn("--no-trunc", queries[0])
    self.assertNotIn("smsd-app", queries[0])

  ##
  ## Stopped is not gone. It still holds the name.
  ##
  def test_a_container_that_still_exists_but_is_stopped_is_incomplete(self):
    completed, log = self.run_deploy(
      postcheck_exit=1, exists_after_removal=CONTAINER_ID
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("DEPLOYMENT INCOMPLETE", completed.stderr)
    self.assertIn("WRITER STATE UNKNOWN", completed.stderr)
    self.assertNotIn("rolled back", completed.stderr)

  ##
  ## An engine that cannot answer has not answered "absent".
  ##
  def test_an_engine_that_cannot_answer_the_existence_query_is_incomplete(self):
    completed, log = self.run_deploy(
      postcheck_exit=1, existence_query_fails=True
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("DEPLOYMENT INCOMPLETE", completed.stderr)
    self.assertIn("WRITER STATE UNKNOWN", completed.stderr)
    self.assertNotIn("rolled back", completed.stderr)

  ##
  ## And a different container coming back from the prefix filter is not this
  ## one, so it must not be read as "still there".
  ##
  def test_another_containers_identifier_does_not_block_the_rollback(self):
    completed, log = self.run_deploy(
      postcheck_exit=1, exists_after_removal="a" * 64
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("rolled back", completed.stderr)
    self.assertNotIn("DEPLOYMENT INCOMPLETE", completed.stderr)

  def test_an_engine_that_cannot_remove_reports_an_incomplete_deployment(self):
    completed, log = self.run_deploy(postcheck_exit=1, remove_fails=True)

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("DEPLOYMENT INCOMPLETE", completed.stderr)
    self.assertIn("WRITER STATE UNKNOWN", completed.stderr)

  ##
  ## The path no ``fail`` covers.
  ##
  ## Every refusal calls the rollback by name, which is easy to read and easy to
  ## verify. ``set -e`` killing the script at an unguarded command is neither -
  ## and the image-identity inspect is unguarded on purpose, because its output
  ## is the value being compared. So an engine that dies there takes the script
  ## with it, and the only thing between that and a live second writer is the
  ## exit trap.
  ##
  def test_an_engine_that_dies_at_an_unguarded_command_still_rolls_back(self):
    completed, log = self.run_deploy(inspect_image_fails=True)

    self.assertNotEqual(0, completed.returncode)
    self.assertEqual(1, len(self.removals(log)), log)
    self.assertNotIn("postcheck", log, "the deployment continued past the failure")

  def test_the_rollback_is_armed_for_signals_as_well(self):
    source = DEPLOY_SCRIPT.read_text(encoding="utf-8")

    self.assertIn(
      """trap 'abandon_started_container "interrupted"; exit 130' HUP INT TERM""",
      source,
    )
    self.assertIn(
      """trap 'abandon_started_container "the deployment did not complete"' EXIT""",
      source,
    )

  def test_an_identifier_the_engine_did_not_return_is_never_removed_blind(self):
    completed, log = self.run_deploy(container_id_value="not-an-identifier")

    self.assertNotEqual(0, completed.returncode)
    self.assertIn("DEPLOYMENT INCOMPLETE", completed.stderr)
    self.assertEqual([], self.removals(log))


if __name__ == "__main__":
  unittest.main()
