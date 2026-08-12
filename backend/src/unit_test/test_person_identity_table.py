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



class PersonCrudTest(unittest.TestCase):
  def test_creating_a_person_returns_the_new_id(self):
    table, cursor = build_table()

    person_id = table.create_person("张三", directory_name="张三_合并")

    self.assertEqual(person_id, cursor.lastrowid)
    sql, params = cursor.calls[0]
    self.assertIn("INSERT INTO person", sql)
    self.assertEqual(params, ("张三", "张三_合并", None))

  def test_a_person_needs_a_name(self):
    table, cursor = build_table()

    with self.assertRaises(ValueError):
      table.create_person("   ")

    self.assertEqual(cursor.calls, [])

  def test_updating_a_person_leaves_unmentioned_fields_alone(self):
    """只改目录时不该把备注抹掉。

    用固定语句 + COALESCE 而非拼 SET 子句：未指定的字段传 None，COALESCE
    保留原值。这样运行时不构造 SQL 文本，符合本库「只有标识符能被插值」的
    不变量。
    """
    table, cursor = build_table()

    table.update_person(3, directory_name="新目录")

    sql, params = cursor.calls[0]
    self.assertIn("note = COALESCE(%s, note)", sql)
    self.assertEqual(params, (None, "新目录", None, 3))

  def test_updating_nothing_touches_no_sql(self):
    table, cursor = build_table()

    table.update_person(3)

    self.assertEqual(cursor.calls, [])

  def test_deleting_a_person_relies_on_cascade(self):
    """账号归属与协作关系由外键级联删除，不在这里手工清。"""
    table, cursor = build_table()

    table.delete_person(3)

    self.assertEqual(len(cursor.calls), 1)
    sql, params = cursor.calls[0]
    self.assertIn("DELETE FROM person", sql)
    self.assertEqual(params, (3,))


class PersonListingTest(unittest.TestCase):
  def test_the_listing_counts_attached_accounts(self):
    table, cursor = build_table(
      rows=[(1, "张三", "张三_合并", None, 3)]
    )

    listed = table.list_persons()

    self.assertEqual(listed[0]["display_name"], "张三")
    self.assertEqual(listed[0]["account_count"], 3)
    sql, _ = cursor.calls[0]
    self.assertIn("LEFT JOIN person_account", sql)

  def test_a_person_with_no_accounts_still_appears(self):
    """先建人后挂号是自然顺序，中间那一刻不该从列表里消失。"""
    table, cursor = build_table(rows=[(2, "摄影师李", None, None, 0)])

    listed = table.list_persons()

    self.assertEqual(listed[0]["account_count"], 0)
    sql, _ = cursor.calls[0]
    self.assertIn("LEFT JOIN", sql)


class AccountSearchTest(unittest.TestCase):
  """1815 个账号无法用下拉框选，必须能搜。"""

  def test_a_keyword_matches_nickname_or_id(self):
    table, cursor = build_table(rows=[("acc-1", "昵称", "目录", None, None)])

    found = table.search_accounts("昵称")

    self.assertEqual(found[0]["owner_user_id"], "acc-1")
    sql, params = cursor.calls[0]
    self.assertIn("LIKE", sql)
    self.assertIn("%昵称%", params)

  def test_the_search_reports_who_an_account_already_belongs_to(self):
    """挂号时必须看得见它是不是已经挂在别人名下。"""
    table, cursor = build_table(rows=[("acc-1", "昵称", "目录", 4, "alt")])

    found = table.search_accounts("昵称")

    self.assertEqual(found[0]["person_id"], 4)
    self.assertEqual(found[0]["role"], "alt")
    sql, _ = cursor.calls[0]
    self.assertIn("LEFT JOIN person_account", sql)

  def test_an_empty_keyword_searches_nothing(self):
    table, cursor = build_table()

    self.assertEqual(table.search_accounts("   "), [])
    self.assertEqual(cursor.calls, [])

if __name__ == "__main__":
  unittest.main()
