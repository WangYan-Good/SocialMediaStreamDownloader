import unittest

from backend.src.database.table.aweme_record import DouyinAwemeRecordTable


class FakeCursor:
  def __init__(self):
    self.calls = []

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


class PostOwnershipTableTest(unittest.TestCase):
  def table(self):
    table = object.__new__(DouyinAwemeRecordTable)
    connection = FakeConnection()
    table.require_write_ready = lambda: None
    table.get_connection = lambda: ConnectionContext(connection)
    return table, connection

  def test_link_is_bound_and_only_softens_the_ownership_primary_key(self):
    table, connection = self.table()

    table.link_post(7, "douyin", "7657271784144009946")

    sql, params = connection.cursor_value.calls[0]
    self.assertIn("INSERT INTO app_user_aweme_record", sql)
    self.assertIn("ON DUPLICATE KEY UPDATE", sql)
    self.assertNotIn("IGNORE", sql.upper())
    self.assertEqual((7, "douyin", "7657271784144009946"), params)
    self.assertEqual(1, connection.commits)

  def test_invalid_identifiers_are_refused_before_sql(self):
    table, connection = self.table()

    for args in ((None, "douyin", "x"), (1, "", "x"), (1, "douyin", "")):
      with self.subTest(args=args):
        with self.assertRaises((TypeError, ValueError)):
          table.link_post(*args)

    self.assertEqual(connection.cursor_value.calls, [])


if __name__ == "__main__":
  unittest.main()
