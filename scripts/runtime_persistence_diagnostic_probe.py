"""No-network runtime proof that persistence diagnostics carry no raw values.

Runs inside the production image against the real persistence modules with an
injected transport standing in for the database driver. No network, no real
database and no platform credentials are involved.

The transport is what makes this a runtime proof rather than a formatter test:
the share urls, record dicts, WHERE mappings and driver messages below travel
through the shipped ``DouyinShareUrlTable``, ``SocialMediaStreamDataTable`` and
``RecordingRecordTable`` code paths, and what is captured is whatever those
paths actually emit at every level a deployment can be configured to.
"""

from contextlib import contextmanager
import io
import logging
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if not (PROJECT_ROOT / "backend").is_dir():
  PROJECT_ROOT = Path("/app")
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.database.table.recording_record import RecordingRecordTable
from backend.src.database.table.share_url import DouyinShareUrlTable
from backend.src.database.table.social_media_stream_db_table import (
  SocialMediaStreamDataTable,
)


SECRET_SHARE_URL = "https://v.douyin.test/SECRET_SHARE_URL_RUNTIME_P18/"
SECRET_QUERY = "SECRET_QUERY_RUNTIME_P18"
SECRET_COOKIE = "SECRET_COOKIE_RUNTIME_P18"
SECRET_RECORD_VALUE = "SECRET_RECORD_VALUE_RUNTIME_P18"
SECRET_SQL_PARAM = "SECRET_SQL_PARAM_RUNTIME_P18"
SECRET_EXCEPTION_MESSAGE = "SECRET_EXCEPTION_MESSAGE_RUNTIME_P18"

SENTINELS = (
  "SECRET_SHARE_URL_RUNTIME_P18",
  SECRET_QUERY,
  SECRET_COOKIE,
  SECRET_RECORD_VALUE,
  SECRET_SQL_PARAM,
  SECRET_EXCEPTION_MESSAGE,
)

LEVELS = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)


def require(condition, message):
  if not condition:
    raise SystemExit("FAIL: " + message)


class DriverError(RuntimeError):
  """Shaped like a real driver failure: statement and parameters in the text."""


def driver_error():
  return DriverError(
    "(1064, \"{} near '{}'; params=({!r},) cookie={}\")".format(
      SECRET_EXCEPTION_MESSAGE,
      SECRET_SQL_PARAM,
      SECRET_RECORD_VALUE,
      SECRET_COOKIE,
    )
  )


class Cursor:
  rowcount = 1
  lastrowid = 11

  def __init__(self, rows=(), error=None):
    self.rows = list(rows)
    self.error = error

  def execute(self, sql, params=None):
    if self.error is not None:
      raise self.error

  def fetchall(self):
    return list(self.rows)

  def fetchone(self):
    return self.rows[0] if self.rows else None

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False


class Connection:
  def __init__(self, cursor):
    self._cursor = cursor

  def cursor(self):
    return self._cursor

  def commit(self):
    return None

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False


class Database:
  def __init__(self, cursor):
    self._cursor = cursor

  def is_table_exist(self, unused):
    return True

  def is_table_registered(self, unused):
    return True

  def register_table(self, *unused):
    return None

  @contextmanager
  def get_connection(self):
    yield Connection(self._cursor)


class ProbeTable(SocialMediaStreamDataTable):
  def get_name(self):
    return "probe_table"

  def get_header(self):
    return ["id", "payload"]

  def get_tuple(self):
    return {"id": None, "payload": None}

  def get_pri_key(self):
    return ["id"]

  def get_auto_increment_field(self):
    return []

  def get_create_sql_cmd(self):
    return "CREATE TABLE probe_table (id VARCHAR(64) PRIMARY KEY)"

  def get_drop_sql_cmd(self):
    return "DROP TABLE probe_table"

  def verify_table_schema(self):
    return True


@contextmanager
def capture(level):
  """Everything a deployment at ``level`` would end up with, from all three sinks."""
  log = io.StringIO()
  out = io.StringIO()
  err = io.StringIO()
  logger = logging.getLogger("bootstrap")
  handler = logging.StreamHandler(log)
  handler.setLevel(level)
  handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
  previous_level = logger.level
  previous_stdout, previous_stderr = sys.stdout, sys.stderr
  logger.addHandler(handler)
  logger.setLevel(level)
  sys.stdout, sys.stderr = out, err
  try:
    yield (log, out, err)
  finally:
    sys.stdout, sys.stderr = previous_stdout, previous_stderr
    logger.removeHandler(handler)
    logger.setLevel(previous_level)


def share_url_table(rows=(), error=None):
  table = DouyinShareUrlTable.__new__(DouyinShareUrlTable)
  cursor = Cursor(rows=rows, error=error)
  table.get_connection = lambda: Connection(cursor)
  table.require_write_ready = lambda: None
  return table


def generic_table(rows=(), error=None):
  table = ProbeTable.__new__(ProbeTable)
  table._initialized = True
  setattr(
    table,
    "_SocialMediaStreamDataTable__database",
    Database(Cursor(rows=rows, error=error)),
  )
  return table


