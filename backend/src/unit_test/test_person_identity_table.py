import unittest

from backend.src.database.table.person_identity import (
  DouyinPersonIdentityTable,
  UnknownRole,
)


##
## 真实连接池用的是 pymysql 的 DictCursor，行是字典而不是元组。假游标最初返回
## 元组，把这个差异藏了起来：所有查询在单测里通过、在真库上 KeyError。
##
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
  """落盘归并依赖这一个查询。

  目录的唯一事实来源是**主账号**在 share_url 里记录的目录，person 自己不持有
  目录：一个 person 存在就意味着有主账号，再复制一份目录只会多一个可能与它
  不一致的地方。
  """

  def test_a_sub_account_reports_the_main_accounts_directory(self):
    table, cursor = build_table(rows=[{"directory_name": "主播甲"}])

    found = table.find_person_directory_name("sub-1")

    self.assertEqual(found, "主播甲")
    sql, params = cursor.calls[0]
    ##
    ## 两次 person_account 自连接：一次定位这个账号，一次定位同一个人的主账号
    ##
    self.assertEqual(2, sql.count("person_account"))
    self.assertIn("role", sql)
    self.assertEqual(params, ("douyin", "sub-1"))

  def test_the_main_account_reports_its_own_directory(self):
    """主账号解析到自己，与没有 person 时的结果相同。"""
    table, _ = build_table(rows=[{"directory_name": "主播甲"}])

    self.assertEqual(table.find_person_directory_name("main-1"), "主播甲")

  def test_a_person_without_a_main_account_reports_nothing(self):
    """没有主账号就没有权威目录，回落到账号自己的记录。"""
    table, _ = build_table(rows=[])

    self.assertIsNone(table.find_person_directory_name("sub-1"))

  def test_an_unattached_account_reports_nothing(self):
    """没挂人的账号必须与今天行为一致，这是整个功能的零影响保证。"""
    table, _ = build_table(rows=[])

    self.assertIsNone(table.find_person_directory_name("owner-1"))

  def test_a_person_without_a_directory_reports_nothing(self):
    """建了人但没填目录，不该把落盘位置变成空字符串。"""
    table, _ = build_table(rows=[{"directory_name": None}])

    self.assertIsNone(table.find_person_directory_name("owner-1"))

  def test_a_blank_directory_reports_nothing(self):
    table, _ = build_table(rows=[{"directory_name": "   "}])

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

    person_id = table.create_person("张三")

    self.assertEqual(person_id, cursor.lastrowid)
    sql, params = cursor.calls[0]
    self.assertIn("INSERT INTO person", sql)
    ##
    ## 不问目录：它来自之后被标为主号的那个账号
    ##
    self.assertNotIn("directory_name", sql)
    self.assertEqual(params, ("张三", None))

  def test_a_person_needs_a_name(self):
    table, cursor = build_table()

    with self.assertRaises(ValueError):
      table.create_person("   ")

    self.assertEqual(cursor.calls, [])

  def test_updating_a_person_leaves_unmentioned_fields_alone(self):
    """只改名字时不该把备注抹掉。

    用固定语句 + COALESCE 而非拼 SET 子句：未指定的字段传 None，COALESCE
    保留原值。这样运行时不构造 SQL 文本，符合本库「只有标识符能被插值」的
    不变量。
    """
    table, cursor = build_table()

    table.update_person(3, display_name="新名字")

    sql, params = cursor.calls[0]
    self.assertIn("note = COALESCE(%s, note)", sql)
    self.assertNotIn("directory_name", sql)
    self.assertEqual(params, ("新名字", None, 3))

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
      rows=[{"person_id": 1, "display_name": "张三",
            "directory_name": "张三_合并", "note": None, "account_count": 3}]
    )

    listed = table.list_persons()

    self.assertEqual(listed[0]["display_name"], "张三")
    self.assertEqual(listed[0]["account_count"], 3)
    sql, _ = cursor.calls[0]
    self.assertIn("LEFT JOIN person_account", sql)

  def test_a_person_with_no_accounts_still_appears(self):
    """先建人后挂号是自然顺序，中间那一刻不该从列表里消失。"""
    table, cursor = build_table(rows=[{"person_id": 2, "display_name": "摄影师李",
                              "directory_name": None, "note": None,
                              "account_count": 0}])

    listed = table.list_persons()

    self.assertEqual(listed[0]["account_count"], 0)
    sql, _ = cursor.calls[0]
    self.assertIn("LEFT JOIN", sql)


