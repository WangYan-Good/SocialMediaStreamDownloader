from pathlib import Path
import unittest
from urllib.parse import urlparse

from backend.src.library.baselib import load_yml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "docs" / "design" / "config.yml.example"


class UnifiedConfigSchemaTest(unittest.TestCase):
  def test_share_url_file_is_not_persistent_configuration(self):
    config = load_yml(CONFIG_EXAMPLE_PATH)

    self.assertNotIn(
      "share_url_file",
      config["platform"]["douyin"]["download"],
    )

  def test_all_legacy_configuration_files_are_removed(self):
    legacy_paths = [
      PROJECT_ROOT / "config" / "base_config.yml",
      PROJECT_ROOT / "config" / "douyin" / "api.yml",
      PROJECT_ROOT / "config" / "douyin" / "download.yml",
      PROJECT_ROOT / "config" / "douyin" / "headers.yml",
      PROJECT_ROOT / "config" / "douyin" / "login.yml",
      PROJECT_ROOT / "config" / "douyin" / "post.yml",
      PROJECT_ROOT / "backend" / "src" / "base" / "default.py",
      PROJECT_ROOT / "backend" / "src" / "platform" / "douyin" / "douyin_config.py",
    ]
    self.assertEqual([path for path in legacy_paths if path.exists()], [])
    self.assertTrue((PROJECT_ROOT / "config" / "douyin" / "conf.ini").is_file())

  def test_example_contains_complete_unified_schema(self):
    config = load_yml(CONFIG_EXAMPLE_PATH)

    self.assertTrue({
      "database",
      "download",
      "log",
      "server",
      "migrate",
      "platform",
    }.issubset(config))

    douyin_config = config["platform"]["douyin"]
    self.assertTrue({
      "download",
      "api",
      "headers",
      "login",
      "post",
      "live",
      "aweme",
    }.issubset(douyin_config))

    self.assertNotIn("stream_url", douyin_config["live"])
    self.assertNotIn("stream_name", douyin_config["live"])

  def test_example_redacts_credentials_and_runtime_identifiers(self):
    config = load_yml(CONFIG_EXAMPLE_PATH)

    self.assertEqual(config["database"]["username"], "<user_name>")
    self.assertEqual(config["database"]["password"], "<password>")
    self.assertEqual(
      config["migrate"]["source_db_username"],
      "<user_name>"
    )
    self.assertEqual(
      config["migrate"]["source_db_password"],
      "<password>"
    )

    sensitive_identifiers = {
      "sec_user_id",
      "sec_uid",
      "webid",
      "web_id",
      "device_id",
      "fp",
      "reflow_id",
      "room_id",
      "strdata",
    }

    def assert_redacted(value):
      if isinstance(value, dict):
        for key, item in value.items():
          normalized_key = str(key).lower()
          is_credential = (
            normalized_key != "cookie_enabled"
            and any(
              marker in normalized_key
              for marker in ("token", "cookie", "verify", "bogus")
            )
          )
          if is_credential or normalized_key in sensitive_identifiers:
            self.assertIsNone(item, f"{key} must be redacted")
          else:
            assert_redacted(item)
      elif isinstance(value, list):
        for item in value:
          assert_redacted(item)

    assert_redacted(config["platform"])

  def test_example_referers_do_not_contain_runtime_identifiers(self):
    config = load_yml(CONFIG_EXAMPLE_PATH)

    def assert_referers_are_generic(value):
      if isinstance(value, dict):
        for key, item in value.items():
          if str(key).lower() == "referer" and isinstance(item, str):
            referer = urlparse(item)
            self.assertIn(referer.path, ("", "/"))
            self.assertEqual(referer.query, "")
            self.assertEqual(referer.fragment, "")
          else:
            assert_referers_are_generic(item)
      elif isinstance(value, list):
        for item in value:
          assert_referers_are_generic(item)

    assert_referers_are_generic(
      config["platform"]["douyin"]["headers"]
    )


if __name__ == "__main__":
  unittest.main()
