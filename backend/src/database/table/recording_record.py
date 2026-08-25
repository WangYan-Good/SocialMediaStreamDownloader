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


class RecordingRecordTable(SocialMediaStreamDataBase):
  """Repository for persistent live recording resources; never runtime DDL."""

  def __init__(self, host: str, user: str, passwd: str, database: str):
    if getattr(self, "_initialized", False):
      return
    super().__init__(host, user, passwd, database)
    self._initialized = True

  def create_recording(self, record: dict) -> int:
    """Insert one execution as one new resource and return its database id."""
    self.require_write_ready()
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
                protocol, output_path, started_at, finished_at, source)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
            ),
          )
          recording_id = int(cursor.lastrowid)
          connector.commit()
          return recording_id
    except Exception as e:
      get_logger().error(
        "record live resource for room {} failed: {}".format(
          record.get("room_id"),
          e,
        )
      )
      raise
