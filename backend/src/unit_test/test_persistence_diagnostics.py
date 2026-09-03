##
## What the persistence layer must never write down.
##
## Every diagnostic in this file's scope goes to a log that is rotated, kept,
## shipped and read by people who are not the account the record belongs to. A
## share url is a capability-shaped link, a record dict is the row itself, and a
## driver's exception message routinely carries the statement *and* the bound
## parameters that failed. None of the three is a diagnostic; all three are the
## data.
##
## DEBUG is included on purpose. "It is only at DEBUG" is an argument about a
## setting, not about the file: ``$.log.level`` is operator-configurable, the
## bootstrap logger runs at DEBUG before any configuration is read, and a
## persisted DEBUG line is exactly as persistent as an ERROR one.
##
## The sentinels are values that appear nowhere else in this codebase, so
## finding one in captured output can only mean it travelled there. Each is fed
## through a real production call - not a formatter unit test - because the
## question is what the shipping code emits, not what a helper is capable of.
##
from contextlib import contextmanager
import io
import logging
import sys
import unittest

from backend.src.database.table.recording_record import RecordingRecordTable
from backend.src.database.table.share_url import DouyinShareUrlTable
from backend.src.database.table.social_media_stream_db_table import (
  SocialMediaStreamDataTable,
)


SECRET_SHARE_URL = "https://v.douyin.test/SECRET_SHARE_URL_P18/"
SECRET_QUERY = "SECRET_QUERY_P18"
SECRET_COOKIE = "SECRET_COOKIE_P18"
SECRET_RECORD_VALUE = "SECRET_RECORD_VALUE_P18"
SECRET_SQL_PARAM = "SECRET_SQL_PARAM_P18"
SECRET_EXCEPTION_MESSAGE = "SECRET_EXCEPTION_MESSAGE_P18"

ALL_SENTINELS = (
  "SECRET_SHARE_URL_P18",
  SECRET_QUERY,
  SECRET_COOKIE,
  SECRET_RECORD_VALUE,
  SECRET_SQL_PARAM,
  SECRET_EXCEPTION_MESSAGE,
)

##
## Every level a deployment can actually be configured to, lowest first. A leak
## that only appears at one of them is still a leak.
##
LEVELS = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)


class Captured:
  """Everything a running deployment would end up with on disk or on a pipe."""

  def __init__(self):
    self.log = io.StringIO()
    self.out = io.StringIO()
    self.err = io.StringIO()

  def visible(self) -> str:
    return self.log.getvalue() + self.out.getvalue() + self.err.getvalue()


@contextmanager
def capture(level):
  """Capture the logger, stdout and stderr at one configured level."""
  captured = Captured()
  logger = logging.getLogger("bootstrap")
  handler = logging.StreamHandler(captured.log)
  handler.setLevel(level)
  handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

  previous_level = logger.level
  previous_stdout = sys.stdout
  previous_stderr = sys.stderr
  logger.addHandler(handler)
  logger.setLevel(level)
  sys.stdout = captured.out
  sys.stderr = captured.err
  try:
    yield captured
  finally:
    sys.stdout = previous_stdout
    sys.stderr = previous_stderr
    logger.removeHandler(handler)
    logger.setLevel(previous_level)


class Boom(RuntimeError):
  """A driver error whose message carries the statement and its parameters."""


def boom():
  return Boom(
    "(1064, \"near '{}' at line 1; params={}\")".format(
      SECRET_SQL_PARAM,
      SECRET_RECORD_VALUE,
    )
  )


##
## >>============================= fake transport =============================>>
##


class FakeCursor:
  rowcount = 1
  lastrowid = 7

  def __init__(self, rows=(), error=None):
    self.rows = list(rows)
    self.error = error
    self.calls = []

  def execute(self, sql, params=None):
    self.calls.append((sql, params))
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


class FakeConnection:
  def __init__(self, cursor):
    self._cursor = cursor
    self.commits = 0

  def cursor(self):
    return self._cursor

  def commit(self):
    self.commits += 1

  def __enter__(self):
    return self

  def __exit__(self, *unused):
    return False


class FakeDatabase:
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
    yield FakeConnection(self._cursor)


