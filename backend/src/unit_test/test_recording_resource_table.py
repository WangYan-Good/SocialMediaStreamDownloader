import unittest

from backend.src.database.table.recording_record import RecordingRecordTable


class FakeCursor:
  def __init__(self, recording_id=71):
    self.calls = []
    self.lastrowid = recording_id

  def __enter__(self):
    return self

  def __exit__(self, *args):
    return False

  def execute(self, sql, params):
    self.calls.append((sql, params))


class FakeConnection:
  def __init__(self):
    self.cursor_value = FakeCursor()
    self.commits = 0

  def cursor(self):
    return self.cursor_value

  def commit(self):
    self.commits += 1


class ConnectionContext:
  def __init__(self, connection):
    self.connection = connection

  def __enter__(self):
    return self.connection

  def __exit__(self, *args):
    return False


def valid_record(**overrides):
  record = {
    "app_user_id": 7,
    "platform": "douyin",
    "room_id": "room-x",
    "owner_user_id": "owner-x",
    "title": "Live title",
    "protocol": "hls",
    "output_path": "/media/live/room.ts",
    "started_at": None,
    "finished_at": None,
    "source": "task_api",
  }
  record.update(overrides)
  return record


class RecordingResourceTableTest(unittest.TestCase):
  def table(self):
    table = object.__new__(RecordingRecordTable)
    connection = FakeConnection()
    table.require_write_ready = lambda: None
    table.get_connection = lambda: ConnectionContext(connection)
    return table, connection

  def test_insert_is_bound_and_returns_the_database_identity(self):
    table, connection = self.table()

    recording_id = table.create_recording(valid_record())

    sql, params = connection.cursor_value.calls[0]
    self.assertIn("INSERT INTO recording_record", sql)
    self.assertNotIn("stream_url", sql)
    ##
    ## Eleven now: the recovery key is bound alongside the resource facts.
    ## It is NULL for an ordinary recording, which is every recording today.
    ##
    self.assertEqual(11, len(params))
    self.assertIsNone(params[10])
    self.assertEqual(71, recording_id)
    self.assertEqual(1, connection.commits)

  def test_each_call_is_an_insert_without_room_or_path_deduplication(self):
    table, connection = self.table()

    table.create_recording(valid_record())
    table.create_recording(valid_record(app_user_id=8))

    for sql, _ in connection.cursor_value.calls:
      self.assertNotIn("ON DUPLICATE", sql.upper())
      self.assertNotIn("IGNORE", sql.upper())

  def test_actual_output_path_is_inserted_without_normalisation(self):
    table, connection = self.table()
    actual_path = " /media/live/room with spaces.ts "

    table.create_recording(valid_record(output_path=actual_path))

    _, params = connection.cursor_value.calls[0]
    self.assertEqual(actual_path, params[6])

  def test_invalid_owner_and_missing_path_are_refused_before_sql(self):
    table, connection = self.table()

    for record in (
      valid_record(app_user_id=True),
      valid_record(app_user_id=0),
      valid_record(output_path=None),
      valid_record(platform=""),
      valid_record(source=""),
    ):
      with self.subTest(record=record):
        with self.assertRaises((TypeError, ValueError)):
          table.create_recording(record)

    self.assertEqual([], connection.cursor_value.calls)


if __name__ == "__main__":
  unittest.main()
