##
## The whole journal lifecycle against a real filesystem, nothing faked.
##
## The unit tests around it replace one leaf at a time to pin ordering and
## failure handling.  This one replaces nothing: a real directory is created, a
## real note is written, committed, linked, read back and removed.  It is the
## only place that can show the protocol works end to end on the filesystem the
## service will actually run on, rather than on a description of one.
##
from datetime import datetime
from pathlib import Path
import os
import stat
import tempfile
import unittest

from backend.src.service.recording_recovery_journal import (
  JOURNAL_DIRECTORY_NAME,
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import (
  RecordingPersistenceIntent,
  RecordingResourceService,
)

KEY = "0123456789abcdef0123456789abcdef"
OTHER_KEY = "fedcba9876543210fedcba9876543210"


def intent(**overrides):
  base = {
    "app_user_id": 41,
    "platform": "douyin",
    "room_id": "998877",
    "owner_user_id": "owner-1",
    "title": "直播标题",
    "protocol": "hls",
    "output_path": "douyin/live/A/live.mp4",
    "started_at": datetime(2026, 8, 30, 9, 0, 0, 123000),
    "finished_at": datetime(2026, 8, 30, 10, 0, 0, 456000),
    "source": "task_api",
  }
  base.update(overrides)
  return RecordingPersistenceIntent(**base)


class RealFilesystemLifecycleTest(unittest.TestCase):
  def journal(self, root):
    return RecordingRecoveryJournal(
      config_loader=lambda: {"download": {"save_path": str(root)}}
    )

  def test_the_full_lifecycle_runs_against_a_real_directory(self):
    with tempfile.TemporaryDirectory() as root:
      service = self.journal(root)
      original = intent()

      ##
      ## Nothing exists until something is actually recorded.
      ##
      self.assertEqual([], sorted(p.name for p in Path(root).iterdir()))

      published = service.publish(original, KEY)

      directory = Path(root).resolve() / JOURNAL_DIRECTORY_NAME
      self.assertTrue(directory.is_dir())
      self.assertEqual(directory / "{}.json".format(KEY), published)
      self.assertTrue(published.is_file())

      ##
      ## What a replay would reconstruct, read back off the disk.
      ##
      self.assertEqual(original, service.load(KEY))

      service.acknowledge(KEY)

      self.assertFalse(published.exists())
      self.assertIsNone(service.load(KEY))
      ##
      ## And nothing is left behind - no half-written note, no temporary.
      ##
      self.assertEqual([], sorted(p.name for p in directory.iterdir()))

  def test_the_journal_directory_is_private(self):
    with tempfile.TemporaryDirectory() as root:
      service = self.journal(root)
      service.publish(intent(), KEY)

      mode = stat.S_IMODE(service.root().stat().st_mode)
      self.assertEqual(0o700, mode)

  def test_a_published_note_is_private(self):
    with tempfile.TemporaryDirectory() as root:
      service = self.journal(root)
      published = service.publish(intent(), KEY)

      self.assertEqual(0o600, stat.S_IMODE(published.stat().st_mode))

  def test_several_recordings_keep_separate_notes(self):
    with tempfile.TemporaryDirectory() as root:
      service = self.journal(root)
      first = intent(output_path="douyin/a.mp4")
      second = intent(output_path="douyin/b.mp4", app_user_id=42)

      service.publish(first, KEY)
      service.publish(second, OTHER_KEY)

      self.assertEqual(first, service.load(KEY))
      self.assertEqual(second, service.load(OTHER_KEY))

      service.acknowledge(KEY)

      ##
      ## Retiring one leaves the other untouched.
      ##
      self.assertIsNone(service.load(KEY))
      self.assertEqual(second, service.load(OTHER_KEY))

  def test_the_lifecycle_leaks_no_descriptors(self):
    if not os.path.isdir("/proc/self/fd"):
      self.skipTest("requires /proc to count descriptors")
    with tempfile.TemporaryDirectory() as root:
      service = self.journal(root)
      service.publish(intent(), OTHER_KEY)
      service.acknowledge(OTHER_KEY)

      before = len(os.listdir("/proc/self/fd"))
      for index in range(20):
        key = "{:032x}".format(index)
        service.publish(intent(), key)
        service.load(key)
        service.acknowledge(key)
      after = len(os.listdir("/proc/self/fd"))

      self.assertEqual(before, after)

  def test_a_note_survives_a_fresh_service_instance(self):
    ##
    ## The point of writing it down: a later process - the one that restarts
    ## after the crash - reads the same note from the same storage.
    ##
    with tempfile.TemporaryDirectory() as root:
      original = intent()
      self.journal(root).publish(original, KEY)

      restarted = self.journal(root)

      self.assertEqual(original, restarted.load(KEY))


if __name__ == "__main__":
  unittest.main()