class SentinelTable(SocialMediaStreamDataTable):
  """A minimal real subclass, so the generic CRUD under test is the shipped one."""

  def get_name(self):
    return "sentinel_table"

  def get_header(self):
    return ["id", "payload"]

  def get_tuple(self):
    return {"id": None, "payload": None}

  def get_pri_key(self):
    return ["id"]

  def get_auto_increment_field(self):
    return []

  def get_create_sql_cmd(self):
    return "CREATE TABLE sentinel_table (id VARCHAR(64) PRIMARY KEY)"

  def get_drop_sql_cmd(self):
    return "DROP TABLE sentinel_table"

  def verify_table_schema(self):
    return True


def generic_table(rows=(), error=None):
  cursor = FakeCursor(rows=rows, error=error)
  table = SentinelTable.__new__(SentinelTable)
  table._initialized = True
  ##
  ## The database reference is private to ``SocialMediaStreamDataTable``, so the
  ## mangled name is the only way in. Reached deliberately rather than by
  ## calling ``__init__``, whose singleton latch would hand every test the first
  ## test's transport.
  ##
  setattr(table, "_SocialMediaStreamDataTable__database", FakeDatabase(cursor))
  return table, cursor


def share_url_table(rows=(), error=None):
  cursor = FakeCursor(rows=rows, error=error)
  table = DouyinShareUrlTable.__new__(DouyinShareUrlTable)
  table.get_connection = lambda: FakeConnection(cursor)
  table.require_write_ready = lambda: None
  return table, cursor


def recording_table(error=None):
  cursor = FakeCursor(error=error)
  table = RecordingRecordTable.__new__(RecordingRecordTable)
  table.get_connection = lambda: FakeConnection(cursor)
  table.require_write_ready = lambda: None
  return table, cursor


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


