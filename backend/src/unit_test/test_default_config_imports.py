import ast
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LEGACY_CONFIG_CONSUMER_FILES = (
  "backend/src/base/downloader.py",
  "backend/src/platform/douyin/douyin_config.py",
  "backend/src/platform/douyin/douyin_post_config.py",
  "backend/src/platform/douyin/douyin_post_downloader.py",
)
UNIFIED_CONFIG_CONSUMER_FILES = (
  "backend/src/platform/douyin/douyin_live_config.py",
  "backend/src/platform/douyin/douyin_live_downloader.py",
)


class DefaultConfigImportTest(unittest.TestCase):
  def test_consumers_import_default_path_from_canonical_module(self):
    for relative_path in LEGACY_CONFIG_CONSUMER_FILES:
      with self.subTest(file=relative_path):
        source_path = PROJECT_ROOT / relative_path
        syntax_tree = ast.parse(source_path.read_text(encoding="utf-8"))

        default_path_import_sources = [
          node.module
          for node in ast.walk(syntax_tree)
          if isinstance(node, ast.ImportFrom)
          for imported_name in node.names
          if imported_name.name == "DEFAULT_BASE_CONFIG_PATH"
        ]

        self.assertEqual(
          default_path_import_sources,
          ["backend.src.base.default"],
          f"{relative_path} must import DEFAULT_BASE_CONFIG_PATH only "
          "from backend.src.base.default",
        )

  def test_unified_config_consumers_do_not_import_legacy_default_path(self):
    for relative_path in UNIFIED_CONFIG_CONSUMER_FILES:
      with self.subTest(file=relative_path):
        source_path = PROJECT_ROOT / relative_path
        syntax_tree = ast.parse(source_path.read_text(encoding="utf-8"))

        default_path_import_sources = [
          node.module
          for node in ast.walk(syntax_tree)
          if isinstance(node, ast.ImportFrom)
          for imported_name in node.names
          if imported_name.name == "DEFAULT_BASE_CONFIG_PATH"
        ]

        self.assertEqual(default_path_import_sources, [])


if __name__ == "__main__":
  unittest.main()