class AccountSearchTest(unittest.TestCase):
  """1815 个账号无法用下拉框选，必须能搜。"""

  def test_a_keyword_matches_nickname_or_id(self):
    table, cursor = build_table(rows=[{"owner_user_id": "acc-1", "nickname": "昵称",
                              "directory_name": "目录", "person_id": None,
                              "role": None}])

    found = table.search_accounts("昵称")

    self.assertEqual(found[0]["owner_user_id"], "acc-1")
    sql, params = cursor.calls[0]
    self.assertIn("LIKE", sql)
    self.assertIn("%昵称%", params)

  def test_the_search_reports_who_an_account_already_belongs_to(self):
    """挂号时必须看得见它是不是已经挂在别人名下。"""
    table, cursor = build_table(rows=[{"owner_user_id": "acc-1", "nickname": "昵称",
                              "directory_name": "目录", "person_id": 4,
                              "role": "alt"}])

    found = table.search_accounts("昵称")

    self.assertEqual(found[0]["person_id"], 4)
    self.assertEqual(found[0]["role"], "alt")
    sql, _ = cursor.calls[0]
    self.assertIn("LEFT JOIN person_account", sql)

  def test_an_empty_keyword_searches_nothing(self):
    table, cursor = build_table()

    self.assertEqual(table.search_accounts("   "), [])
    self.assertEqual(cursor.calls, [])


class PersonAggregationTest(unittest.TestCase):
  """按人聚合：一个人名下所有账号的作品与录播一起看。"""

  def test_a_persons_accounts_are_listed_with_their_roles(self):
    table, cursor = build_table(
      rows=[{"owner_user_id": "acc-1", "nickname": "昵称A", "role": "main"},
            {"owner_user_id": "acc-2", "nickname": "昵称B", "role": "alt"}]
    )

    accounts = table.list_person_accounts(3)

    self.assertEqual([a["role"] for a in accounts], ["main", "alt"])
    sql, params = cursor.calls[0]
    self.assertIn("person_account", sql)
    self.assertEqual(params, (3,))

  def test_the_summary_counts_posts_and_recordings_across_accounts(self):
    table, cursor = build_table(rows=[{"aweme_count": 12, "live_count": 47}])

    summary = table.person_summary(3)

    self.assertEqual(summary["aweme_count"], 12)
    self.assertEqual(summary["live_count"], 47)
    sql, _ = cursor.calls[0]
    self.assertIn("aweme_record", sql)
    self.assertIn("live_record", sql)

  def test_a_person_with_nothing_downloaded_counts_zero(self):
    table, _ = build_table(rows=[])

    summary = table.person_summary(3)

    self.assertEqual(summary, {"aweme_count": 0, "live_count": 0})


class PhotographerSearchTest(unittest.TestCase):
  """按摄影师检索：先找他合作过的主播，再取那些人名下账号的作品。"""

  def test_the_subjects_of_a_photographer_are_listed(self):
    table, cursor = build_table(rows=[{"person_id": 9, "display_name": "主播甲", "note": None},
            {"person_id": 10, "display_name": "主播乙", "note": "备注"}])

    subjects = table.list_subjects_of(2)

    self.assertEqual([s["display_name"] for s in subjects], ["主播甲", "主播乙"])
    sql, params = cursor.calls[0]
    self.assertIn("person_collaboration", sql)
    self.assertEqual(params, (2,))

  def test_the_photographers_of_a_subject_are_listed(self):
    """方向相反的一问：这个主播被谁拍过。"""
    table, cursor = build_table(rows=[{"person_id": 2, "display_name": "摄影师李", "note": None}])

    photographers = table.list_photographers_of(9)

    self.assertEqual(photographers[0]["display_name"], "摄影师李")
    sql, params = cursor.calls[0]
    self.assertIn("person_collaboration", sql)
    self.assertEqual(params, (9,))

  def test_works_shot_by_a_photographer_span_every_subject_account(self):
    table, cursor = build_table(
      rows=[{"aweme_id": "7", "desc": "作品描述",
            "save_dir": "/mnt/video/x", "downloaded_at": None,
            "display_name": "主播甲"}]
    )

    works = table.list_works_by_photographer(2)

    self.assertEqual(works[0]["aweme_id"], "7")
    self.assertEqual(works[0]["owner_display_name"], "主播甲")
    sql, params = cursor.calls[0]
    self.assertIn("person_collaboration", sql)
    self.assertIn("person_account", sql)
    self.assertIn("aweme_record", sql)
    self.assertEqual(params[:1], (2,))


