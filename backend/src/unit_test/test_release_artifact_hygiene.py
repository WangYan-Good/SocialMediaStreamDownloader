import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HYGIENE_SCRIPT = PROJECT_ROOT / "scripts" / "check_release_artifact_hygiene.py"
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
SECURITY_DOC = PROJECT_ROOT / "docs" / "security.md"


def load_hygiene_module():
  spec = importlib.util.spec_from_file_location(
    "check_release_artifact_hygiene", HYGIENE_SCRIPT
  )
  if spec is None or spec.loader is None:
    raise AssertionError("release artifact hygiene guard cannot be imported")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


class ReleaseArtifactHygieneTest(unittest.TestCase):
  def create_policy_root(self, temporary: str) -> Path:
    root = Path(temporary)
    (root / ".gitignore").write_text(
      "/api/douyin/*.json\n", encoding="utf-8"
    )
    (root / ".dockerignore").write_text(
      "/api/douyin/\n", encoding="utf-8"
    )
    return root

  def test_repository_policy_accepts_clean_tree_and_synthetic_test_fixture(self):
    module = load_hygiene_module()
    with tempfile.TemporaryDirectory() as temporary:
      root = self.create_policy_root(temporary)

      issues = module.check_repository_hygiene(
        root,
        tracked_paths=[
          "backend/src/unit_test/fixtures/douyin/synthetic-response.json"
        ],
      )

    self.assertEqual([], issues)

  def test_repository_policy_rejects_tracked_capture(self):
    module = load_hygiene_module()
    with tempfile.TemporaryDirectory() as temporary:
      root = self.create_policy_root(temporary)

      issues = module.check_repository_hygiene(
        root,
        tracked_paths=["api/douyin/synthetic-capture.json"],
      )

    self.assertIn("tracked upstream response capture", "\n".join(issues))

  def test_repository_policy_requires_gitignore_capture_rule(self):
    module = load_hygiene_module()
    with tempfile.TemporaryDirectory() as temporary:
      root = self.create_policy_root(temporary)
      (root / ".gitignore").write_text("/downloads/\n", encoding="utf-8")

      issues = module.check_repository_hygiene(root, tracked_paths=[])

    self.assertIn(".gitignore", "\n".join(issues))

  def test_repository_policy_requires_docker_context_capture_rule(self):
    module = load_hygiene_module()
    with tempfile.TemporaryDirectory() as temporary:
      root = self.create_policy_root(temporary)
      (root / ".dockerignore").write_text("docs/\n", encoding="utf-8")

      issues = module.check_repository_hygiene(root, tracked_paths=[])

    self.assertIn(".dockerignore", "\n".join(issues))

  def test_image_policy_rejects_capture_without_reading_it(self):
    module = load_hygiene_module()
    with tempfile.TemporaryDirectory() as temporary:
      root = Path(temporary)
      capture_directory = root / "api" / "douyin"
      capture_directory.mkdir(parents=True)
      capture = capture_directory / "synthetic-capture.json"
      capture.write_text("not inspected", encoding="utf-8")

      issues = module.check_image_hygiene(root)

    self.assertIn("production image contains upstream response capture", issues)

  def test_ci_runs_repository_and_production_image_negative_guards(self):
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    parsed_workflow = yaml.safe_load(workflow)

    self.assertIn(
      "python scripts/check_release_artifact_hygiene.py", workflow
    )
    self.assertIn(
      "--image-root /app", workflow
    )
    self.assertTrue(
      {
        "Python tests",
        "MySQL schema and migrations",
        "Frontend build and tests",
        "Docker build and runtime smoke",
      }.issubset({job["name"] for job in parsed_workflow["jobs"].values()}),
    )

  def test_security_contract_treats_real_captures_as_non_release_assets(self):
    security = SECURITY_DOC.read_text(encoding="utf-8")

    self.assertIn("真实上游 API 响应只属于诊断或开发过程", security)
    self.assertIn("不得以 JSON capture", security)
    self.assertIn("不得进入 production image", security)
    self.assertIn("最小 synthetic fixture", security)


if __name__ == "__main__":
  unittest.main()
