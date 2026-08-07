from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_PATHS = [PROJECT_ROOT / "server.py", PROJECT_ROOT / "backend" / "src"]
FORBIDDEN_TEXT = (
  "DEFAULT_BASE_CONFIG_PATH",
  "base_config.yml",
  "config/douyin/api.yml",
  "config/douyin/download.yml",
  "config/douyin/headers.yml",
  "config/douyin/login.yml",
  "config/douyin/post.yml",
  "SERVER_HOST",
  "SERVER_PORT",
  "FLASK_DEBUG",
  "DOUYIN_MSTOKEN",
  "DOUYIN_DISABLE_F2_TOKEN_MANAGER",
)


class DefaultConfigImportTest(unittest.TestCase):
  def test_runtime_sources_have_no_legacy_configuration_dependency(self):
    sources = [PROJECT_ROOT / "server.py"]
    sources.extend(
      path for path in (PROJECT_ROOT / "backend" / "src").rglob("*.py")
      if "unit_test" not in path.parts
    )
    violations = {
      str(path.relative_to(PROJECT_ROOT)): marker
      for path in sources
      for marker in FORBIDDEN_TEXT
      if marker in path.read_text(encoding="utf-8")
    }
    self.assertEqual(violations, {})

  def test_conf_ini_is_referenced_only_by_tests(self):
    production_sources = [
      path for path in (PROJECT_ROOT / "backend" / "src").rglob("*.py")
      if "unit_test" not in path.parts
    ]
    self.assertEqual([
      str(path.relative_to(PROJECT_ROOT))
      for path in production_sources
      if "conf.ini" in path.read_text(encoding="utf-8")
    ], [])


if __name__ == "__main__":
  unittest.main()
