import unittest

from backend.src.database.table.person_identity import (
  DouyinPersonIdentityTable,
  UnknownRole,
)


class FakeCursor:
  def __init__(self):
    self.calls = []
    self.rows = []
    self.lastrowid = 7

  def execute(self, sql, params=None):
    self.calls.append((" ".join(sql.split()), params))

  def fetchall(self):
    return self.rows

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


def build_table(rows=()):
  table = DouyinPersonIdentityTable.__new__(DouyinPersonIdentityTable)
  cursor = FakeCursor()
  cursor.rows = list(rows)
  connection = FakeConnection(cursor)
  table.get_connection = lambda: connection
  table.require_write_ready = lambda: None
  return table, cursor


class RoleValidationTest(unittest.TestCase):
  """角色必须是三个已知值之一，且不能省略。

  留空只会攒出一批将来没人记得该填什么的行，所以宁可在写入点就拒绝。
  """

  def test_a_known_role_is_accepted(self):
    for role in ("main", "alt", "matrix"):
      table, cursor = build_table()
      table.attach_account("douyin", "owner-1", 3, role)
      self.assertEqual(len(cursor.calls), 1)

  def test_an_unknown_role_is_rejected_before_any_sql(self):
    table, cursor = build_table()

    with self.assertRaises(UnknownRole):
      table.attach_account("douyin", "owner-1", 3, "boss")

    self.assertEqual(cursor.calls, [])

  def test_a_missing_role_is_rejected(self):
    table, _ = build_table()

    with self.assertRaises(UnknownRole):
      table.attach_account("douyin", "owner-1", 3, None)


class AttachAccountTest(unittest.TestCase):
  def test_attaching_replaces_any_earlier_owner_of_the_account(self):
    """一个账号至多属于一个人。

    重新挂载是纠错的正常操作——标错了要能改——所以按主键 upsert，
    而不是插入第二行。
    """
    table, cursor = build_table()

    table.attach_account("douyin", "owner-1", 5, "alt")

    sql, params = cursor.calls[0]
    self.assertIn("ON DUPLICATE KEY UPDATE", sql)
    self.assertIn("person_id", sql)
    self.assertIn("role", sql)
    self.assertEqual(params, ("douyin", "owner-1", 5, "alt"))

  def test_detaching_removes_the_row(self):
    table, cursor = build_table()

    table.detach_account("douyin", "owner-1")

    sql, params = cursor.calls[0]
    self.assertIn("DELETE FROM person_account", sql)
    self.assertEqual(params, ("douyin", "owner-1"))


class PersonDirectoryLookupTest(unittest.TestCase):
  """B2 的落盘归并依赖这一个查询。"""

  def test_an_attached_account_reports_its_persons_directory(self):
    table, cursor = build_table(rows=[("合并目录",)])

    found = table.find_person_directory_name("owner-1")

    self.assertEqual(found, "合并目录")
    sql, params = cursor.calls[0]
    self.assertIn("person_account", sql)
    self.assertIn("person", sql)
    self.assertEqual(params, ("douyin", "owner-1"))

  def test_an_unattached_account_reports_nothing(self):
    """没挂人的账号必须与今天行为一致，这是整个功能的零影响保证。"""
    table, _ = build_table(rows=[])

    self.assertIsNone(table.find_person_directory_name("owner-1"))

  def test_a_person_without_a_directory_reports_nothing(self):
    """建了人但没填目录，不该把落盘位置变成空字符串。"""
    table, _ = build_table(rows=[(None,)])

    self.assertIsNone(table.find_person_directory_name("owner-1"))

  def test_a_blank_directory_reports_nothing(self):
    table, _ = build_table(rows=[("   ",)])

    self.assertIsNone(table.find_person_directory_name("owner-1"))


class CollaborationTest(unittest.TestCase):
  def test_a_collaboration_is_recorded_in_one_direction(self):
    table, cursor = build_table()

    table.add_collaboration(photographer_id=2, subject_id=9)

    sql, params = cursor.calls[0]
    self.assertIn("person_collaboration", sql)
    self.assertEqual(params[:2], (2, 9))

  def test_a_person_cannot_be_recorded_as_photographing_themselves(self):
    table, cursor = build_table()

    with self.assertRaises(ValueError):
      table.add_collaboration(photographer_id=4, subject_id=4)

    self.assertEqual(cursor.calls, [])


if __name__ == "__main__":
  unittest.main()
