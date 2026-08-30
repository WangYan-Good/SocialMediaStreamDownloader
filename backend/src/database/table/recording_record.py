from backend.src.database.social_media_stream_database import (
  SocialMediaStreamDataBase,
)
from backend.src.library.loglib import get_logger


def _required_text(value, name: str) -> str:
  if not isinstance(value, str) or not value.strip():
    raise ValueError("{} is required".format(name))
  return value.strip()


def _required_path(value, name: str) -> str:
  """Validate a path without changing the downloader's actual file name."""
  if not isinstance(value, str) or not value.strip():
    raise ValueError("{} is required".format(name))
  return value


##
## One recovery identity must name one media resource.
##
## Raised when a replay presents a key that already exists but describes a
## different recording. Returning the stored id would attach this recording's
## identity to somebody else's bytes; inserting would defeat the whole point of
## the key. Neither is a safe guess, so the caller is told.
##
class RecordingRecoveryConflict(RuntimeError):
  pass


##
## The only shape a recovery key may take: exactly 32 lowercase hex characters,
## which is what ``uuid4().hex`` produces.
##
## Nothing is normalised here on purpose. The value is compared against a
## database unique constraint under a binary collation, so accepting ``ABC...``
## and silently storing ``abc...`` would mean two callers believing they hold
## different keys while the database sees one - or the reverse. Stripping
## whitespace would hide a caller building keys by concatenation. A key that is
## not already canonical is a bug at its source, and this is where it surfaces.
##
_RECOVERY_KEY_DIGITS = frozenset("0123456789abcdef")


def canonical_recovery_key(value):
  """Answer ``value`` unchanged if it is a canonical recovery key, or ``None``."""
  if value is None:
    return None
  ##
  ## ``bool`` is an ``int``, and an ``int`` reaching a hex comparison would be
  ## a key nobody could reproduce - so type is checked before anything else.
  ##
  if not isinstance(value, str):
    raise TypeError("recovery_key must be a string or None")
  if len(value) != 32:
    raise ValueError("recovery_key must be exactly 32 characters")
  if not _RECOVERY_KEY_DIGITS.issuperset(value):
    raise ValueError("recovery_key must be lowercase hexadecimal")
  return value


##
## MySQL reports every unique violation as 1062, so the index has to be named.
## Reading any duplicate as a recovery replay would turn an unrelated
## constraint - including one added by a future migration - into a silent
## "already recorded".
##
## The numeric code and the index name are matched, never the driver's message:
## that prose is written by MySQL and would break silently the day it is
## reworded.
##
##
## Normalised only for comparison, never for storage: a column that came back
## as NULL and a field that was never set describe the same absence, and an id
## stored as a string by one driver should not read as a different recording.
##
def _comparable(value):
  if value is None:
    return None
  if isinstance(value, int) and not isinstance(value, bool):
    return str(value)
  return str(value)


_MYSQL_DUPLICATE_KEY = 1062
RECOVERY_KEY_INDEX = "uq_recording_record_recovery_key"


def _is_duplicate_recovery_key(error) -> bool:
  arguments = getattr(error, "args", ()) or ()
  if not arguments or arguments[0] != _MYSQL_DUPLICATE_KEY:
    return False
  return RECOVERY_KEY_INDEX in "".join(str(one) for one in arguments)


