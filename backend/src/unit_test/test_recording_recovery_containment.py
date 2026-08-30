##
## A journal may only describe media inside the configured storage root.
##
## In the ordinary path the output path comes from the downloader, which wrote
## the file itself, so this check has little to do.  The journal changes that:
## it is a *persistent input to a future replay*, read back after a crash by a
## process that did not record anything.  A note that was corrupted, wrongly
## generated, or rewritten by another local process could otherwise name
## ``/etc/passwd`` or climb out with ``../``, and Phase 11C would catalogue it
## as a recording resource.
##
## The trust root is the *resolved* configured save path, not the literal
## string: an operator is entitled to point ``save_path`` at a symlink or a
## mount, and refusing that would break a legitimate deployment.  Containment
## is a path-segment relationship, never a string prefix - ``/downloads2`` is
## not inside ``/downloads``.
##
from datetime import datetime
from pathlib import Path
import json
import os
import tempfile
import unittest

from backend.src.service.recording_recovery_journal import (
  RecordingJournalCorrupt,
  RecordingJournalUnavailable,
  RecordingRecoveryJournal,
  payload_for,
)
from backend.src.service.recording_resource import RecordingPersistenceIntent

KEY = "0123456789abcdef0123456789abcdef"


def intent(output_path, **overrides):
  base = {
    "app_user_id": 41,
    "platform": "douyin",
    "room_id": "998877",
    "owner_user_id": "owner-1",
    "title": "Launch title",
    "protocol": "hls",
    "output_path": str(output_path),
    "started_at": datetime(2026, 8, 30, 9, 0, 0),
    "finished_at": datetime(2026, 8, 30, 10, 0, 0),
    "source": "task_api",
  }
  base.update(overrides)
  return RecordingPersistenceIntent(**base)


def journal(root):
  return RecordingRecoveryJournal(
    config_loader=lambda: {"download": {"save_path": str(root)}}
  )


class PublishContainmentTest(unittest.TestCase):
  """Refuse before the note is ever written."""

  def test_a_recording_directly_under_the_root_is_accepted(self):
    with tempfile.TemporaryDirectory() as root:
      published = journal(root).publish(
        intent(Path(root) / "live.mp4"), KEY
      )

      self.assertTrue(published.is_file())

  def test_a_nested_recording_is_accepted(self):
    ##
    ## The real shape: douyin/live/<owner>/<file>.
    ##
    with tempfile.TemporaryDirectory() as root:
      nested = Path(root) / "douyin" / "live" / "Test_Host" / "live.mp4"
      nested.parent.mkdir(parents=True)

      published = journal(root).publish(intent(nested), KEY)

      self.assertTrue(published.is_file())

  def test_a_traversal_escape_is_refused(self):
    with tempfile.TemporaryDirectory() as base:
      root = Path(base) / "storage"
      root.mkdir()
      (Path(base) / "outside.mp4").write_bytes(b"x")

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).publish(
          intent(root / "douyin" / ".." / ".." / "outside.mp4"), KEY
        )

  def test_an_absolute_path_outside_the_root_is_refused(self):
    with tempfile.TemporaryDirectory() as root:
      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).publish(intent("/etc/passwd"), KEY)

  def test_a_sibling_directory_sharing_a_prefix_is_refused(self):
    ##
    ## The classic string-prefix bug: ``/downloads2`` starts with
    ## ``/downloads`` and is a completely different directory.
    ##
    with tempfile.TemporaryDirectory() as base:
      root = Path(base) / "downloads"
      root.mkdir()
      sibling = Path(base) / "downloads2"
      sibling.mkdir()

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).publish(intent(sibling / "live.mp4"), KEY)

  def test_the_storage_root_itself_is_not_a_recording(self):
    ##
    ## A recording is a file inside the root, never the root. Accepting the
    ## directory would let a note describe the whole library as one resource.
    ##
    with tempfile.TemporaryDirectory() as root:
      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).publish(intent(root), KEY)

  def test_a_refused_path_leaves_no_note_and_no_temporary(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      try:
        service.publish(intent("/etc/passwd"), KEY)
      except RecordingJournalUnavailable:
        pass

      directory = service.root()
      if directory.exists():
        self.assertEqual([], sorted(p.name for p in directory.iterdir()))


class SymlinkRootTest(unittest.TestCase):
  """An operator's symlinked or mounted storage root is legitimate."""

  def test_a_symlinked_storage_root_still_accepts_its_own_recordings(self):
    with tempfile.TemporaryDirectory() as base:
      real = Path(base) / "real-storage"
      real.mkdir()
      link = Path(base) / "storage-link"
      link.symlink_to(real)
      recording = real / "douyin" / "live.mp4"
      recording.parent.mkdir(parents=True)

      ##
      ## Configured through the link, recorded through the real path: the same
      ## place, and both must resolve to the same trust root.
      ##
      published = journal(link).publish(intent(recording), KEY)

      self.assertTrue(published.is_file())

  def test_a_path_reached_through_the_symlinked_root_is_accepted(self):
    with tempfile.TemporaryDirectory() as base:
      real = Path(base) / "real-storage"
      real.mkdir()
      link = Path(base) / "storage-link"
      link.symlink_to(real)
      (real / "douyin").mkdir()

      published = journal(link).publish(
        intent(link / "douyin" / "live.mp4"), KEY
      )

      self.assertTrue(published.is_file())

  def test_a_recording_symlinked_out_of_the_root_is_refused(self):
    ##
    ## The file is inside the root by name only; following it leaves. The
    ## resolved location is what counts.
    ##
    with tempfile.TemporaryDirectory() as base:
      root = Path(base) / "storage"
      root.mkdir()
      outside = Path(base) / "outside.mp4"
      outside.write_bytes(b"x")
      escaping = root / "live.mp4"
      escaping.symlink_to(outside)

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).publish(intent(escaping), KEY)


