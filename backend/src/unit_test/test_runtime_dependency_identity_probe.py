import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROBE = PROJECT_ROOT / "scripts" / "runtime_dependency_identity_probe.py"


def load_probe():
  spec = importlib.util.spec_from_file_location(
    "runtime_dependency_identity_probe", PROBE
  )
  if spec is None or spec.loader is None:
    raise AssertionError("runtime dependency identity probe cannot be imported")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


class RuntimeDependencyIdentityProbeTest(unittest.TestCase):
  def setUp(self):
    self.probe = load_probe()
    self.temporary = tempfile.TemporaryDirectory()
    self.lock = Path(self.temporary.name) / "requirements.txt"
    self.lock.write_text(
      "Example_Package==1.2.3 \\\n    --hash=sha256:" + "a" * 64 + "\n"
      "second.package==4.5.6 \\\n    --hash=sha256:" + "b" * 64 + "\n",
      encoding="utf-8",
    )

  def tearDown(self):
    self.temporary.cleanup()

  def test_exact_lock_hash_versions_and_pip_check_pass(self):
    versions = {"example-package": "1.2.3", "second-package": "4.5.6"}
    pip_checks = []

    installed = self.probe.verify_dependency_identity(
      self.lock,
      expected_lock_sha=self.probe.sha256_file(self.lock),
      version_reader=lambda name: versions[name],
      pip_check=lambda: pip_checks.append(True),
    )

    self.assertEqual(versions, installed)
    self.assertEqual([True], pip_checks)

  def test_lock_hash_mismatch_fails_before_version_reads(self):
    reads = []
    with self.assertRaisesRegex(ValueError, "lock SHA-256"):
      self.probe.verify_dependency_identity(
        self.lock,
        expected_lock_sha="0" * 64,
        version_reader=lambda name: reads.append(name),
        pip_check=lambda: None,
      )
    self.assertEqual([], reads)

  def test_failed_identity_never_prints_the_runtime_marker(self):
    result = subprocess.run(
      [
        sys.executable,
        str(PROBE),
        "--requirements",
        str(self.lock),
        "--expected-lock-sha",
        "0" * 64,
      ],
      text=True,
      capture_output=True,
    )

    self.assertNotEqual(0, result.returncode)
    self.assertNotIn("ok   runtime locked dependency identity", result.stdout)

  def test_missing_or_wrong_installed_version_fails_before_pip_check(self):
    for versions in (
      {"example-package": "1.2.3"},
      {"example-package": "9.9.9", "second-package": "4.5.6"},
    ):
      checks = []

      def version_reader(name):
        if name not in versions:
          raise self.probe.PackageNotFoundError(name)
        return versions[name]

      with self.subTest(versions=versions), self.assertRaisesRegex(
        ValueError, "missing|version mismatch"
      ):
        self.probe.verify_dependency_identity(
          self.lock,
          expected_lock_sha=self.probe.sha256_file(self.lock),
          version_reader=version_reader,
          pip_check=lambda: checks.append(True),
        )
      self.assertEqual([], checks)

  def test_only_fixed_bootstrap_tools_may_be_excluded(self):
    self.assertEqual(frozenset({"pip"}), self.probe.BOOTSTRAP_EXCLUSIONS)

  def test_lock_parser_normalizes_extras_without_changing_distribution_identity(self):
    self.lock.write_text(
      "urllib3[socks]==2.6.3 \\\n    --hash=sha256:" + "c" * 64 + "\n",
      encoding="utf-8",
    )

    self.assertEqual({"urllib3": "2.6.3"}, self.probe.parse_lock(self.lock))


if __name__ == "__main__":
  unittest.main()
