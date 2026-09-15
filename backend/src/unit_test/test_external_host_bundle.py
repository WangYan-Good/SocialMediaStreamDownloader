##
## One bundle format, two topologies.
##
## The Compose backup captures media as ``downloads.tar`` because a named volume
## is small enough to stream into a tar. Production's media is two terabytes on
## a filesystem with 1.8 free, so a tar of it cannot be written at all - not
## slowly, not overnight, not ever. It is captured as a reflink snapshot
## instead, and what travels in the bundle is the snapshot's identity rather
## than its bytes.
##
## That is a different *asset*, not a different format. The manifest, the
## checksum file, the schema-status parsing and the isolated-restore rule are
## the same machinery, because a second backup format would be a second thing to
## get subtly wrong and only one of them would be exercised by any given
## release.
##
## The discriminator is explicit. A bundle says which topology produced it, and
## a reader that does not understand a topology refuses the bundle rather than
## guessing which assets should have been there.
##
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUNDLE_HELPER = PROJECT_ROOT / "scripts" / "release_bundle.py"

SCHEMA_STATUS = "state=ready current=0011_recording_recovery_key heads=0011_recording_recovery_key"


def bundle_module():
  specification = importlib.util.spec_from_file_location(
    "release_bundle_external", BUNDLE_HELPER
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


class ExternalBundleTestCase(unittest.TestCase):
  def setUp(self):
    self.module = bundle_module()

  def snapshot_document(self, **overrides):
    document = {
      "format_version": 1,
      "media_root": "/mnt/video",
      "snapshot_path": "/mnt/video/.smsd-release-snapshot/2026-09-15",
      "entry_count": 2,
      "total_bytes": 24,
      "entries": [
        {
          "relative_path": "douyin/live/a.flv",
          "size": 12,
          "mtime_ns": 1,
          "device": 66,
          "inode": 101,
        },
        {
          "relative_path": ".smsd-recording-recovery/k.json",
          "size": 12,
          "mtime_ns": 2,
          "device": 66,
          "inode": 102,
        },
      ],
    }
    document.update(overrides)
    return document

  def write_external_bundle(self, directory: Path, **overrides):
    (directory / "database.sql").write_bytes(b"-- dump\n")
    (directory / "media-snapshot.json").write_text(
      json.dumps(self.snapshot_document(**overrides)), encoding="utf-8"
    )
    manifest = self.module.write_manifest(
      directory,
      source_git_commit="c" * 40,
      source_image="ghcr.io/example/app@sha256:" + "a" * 64,
      source_project="smsd-external",
      database_name="social_media_stream_downloader_v2",
      schema_status=SCHEMA_STATUS,
      topology=self.module.TOPOLOGY_EXTERNAL,
    )
    self.module.write_checksums(directory, topology=self.module.TOPOLOGY_EXTERNAL)
    return manifest

  def write_compose_bundle(self, directory: Path):
    (directory / "database.sql").write_bytes(b"-- dump\n")
    (directory / "downloads.tar").write_bytes(b"tar-bytes\n")
    manifest = self.module.write_manifest(
      directory,
      source_git_commit="c" * 40,
      source_image="sha256:" + "b" * 64,
      source_project="smsd-compose",
      database_name="smsd",
      schema_status=SCHEMA_STATUS,
    )
    self.module.write_checksums(directory)
    return manifest


class ExternalBundleShapeTest(ExternalBundleTestCase):
  def test_an_external_bundle_names_its_topology_and_its_media_asset(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      manifest = self.write_external_bundle(root)

      self.assertEqual(self.module.TOPOLOGY_EXTERNAL, manifest["topology"])
      ##
      ## The snapshot's identity, not its bytes. The bytes are on the
      ## filesystem the snapshot shares extents with.
      ##
      self.assertIn("media_snapshot_sha256", manifest)
      self.assertNotIn("download_archive_sha256", manifest)

  def test_an_external_bundle_verifies(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_external_bundle(root)

      verified = self.module.verify_bundle(root)

      self.assertEqual(self.module.TOPOLOGY_EXTERNAL, verified["topology"])

  ##
  ## The Compose path is what production is being moved *away* from, and it must
  ## keep working unchanged for as long as it is still the tested one.
  ##
  def test_a_compose_bundle_still_verifies_and_says_so(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_compose_bundle(root)

      verified = self.module.verify_bundle(root)

      self.assertEqual(self.module.TOPOLOGY_COMPOSE, verified["topology"])
      self.assertIn("download_archive_sha256", verified)

  def test_a_bundle_from_an_older_format_still_verifies(self):
    ##
    ## Version 1 predates the topology field. It was only ever written by the
    ## Compose path, so it is read as Compose rather than rejected - a bundle
    ## taken before this change is still a bundle somebody may need.
    ##
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_compose_bundle(root)
      path = root / "manifest.json"
      manifest = json.loads(path.read_text(encoding="utf-8"))
      manifest["format_version"] = 1
      del manifest["topology"]
      path.write_text(json.dumps(manifest), encoding="utf-8")
      self.module.write_checksums(root)

      verified = self.module.verify_bundle(root)

      self.assertEqual(self.module.TOPOLOGY_COMPOSE, verified["topology"])

  def test_a_current_format_bundle_without_a_topology_is_refused(self):
    ##
    ## Only version 1 may be *interpreted* as Compose, and only because it
    ## predates the field and could have been nothing else. A current-format
    ## bundle that does not say which topology produced it is a bundle this
    ## build did not write, and the answer is never to infer one from whatever
    ## the current environment happens to be.
    ##
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_compose_bundle(root)
      path = root / "manifest.json"
      manifest = json.loads(path.read_text(encoding="utf-8"))
      del manifest["topology"]
      path.write_text(json.dumps(manifest), encoding="utf-8")
      self.module.write_checksums(root)

      with self.assertRaises(ValueError):
        self.module.verify_bundle(root)

  def test_an_unknown_topology_is_refused_rather_than_guessed(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_external_bundle(root)
      path = root / "manifest.json"
      manifest = json.loads(path.read_text(encoding="utf-8"))
      manifest["topology"] = "something-else"
      path.write_text(json.dumps(manifest), encoding="utf-8")
      self.module.write_checksums(root, topology=self.module.TOPOLOGY_EXTERNAL)

      with self.assertRaises(ValueError):
        self.module.verify_bundle(root)


class ExternalBundleTamperTest(ExternalBundleTestCase):
  def test_a_tampered_snapshot_manifest_is_caught(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_external_bundle(root)

      snapshot = root / "media-snapshot.json"
      document = json.loads(snapshot.read_text(encoding="utf-8"))
      document["entries"][0]["inode"] = 999
      snapshot.write_text(json.dumps(document), encoding="utf-8")

      with self.assertRaises(ValueError):
        self.module.verify_bundle(root)

  def test_a_missing_media_asset_is_caught(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_external_bundle(root)
      (root / "media-snapshot.json").unlink()

      with self.assertRaises(ValueError):
        self.module.verify_bundle(root)

  ##
  ## A bundle that claims the external topology but carries the Compose asset -
  ## or the other way round - is not a bundle this build produced, and acting on
  ## it would mean restoring something nobody captured.
  ##
  def test_a_topology_whose_assets_do_not_match_is_refused(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      self.write_compose_bundle(root)
      path = root / "manifest.json"
      manifest = json.loads(path.read_text(encoding="utf-8"))
      manifest["topology"] = self.module.TOPOLOGY_EXTERNAL
      path.write_text(json.dumps(manifest), encoding="utf-8")
      self.module.write_checksums(root)

      with self.assertRaises(ValueError):
        self.module.verify_bundle(root)


class SnapshotIdentityTest(ExternalBundleTestCase):
  ##
  ## The media asset is an identity document, so the rules about what counts as
  ## identity live here rather than in the script that writes it.
  ##
  def test_a_snapshot_document_missing_an_identity_field_is_refused(self):
    for field in ("relative_path", "size", "mtime_ns", "device", "inode"):
      with self.subTest(field=field):
        document = self.snapshot_document()
        del document["entries"][0][field]

        with self.assertRaises(ValueError):
          self.module.validate_media_snapshot(document)

  def test_a_snapshot_document_whose_totals_disagree_is_refused(self):
    with self.assertRaises(ValueError):
      self.module.validate_media_snapshot(self.snapshot_document(entry_count=99))

    with self.assertRaises(ValueError):
      self.module.validate_media_snapshot(self.snapshot_document(total_bytes=99))

  def test_a_valid_snapshot_document_is_accepted(self):
    document = self.snapshot_document()

    self.assertEqual(document, self.module.validate_media_snapshot(document))

  ##
  ## The hidden state P18 added lives under the media root and has to travel
  ## with it. A snapshot that captured only the visible tree would restore a
  ## library whose recovery journal and quarantine belonged to another moment.
  ##
  def test_hidden_recovery_state_is_part_of_the_snapshot(self):
    document = self.snapshot_document()

    paths = [entry["relative_path"] for entry in document["entries"]]

    self.assertTrue(
      any(path.startswith(".smsd-recording-recovery/") for path in paths)
    )


if __name__ == "__main__":
  unittest.main()