class LoadContainmentTest(unittest.TestCase):
  """The side that matters: bytes off disk becoming a replayable intent."""

  def plant(self, service, output_path):
    directory = service.ensure_root()
    body = payload_for(intent(output_path), KEY)
    target = directory / "{}.json".format(KEY)
    target.write_text(json.dumps(body), encoding="utf-8")
    return target

  def test_a_syntactically_valid_note_naming_media_outside_the_root_is_refused(self):
    ##
    ## Correct schema, correct version, key matching its filename - and a path
    ## that is not this server's to catalogue. Phase 11C must not have to
    ## re-decide whether a loaded note can be trusted.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      self.plant(service, "/etc/passwd")

      with self.assertRaises((RecordingJournalCorrupt,
                              RecordingJournalUnavailable)):
        service.load(KEY)

  def test_a_note_with_a_traversal_path_is_refused(self):
    with tempfile.TemporaryDirectory() as base:
      root = Path(base) / "storage"
      root.mkdir()
      service = journal(root)
      self.plant(service, root / "a" / ".." / ".." / "outside.mp4")

      with self.assertRaises((RecordingJournalCorrupt,
                              RecordingJournalUnavailable)):
        service.load(KEY)

  def test_a_note_with_a_sibling_prefix_path_is_refused(self):
    with tempfile.TemporaryDirectory() as base:
      root = Path(base) / "downloads"
      root.mkdir()
      (Path(base) / "downloads2").mkdir()
      service = journal(root)
      self.plant(service, Path(base) / "downloads2" / "live.mp4")

      with self.assertRaises((RecordingJournalCorrupt,
                              RecordingJournalUnavailable)):
        service.load(KEY)

  def test_a_note_naming_media_inside_the_root_still_loads(self):
    ##
    ## The negative tests above would pass on a load that refused everything.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      recording = Path(root) / "douyin" / "live.mp4"
      recording.parent.mkdir(parents=True)
      original = intent(recording)
      service.publish(original, KEY)

      self.assertEqual(original, service.load(KEY))

  def test_a_refused_note_is_not_deleted(self):
    ##
    ## It is evidence. An operator has to be able to look at what a corrupted
    ## or hostile note actually said.
    ##
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      target = self.plant(service, "/etc/passwd")
      original = target.read_bytes()

      try:
        service.load(KEY)
      except RecordingJournalUnavailable:
        pass

      self.assertTrue(target.is_file())
      self.assertEqual(original, target.read_bytes())


if __name__ == "__main__":
  unittest.main()
