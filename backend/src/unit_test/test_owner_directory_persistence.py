import re
import unittest


##
## 一个主播的 directory_name 是「他的文件放在哪个目录」这一既成事实，可能来自很久
## 之前的直播录制。改名后作品下载再写一次当前昵称，就会把这条记录改掉，于是同一个
## 主播的历史目录被丢弃、后续作品全部落到新昵称目录下。
##
## 实测（2026-08-12 日志 + 库）：owner 2925118187373371 首个作品按记录落在
## 淘淘妈_，随后 share_url.directory_name 被覆盖成当前昵称 九儿__，其余 150 个
## 作品全部改落 九儿__。
##
class FakeCursor:
  def __init__(self):
    self.calls = []

  def execute(self, sql, params=None):
    self.calls.append((sql, params))

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


def build_table():
  from backend.src.database.table.aweme_record import DouyinAwemeRecordTable

  table = DouyinAwemeRecordTable.__new__(DouyinAwemeRecordTable)
  cursor = FakeCursor()
  connection = FakeConnection(cursor)
  table.get_connection = lambda: connection
  table.require_write_ready = lambda: None
  return table, cursor


def split_assignments(clause: str):
  """Split on the commas that separate assignments, not those inside calls."""
  assignments = []
  depth = 0
  current = ""
  for character in clause:
    if character == "(":
      depth += 1
    elif character == ")":
      depth -= 1
    if character == "," and depth == 0:
      assignments.append(current)
      current = ""
      continue
    current += character
  assignments.append(current)
  return assignments


def update_assignment(sql: str, column: str) -> str:
  """Return the ``column = ...`` assignment from ON DUPLICATE KEY UPDATE."""
  clause = sql.split("ON DUPLICATE KEY UPDATE", 1)[1]
  for assignment in split_assignments(clause):
    normalised = " ".join(assignment.split())
    if normalised.startswith(column + " ="):
      return normalised.rstrip(";")
  raise AssertionError("{} is not assigned in {}".format(column, clause))


class OwnerDirectoryPersistenceTest(unittest.TestCase):
  def _upsert_sql(self) -> str:
    table, cursor = build_table()
    table.upsert_post_owner({
      "owner_user_id": "2925118187373371",
      "sec_user_id": "sec-1",
      "nickname": "九儿📿～",
      "post_share_url": None,
      "directory_name": "九儿__",
    })
    self.assertEqual(len(cursor.calls), 1)
    return cursor.calls[0][0]

  def test_an_existing_owner_directory_is_not_replaced_by_the_new_nickname(self):
    """The recorded folder is the fact; a nickname is only today's name."""
    assignment = update_assignment(self._upsert_sql(), "directory_name")

    ##
    ## the stored column has to be read before VALUES(), or a rename overwrites
    ## the folder that the owner's files already live in
    ##
    stored = assignment.index("directory_name", assignment.index("="))
    incoming = assignment.index("VALUES(directory_name)")
    self.assertLess(
      stored,
      incoming,
      "existing directory_name must win over the incoming one: {}".format(
        assignment
      ),
    )

  def test_a_new_owner_still_records_a_directory(self):
    """Preserving must not become never writing: a fresh row needs a folder."""
    sql = self._upsert_sql()
    columns = sql.split("ON DUPLICATE KEY UPDATE", 1)[0]

    self.assertIn("directory_name", columns)

  def test_the_nickname_is_still_kept_current(self):
    """Only the folder is pinned; the nickname is meant to track renames."""
    assignment = update_assignment(self._upsert_sql(), "nickname")

    self.assertTrue(
      re.match(r"nickname = COALESCE\(VALUES\(nickname\)", assignment),
      "nickname should follow the incoming value: {}".format(assignment),
    )


if __name__ == "__main__":
  unittest.main()