class RecordingRecordTable(SocialMediaStreamDataBase):
  """Repository for persistent live recording resources; never runtime DDL."""

  def __init__(self, host: str, user: str, passwd: str, database: str):
    if getattr(self, "_initialized", False):
      return
    super().__init__(host, user, passwd, database)
    self._initialized = True

  ##
  ## Which fields make two rows the same recording.
  ##
  ## Deliberately excludes the timestamps.  ``started_at`` and ``finished_at``
  ## are stored as DATETIME(3) while Python carries microseconds, so comparing
  ## them would manufacture conflicts out of rounding rather than out of
  ## disagreement.  What is compared here is stable under that rounding and is
  ## enough to notice a key being reused for different media.
  ##
  RECOVERY_IDENTITY_FIELDS = (
    "app_user_id",
    "platform",
    "output_path",
    "source",
    "room_id",
    "owner_user_id",
    "protocol",
  )

  def find_by_recovery_key(self, recovery_key):
    """The stored row for a recovery key, or ``None``.

    Kept here rather than in the library query layer: this is a recovery
    concern, and ordinary recording listings have no reason to start carrying
    the column.
    """
    key = canonical_recovery_key(recovery_key)
    if key is None:
      return None
    sql = '''SELECT recording_id, app_user_id, platform, room_id,
                    owner_user_id, protocol, output_path, source
               FROM recording_record
              WHERE recovery_key = %s;
          '''
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql, (key,))
        row = cursor.fetchone()
    if row is None:
      return None
    if isinstance(row, dict):
      return row
    names = (
      "recording_id", "app_user_id", "platform", "room_id",
      "owner_user_id", "protocol", "output_path", "source",
    )
    return dict(zip(names, row))

  ##
  ## The insert lost the race, so somebody else already stored this recording.
  ##
  ## Answering with their id is only correct if the row really is this
  ## recording. A key that names different media is a corrupted journal or a
  ## caller bug, and returning the stored id would attach this recording's
  ## identity to somebody else's bytes.
  ##
  def _resolve_replay(self, record, recovery_key):
    existing = self.find_by_recovery_key(recovery_key)
    if existing is None:
      ##
      ## The constraint fired but the row is gone - a concurrent delete, or a
      ## collision on some other index that happens to carry this name. Either
      ## way this cannot be answered as a replay.
      ##
      raise RecordingRecoveryConflict(
        "recovery key {} collided but no stored recording matches it".format(
          recovery_key[:8]
        )
      )
    differing = [
      field for field in self.RECOVERY_IDENTITY_FIELDS
      if _comparable(existing.get(field)) != _comparable(record.get(field))
    ]
    if differing:
      raise RecordingRecoveryConflict(
        "recovery key {} already names a different recording (differs on {})".format(
          recovery_key[:8],
          ", ".join(differing),
        )
      )
    return int(existing["recording_id"])

  def create_recording(self, record: dict, recovery_key=None) -> int:
    """Insert one execution as one new resource and return its database id.

    Without a recovery key this is what it has always been: one call, one row.
    Two identical ordinary recordings are two resources, because two broadcasts
    were captured.

    With a recovery key it becomes create-or-get. A recovery replay presents
    the same key for the same recording, and the answer must be the id that
    already exists rather than a second row.

    The uniqueness is the database's to enforce, not this method's. Two
    processes replaying the same journal can both pass a SELECT and both go on
    to insert, so the insert is attempted and the constraint decides; only
    after it fires does this look up what already won.
    """
    self.require_write_ready()
    recovery_key = canonical_recovery_key(recovery_key)
    app_user_id = record.get("app_user_id")
    if app_user_id is not None and (
      type(app_user_id) is not int or app_user_id < 1
    ):
      raise ValueError("app_user_id must be a positive integer or None")
    platform = _required_text(record.get("platform"), "platform")
    output_path = _required_path(record.get("output_path"), "output_path")
    source = _required_text(record.get("source"), "source")

    sql = '''INSERT INTO recording_record
               (app_user_id, platform, room_id, owner_user_id, title,
                protocol, output_path, started_at, finished_at, source,
                recovery_key)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            sql,
            (
              app_user_id,
              platform,
              record.get("room_id"),
              record.get("owner_user_id"),
              record.get("title"),
              record.get("protocol"),
              output_path,
              record.get("started_at"),
              record.get("finished_at"),
              source,
              recovery_key,
            ),
          )
          recording_id = int(cursor.lastrowid)
          connector.commit()
          return recording_id
    except Exception as e:
      ##
      ## Only a collision on this recording's own recovery key means "already
      ## replayed".  A foreign key failure, a malformed row, or any unique
      ## index added later must still surface - swallowing those as idempotent
      ## success would report a recording that was never stored.
      ##
      if recovery_key is not None and _is_duplicate_recovery_key(e):
        return self._resolve_replay(record, recovery_key)
      get_logger().error(
        "record live resource for room {} failed: {}".format(
          record.get("room_id"),
          e,
        )
      )
      raise
