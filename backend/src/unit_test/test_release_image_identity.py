##
## What a release command is allowed to run.
##
## One validator, shared by the deployment, the backup and the restore drill,
## because three regular expressions agree only until one of them is edited.
##
## The reason this is worth its own suite is what those scripts do with an
## image: they mount the operator's configuration - the file holding the
## production database password - into it and then run its code against a
## database. An image nobody has pinned is an image somebody can replace, and
## replacing it hands over the credential.
##
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HELPER = PROJECT_ROOT / "scripts" / "release_image_identity.py"

DIGEST = "a" * 64
CANONICAL = "ghcr.io/wangyan-good/socialmediastreamdownloader@sha256:" + DIGEST


def helper_module():
  specification = importlib.util.spec_from_file_location(
    "release_image_identity", HELPER
  )
  module = importlib.util.module_from_spec(specification)
  specification.loader.exec_module(module)
  return module


class CanonicalImageTest(unittest.TestCase):
  def setUp(self):
    self.module = helper_module()

  def test_the_projects_own_digest_is_accepted(self):
    self.assertEqual(CANONICAL, self.module.require_canonical_image(CANONICAL))

  ##
  ## A tag is a name whoever controls the registry can repoint after the review.
  ##
  def test_every_tag_is_refused(self):
    for tag in ("latest", "sha-abcdef", "v1.0", "main"):
      with self.subTest(tag=tag):
        with self.assertRaises(self.module.ImageIdentityError):
          self.module.require_canonical_image(
            "ghcr.io/wangyan-good/socialmediastreamdownloader:" + tag
          )

  ##
  ## A digest from somebody else's repository is not this project's artifact.
  ##
  def test_another_repository_is_refused_even_by_digest(self):
    for repository in (
      "ghcr.io/example/socialmediastreamdownloader",
      "ghcr.io/wangyan-good/somethingelse",
      "docker.io/wangyan-good/socialmediastreamdownloader",
      "localhost/socialmediastreamdownloader",
    ):
      with self.subTest(repository=repository):
        with self.assertRaises(self.module.ImageIdentityError):
          self.module.require_canonical_image(repository + "@sha256:" + DIGEST)

  def test_a_malformed_digest_is_refused(self):
    for suffix in ("@sha256:deadbeef", "@sha256:" + "A" * 64,
                   "@sha1:" + DIGEST, "@sha256:" + "a" * 63, ""):
      with self.subTest(suffix=suffix):
        with self.assertRaises(self.module.ImageIdentityError):
          self.module.require_canonical_image(
            "ghcr.io/wangyan-good/socialmediastreamdownloader" + suffix
          )

  ##
  ## An OCI reference is lowercase; accepting a capitalised spelling would mean
  ## two strings naming one artifact, which is how a comparison starts failing.
  ##
  def test_a_capitalised_repository_is_refused(self):
    with self.assertRaises(self.module.ImageIdentityError):
      self.module.require_canonical_image(
        "ghcr.io/WangYan-Good/SocialMediaStreamDownloader@sha256:" + DIGEST
      )

  def test_nothing_at_all_is_refused(self):
    for value in (None, "", 17):
      with self.subTest(value=value):
        with self.assertRaises(self.module.ImageIdentityError):
          self.module.require_canonical_image(value)

  ##
  ## The refusal reaches a terminal and a ticket, so it does not quote back a
  ## reference an operator may have mistyped a private registry host into.
  ##
  def test_the_refusal_does_not_echo_the_reference(self):
    completed = subprocess.run(
      [sys.executable, str(HELPER), "require-canonical",
       "ghcr.io/private-registry-name/thing@sha256:" + DIGEST],
      capture_output=True, text=True,
    )

    self.assertNotEqual(0, completed.returncode)
    self.assertNotIn("private-registry-name", completed.stderr)


class SharedValidatorTest(unittest.TestCase):
  ##
  ## Every script that hands an image to the engine uses this one, rather than
  ## carrying a regular expression of its own.
  ##
  def test_the_release_scripts_all_defer_to_it(self):
    for name in (
      "release_external_deploy.sh",
      "release_external_backup.sh",
      "release_external_restore_drill.sh",
    ):
      source = (PROJECT_ROOT / "scripts" / name).read_text(encoding="utf-8")
      with self.subTest(script=name):
        self.assertIn("require-canonical", source)
        ##
        ## And none of them re-implements the check.
        ##
        self.assertNotIn("@sha256:[0-9a-f]{64}", source)


if __name__ == "__main__":
  unittest.main()
