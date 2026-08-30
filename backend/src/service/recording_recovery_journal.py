##
## A durable handoff note, written just before a finished recording is told to
## the database.
##
## The crash this exists for: the media is durable on disk, and the process
## dies before ``recording_record`` has the row that makes it discoverable. The
## bytes survive and the library cannot see them. A journal published *before*
## the insert turns that into a recoverable state - Phase 11C can replay it,
## and Phase 11B-0 already guarantees the replay cannot create a duplicate.
##
## What this is not: a queue, a scanner, or a recovery mechanism. It publishes
## one note, reads one note back, and removes one note. Nothing here enumerates
## a directory or replays anything.
##
## Where it lives matters as much as what it says. The journal sits on the same
## persistent storage as the media it describes, so replacing the container
## leaves the note beside the recording rather than deleting one and keeping
## the other.
##
from datetime import datetime
import errno
import json
import os
from pathlib import Path
import stat

from backend.src.database.table.recording_record import canonical_recovery_key
from backend.src.library.baselib import get_dict_attr
from backend.src.service.media_asset import contained_path
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger


##
## Hidden, and a name nothing else would choose. Hidden because it is not media
## and not for people: a visible directory in the download root invites both a
## user and a media scan to treat it as content.
##
JOURNAL_DIRECTORY_NAME = ".smsd-recording-recovery"


##
## The note format. Bumped only when a note written by an older build could be
## misread by a newer one; a reader that does not recognise the version must
## refuse rather than guess, so this is checked before any field is trusted.
##
JOURNAL_SCHEMA_VERSION = 1

##
## A note is a few hundred bytes. A file that is not is either corrupt or
## something else entirely, and reading it unbounded is how one damaged file in
## a directory becomes an outage.
##
JOURNAL_MAX_BYTES = 64 * 1024

##
## Milliseconds, because that is what ``recording_record`` stores -
## ``DATETIME(3)``. Journalling microseconds would write a value the column
## cannot hold, and a replay would then produce a row that differs from the one
## the original insert would have made.
##
_TIMESTAMP_PRECISION = "milliseconds"

_PAYLOAD_FIELDS = (
  "app_user_id",
  "platform",
  "room_id",
  "owner_user_id",
  "title",
  "protocol",
  "output_path",
  "started_at",
  "finished_at",
  "source",
)


def _timestamp_text(value):
  if value is None:
    return None
  return value.isoformat(timespec=_TIMESTAMP_PRECISION)


def _timestamp_value(text):
  if text is None:
    return None
  return datetime.fromisoformat(text)


##
## Everything the note says, and nothing else.
##
## A closed set on purpose: an extra field is either a fact the database does
## not store - which a replay would have to ignore - or something that should
## never have been written down at all. The intent has no field for a stream
## url, headers, cookies or a task id, so none can arrive here.
##
def payload_for(intent, recovery_key) -> dict:
  payload = {
    "schema_version": JOURNAL_SCHEMA_VERSION,
    "recovery_key": recovery_key,
  }
  for field in _PAYLOAD_FIELDS:
    value = getattr(intent, field)
    if field in ("started_at", "finished_at"):
      value = _timestamp_text(value)
    payload[field] = value
  return payload


def intent_from_payload(payload):
  """Rebuild the persistence intent a note describes."""
  from backend.src.service.recording_resource import RecordingPersistenceIntent

  return RecordingPersistenceIntent(
    app_user_id=payload["app_user_id"],
    platform=payload["platform"],
    room_id=payload["room_id"],
    owner_user_id=payload["owner_user_id"],
    title=payload["title"],
    protocol=payload["protocol"],
    output_path=payload["output_path"],
    started_at=_timestamp_value(payload["started_at"]),
    finished_at=_timestamp_value(payload["finished_at"]),
    source=payload["source"],
  )


##
## Deterministic bytes: sorted keys, no incidental whitespace, and no NaN or
## Infinity - none of which JSON can express and all of which would produce a
## note no conforming reader could parse.
##
## ``ensure_ascii=False`` so a Chinese stream title stays readable text rather
## than a wall of escapes; the file is UTF-8 either way.
##
def journal_bytes(intent, recovery_key) -> bytes:
  text = json.dumps(
    payload_for(intent, recovery_key),
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
  )
  return (text + "\n").encode("utf-8")


