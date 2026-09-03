import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_HELPER = PROJECT_ROOT / "scripts" / "release_artifact_manifest.py"
PYTHON_BASE = (
  "python:3.12.14-slim-trixie@sha256:"
  + "1" * 64
)
NODE_BASE = "node:24.20.0-bookworm-slim@sha256:" + "2" * 64
MYSQL_IMAGE = "mysql:8.0.46@sha256:" + "3" * 64


def load_manifest_helper():
  spec = importlib.util.spec_from_file_location(
    "release_artifact_manifest", MANIFEST_HELPER
  )
  if spec is None or spec.loader is None:
    raise AssertionError("release artifact manifest helper cannot be imported")
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


class ReleaseArtifactManifestTest(unittest.TestCase):
  def setUp(self):
    self.helper = load_manifest_helper()
    self.temporary = tempfile.TemporaryDirectory()
    self.root = Path(self.temporary.name)
    self.archive = self.root / "smsd-tested-image.tar.gz"
    self.requirements = self.root / "requirements.txt"
    self.manifest_path = self.root / "manifest.json"
    self.archive.write_bytes(b"exact tested image archive\n")
    self.requirements.write_bytes(b"example==1.0 --hash=sha256:" + b"a" * 64 + b"\n")
    self.values = {
      "source_commit_sha": "4" * 40,
      "source_tree_sha": "5" * 40,
      "image_id": "sha256:" + "6" * 64,
      "python_base_ref": PYTHON_BASE,
      "node_base_ref": NODE_BASE,
      "mysql_image_ref": MYSQL_IMAGE,
      "runtime_marker_count": 18,
      "created_by_workflow": "CI",
    }
    self.helper.create_manifest(
      self.manifest_path,
      archive_path=self.archive,
      requirements_path=self.requirements,
      **self.values,
    )

  def tearDown(self):
    self.temporary.cleanup()

  def verify(self, **overrides):
    arguments = {
      "expected_source_commit": self.values["source_commit_sha"],
      "expected_source_tree": self.values["source_tree_sha"],
      "loaded_image_id": self.values["image_id"],
      "revision_label": self.values["source_commit_sha"],
      "requirements_label": self.helper.sha256_file(self.requirements),
    }
    arguments.update(overrides)
    return self.helper.verify_manifest(
      self.manifest_path,
      archive_path=self.archive,
      requirements_path=self.requirements,
      **arguments,
    )

  def mutate_manifest(self, mutation):
    manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
    mutation(manifest)
    self.manifest_path.write_text(
      json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
    )

  def test_a1_valid_manifest_passes_with_every_identity(self):
    manifest = self.verify()
    self.assertEqual(1, manifest["schema_version"])
    self.assertEqual(18, manifest["runtime_marker_count"])

  def test_a2_archive_sha_mismatch_fails(self):
    self.archive.write_bytes(b"different archive")
    with self.assertRaisesRegex(ValueError, "archive SHA-256"):
      self.verify()

  def test_a3_source_commit_mismatch_fails(self):
    with self.assertRaisesRegex(ValueError, "source commit"):
      self.verify(expected_source_commit="7" * 40)

  def test_a4_source_tree_mismatch_fails(self):
    with self.assertRaisesRegex(ValueError, "source tree"):
      self.verify(expected_source_tree="8" * 40)

  def test_a5_requirements_file_or_label_mismatch_fails(self):
    self.requirements.write_bytes(b"changed lock")
    with self.assertRaisesRegex(ValueError, "requirements SHA-256"):
      self.verify()

  def test_a6_loaded_image_id_mismatch_fails(self):
    with self.assertRaisesRegex(ValueError, "loaded image ID"):
      self.verify(loaded_image_id="sha256:" + "9" * 64)

  def test_a7_revision_or_requirements_label_mismatch_fails(self):
    with self.assertRaisesRegex(ValueError, "revision label"):
      self.verify(revision_label="a" * 40)
    with self.assertRaisesRegex(ValueError, "requirements label"):
      self.verify(requirements_label="b" * 64)

  def test_a8_missing_manifest_field_fails(self):
    self.mutate_manifest(lambda manifest: manifest.pop("source_tree_sha"))
    with self.assertRaisesRegex(ValueError, "missing manifest field"):
      self.verify()

  def test_a9_malformed_digest_fails(self):
    self.mutate_manifest(lambda manifest: manifest.__setitem__("image_id", "latest"))
    with self.assertRaisesRegex(ValueError, "image_id"):
      self.verify()

  def test_a10_unknown_schema_version_fails(self):
    self.mutate_manifest(lambda manifest: manifest.__setitem__("schema_version", 2))
    with self.assertRaisesRegex(ValueError, "schema version"):
      self.verify()

  def test_manifest_is_canonical_private_and_contains_no_credentials(self):
    serialized = self.manifest_path.read_text(encoding="utf-8")
    self.assertEqual(0o600, self.manifest_path.stat().st_mode & 0o777)
    self.assertEqual(serialized, json.dumps(json.loads(serialized), sort_keys=True, separators=(",", ":")) + "\n")
    lowered = serialized.lower()
    for forbidden in ("token", "cookie", "password", "credential"):
      self.assertNotIn(forbidden, lowered)

  def test_promotion_record_links_the_verified_artifact_to_one_registry_digest(self):
    promotion_path = self.root / "promotion.json"

    promotion = self.helper.create_promotion_manifest(
      promotion_path,
      artifact_manifest_path=self.manifest_path,
      registry_digest="ghcr.io/example/smsd@sha256:" + "c" * 64,
      ci_run_id="123456",
      ci_run_attempt="2",
    )

    self.assertEqual(self.values["source_commit_sha"], promotion["source_commit_sha"])
    self.assertEqual(self.values["image_id"], promotion["tested_image_id"])
    self.assertEqual("123456", promotion["ci_run_id"])
    self.assertEqual(0o600, promotion_path.stat().st_mode & 0o777)


if __name__ == "__main__":
  unittest.main()
