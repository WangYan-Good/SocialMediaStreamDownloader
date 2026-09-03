import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHECKER = PROJECT_ROOT / "scripts" / "check_release_reproducibility.py"


def load_checker():
  spec = importlib.util.spec_from_file_location(
    "check_release_reproducibility", CHECKER
  )
  if spec is None or spec.loader is None:
    raise AssertionError("release reproducibility checker cannot be imported")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


class ReleaseReproducibilityTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.checker = load_checker()
    cls.issues = cls.checker.check_repository(PROJECT_ROOT)
    cls.issue_codes = {issue.code for issue in cls.issues}

  def assertContract(self, code):
    messages = "\n".join(str(issue) for issue in self.issues)
    self.assertNotIn(code, self.issue_codes, messages)

  def test_d1_python_production_lock_is_complete_exact_and_hashed(self):
    self.assertContract("python-lock")

  def test_d2_d3_production_and_ci_install_the_hashed_lock(self):
    self.assertContract("python-install")

  def test_d4_floating_pip_bootstrap_is_absent(self):
    self.assertContract("pip-bootstrap")

  def test_d5_d6_python_builder_and_runtime_share_an_immutable_base(self):
    self.assertContract("python-base")

  def test_d7_node_builder_uses_an_immutable_exact_base(self):
    self.assertContract("node-base")

  def test_d8_d9_compose_and_ci_share_an_immutable_mysql_image(self):
    self.assertContract("mysql-image")

  def test_d10_d11_apt_uses_one_fixed_snapshot_and_exact_requested_versions(self):
    self.assertContract("apt-inputs")

  def test_d12_release_critical_actions_are_full_sha_pinned(self):
    self.assertContract("action-pins")

  def test_d13_frontend_installations_remain_lockfile_strict(self):
    self.assertContract("frontend-lock")

  def test_d14_d15_release_deploy_is_digest_only_and_no_build(self):
    self.assertContract("release-deploy")

  def test_d16_promotion_never_rebuilds_the_application_image(self):
    self.assertContract("promotion-rebuild")

  def test_d17_promotion_is_reachable_only_from_develop_pushes(self):
    self.assertContract("promotion-scope")

  def test_d18_promotion_depends_on_all_four_verification_jobs(self):
    self.assertContract("promotion-needs")

  def test_d19_package_write_permission_exists_only_at_promotion_boundary(self):
    self.assertContract("promotion-permissions")

  def test_d20_required_ci_names_remain_byte_for_byte_stable(self):
    self.assertContract("required-ci-names")

  def test_tested_image_is_exported_only_after_every_runtime_proof(self):
    self.assertContract("artifact-order")

  def test_promotion_verifies_archive_source_and_loaded_image_identity(self):
    self.assertContract("promotion-identity")

  def test_promotion_identity_guard_rejects_missing_archive_source_or_loaded_image_checks(self):
    mutations = (
      ('--archive "$ARCHIVE"', '--archive-check-removed "$ARCHIVE"'),
      ('--expected-source-tree "$SOURCE_TREE"', '--source-tree-check-removed "$SOURCE_TREE"'),
      ('--loaded-image-id "$LOADED_IMAGE_ID"', '--loaded-image-check-removed "$LOADED_IMAGE_ID"'),
      ('test "$PULLED_IMAGE_ID" = "$TESTED_IMAGE_ID"', 'test "$PULLED_IMAGE_ID" != "$TESTED_IMAGE_ID"'),
    )
    required_paths = (
      "requirements.in",
      "requirements.txt",
      "Dockerfile",
      "docker-compose.yml",
      "run-server.sh",
      "scripts/release_deploy.sh",
      "docker/debian-snapshot.sources",
      "docker/apt-snapshot.conf",
      "frontend/app/package-lock.json",
      ".github/workflows/ci.yml",
    )
    for original, replacement in mutations:
      with self.subTest(original=original), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for relative in required_paths:
          source = PROJECT_ROOT / relative
          target = root / relative
          target.parent.mkdir(parents=True, exist_ok=True)
          shutil.copyfile(source, target)
        workflow_path = root / ".github/workflows/ci.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn(original, workflow)
        workflow_path.write_text(
          workflow.replace(original, replacement), encoding="utf-8"
        )

        issue_codes = {
          issue.code for issue in self.checker.check_repository(root)
        }

        self.assertIn("promotion-identity", issue_codes)

  def test_phase17b_static_mutation_matrix_is_killed(self):
    mutations = (
      ("M1", "requirements.txt", "aiofiles==24.1.0", "aiofiles>=24.1.0", "python-lock"),
      (
        "M2",
        "requirements.txt",
        "aiofiles==24.1.0 \\\n    --hash=sha256:22a075c9e5a3810f0c2e48f3008c94d68c65d763b9b03857924c99e57355166c \\\n    --hash=sha256:b4ec55f4195e3eb5d7abd1bf7e061763e864dd4954231fb8539a0ef8bb8260e5",
        "aiofiles==24.1.0",
        "python-lock",
      ),
      (
        "M3",
        "Dockerfile",
        "pip install --no-cache-dir --require-hashes -r requirements.txt",
        "pip install --no-cache-dir -r requirements.txt",
        "python-install",
      ),
      (
        "M3-extra",
        "Dockerfile",
        "WORKDIR /build",
        "WORKDIR /build\nRUN pip install bypass-package==1.0",
        "python-install",
      ),
      (
        "M4",
        "Dockerfile",
        "python -m venv /opt/venv &&",
        "python -m venv /opt/venv && pip install --upgrade pip &&",
        "pip-bootstrap",
      ),
      (
        "M5",
        "Dockerfile",
        "python:3.12.14-slim-trixie@sha256:",
        "python:3.12.14-slim-trixie#sha256:",
        "python-base",
      ),
      (
        "M6",
        "Dockerfile",
        "node:24.20.0-bookworm-slim@sha256:",
        "node:24.20.0-bookworm-slim#sha256:",
        "node-base",
      ),
      (
        "M7",
        "docker-compose.yml",
        "mysql:8.0.46@sha256:7dcddc01f13bab2f15cde676d44d01f61fc9f99fe7785e86196dfc07d358ae2b",
        "mysql:8.0",
        "mysql-image",
      ),
      (
        "M8",
        "Dockerfile",
        "ffmpeg=7:7.1.5-0+deb13u1",
        "ffmpeg",
        "apt-inputs",
      ),
      (
        "M9",
        ".github/workflows/ci.yml",
        "          # Phase 17B: compare the lock copied into the production image with",
        "          docker save smsd:ci >/tmp/premature.tar\n          # Phase 17B: compare the lock copied into the production image with",
        "artifact-order",
      ),
      (
        "M10",
        ".github/workflows/ci.yml",
        "      - name: Verify load promote and pull back the tested image",
        "      - name: Forbidden promotion rebuild\n        run: docker build .\n\n      - name: Verify load promote and pull back the tested image",
        "promotion-rebuild",
      ),
      (
        "M17",
        ".github/workflows/ci.yml",
        "    needs: [backend, mysql, frontend, image]",
        "    needs: [backend, frontend, image]",
        "promotion-needs",
      ),
      (
        "M18",
        ".github/workflows/ci.yml",
        "  image:\n    name: Docker build and runtime smoke",
        "  image:\n    name: Docker build and runtime smoke\n    permissions:\n      packages: write",
        "promotion-permissions",
      ),
    )
    required_paths = (
      "requirements.in",
      "requirements.txt",
      "Dockerfile",
      "docker-compose.yml",
      "run-server.sh",
      "scripts/release_deploy.sh",
      "docker/debian-snapshot.sources",
      "docker/apt-snapshot.conf",
      "frontend/app/package-lock.json",
      ".github/workflows/ci.yml",
    )
    for mutation, relative, original, replacement, expected_code in mutations:
      with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for required in required_paths:
          source = PROJECT_ROOT / required
          target = root / required
          target.parent.mkdir(parents=True, exist_ok=True)
          shutil.copyfile(source, target)
        target = root / relative
        contents = target.read_text(encoding="utf-8")
        self.assertIn(original, contents)
        target.write_text(contents.replace(original, replacement, 1), encoding="utf-8")

        issue_codes = {
          issue.code for issue in self.checker.check_repository(root)
        }

        self.assertIn(expected_code, issue_codes)


if __name__ == "__main__":
  unittest.main()
