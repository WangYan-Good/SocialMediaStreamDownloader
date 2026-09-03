from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
README = PROJECT_ROOT / "README.md"
MIGRATION_GUIDE = PROJECT_ROOT / "docs" / "operations" / "migrations.md"
RELEASE_GUIDE = PROJECT_ROOT / "docs" / "operations" / "release.md"
RELEASE_RECORD = PROJECT_ROOT / "docs" / "operations" / "release-record-template.md"


class ReleaseOperationsDocumentationTest(unittest.TestCase):
  def test_readme_links_the_current_migration_guide(self):
    text = README.read_text(encoding="utf-8")

    self.assertTrue(MIGRATION_GUIDE.is_file())
    self.assertIn("docs/operations/migrations.md", text)

  def test_readme_no_longer_presents_the_0003_release_as_current(self):
    text = README.read_text(encoding="utf-8")

    self.assertNotIn("升级到作品下载版本", text)
    self.assertNotRegex(
      text,
      r"migration_cli\s+downgrade\s+(?:\\\s*)?000[0-9]_",
    )

  def test_generic_rollback_uses_an_explicit_reviewed_target(self):
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")

    self.assertIn("TARGET_REVISION=<reviewed revision>", text)
    self.assertIn('"$TARGET_REVISION"', text)
    self.assertIn("release compatibility record", text)
    self.assertNotRegex(
      text,
      r"migration_cli\s+downgrade\s+(?:\\\s*)?00[0-9][0-9]_",
    )
    self.assertNotRegex(text, r"migration_cli\s+downgrade\s+-1(?:\s|$)")

  def test_migration_preflight_and_postcheck_are_mandatory(self):
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")

    for required in (
      "migration_cli status",
      "migration_cli check",
      "pre-upgrade backup",
      "state=ready",
      "current=head",
      "post-upgrade gate",
    ):
      with self.subTest(required=required):
        self.assertIn(required, text)

  def test_release_guide_is_part_of_the_operator_surface(self):
    text = README.read_text(encoding="utf-8")

    self.assertTrue(RELEASE_GUIDE.is_file())
    self.assertIn("docs/operations/release.md", text)

  def test_release_guide_distinguishes_backup_and_rollback_models(self):
    text = RELEASE_GUIDE.read_text(encoding="utf-8")

    for required in (
      "App-only rollback",
      "Schema-changing rollback default",
      "In-place downgrade",
      "pre-release full backup restore",
      ".smsd-recording-recovery/",
      "fresh/isolated",
      "release_postcheck.sh",
    ):
      with self.subTest(required=required):
        self.assertIn(required, text)

  def test_restore_guide_matches_the_safe_logical_restore_contract(self):
    text = RELEASE_GUIDE.read_text(encoding="utf-8")

    for required in (
      "--health-url HEALTH_URL",
      "logical restore",
      "raw mysql_data",
      "new MySQL root secret",
      "database.name",
      "backup manifest",
      "canonical config.yml",
    ):
      with self.subTest(required=required):
        self.assertIn(required, text)

  def test_release_guide_does_not_claim_file_edits_rotate_credentials(self):
    text = RELEASE_GUIDE.read_text(encoding="utf-8")

    self.assertIn("不会修改 MySQL account", text)
    self.assertIn("不会 rotate 已初始化", text)
    self.assertIn("不能只改文件然后 restart", text)
    for command in (
      "set-password",
      "disable-user",
      "enable-user",
      "revoke-sessions",
    ):
      self.assertIn(command, text)

  def test_backup_is_documented_as_sensitive_without_plaintext_credentials(self):
    text = RELEASE_GUIDE.read_text(encoding="utf-8")
    lowered = " ".join(text.lower().split())

    for required in (
      "plaintext deployment credentials",
      "raw session tokens",
      "csrf tokens",
      "mysql root secret",
      "password hashes",
      "session-token hashes",
      "entire backup bundle",
      "sensitive data",
    ):
      with self.subTest(required=required):
        self.assertIn(required, lowered)
    for forbidden in (
      "backup bundle contains no secrets",
      "backup bundle contains no session material",
      "整个 backup bundle 不包含敏感数据",
    ):
      with self.subTest(forbidden=forbidden):
        self.assertNotIn(forbidden, lowered)

  def test_release_guide_deploys_only_the_promoted_tested_digest(self):
    text = RELEASE_GUIDE.read_text(encoding="utf-8")

    for required in (
      "develop push CI",
      "promotion manifest",
      "ghcr.io/OWNER/REPOSITORY@sha256:",
      "release_deploy.sh",
      "--expected-revision",
      "--no-build",
      "不得从 Git checkout 重新 docker build",
      "running image ID",
    ):
      with self.subTest(required=required):
        self.assertIn(required, text)

  def test_release_record_captures_artifact_identity_without_registry_credentials(self):
    text = RELEASE_RECORD.read_text(encoding="utf-8")
    for required in (
      "source_commit_sha",
      "source_tree_sha",
      "ci_run_id",
      "tested_image_id",
      "promotion_digest",
      "requirements_sha256",
      "python_base_digest",
      "node_base_digest",
      "mysql_digest",
      "postcheck_image_identity",
    ):
      with self.subTest(required=required):
        self.assertIn(required, text)
    self.assertIn("registry credential", text)


if __name__ == "__main__":
  unittest.main()
