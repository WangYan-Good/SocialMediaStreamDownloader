import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUNDLE_HELPER = PROJECT_ROOT / "scripts" / "release_bundle.py"
BACKUP_SCRIPT = PROJECT_ROOT / "scripts" / "release_backup.sh"
RESTORE_SCRIPT = PROJECT_ROOT / "scripts" / "release_restore.sh"
DRILL_SCRIPT = PROJECT_ROOT / "scripts" / "release_restore_drill.sh"
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


def load_bundle_helper():
  spec = importlib.util.spec_from_file_location("release_bundle", BUNDLE_HELPER)
  if spec is None or spec.loader is None:
    raise AssertionError("release bundle helper cannot be imported")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


class ReleaseBundleTest(unittest.TestCase):
  def create_bundle(self, root: Path):
    database = root / "database.sql"
    downloads = root / "downloads.tar"
    database.write_bytes(b"database dump\n")
    downloads.write_bytes(b"download archive\n")
    helper = load_bundle_helper()
    helper.write_manifest(
      root,
      source_git_commit="a" * 40,
      source_image="sha256:" + "b" * 64,
      source_project="smsd-release-source",
      database_name="DATABASE_NAME",
      schema_status=(
        "state=ready current=0011_recording_recovery_key "
        "heads=0011_recording_recovery_key"
      ),
    )
    helper.write_checksums(root)
    return helper

  def test_manifest_records_required_nonsecret_release_state(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      helper = self.create_bundle(root)

      manifest = helper.verify_bundle(root)

      self.assertEqual(1, manifest["format_version"])
      self.assertEqual("ready", manifest["schema_status"])
      self.assertEqual(
        "0011_recording_recovery_key", manifest["schema_current"]
      )
      self.assertEqual(
        ["0011_recording_recovery_key"], manifest["schema_heads"]
      )
      self.assertEqual(64, len(manifest["database_dump_sha256"]))
      self.assertEqual(64, len(manifest["download_archive_sha256"]))
      serialized = json.dumps(manifest).lower()
      for forbidden in ("password", "cookie", "csrf", "session_token"):
        self.assertNotIn(forbidden, serialized)

  def test_checksum_mismatch_missing_asset_and_unknown_format_are_refused(self):
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      helper = self.create_bundle(root)
      (root / "downloads.tar").write_bytes(b"tampered")
      with self.assertRaisesRegex(ValueError, "checksum"):
        helper.verify_bundle(root)

      helper = self.create_bundle(root)
      (root / "database.sql").unlink()
      with self.assertRaisesRegex(ValueError, "database.sql"):
        helper.verify_bundle(root)

      helper = self.create_bundle(root)
      manifest_path = root / "manifest.json"
      manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
      manifest["format_version"] = 999
      manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
      helper.write_checksums(root)
      with self.assertRaisesRegex(ValueError, "format"):
        helper.verify_bundle(root)

  def test_restore_project_name_must_be_explicit_isolated_and_not_source(self):
    helper = load_bundle_helper()

    helper.validate_restore_project(
      "smsd-restore-test-unique", source_project="smsd-release-source"
    )
    for unsafe in ("", "smsd", "default", "smsd-release-source", "../escape"):
      with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
        helper.validate_restore_project(
          unsafe, source_project="smsd-release-source"
        )

  def test_bundle_permissions_are_private_even_under_umask_022(self):
    helper = load_bundle_helper()
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary) / "existing-empty-output"
      root.mkdir(mode=0o755)
      root.chmod(0o755)
      previous_umask = os.umask(0o022)
      try:
        helper.prepare_output(root)
        (root / "database.sql").write_bytes(b"database dump\n")
        (root / "downloads.tar").write_bytes(b"download archive\n")
        helper.write_manifest(
          root,
          source_git_commit="a" * 40,
          source_image="sha256:" + "b" * 64,
          source_project="smsd-release-source",
          database_name="DATABASE_NAME",
          schema_status=(
            "state=ready current=0011_recording_recovery_key "
            "heads=0011_recording_recovery_key"
          ),
        )
        helper.write_checksums(root)
      finally:
        os.umask(previous_umask)

      self.assertEqual(0o700, root.stat().st_mode & 0o777)
      for name in (
        "database.sql",
        "downloads.tar",
        "manifest.json",
        "SHA256SUMS",
      ):
        with self.subTest(name=name):
          self.assertEqual(0o600, (root / name).stat().st_mode & 0o777)


