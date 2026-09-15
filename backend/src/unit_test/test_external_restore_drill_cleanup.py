##
## The drill is not finished until the host is as it was found.
##
## Cleanup used to be a warning printed on the way out: the marker went first,
## and a failure to remove the container, the database or the cloned tree
## produced a line on stderr and an exit status of zero. So "the bundle is
## restorable" and "there is now an orphaned database, a running container and a
## cloned media tree on this host" were the same result.
##
## They are not the same result. The next run of the drill meets that leftover
## as a refusal - it requires a database name that does not exist and a
## destination that is empty - and an operator reading a green line has no
## reason to look.
##
## These tests run the real script against stubbed collaborators, because the
## question is about the script's own ordering and exit status, which is exactly
## what a contract test that greps the file cannot answer.
##
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

import yaml

from backend.src.unit_test.config_fixture import unified_config


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DRILL = PROJECT_ROOT / "scripts" / "release_external_restore_drill.sh"
MARKER = "ok   runtime external host restore drill"

IMAGE = "ghcr.io/wangyan-good/socialmediastreamdownloader@sha256:" + "a" * 64
REVISION = "b" * 40
CONTAINER_ID = "0123456789ab" + "cdef" * 13


def reflink_supported(directory: Path) -> bool:
  source = directory / ".probe-src"
  target = directory / ".probe-dst"
  try:
    source.write_bytes(b"probe")
    return subprocess.run(
      ["cp", "--reflink=always", str(source), str(target)], capture_output=True
    ).returncode == 0
  finally:
    for path in (source, target):
      try:
        path.unlink()
      except FileNotFoundError:
        pass