class PersistenceDiagnosticLeakTest(unittest.TestCase):
  def assert_no_sentinel(self, captured, where):
    visible = captured.visible()
    for sentinel in ALL_SENTINELS:
      self.assertNotIn(
        sentinel,
        visible,
        "{} leaked {} into visible output:\n{}".format(where, sentinel, visible),
      )

  ##
  ## >>========================= share url persistence =========================>>
  ##

  def test_share_url_update_never_writes_a_raw_record_or_url(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = share_url_table(
          rows=[
            {
              "owner_user_id": "9001",
              "nickname": "before",
              "live_share_url": None,
              "user_status": "正常",
            }
          ]
        )
        with capture(level) as captured:
          table.update_live_share_url_record(sentinel_record())
        self.assert_no_sentinel(captured, "update_live_share_url_record")

  def test_share_url_insert_never_writes_a_raw_record_or_url(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = share_url_table(rows=[])
        with capture(level) as captured:
          table.insert_live_share_url_record(sentinel_record())
        self.assert_no_sentinel(captured, "insert_live_share_url_record")

  def test_share_url_update_failure_never_writes_the_driver_message(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = share_url_table(error=boom())
        with capture(level) as captured:
          with self.assertRaises(Boom):
            table.update_live_share_url_record(sentinel_record())
        self.assert_no_sentinel(captured, "update_live_share_url_record failure")

  def test_share_url_insert_failure_never_writes_the_driver_message(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = share_url_table(error=boom())
        with capture(level) as captured:
          with self.assertRaises(Boom):
            table.insert_live_share_url_record(sentinel_record())
        self.assert_no_sentinel(captured, "insert_live_share_url_record failure")

  def test_share_url_lookups_never_write_the_url_they_searched_for(self):
    lookups = (
      ("is_live_share_url_record_exist", (SECRET_SHARE_URL,)),
      ("get_owner_directory_name_by_live_share_url", (SECRET_SHARE_URL,)),
      ("get_owner_nickname_by_live_share_url", (SECRET_SHARE_URL,)),
    )
    for name, arguments in lookups:
      if not hasattr(DouyinShareUrlTable, name):
        continue
      for level in LEVELS:
        with self.subTest(lookup=name, level=logging.getLevelName(level)):
          table, unused = share_url_table(error=boom())
          with capture(level) as captured:
            with self.assertRaises(Boom):
              getattr(table, name)(*arguments)
          self.assert_no_sentinel(captured, name)

  ##
  ## >>========================== generic table CRUD ==========================>>
  ##

  def test_generic_insert_never_writes_sql_params_or_the_record(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table()
        with capture(level) as captured:
          table.insert_record({"id": "1", "payload": SECRET_SQL_PARAM})
        self.assert_no_sentinel(captured, "insert_record")

  def test_generic_insert_failure_never_writes_the_record_data(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table(error=boom())
        with capture(level) as captured:
          with self.assertRaises(Boom):
            table.insert_record({"id": "1", "payload": SECRET_RECORD_VALUE})
        self.assert_no_sentinel(captured, "insert_record failure")

  def test_generic_update_never_writes_sql_params_or_update_data(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table()
        with capture(level) as captured:
          table.update_record({"id": SECRET_SQL_PARAM, "payload": SECRET_RECORD_VALUE})
        self.assert_no_sentinel(captured, "update_record")

  def test_generic_update_failure_never_writes_update_data(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table(error=boom())
        with capture(level) as captured:
          with self.assertRaises(Boom):
            table.update_record(
              {"id": SECRET_SQL_PARAM, "payload": SECRET_RECORD_VALUE}
            )
        self.assert_no_sentinel(captured, "update_record failure")

  def test_generic_delete_never_writes_its_conditions(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table()
        with capture(level) as captured:
          table.delete_record({"id": SECRET_SQL_PARAM})
        self.assert_no_sentinel(captured, "delete_record")

  def test_generic_delete_failure_never_writes_its_conditions(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table(error=boom())
        with capture(level) as captured:
          with self.assertRaises(Boom):
            table.delete_record({"id": SECRET_SQL_PARAM})
        self.assert_no_sentinel(captured, "delete_record failure")

  def test_generic_query_never_writes_conditions_or_returned_rows(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table(
          rows=[{"id": "1", "payload": SECRET_RECORD_VALUE}]
        )
        with capture(level) as captured:
          table.get_record({"id": SECRET_SQL_PARAM})
        self.assert_no_sentinel(captured, "get_record")

  def test_generic_query_failure_never_writes_its_conditions(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = generic_table(error=boom())
        with capture(level) as captured:
          with self.assertRaises(Boom):
            table.get_record({"id": SECRET_SQL_PARAM})
        self.assert_no_sentinel(captured, "get_record failure")

  ##
  ## >>========================= recording persistence =========================>>
  ##

  def test_recording_persistence_failure_never_writes_the_driver_message(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        table, unused = recording_table(error=boom())
        with capture(level) as captured:
          with self.assertRaises(Boom):
            table.create_recording(
              {
                "app_user_id": 1,
                "platform": "douyin",
                "room_id": "77",
                "owner_user_id": "9001",
                "title": SECRET_RECORD_VALUE,
                "protocol": "flv",
                "output_path": "/tmp/{}.flv".format(SECRET_RECORD_VALUE),
                "source": "live",
              }
            )
        self.assert_no_sentinel(captured, "create_recording failure")


class PersistenceDiagnosticUsefulnessTest(unittest.TestCase):
  """Redaction that deletes the diagnostic is not redaction, it is silence."""

  def test_a_failed_share_url_update_still_reports_a_closed_event(self):
    table, unused = share_url_table(error=boom())
    with capture(logging.ERROR) as captured:
      with self.assertRaises(Boom):
        table.update_live_share_url_record(sentinel_record())
    visible = captured.visible()
    self.assertIn("persistence diagnostic", visible)
    self.assertIn("table=share_url", visible)
    self.assertIn("error=Boom", visible)

  def test_a_failed_generic_insert_still_reports_a_closed_event(self):
    table, unused = generic_table(error=boom())
    with capture(logging.ERROR) as captured:
      with self.assertRaises(Boom):
        table.insert_record({"id": "1", "payload": SECRET_RECORD_VALUE})
    visible = captured.visible()
    self.assertIn("persistence diagnostic", visible)
    self.assertIn("table=sentinel_table", visible)
    self.assertIn("error=Boom", visible)

  def test_a_successful_generic_update_still_reports_the_affected_rows(self):
    table, unused = generic_table()
    with capture(logging.INFO) as captured:
      table.update_record({"id": "1", "payload": "value"})
    visible = captured.visible()
    self.assertIn("persistence diagnostic", visible)
    self.assertIn("rows=1", visible)


if __name__ == "__main__":
  unittest.main()


##
## >>===================== the invariant, not the instance =====================>>
##
##
## The tests above prove that today's call sites do not leak. This one proves
## that tomorrow's cannot be written by accident.
##
## Every leak closed in P18 had the same shape - a value interpolated into a log
## message with ``str.format``, an f-string or ``%`` - and every one of them was
## written by somebody adding a perfectly reasonable diagnostic. A sentinel test
## only catches the paths it happens to exercise; this reads the source and
## refuses the *shape*, so a new method with a new leak fails here even though
## no sentinel test knows it exists.
##
## The rule: inside these modules, a logger call is either a plain string
## literal or a ``persistence_diagnostic(...)`` call. Nothing else. Building the
## message some other way is exactly how a record dict, a parameter tuple or a
## driver message reaches a log file.
##
import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

##
## Production persistence. ``table_export`` and ``library/databaselib`` are
## deliberately absent: neither is imported by anything the server runs, and
## rewriting unreachable code would be churn dressed up as a fix.
##
PERSISTENCE_MODULES = (
  "backend/src/database/social_media_stream_database.py",
  "backend/src/database/query/owner_history.py",
  "backend/src/database/table/aweme_record.py",
  "backend/src/database/table/person_identity.py",
  "backend/src/database/table/recording_record.py",
  "backend/src/database/table/share_url.py",
  "backend/src/database/table/social_media_stream_db_table.py",
  "backend/src/database/table/table_import.py",
)

LOG_METHODS = frozenset({"debug", "info", "warning", "error", "exception", "critical"})


def _is_logger_call(node):
  """Whether ``node`` is ``get_logger(...).<level>(...)``."""
  if not isinstance(node, ast.Call):
    return False
  method = node.func
  if not isinstance(method, ast.Attribute) or method.attr not in LOG_METHODS:
    return False
  receiver = method.value
  return (
    isinstance(receiver, ast.Call)
    and isinstance(receiver.func, ast.Name)
    and receiver.func.id == "get_logger"
  )


def _is_closed_message(node):
  if isinstance(node, ast.Constant) and isinstance(node.value, str):
    return True
  return (
    isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "persistence_diagnostic"
  )


class PersistenceDiagnosticSourceInvariantTest(unittest.TestCase):
  def test_no_persistence_log_message_is_built_from_a_value(self):
    offenders = []
    for relative in PERSISTENCE_MODULES:
      source_path = PROJECT_ROOT / relative
      tree = ast.parse(source_path.read_text(encoding="utf-8"))
      for node in ast.walk(tree):
        if not _is_logger_call(node):
          continue
        if not node.args:
          continue
        if not _is_closed_message(node.args[0]):
          offenders.append(
            "{}:{}".format(relative, node.lineno)
          )
        ##
        ## Lazy ``%``-style logging takes its values as extra positional
        ## arguments, which the formatter interpolates just as eagerly once a
        ## handler is attached. A closed message never needs them.
        ##
        if len(node.args) > 1:
          offenders.append(
            "{}:{} (lazy interpolation arguments)".format(relative, node.lineno)
          )

    self.assertEqual(
      [],
      offenders,
      "persistence diagnostics must be a plain literal or "
      "persistence_diagnostic(...), never a formatted value: {}".format(offenders),
    )

  def test_the_closed_builder_has_no_escape_hatch(self):
    from backend.src.library import safe_diagnostics

    signature = ast.parse(
      Path(safe_diagnostics.__file__).read_text(encoding="utf-8")
    )
    builder = next(
      node for node in ast.walk(signature)
      if isinstance(node, ast.FunctionDef)
      and node.name == "persistence_diagnostic"
    )
    self.assertIsNone(builder.args.kwarg, "**kwargs would reopen the boundary")
    self.assertIsNone(builder.args.vararg, "*args would reopen the boundary")
    self.assertEqual(
      ["event"],
      [argument.arg for argument in builder.args.args],
      "every field beyond the event must be keyword-only and named",
    )

  def test_an_unknown_event_is_refused_rather_than_rendered(self):
    from backend.src.library.safe_diagnostics import persistence_diagnostic

    with self.assertRaises(ValueError):
      persistence_diagnostic("anything_a_caller_wants_to_say")

  def test_values_that_are_not_identifiers_render_as_unknown(self):
    from backend.src.library.safe_diagnostics import persistence_diagnostic

    rendered = persistence_diagnostic(
      "persistence_query_failed",
      identity=SECRET_SHARE_URL,
      related_identity="昵称",
      rows=True,
      columns=-1,
    )
    self.assertNotIn("SECRET_SHARE_URL_P18", rendered)
    self.assertNotIn("昵称", rendered)
    self.assertIn("identity=unknown", rendered)
    self.assertIn("related_identity=unknown", rendered)
    ##
    ## ``True`` is an ``int`` in Python and would otherwise render as a row
    ## count of 1 that no statement produced.
    ##
    self.assertIn("rows=unknown", rendered)
    self.assertIn("columns=unknown", rendered)