class ReleaseScriptContractTest(unittest.TestCase):
  def test_backup_quiesces_app_and_preserves_complete_download_volume(self):
    source = BACKUP_SCRIPT.read_text(encoding="utf-8")

    stop = source.index('stop app')
    dump = source.index("mysqldump --single-transaction")
    archive = source.index("/app/downloads")
    manifest = source.index("write-manifest")
    self.assertLess(stop, dump)
    self.assertLess(dump, archive)
    self.assertLess(archive, manifest)
    self.assertIn("/run/secrets/mysql_root_password", source)
    self.assertIn("--numeric-owner", source)
    self.assertRegex(source, r"-C\s+/app/downloads\s+-cpf\s+-\s+\.")
    self.assertIn("trap restore_app", source)
    self.assertIn("umask 077", source)
    self.assertNotIn("config/config.yml database.sql", source)
    self.assertNotIn("mysql-root-password database.sql", source)

  def test_restore_order_never_starts_app_before_database_and_downloads(self):
    source = RESTORE_SCRIPT.read_text(encoding="utf-8")

    verify = source.index("verify")
    mysql_start = source.index("up -d mysql")
    database_restore = source.index("mysql --protocol=TCP")
    app_create = source.index("create app")
    download_restore = source.index("/app/downloads")
    app_start = source.index("up -d app")
    postcheck = source.index("release_postcheck.sh")
    self.assertEqual(
      sorted(
        [
          verify,
          mysql_start,
          database_restore,
          app_create,
          download_restore,
          app_start,
          postcheck,
        ]
      ),
      [
        verify,
        mysql_start,
        database_restore,
        app_create,
        download_restore,
        app_start,
        postcheck,
      ],
    )
    self.assertIn("validate-restore-project", source)
    self.assertIn("destination project already has recoverable state", source)
    self.assertNotIn("--force", source)

  def test_restore_matches_manifest_database_before_sql_import(self):
    source = RESTORE_SCRIPT.read_text(encoding="utf-8")

    manifest_database = source.index(
      'field "$backup_directory" database_name'
    )
    configured_database = source.index("printenv MYSQL_DATABASE")
    mismatch_refusal = source.index("restore database name differs from backup")
    database_restore = source.index("mysql --protocol=TCP")
    self.assertEqual(
      sorted(
        [
          manifest_database,
          configured_database,
          mismatch_refusal,
          database_restore,
        ]
      ),
      [
        manifest_database,
        configured_database,
        mismatch_refusal,
        database_restore,
      ],
    )

  def test_ci_runs_a_real_disposable_restore_drill_with_an_exact_marker(self):
    helper = load_bundle_helper()
    drill = DRILL_SCRIPT.read_text(encoding="utf-8")
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    marker = "ok   runtime release backup restore drill"

    restore_project = re.search(
      r"^\s*RESTORE_PROJECT=(\S+)\s*$", workflow, re.MULTILINE
    )
    self.assertIsNotNone(restore_project)
    helper.validate_restore_project(
      restore_project.group(1), source_project="smsd-ci-release-source"
    )

    self.assertIn('"$DOCKER_BIN" cp', drill)
    self.assertIn("/tmp/release-drill-seed.py", drill)
    self.assertIn("/tmp/release-drill-verify.py", drill)
    self.assertNotIn("docker exec smsd", drill)
    self.assertNotIn("python - <<", drill)
    self.assertIn(".smsd-recording-recovery", drill)
    self.assertIn("stat -c '%a'", drill)
    self.assertIn("backup directory is not mode 0700", drill)
    self.assertIn("backup asset is not mode 0600", drill)
    self.assertIn("down -v --remove-orphans", drill)
    self.assertIn("recording_record", drill)
    self.assertIn(marker, drill)
    self.assertIn("scripts/release_restore_drill.sh", workflow)
    self.assertIn(f"grep -Fxq '{marker}'", workflow)
    self.assertEqual(1, drill.count(marker))
    self.assertEqual(1, workflow.count(marker))


if __name__ == "__main__":
  unittest.main()