##
## The shape each field must have. ``bool`` is excluded from the integer check
## on purpose: it is an ``int`` in Python, and a ``true`` owner id would sail
## through as user 1.
##
_REQUIRED_TEXT = ("platform", "output_path", "source")
_OPTIONAL_TEXT = ("room_id", "owner_user_id", "title", "protocol")
_TIMESTAMPS = ("started_at", "finished_at")


def _validate_payload(payload, key):
  for field in _REQUIRED_TEXT:
    value = payload.get(field, _MISSING)
    if not isinstance(value, str) or not value:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} has an invalid {}".format(key[:8], field)
      )
  for field in _OPTIONAL_TEXT:
    value = payload.get(field, _MISSING)
    if value is not None and not isinstance(value, str):
      raise RecordingJournalCorrupt(
        "recording recovery journal {} has an invalid {}".format(key[:8], field)
      )
    if value is _MISSING:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} is missing {}".format(key[:8], field)
      )
  owner = payload.get("app_user_id", _MISSING)
  if owner is _MISSING:
    raise RecordingJournalCorrupt(
      "recording recovery journal {} is missing app_user_id".format(key[:8])
    )
  if owner is not None and (
    isinstance(owner, bool) or not isinstance(owner, int) or owner < 1
  ):
    raise RecordingJournalCorrupt(
      "recording recovery journal {} has an invalid app_user_id".format(key[:8])
    )
  for field in _TIMESTAMPS:
    value = payload.get(field, _MISSING)
    if value is _MISSING:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} is missing {}".format(key[:8], field)
      )
    if value is None:
      continue
    if not isinstance(value, str):
      raise RecordingJournalCorrupt(
        "recording recovery journal {} has an invalid {}".format(key[:8], field)
      )
    try:
      datetime.fromisoformat(value)
    except ValueError as e:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} has an unreadable {}".format(
          key[:8], field
        )
      ) from e


_MISSING = object()


class RecordingJournalUnavailable(RuntimeError):
  """The journal cannot be used, so no recording may be catalogued yet."""


##
## A note already exists under this key.
##
## Its own type because it is not a storage failure: the filesystem worked
## exactly as asked and refused to overwrite. Production generates a fresh key
## per attempt, so reaching this means a key was reused or a replay called
## ``publish`` where it should have called ``load`` - and overwriting would
## destroy the note describing whatever was recorded first.
##
class RecordingJournalConflict(RecordingJournalUnavailable):
  pass


##
## The note exists but this build cannot faithfully reproduce it.
##
## Separate from "unavailable" because the storage is fine: the file is
## unreadable or says something this build does not understand. Both fail
## closed - a replay driven by a guess would insert a recording nobody made -
## but only one of them means an operator should go and look at the file.
##
class RecordingJournalCorrupt(RecordingJournalUnavailable):
  pass


class RecordingJournalUnsupportedVersion(RecordingJournalUnavailable):
  pass