class RestoreDrillCleanupTest(unittest.TestCase):
  def python_command(self, directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path

  def command(self, directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(
      "#!/usr/bin/env bash\nset -uo pipefail\n" + body, encoding="utf-8"
    )
    path.chmod(0o700)
    return path

  def run_drill(self, **overrides):
    root = Path(tempfile.mkdtemp())
    self.addCleanup(self.force_remove, root)
    if not reflink_supported(root):
      self.skipTest("the scratch filesystem cannot reflink")

    ##
    ## A snapshot that really exists, because the drill clones it and then
    ## compares what it produced against the document.
    ##
    snapshot = root / "snapshot"
    (snapshot / ".smsd-recording-recovery").mkdir(parents=True)
    (snapshot / "a.flv").write_bytes(b"recording")
    (snapshot / ".smsd-recording-recovery" / "k.json").write_text("{}", encoding="utf-8")

    bundle = root / "bundle"
    bundle.mkdir()
    (bundle / "database.sql").write_text("-- dump\n", encoding="utf-8")
    entries = []
    for path in sorted(snapshot.rglob("*")):
      if path.is_file():
        entries.append({
          "relative_path": str(path.relative_to(snapshot)),
          "size": path.stat().st_size,
          "mtime_ns": path.stat().st_mtime_ns,
          "device": path.stat().st_dev,
          "inode": path.stat().st_ino,
        })
    (bundle / "media-snapshot.json").write_text(
      json.dumps({
        "media_root": str(root / "live-media"),
        "snapshot_path": str(snapshot),
        "entries": entries,
      }),
      encoding="utf-8",
    )

    config = root / "config.yml"
    document = unified_config()
    document["database"]["host"] = "127.0.0.1"
    config.write_text(yaml.safe_dump(document), encoding="utf-8")
    config.chmod(0o600)

    restore_media = root / "restore" / "media"
    calls = root / "calls.log"
    calls.touch()

    ##
    ## These three are invoked as ``$PYTHON_BIN <helper> ...``, exactly as the
    ## real ones are, so the stubs have to be Python rather than shell.
    ##
    bundle_helper = self.python_command(root, "bundle_helper.py", textwrap.dedent(
      """\
      import os, sys
      with open(os.environ["CALL_LOG"], "a") as log:
          log.write("bundle " + " ".join(sys.argv[1:]) + "\\n")
      command = sys.argv[1]
      if command == "field":
          answers = {
              "topology": "external-host",
              "database_name": "smsd_source",
              "source_image": os.environ["BUNDLE_IMAGE"],
              "source_git_commit": os.environ["BUNDLE_REVISION"],
          }
          sys.stdout.write(answers[sys.argv[3]])
      elif command not in (
          "verify", "validate-external-restore-target",
          "require-empty-restore-destination",
      ):
          raise SystemExit(91)
      """
    ))
    snapshot_helper = self.python_command(root, "snapshot_helper.py", textwrap.dedent(
      """\
      import os, sys
      with open(os.environ["CALL_LOG"], "a") as log:
          log.write("snapshot " + " ".join(sys.argv[1:]) + "\\n")
      """
    ))
    invariant_helper = self.python_command(root, "invariant_helper.py", textwrap.dedent(
      """\
      import os, sys
      with open(os.environ["CALL_LOG"], "a") as log:
          log.write("invariants " + " ".join(sys.argv[1:]) + "\\n")
      arguments = sys.argv[1:]
      output = arguments[arguments.index("--output") + 1]
      with open(output, "w") as handle:
          handle.write('{"tables": {"live": {"rows": 5}}}')
      print("database invariants collected: tables=1 rows=5")
      """
    ))
    postcheck = self.command(root, "postcheck.sh", textwrap.dedent(
      """\
      echo "postcheck $*" >> "$CALL_LOG"
      ##
      ## The one place a test can intervene between the media restore and the
      ## cleanup: a parent nothing may unlink from makes the removal fail.
      ##
      if [[ "${LOCK_MEDIA_PARENT:-}" == "true" ]]; then
        chmod 0555 "$(dirname "$RESTORE_MEDIA_ROOT")"
      fi
      exit "${POSTCHECK_STATUS:-0}"
      """
    ))
    engine = self.command(root, "engine.sh", textwrap.dedent(
      """\
      echo "engine $*" >> "$CALL_LOG"
      case "$1 ${2:-}" in
        "pull "*) exit 0 ;;
        "image inspect")
          case "$*" in
            *"org.opencontainers.image.revision"*) printf '%s\\n' "$BUNDLE_REVISION" ;;
            *"io.smsd.requirements.sha256"*) printf '%s\\n' "$LOCK_LABEL" ;;
            *) printf 'sha256:%s\\n' "$(printf 'c%.0s' {1..64})" ;;
          esac ;;
        "run "*)
          case "$*" in
            *"id -u"*) printf '999\\n999\\n' ;;
            *) printf '%s\\n' "$CONTAINER_ID" ;;
          esac ;;
        "exec "*) exit 0 ;;
        "rm "*) [[ "${REMOVE_FAILS:-}" != "true" ]] || exit 1 ;;
        "ps "*)
          [[ "${EXISTENCE_QUERY_FAILS:-}" != "true" ]] || exit 1
          printf '%s' "${CONTAINER_PERSISTS:-}" ;;
        *) exit 91 ;;
      esac
      """
    ))
    mysql = self.command(root, "mysql.sh", textwrap.dedent(
      """\
      echo "mysql $*" >> "$CALL_LOG"
      case "$*" in
        *"information_schema.schemata"*)
          if [[ -f "$STATE_DIR/dropped" ]]; then
            printf '%s\\n' "${DB_PERSISTS:-0}"
          else
            printf '0\\n'
          fi ;;
        *"CREATE DATABASE"*) exit 0 ;;
        *"DROP DATABASE"*)
          [[ "${DROP_FAILS:-}" != "true" ]] || exit 1
          touch "$STATE_DIR/dropped" ;;
        *"information_schema.tables"*) printf '21\\n' ;;
        *) exit 0 ;;
      esac
      """
    ))

    state = root / "state"
    state.mkdir()
    requirements = root / "requirements.txt"
    requirements.write_text("example==1.0\n", encoding="utf-8")
    import hashlib
    lock_sha = hashlib.sha256(requirements.read_bytes()).hexdigest()

    environment = dict(os.environ)
    environment.update({
      "CALL_LOG": str(calls),
      "STATE_DIR": str(state),
      "CONTAINER_ID": CONTAINER_ID,
      "BUNDLE_IMAGE": overrides.pop("bundle_image", IMAGE),
      "BUNDLE_REVISION": REVISION,
      "LOCK_LABEL": overrides.pop("lock_label", lock_sha),
      "RESTORE_MEDIA_ROOT": str(restore_media),
      "PYTHON_BIN": sys.executable,
      "ENGINE_BIN": str(engine),
      "MYSQL_BIN": str(mysql),
      "BUNDLE_HELPER": str(bundle_helper),
      "SNAPSHOT_HELPER": str(snapshot_helper),
      "INVARIANT_HELPER": str(invariant_helper),
      "EXTERNAL_POSTCHECK_SCRIPT": str(postcheck),
      "REQUIREMENTS_FILE": str(requirements),
      "REMOVE_FAILS": "true" if overrides.pop("remove_fails", False) else "",
      "CONTAINER_PERSISTS": (
        CONTAINER_ID if overrides.pop("container_persists", False) else ""
      ),
      "EXISTENCE_QUERY_FAILS": (
        "true" if overrides.pop("existence_query_fails", False) else ""
      ),
      "DROP_FAILS": "true" if overrides.pop("drop_fails", False) else "",
      "DB_PERSISTS": "1" if overrides.pop("db_persists", False) else "0",
      "LOCK_MEDIA_PARENT": (
        "true" if overrides.pop("lock_media_parent", False) else ""
      ),
      "POSTCHECK_STATUS": str(overrides.pop("postcheck_status", 0)),
    })
    self.assertEqual({}, overrides, "unused override")

    completed = subprocess.run(
      [
        "bash", str(DRILL),
        "--backup", str(bundle),
        "--restore-database", "smsd_restore_test_drill",
        "--restore-media-root", str(restore_media),
        "--config-file", str(config),
        "--image", IMAGE,
        "--db-host", "host.containers.internal",
        "--port", "13999",
        "--container-name", "smsd-drill-test",
      ],
      capture_output=True, text=True, env=environment,
    )
    ##
    ## Whatever the test did to the filesystem, leave it removable.
    ##
    try:
      (root / "restore").chmod(0o755)
    except OSError:
      pass
    return completed, calls.read_text(encoding="utf-8"), restore_media

  def force_remove(self, root: Path):
    for path in root.rglob("*"):
      try:
        if path.is_dir():
          path.chmod(0o755)
      except OSError:
        pass
    shutil.rmtree(root, ignore_errors=True)


class RestoreDrillSuccessTest(RestoreDrillCleanupTest):
  def test_a_complete_drill_cleans_up_and_prints_the_marker_once(self):
    completed, log, media = self.run_drill()

    self.assertEqual(0, completed.returncode, completed.stderr)
    self.assertEqual(1, completed.stdout.count(MARKER), completed.stdout)
    self.assertFalse(media.exists(), "the restored media tree was left behind")

  ##
  ## The marker is the last thing, after the removals are proved - not before
  ## them with the removals attempted on the way out.
  ##
  def test_the_removals_are_proved_before_the_marker_is_printed(self):
    completed, log, media = self.run_drill()

    self.assertEqual(0, completed.returncode, completed.stderr)
    lines = log.splitlines()
    removal = next(i for i, line in enumerate(lines) if line.startswith("engine rm"))
    drop = next(i for i, line in enumerate(lines) if "DROP DATABASE" in line)
    self.assertLess(removal, len(lines))
    self.assertLess(drop, len(lines))
    ##
    ## And the container is removed by the identifier the engine returned.
    ##
    self.assertIn(CONTAINER_ID, lines[removal])
    self.assertNotIn("smsd-drill-test", lines[removal])


class RestoreDrillCleanupFailureTest(RestoreDrillCleanupTest):
  def assertFailedWithoutMarker(self, completed):
    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn(MARKER, completed.stdout)

  def test_a_container_that_cannot_be_removed_fails_the_drill(self):
    completed, log, media = self.run_drill(remove_fails=True)

    self.assertFailedWithoutMarker(completed)
    self.assertIn("container was not removed", completed.stderr)

  def test_a_container_that_still_exists_fails_the_drill(self):
    completed, log, media = self.run_drill(container_persists=True)

    self.assertFailedWithoutMarker(completed)
    self.assertIn("still exists", completed.stderr)

  def test_an_engine_that_cannot_confirm_removal_fails_the_drill(self):
    completed, log, media = self.run_drill(existence_query_fails=True)

    self.assertFailedWithoutMarker(completed)
    self.assertIn("could not confirm", completed.stderr)

  def test_a_database_that_cannot_be_dropped_fails_the_drill(self):
    completed, log, media = self.run_drill(drop_fails=True)

    self.assertFailedWithoutMarker(completed)
    self.assertIn("was not dropped", completed.stderr)

  def test_a_database_that_survives_the_drop_fails_the_drill(self):
    completed, log, media = self.run_drill(db_persists=True)

    self.assertFailedWithoutMarker(completed)
    self.assertIn("still exists", completed.stderr)

  def test_a_restored_media_tree_that_cannot_be_removed_fails_the_drill(self):
    completed, log, media = self.run_drill(lock_media_parent=True)

    self.assertFailedWithoutMarker(completed)
    self.assertIn("media tree still exists", completed.stderr)


class RestoreDrillEarlyFailureTest(RestoreDrillCleanupTest):
  ##
  ## An early failure keeps its own meaning. The exit trap still takes the
  ## disposable state away, but the drill fails for the reason it failed - the
  ## cleanup does not overwrite that.
  ##
  def test_a_failing_postcheck_still_removes_what_was_created(self):
    completed, log, media = self.run_drill(postcheck_status=1)

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn(MARKER, completed.stdout)
    self.assertIn("did not pass the external postcheck", completed.stderr)
    self.assertIn("engine rm", log)
    self.assertFalse(media.exists())


if __name__ == "__main__":
  unittest.main()
