##
## Which directories a container may lose, and which it may not.
##
## A container's own filesystem goes away when the container does. That is fine
## for most of what an application writes and fatal for some of it, and the
## difference is not obvious from the outside: the media tree and the recovery
## journal look like ordinary output directories until a restart discovers that
## one of them was the record of what to do next.
##
## So the roots are classified rather than assumed, and the classification is
## pinned here:
##
##   correctness-critical  losing it loses data or bookkeeping the application
##                         cannot reconstruct. Must survive the container.
##   diagnostic            useful afterwards, reconstructible in the sense that
##                         losing it costs explanation rather than state.
##   ephemeral             scratch. Belongs in the container layer.
##
## The Compose topology answers this with named volumes. The external topology
## has to answer it with bind mounts, and this is the test that says so.
##
from pathlib import Path
import unittest

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEPLOY = PROJECT_ROOT / "scripts" / "release_external_deploy.sh"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
CONFIG_EXAMPLE = PROJECT_ROOT / "docs" / "design" / "config.yml.example"

##
## The journal and the quarantine both live *under* the storage root, hidden, so
## a bind mount of the storage root carries them. That is why the media mount is
## the whole root rather than the recording subtree.
##
CORRECTNESS_CRITICAL_UNDER_MEDIA_ROOT = (
  ".smsd-recording-recovery",
  ".smsd-recording-orphan-quarantine",
)


class WritablePathInventoryTest(unittest.TestCase):
  def setUp(self):
    self.deploy = DEPLOY.read_text(encoding="utf-8")
    self.dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    self.example = yaml.safe_load(CONFIG_EXAMPLE.read_text(encoding="utf-8"))

  ##
  ## The one root that must outlive the container, mounted from the host at the
  ## path the database already refers to.
  ##
  def test_the_media_root_is_bind_mounted_rather_than_left_in_the_container(self):
    self.assertIn('--volume "${media_resolved}:${media_resolved}"', self.deploy)

  def test_the_media_mount_is_the_storage_root_not_the_recording_subtree(self):
    ##
    ## Pinned because mounting ``douyin/live`` instead would leave the recovery
    ## journal and the quarantine inside the container, where a restart would
    ## find neither - and the application would conclude nothing was interrupted.
    ##
    self.assertIn("$.download.save_path", self.example_source())
    self.assertNotIn("douyin/live", self.deploy)

  def example_source(self) -> str:
    return (PROJECT_ROOT / "scripts" / "runtime_config.py").read_text(
      encoding="utf-8"
    )

  ##
  ## The hidden state is under the media root by construction, so nothing extra
  ## has to be mounted for it - but that only holds while it stays there.
  ##
  def test_the_hidden_state_lives_under_the_media_root(self):
    from backend.src.service.recording_orphan import QUARANTINE_DIRECTORY_NAME
    from backend.src.service.recording_recovery_journal import (
      JOURNAL_DIRECTORY_NAME,
    )

    self.assertIn(JOURNAL_DIRECTORY_NAME, CORRECTNESS_CRITICAL_UNDER_MEDIA_ROOT)
    self.assertIn(
      QUARANTINE_DIRECTORY_NAME, CORRECTNESS_CRITICAL_UNDER_MEDIA_ROOT
    )
    ##
    ## Both are hidden, which is also what keeps the release snapshot store out
    ## of the orphan scan. One property, two things depending on it.
    ##
    for name in (JOURNAL_DIRECTORY_NAME, QUARANTINE_DIRECTORY_NAME):
      self.assertTrue(name.startswith("."))

  ##
  ## Logs are diagnostic. They are allowed to be a container-layer directory in
  ## external mode - the deployment does not promise to keep them - but the
  ## image must still create them owned by the unprivileged account, or the
  ## application cannot write its own log.
  ##
  def test_the_image_prepares_the_writable_directories_it_keeps(self):
    self.assertIn("/app/logs", self.dockerfile)
    self.assertIn("/app/downloads", self.dockerfile)
    self.assertIn("-o appuser -g appuser", self.dockerfile)

  ##
  ## Never a recursive chown of a mounted tree at startup. On two terabytes it
  ## would take hours, and it would rewrite metadata on media the release is
  ## supposed to leave alone.
  ##
  def test_nothing_recursively_chowns_the_mounted_media(self):
    for source in (self.deploy, self.dockerfile):
      self.assertNotIn("chown -R", source)
      self.assertNotIn("chmod -R", source)

  ##
  ## The deployment mounts what it needs and nothing above it. A mount of the
  ## media root's parent would expose every sibling directory to the container.
  ##
  def test_no_broader_host_path_is_mounted(self):
    for forbidden in ('--volume "/:', "--volume /:", '--volume "/mnt:',
                      '--volume "/home'):
      self.assertNotIn(forbidden, self.deploy)


if __name__ == "__main__":
  unittest.main()