class RecordingRecoveryJournal:
  """Publish, read and retire one recovery note per recording attempt."""

  def __init__(self, config_loader=load_config):
    self._config_loader = config_loader
    self._config = None

  def _settings(self):
    if self._config is None:
      self._config = self._config_loader()
    return self._config

  ##
  ## Commit an open file's contents to stable storage.
  ##
  ## Takes the descriptor already being written rather than reopening by name:
  ## the bytes being committed must be the bytes just written, and a second
  ## open by path is a second chance for the name to mean something else.
  ##
  @staticmethod
  def _sync_file(descriptor):
    os.fsync(descriptor)

  ##
  ## Commit a directory's entries to stable storage.
  ##
  ## A name lives in its parent directory, so a file can be fully written while
  ## the entry that reaches it is still only in an uncommitted journal.
  ##
  ## Opened per call and never cached: a descriptor held across a long-running
  ## server would pin a directory that may be replaced underneath it.
  ##
  @staticmethod
  def _sync_directory(path):
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
      os.fsync(descriptor)
    finally:
      os.close(descriptor)

  ##
  ## The configured storage root, resolved.
  ##
  ## Resolved rather than taken literally because an operator is entitled to
  ## point ``save_path`` at a symlink - a mounted volume very often is one -
  ## and the target is the real trust root.
  ##
  def _storage_root(self) -> Path:
    configured = get_dict_attr(self._settings(), "$.download.save_path")
    if not isinstance(configured, str) or not configured.strip():
      raise RecordingJournalUnavailable(
        "recording recovery requires a configured download save path"
      )
    try:
      return Path(os.path.realpath(configured.strip()))
    except (OSError, ValueError) as e:
      raise RecordingJournalUnavailable(
        "configured download save path cannot be resolved"
      ) from e

  ##
  ## A note may only describe media inside the configured storage root.
  ##
  ## In the ordinary path the output path came from the downloader, which wrote
  ## the file, so there is little to catch. The journal changes that: it is a
  ## persistent input to a future replay, read back by a process that recorded
  ## nothing and has no other way to judge what it is being told. A note that
  ## was corrupted, wrongly generated, or rewritten by another local process
  ## could otherwise name a path outside the library entirely, and a replay
  ## would catalogue it as a recording resource.
  ##
  ## Delegated to the media layer's ``contained_path`` rather than reimplemented:
  ## containment is a path-segment relationship after resolution, never a string
  ## prefix - ``/downloads2`` starts with ``/downloads`` and is a different
  ## directory - and there should be one answer to that question in this
  ## codebase, not two.
  ##
  ## Resolution also settles the legitimate cases: an operator may point
  ## ``save_path`` at a symlink or a mount, and a recording reached through
  ## either spelling resolves to the same place. A file that is inside the root
  ## by name but symlinked out of it does not, which is the point.
  ##
  def _contained_output_path(self, output_path) -> Path:
    root = self._storage_root()
    resolved = contained_path(root, output_path)
    if resolved is None:
      raise RecordingJournalUnavailable(
        "recording output path is outside the configured storage root"
      )
    ##
    ## A recording is a file *in* the root, never the root itself: a note
    ## naming the directory would describe the whole library as one resource.
    ##
    if resolved == root:
      raise RecordingJournalUnavailable(
        "recording output path is the storage root itself"
      )
    return resolved

  ##
  ## Where notes go. A pure function of configuration - no part of this path
  ## comes from a recording, a payload, or a request.
  ##
  def root(self) -> Path:
    return self._storage_root() / JOURNAL_DIRECTORY_NAME

  ##
  ## Create the directory the first time something is actually written.
  ##
  ## Lazily, so a server that never records - or one started against read-only
  ## storage - does not have a directory appear underneath it merely because
  ## this service was wired up.
  ##
  ## The parent is committed after creating it. Everything published here later
  ## argues that its name survives a crash, and that argument cannot rest on a
  ## directory entry still sitting in an uncommitted metadata journal.
  ##
  def ensure_root(self) -> Path:
    storage = self._storage_root()
    target = storage / JOURNAL_DIRECTORY_NAME
    try:
      created = False
      try:
        ##
        ## 0700: these notes describe who owns which recording, and nothing
        ## outside this service has any reason to read them.
        ##
        os.mkdir(target, 0o700)
        created = True
      except FileExistsError:
        pass

      ##
      ## Checked with lstat, so a symlink is seen as a symlink rather than
      ## followed to whatever it points at. This directory is internal and this
      ## service is the only thing that should ever create it; finding a link
      ## here means something else chose where these writes land, which is
      ## exactly when writing anyway would be worst.
      ##
      info = os.lstat(target)
      if stat.S_ISLNK(info.st_mode):
        raise RecordingJournalUnavailable(
          "recording recovery journal directory must not be a symlink"
        )
      if not stat.S_ISDIR(info.st_mode):
        raise RecordingJournalUnavailable(
          "recording recovery journal path is not a directory"
        )

      if created:
        self._sync_directory(storage)
    except RecordingJournalUnavailable:
      raise
    except OSError as e:
      raise RecordingJournalUnavailable(
        "recording recovery journal directory is unusable ({}: {})".format(
          type(e).__name__, e
        )
      ) from e
    return target


  ##
  ## A hidden, per-attempt temporary in the journal directory itself.
  ##
  ## Same directory because publication is a hard link, which cannot cross a
  ## filesystem. Hidden and suffixed so that a future scanner - which will only
  ## ever accept ``<key>.json`` - can never mistake an in-flight write for a
  ## finished note.
  ##
  @staticmethod
  def _temporary_path(directory, key):
    return directory / ".{}.journal-{}.part".format(key, os.urandom(8).hex())

  ##
  ## Write every byte.
  ##
  ## ``os.write`` is not obliged to consume the whole buffer, and a short write
  ## that went unnoticed would produce a note that is valid JSON right up to
  ## the point where it stops.
  ##
  @staticmethod
  def _write_all(descriptor, payload):
    written = 0
    while written < len(payload):
      written += os.write(descriptor, payload[written:])

  def publish(self, intent, recovery_key) -> Path:
    """Write one note durably, and answer where it landed.

    Returns only once the note's bytes *and* its name are on stable storage.
    Until then the caller must not treat the recording as recoverable, which is
    why every failure here raises rather than returning a path.
    """
    key = canonical_recovery_key(recovery_key)
    if key is None:
      raise ValueError("publishing a recovery journal requires a recovery key")

    ##
    ## Before the directory is created or a byte is written: a note that could
    ## not legitimately be replayed should never exist.
    ##
    self._contained_output_path(intent.output_path)

    directory = self.ensure_root()
    final = directory / "{}.json".format(key)
    payload = journal_bytes(intent, key)
    temporary = self._temporary_path(directory, key)

    ##
    ## O_EXCL so this attempt owns the temporary outright; O_NOFOLLOW so a
    ## planted symlink cannot redirect the write. 0600 because the note says
    ## who owns which recording.
    ##
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
      descriptor = os.open(temporary, flags, 0o600)
    except OSError as e:
      raise RecordingJournalUnavailable(
        "recording recovery journal could not be opened ({}: {})".format(
          type(e).__name__, e
        )
      ) from e

    published = False
    try:
      try:
        self._write_all(descriptor, payload)
        self._sync_file(descriptor)
      finally:
        os.close(descriptor)

      ##
      ## A hard link rather than a rename. ``os.replace`` would silently
      ## destroy an existing note; ``os.link`` refuses, which turns a reused
      ## key into a reported conflict instead of a lost record.
      ##
      try:
        os.link(temporary, final)
      except FileExistsError as e:
        raise RecordingJournalConflict(
          "a recovery journal already exists for {}".format(key[:8])
        ) from e

      try:
        self._sync_directory(directory)
      except OSError as e:
        ##
        ## The name exists but is not committed, so it does not describe a note
        ## anything may act on. This attempt created it, so this attempt takes
        ## it away.
        ##
        try:
          os.unlink(final)
        except OSError:
          pass
        else:
          try:
            self._sync_directory(directory)
          except OSError:
            pass
        raise RecordingJournalUnavailable(
          "recording recovery journal could not be committed ({}: {})".format(
            type(e).__name__, e
          )
        ) from e
      published = True
    except RecordingJournalUnavailable:
      self._discard(temporary)
      raise
    except OSError as e:
      self._discard(temporary)
      raise RecordingJournalUnavailable(
        "recording recovery journal could not be written ({}: {})".format(
          type(e).__name__, e
        )
      ) from e

    ##
    ## Durable. The temporary is now a second name for bytes the final name
    ## also holds, so dropping it cannot lose anything - and failing to drop it
    ## is hygiene, not a reason to refuse to catalogue the recording.
    ##
    try:
      os.unlink(temporary)
    except OSError as e:
      get_logger().warning(
        "recording recovery journal {} published but its temporary "
        "could not be removed ({}: {})".format(key[:8], type(e).__name__, e)
      )
    else:
      try:
        self._sync_directory(directory)
      except OSError:
        pass
    return final

  ##
  ## Read one note back, by name.
  ##
  ## Deliberately not a scan: this addresses exactly ``<key>.json`` and nothing
  ## else, so a decoy, a backup copy or an in-flight temporary in the same
  ## directory cannot be mistaken for a replayable note. Enumerating the
  ## directory is a scanner, and a scanner is a later phase.
  ##
  ## Every check below fails closed. What comes out of here eventually becomes
  ## a database row, so "probably fine" is not an acceptable answer.
  ##
  def load(self, recovery_key):
    key = canonical_recovery_key(recovery_key)
    if key is None:
      raise ValueError("loading a recovery journal requires a recovery key")

    target = self.root() / "{}.json".format(key)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
      descriptor = os.open(target, flags)
    except FileNotFoundError:
      ##
      ## Nothing to replay is an ordinary answer, not a fault: most keys were
      ## acknowledged and removed on purpose.
      ##
      return None
    except OSError as e:
      raise RecordingJournalUnavailable(
        "recording recovery journal {} could not be opened ({}: {})".format(
          key[:8], type(e).__name__, e
        )
      ) from e

    try:
      info = os.fstat(descriptor)
      if not stat.S_ISREG(info.st_mode):
        raise RecordingJournalUnavailable(
          "recording recovery journal {} is not a regular file".format(key[:8])
        )
      if info.st_size > JOURNAL_MAX_BYTES:
        raise RecordingJournalCorrupt(
          "recording recovery journal {} is larger than {} bytes".format(
            key[:8], JOURNAL_MAX_BYTES
          )
        )
      raw = os.read(descriptor, JOURNAL_MAX_BYTES + 1)
    finally:
      os.close(descriptor)

    if len(raw) > JOURNAL_MAX_BYTES:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} is oversized".format(key[:8])
      )
    try:
      payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} is not readable JSON".format(key[:8])
      ) from e

    if not isinstance(payload, dict):
      raise RecordingJournalCorrupt(
        "recording recovery journal {} is not an object".format(key[:8])
      )
    ##
    ## Version before fields: a newer build may have changed what a field
    ## means, so nothing in it may be trusted until the format is recognised.
    ##
    if payload.get("schema_version") != JOURNAL_SCHEMA_VERSION:
      raise RecordingJournalUnsupportedVersion(
        "recording recovery journal {} declares version {!r}".format(
          key[:8], payload.get("schema_version")
        )
      )
    ##
    ## The note must claim the name it was found under. Otherwise a renamed
    ## file could lend one recording's facts to another recording's identity.
    ##
    if payload.get("recovery_key") != key:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} does not claim its own key".format(
          key[:8]
        )
      )
    _validate_payload(payload, key)
    ##
    ## The load-bearing check on this side. Phase 11C must not have to decide
    ## for itself whether a loaded note names something it may catalogue.
    ##
    self._contained_output_path(payload["output_path"])
    try:
      return intent_from_payload(payload)
    except (TypeError, ValueError) as e:
      raise RecordingJournalCorrupt(
        "recording recovery journal {} could not be rebuilt".format(key[:8])
      ) from e

  ##
  ## Retire a note once the database owns the recording.
  ##
  ## Called only after a successful insert, so by this point the note has done
  ## its job. The removal is committed because an unlinked-but-uncommitted
  ## entry can come back after a crash - survivable, since a replay of a key
  ## that already has a row resolves to that row rather than inserting a second
  ## one, but the common case should leave nothing behind.
  ##
  ## Absent is success: the note may already have been retired by an earlier
  ## attempt or removed by an operator, and nothing is owed to a caller who
  ## asked twice.
  ##
  def acknowledge(self, recovery_key) -> None:
    key = canonical_recovery_key(recovery_key)
    if key is None:
      raise ValueError("acknowledging a recovery journal requires a key")

    directory = self.root()
    target = directory / "{}.json".format(key)
    try:
      os.unlink(target)
    except FileNotFoundError:
      return
    except OSError as e:
      raise RecordingJournalUnavailable(
        "recording recovery journal {} could not be retired ({}: {})".format(
          key[:8], type(e).__name__, e
        )
      ) from e
    self._sync_directory(directory)

  @staticmethod
  def _discard(path):
    try:
      os.unlink(path)
    except OSError:
      pass


__all__ = [
  "JOURNAL_DIRECTORY_NAME",
  "JOURNAL_MAX_BYTES",
  "RecordingJournalConflict",
  "RecordingJournalCorrupt",
  "RecordingJournalUnsupportedVersion",
  "JOURNAL_SCHEMA_VERSION",
  "intent_from_payload",
  "journal_bytes",
  "payload_for",
  "RecordingJournalUnavailable",
  "RecordingRecoveryJournal",
]
