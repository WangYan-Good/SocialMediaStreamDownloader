##
## Where the recovery journal lives, and what it refuses to live in.
##
## The journal is a handoff note written just before the database is told about
## a finished recording.  It only has value if it survives whatever kills the
## process, which means it has to sit on the same persistent storage as the
## media it describes - not in /tmp, not beside the logs, not in the container
## image.  Replace the container and the journal must still be there next to
## the recording.
##
## It is also internal: nothing outside this service may choose a path
## component, and the directory is not a place a media scan should ever look.
##
from pathlib import Path
import os
import stat
import tempfile
import unittest

from backend.src.service.recording_recovery_journal import (
  JOURNAL_DIRECTORY_NAME,
  RecordingRecoveryJournal,
  RecordingJournalUnavailable,
)


def journal(root, **kwargs):
  return RecordingRecoveryJournal(
    config_loader=lambda: {"download": {"save_path": str(root)}},
    **kwargs,
  )


class JournalRootLocationTest(unittest.TestCase):
  def test_the_journal_lives_under_the_configured_storage_root(self):
    ##
    ## Same persistent storage as the media. A journal on a different mount is
    ## a journal that can disappear while the recording it describes survives -
    ## or the reverse.
    ##
    with tempfile.TemporaryDirectory() as root:
      resolved = journal(root).root()

      self.assertEqual(Path(root).resolve() / JOURNAL_DIRECTORY_NAME, resolved)

  def test_the_directory_is_hidden(self):
    ##
    ## Hidden because it is not media and not for people. A visible directory
    ## in the download root invites both a user and a scanner to treat it as
    ## content.
    ##
    self.assertTrue(JOURNAL_DIRECTORY_NAME.startswith("."))
    self.assertEqual(".smsd-recording-recovery", JOURNAL_DIRECTORY_NAME)

  def test_a_symlinked_storage_root_is_honoured(self):
    ##
    ## An operator is entitled to point save_path at a symlink - a mounted
    ## volume very often is one. The resolved target is the trust root, so this
    ## must not be mistaken for an attack.
    ##
    with tempfile.TemporaryDirectory() as base:
      real = Path(base) / "real-storage"
      real.mkdir()
      link = Path(base) / "storage-link"
      link.symlink_to(real)

      resolved = journal(link).root()

      self.assertEqual(real.resolve() / JOURNAL_DIRECTORY_NAME, resolved)

  def test_an_unconfigured_storage_root_is_refused(self):
    for settings in ({}, {"download": {}}, {"download": {"save_path": "  "}}):
      with self.subTest(settings=settings):
        service = RecordingRecoveryJournal(config_loader=lambda: settings)
        with self.assertRaises(RecordingJournalUnavailable):
          service.root()


class JournalRootCreationTest(unittest.TestCase):
  def test_the_directory_is_not_created_just_by_wiring_the_service(self):
    ##
    ## A server that never records - or one started read-only - must not have a
    ## directory created underneath it merely because the service exists.
    ##
    with tempfile.TemporaryDirectory() as root:
      journal(root)

      self.assertEqual([], list(Path(root).iterdir()))

  def test_the_directory_is_created_on_first_use(self):
    with tempfile.TemporaryDirectory() as root:
      created = journal(root).ensure_root()

      self.assertTrue(created.is_dir())
      self.assertEqual(
        [JOURNAL_DIRECTORY_NAME],
        [p.name for p in Path(root).iterdir()],
      )

  def test_the_directory_is_private_to_the_service_account(self):
    with tempfile.TemporaryDirectory() as root:
      created = journal(root).ensure_root()

      mode = stat.S_IMODE(created.stat().st_mode)
      self.assertEqual(0o700, mode)

  def test_creating_the_directory_commits_the_parent(self):
    ##
    ## The journal's whole durability argument rests on this directory's name
    ## existing after a crash. Creating it and immediately writing into it
    ## would build that argument on a directory entry still sitting in an
    ## uncommitted journal.
    ##
    synced = []
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      real_sync = service._sync_directory
      service._sync_directory = lambda path: (
        synced.append(Path(path)), real_sync(path)
      )[1]

      service.ensure_root()

      self.assertIn(Path(root).resolve(), synced)

  def test_using_an_existing_directory_does_not_recreate_it(self):
    with tempfile.TemporaryDirectory() as root:
      service = journal(root)
      first = service.ensure_root()
      marker = first / "keep-me"
      marker.write_text("x")

      second = service.ensure_root()

      self.assertEqual(first, second)
      self.assertTrue(marker.is_file())


class JournalRootSymlinkTest(unittest.TestCase):
  def test_a_symlinked_journal_directory_fails_closed(self):
    ##
    ## The journal directory is internal and this service is the only thing
    ## that should ever create it. Finding a symlink there means something else
    ## chose where these writes land, which is exactly the case where writing
    ## anyway would be worst.
    ##
    with tempfile.TemporaryDirectory() as base:
      root = Path(base) / "storage"
      root.mkdir()
      elsewhere = Path(base) / "elsewhere"
      elsewhere.mkdir()
      (root / JOURNAL_DIRECTORY_NAME).symlink_to(elsewhere)

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).ensure_root()

      ##
      ## And nothing was written through it.
      ##
      self.assertEqual([], list(elsewhere.iterdir()))

  def test_a_journal_path_that_is_a_file_fails_closed(self):
    with tempfile.TemporaryDirectory() as root:
      (Path(root) / JOURNAL_DIRECTORY_NAME).write_text("not a directory")

      with self.assertRaises(RecordingJournalUnavailable):
        journal(root).ensure_root()


class JournalRootContainmentTest(unittest.TestCase):
  def test_the_journal_root_is_inside_the_configured_root(self):
    ##
    ## Stated as an assertion rather than assumed from string building: the
    ## directory name is a constant this service owns, and no part of it comes
    ## from a recording, a payload, or a request.
    ##
    with tempfile.TemporaryDirectory() as root:
      storage = Path(root).resolve()
      resolved = journal(root).root()

      self.assertIn(storage, resolved.parents)
      self.assertEqual(1, len(resolved.relative_to(storage).parts))


if __name__ == "__main__":
  unittest.main()
