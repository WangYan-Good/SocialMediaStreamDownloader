import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SHARE_URL_SOURCE = PROJECT_ROOT / "backend/src/database/table/share_url.py"

##
## 昵称、目录名等字段来自平台，完全由对方控制。曾经它们被 str.format 直接拼进
## SQL 字面量，一个形如 `名字", actived_count="999999` 的昵称即可改写同一条
## 语句中的其它列；逃逸到 WHERE 子句还能造成全表改写。
##
INJECTION_NICKNAME = '被改的昵称", actived_count="999999'


class FakeCursor:
  def __init__(self):
    self.calls = []
    self.rows = []

  def execute(self, sql, params=None):
    self.calls.append((sql, params))

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
  from backend.src.database.table.share_url import DouyinShareUrlTable

  table = DouyinShareUrlTable.__new__(DouyinShareUrlTable)
  cursor = FakeCursor()
  cursor.rows = list(rows)
  connection = FakeConnection(cursor)
  table.get_connection = lambda: connection
  table.require_write_ready = lambda: None
  return table, cursor


class ShareUrlSqlSafetyTest(unittest.TestCase):
  def test_no_sql_statement_is_built_by_string_interpolation(self):
    source = SHARE_URL_SOURCE.read_text(encoding="utf-8")

    offenders = []
    for number, line in enumerate(source.splitlines(), start=1):
      if ".format(" not in line:
        continue
      ##
      ## 允许：日志、异常文案，以及把私有常量表名填进 DDL。
      ##
      if re.search(r"get_logger|ValueError|TABLE_NAME", line):
        continue
      offenders.append((number, line.strip()))

    self.assertEqual(
      [],
      offenders,
      "SQL 必须参数化，不得用 str.format 拼接: {}".format(offenders),
    )

  def test_an_injecting_nickname_is_bound_as_a_value_on_update(self):
    table, cursor = build_table(
      rows=[
        {
          "owner_user_id": "victim",
          "nickname": "原昵称",
          "live_share_url": "https://example.test/a",
          "user_status": "正常",
        }
      ]
    )

    table.update_live_share_url_record(
      {
        "owner_user_id": "victim",
        "nickname": INJECTION_NICKNAME,
        "live_share_url": "https://example.test/a",
        "user_status": "正常",
      }
    )

    update_sql, params = cursor.calls[-1]
    self.assertIn("SET nickname = %s", update_sql)
    self.assertNotIn(INJECTION_NICKNAME, update_sql)
    self.assertIn(INJECTION_NICKNAME, params)

  def test_an_injecting_nickname_is_bound_as_a_value_on_insert(self):
    table, cursor = build_table(rows=[])

    table.update_live_share_url_record(
      {
        "owner_user_id": "fresh",
        "nickname": INJECTION_NICKNAME,
        "live_share_url": "https://example.test/b",
        "user_status": None,
      }
    )

    insert_sql, params = cursor.calls[-1]
    self.assertIn("VALUES (%s, %s, %s, %s, %s, %s, %s)", insert_sql)
    self.assertNotIn(INJECTION_NICKNAME, insert_sql)
    self.assertIn(INJECTION_NICKNAME, params)
    ##
    ## 缺失字段必须以 None 绑定，而不是被格式化成字面量 "None"。
    ##
    self.assertIn(None, params)

  def test_lookup_helpers_bind_their_arguments(self):
    for method, argument in (
      ("is_live_share_url_record_exist", "https://example.test/a"),
      ("get_owner_directory_name_by_live_share_url", "https://example.test/a"),
      ("get_directory_name_by_owner_user_id", "owner-1"),
      ("get_owner_nickname_by_live_share_url", "https://example.test/a"),
      ("is_owner_user_id_record_exist", "owner-1"),
    ):
      with self.subTest(method=method):
        table, cursor = build_table(rows=[])
        try:
          getattr(table, method)(argument)
        except Exception:
          ##
          ## 取值类方法在空结果时可能抛错，这里只关心 SQL 的构造方式。
          ##
          pass
        sql, params = cursor.calls[-1]
        self.assertIn("%s", sql)
        self.assertEqual((argument,), params)


if __name__ == "__main__":
  unittest.main()