def recording_table(error=None):
  table = RecordingRecordTable.__new__(RecordingRecordTable)
  cursor = Cursor(error=error)
  table.get_connection = lambda: Connection(cursor)
  table.require_write_ready = lambda: None
  return table


def sentinel_record():
  return {
    "owner_user_id": "9001",
    "sec_user_id": SECRET_RECORD_VALUE,
    "nickname": SECRET_RECORD_VALUE,
    "post_share_url": SECRET_SHARE_URL + "?" + SECRET_QUERY,
    "live_share_url": SECRET_SHARE_URL + "?" + SECRET_QUERY,
    "directory_name": SECRET_RECORD_VALUE,
    "user_status": SECRET_COOKIE,
  }


def recording_record():
  return {
    "app_user_id": 1,
    "platform": "douyin",
    "room_id": "7700",
    "owner_user_id": "9001",
    "title": SECRET_RECORD_VALUE,
    "protocol": "flv",
    "output_path": "/srv/media/{}.flv".format(SECRET_RECORD_VALUE),
    "source": "live",
  }


def swallow(call):
  """Run a call that is expected to re-raise the injected driver failure."""
  try:
    call()
  except DriverError:
    return
  except Exception as e:
    raise SystemExit(
      "FAIL: a persistence path raised {} rather than the driver error".format(
        type(e).__name__
      )
    )


##
## Every production persistence path P18 covers, exercised once per level.
##
## Success and failure both, because they leak differently: a success used to
## write the record it had just stored, and a failure used to write the driver's
## message - which carries the statement and the parameters bound into it.
##
def exercise(level):
  existing = [
    {
      "owner_user_id": "9001",
      "nickname": "before",
      "live_share_url": None,
      "user_status": "正常",
    }
  ]

  share_url_table(rows=existing).update_live_share_url_record(sentinel_record())
  share_url_table(rows=[]).insert_live_share_url_record(sentinel_record())
  swallow(
    lambda: share_url_table(error=driver_error()).update_live_share_url_record(
      sentinel_record()
    )
  )
  swallow(
    lambda: share_url_table(error=driver_error()).insert_live_share_url_record(
      sentinel_record()
    )
  )
  swallow(
    lambda: share_url_table(
      error=driver_error()
    ).is_live_share_url_record_exist(SECRET_SHARE_URL)
  )

  generic_table().insert_record({"id": "1", "payload": SECRET_SQL_PARAM})
  generic_table().update_record({"id": "1", "payload": SECRET_RECORD_VALUE})
  generic_table().delete_record({"id": SECRET_SQL_PARAM})
  generic_table(
    rows=[{"id": "1", "payload": SECRET_RECORD_VALUE}]
  ).get_record({"id": SECRET_SQL_PARAM})

  swallow(
    lambda: generic_table(error=driver_error()).insert_record(
      {"id": "1", "payload": SECRET_RECORD_VALUE}
    )
  )
  swallow(
    lambda: generic_table(error=driver_error()).update_record(
      {"id": SECRET_SQL_PARAM, "payload": SECRET_RECORD_VALUE}
    )
  )
  swallow(
    lambda: generic_table(error=driver_error()).delete_record(
      {"id": SECRET_SQL_PARAM}
    )
  )
  swallow(
    lambda: generic_table(error=driver_error()).get_record(
      {"id": SECRET_SQL_PARAM}
    )
  )

  swallow(
    lambda: recording_table(error=driver_error()).create_recording(
      recording_record()
    )
  )


def main():
  ##
  ## Collected across every level first, so a leak that only appears at one of
  ## them is still a failure of the whole probe.
  ##
  everything = []
  for level in LEVELS:
    with capture(level) as (log, out, err):
      exercise(level)
    visible = log.getvalue() + out.getvalue() + err.getvalue()
    everything.append((level, visible))

  for level, visible in everything:
    name = logging.getLevelName(level)
    for sentinel in SENTINELS:
      require(
        sentinel not in visible,
        "persistence diagnostics leaked {} at {}".format(sentinel, name),
      )

  ##
  ## Redaction that deleted the diagnostic would pass every check above and be
  ## useless, so the closed fields have to still be there.
  ##
  error_output = dict(everything)[logging.ERROR]
  for expected in (
    "persistence diagnostic",
    "table=share_url",
    "table=probe_table",
    "table=recording_record",
    "error=DriverError",
    "operation=insert",
    "operation=update",
    "operation=query",
    "operation=delete",
  ):
    require(
      expected in error_output,
      "the closed diagnostic lost a field it must keep: " + expected,
    )

  debug_output = dict(everything)[logging.DEBUG]
  require(
    "persistence diagnostic" in debug_output,
    "DEBUG lost its persistence diagnostics entirely",
  )
  info_output = dict(everything)[logging.INFO]
  require("rows=" in info_output, "a successful write reported no row count")

  print("ok   runtime persistence diagnostic redaction")


if __name__ == "__main__":
  main()