class AccountIdentitySeedTest(unittest.TestCase):
  """标记一个还没下载过的主播时，顺便留一行身份记录。

  否则人物页只能把这个账号显示成一串 owner_user_id——share_url 里还没有它。
  身份是明确表态的产物，与「浏览了一下」不同，所以这一行是有依据的。
  """

  def test_only_identity_columns_are_written(self):
    table, cursor = build_table()

    table.upsert_account_identity("acc-9", "sec-9", "主播甲")

    sql, params = cursor.calls[0]
    self.assertIn("INSERT INTO share_url", sql)
    self.assertEqual(params, ("acc-9", "sec-9", "主播甲"))
    ##
    ## 这四列各有其主：目录归 person 与下载链路，两个 share_url 归各自的
    ## 链路，计数归直播。身份录入一列都不许碰。
    ##
    for owned_elsewhere in (
      "directory_name",
      "post_share_url",
      "live_share_url",
      "actived_count",
    ):
      self.assertNotIn(owned_elsewhere, sql)

  def test_an_existing_row_keeps_what_it_has(self):
    """已有主播被标记时，昵称可以更新，但不得抹掉任何既有值。"""
    table, cursor = build_table()

    table.upsert_account_identity("acc-9", None, None)

    sql, _ = cursor.calls[0]
    self.assertIn("COALESCE(VALUES(sec_user_id), sec_user_id)", sql)
    self.assertIn("COALESCE(VALUES(nickname), nickname)", sql)

  def test_a_missing_owner_id_is_rejected(self):
    """owner_user_id 是主键，空值会造出一行谁也匹配不上的记录。"""
    table, cursor = build_table()

    with self.assertRaises(ValueError):
      table.upsert_account_identity("   ", "sec-9", "主播甲")

    self.assertEqual(cursor.calls, [])



class AlignToMainAccountTest(unittest.TestCase):
  """子账号自己记录的目录也要与主账号一致。

  不这样做，库里会写着「甲小号目录」而文件实际落在「主播甲」下——两处说法不同，
  以后谁读到哪一处都可能是错的。落盘用主账号的目录，记录也就该是它。
  """

  def test_sub_accounts_take_the_main_accounts_folder(self):
    table, cursor = build_table()

    table.align_accounts_to_main(3)

    sql, params = cursor.calls[0]
    self.assertIn("UPDATE share_url", sql)
    self.assertIn("role", sql)
    self.assertEqual(params, ("douyin", 3))

  def test_the_main_accounts_own_row_is_left_alone(self):
    """它就是那个事实来源，不该被自己覆盖。"""
    table, cursor = build_table()

    table.align_accounts_to_main(3)

    sql, _ = cursor.calls[0]
    self.assertIn("<>", sql)

  def test_a_main_account_without_a_folder_changes_nothing(self):
    """主账号自己都还没有目录时，不能把子账号的清空。"""
    table, cursor = build_table()

    table.align_accounts_to_main(3)

    sql, _ = cursor.calls[0]
    self.assertIn("IS NOT NULL", sql)


class IdentityAwareCountTest(unittest.TestCase):
  """消歧要按身份组计数：一个 person 算一组，未标记的账号各算一组。

  对齐之后，同一个 person 的多个账号在 share_url 里记着同一个目录名。若仍按
  账号数计，一个人自己就把计数顶到 2，于是被当成撞名而各自加后缀——归并当场
  失效。而两个真正不同的人同名时，计数必须仍然大于 1。
  """

  def test_one_person_with_many_accounts_counts_once(self):
    table, cursor = build_table(rows=[{"identity_count": 1}])

    self.assertEqual(1, table.count_identities_using_directory_name("主播甲"))
    sql, params = cursor.calls[0]
    self.assertIn("COUNT(DISTINCT", sql)
    self.assertIn("person_account", sql)
    self.assertEqual(params, ("douyin", "主播甲"))

  def test_two_people_sharing_a_name_count_twice(self):
    table, _ = build_table(rows=[{"identity_count": 2}])

    self.assertEqual(2, table.count_identities_using_directory_name("主播甲"))

  def test_a_name_nobody_uses_counts_zero(self):
    table, _ = build_table(rows=[])

    self.assertEqual(0, table.count_identities_using_directory_name("主播甲"))

  def test_a_blank_name_is_not_queried(self):
    table, cursor = build_table()

    self.assertEqual(0, table.count_identities_using_directory_name("  "))
    self.assertEqual(cursor.calls, [])


class PersonFolderTest(unittest.TestCase):
  """落盘既要目录名，也要主账号 id 作为消歧后缀。"""

  def test_the_main_accounts_folder_and_id_are_returned_together(self):
    table, _ = build_table(
      rows=[{"directory_name": "主播甲", "owner_user_id": "main-1"}]
    )

    found = table.find_person_folder("sub-1")

    self.assertEqual(found["directory_name"], "主播甲")
    self.assertEqual(found["main_owner_user_id"], "main-1")

  def test_an_unmarked_account_returns_nothing(self):
    table, _ = build_table(rows=[])

    self.assertIsNone(table.find_person_folder("nobody"))

  def test_a_main_account_without_a_folder_returns_nothing(self):
    table, _ = build_table(
      rows=[{"directory_name": "   ", "owner_user_id": "main-1"}]
    )

    self.assertIsNone(table.find_person_folder("sub-1"))

if __name__ == "__main__":
  unittest.main()
