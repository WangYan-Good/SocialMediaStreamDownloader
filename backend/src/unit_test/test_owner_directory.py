import unittest

from backend.src.platform.douyin.douyin_owner_directory import (
  safe_directory_name,
  MAX_DIRECTORY_NAME_BYTES,
  choose_owner_directory,
  fit_directory_name,
)


OWNER = "1787149971110371"


class ChooseOwnerDirectoryTest(unittest.TestCase):
  """The folder naming policy both download paths share."""

  def test_a_plain_owner_keeps_their_nickname(self):
    self.assertEqual(choose_owner_directory("绿萝"), "绿萝")

  def test_the_recorded_folder_wins_over_the_current_nickname(self):
    """A renamed owner stays in one folder rather than starting a second."""
    self.assertEqual(
      choose_owner_directory("改名后的昵称", recorded_directory="原来的目录"),
      "原来的目录",
    )

  def test_the_nickname_is_used_when_nothing_is_recorded(self):
    self.assertEqual(
      choose_owner_directory("新主播", recorded_directory=None),
      "新主播",
    )

  def test_an_empty_recorded_value_does_not_win(self):
    for recorded in (None, ""):
      with self.subTest(recorded=recorded):
        self.assertEqual(
          choose_owner_directory("绿萝", recorded_directory=recorded),
          "绿萝",
        )

  def test_a_shared_name_gains_the_owner_id(self):
    """Douyin allows duplicate nicknames, so the folder cannot identify an owner."""
    self.assertEqual(
      choose_owner_directory("怡宝", owner_user_id=OWNER, owner_count=2),
      "怡宝_" + OWNER,
    )

  def test_a_name_used_by_one_owner_is_left_alone(self):
    self.assertEqual(
      choose_owner_directory("怡宝", owner_user_id=OWNER, owner_count=1),
      "怡宝",
    )

  def test_the_discriminator_applies_on_top_of_the_recorded_name(self):
    self.assertEqual(
      choose_owner_directory(
        "今天的昵称",
        recorded_directory="记录的目录",
        owner_user_id=OWNER,
        owner_count=3,
      ),
      "记录的目录_" + OWNER,
    )

  def test_every_owner_in_a_group_is_discriminated(self):
    """Including whoever was downloaded first.

    Otherwise the layout would depend on download order: one owner would hold the
    bare folder and the rest would be suffixed.
    """
    folders = {
      choose_owner_directory("怡宝", owner_user_id=owner, owner_count=3)
      for owner in ("111", "222", "333")
    }

    self.assertEqual(folders, {"怡宝_111", "怡宝_222", "怡宝_333"})

  def test_a_missing_owner_id_cannot_be_discriminated(self):
    self.assertEqual(
      choose_owner_directory("怡宝", owner_user_id=None, owner_count=5),
      "怡宝",
    )

  def test_a_numeric_owner_id_is_accepted(self):
    self.assertEqual(
      choose_owner_directory("怡宝", owner_user_id=42, owner_count=2),
      "怡宝_42",
    )

  def test_no_name_at_all_yields_nothing(self):
    self.assertEqual(choose_owner_directory("", owner_count=2), "")
    self.assertEqual(choose_owner_directory(None), "")


class FitDirectoryNameTest(unittest.TestCase):
  """A folder is a path component, so the byte limit applies to it too.

  share_url.directory_name is VARCHAR(100) and 100 CJK characters are 300 bytes,
  so the column permits more than the filesystem accepts.
  """

  def test_a_short_name_is_untouched(self):
    self.assertEqual(fit_directory_name("绿萝"), "绿萝")

  def test_a_long_name_is_capped(self):
    capped = fit_directory_name("中" * 200)

    self.assertLessEqual(len(capped.encode("utf-8")), MAX_DIRECTORY_NAME_BYTES)

  def test_the_discriminator_survives_a_long_name(self):
    capped = fit_directory_name("中" * 200, "_" + OWNER)

    self.assertLessEqual(len(capped.encode("utf-8")), MAX_DIRECTORY_NAME_BYTES)
    self.assertTrue(capped.endswith("_" + OWNER))

  def test_a_name_is_never_split_mid_character(self):
    capped = fit_directory_name("中" * 200)

    self.assertEqual(capped, capped.encode("utf-8").decode("utf-8"))
    self.assertNotIn("�", capped)

  def test_a_suffix_alone_survives_an_impossible_budget(self):
    suffix = "_" + "x" * MAX_DIRECTORY_NAME_BYTES
    self.assertEqual(fit_directory_name("中" * 10, suffix), suffix)

  def test_an_empty_name_yields_the_suffix(self):
    self.assertEqual(fit_directory_name("", "_42"), "_42")

  def test_the_cap_holds_across_the_boundary(self):
    for length in (80, 84, 85, 86, 100, 300):
      with self.subTest(length=length):
        capped = fit_directory_name("中" * length, "_" + OWNER)
        self.assertLessEqual(
          len(capped.encode("utf-8")),
          MAX_DIRECTORY_NAME_BYTES,
        )


if __name__ == "__main__":
  unittest.main()


class PersonDirectoryTest(unittest.TestCase):
  """一个人名下的多个账号，以后的下载落到同一个目录。

  这个目录由人显式命名，不从任何账号推导——取自被标为主号的那个账号会让
  落盘位置随主号变动而搬家。
  """

  def test_the_person_folder_wins_over_the_recorded_one(self):
    self.assertEqual(
      "某人_合并",
      choose_owner_directory(
        "当前昵称",
        recorded_directory="旧账号目录",
        person_directory="某人_合并",
      ),
    )

  def test_a_blank_person_folder_changes_nothing(self):
    """建了人但没填目录，不该把落盘位置变成空。"""
    self.assertEqual(
      "旧账号目录",
      choose_owner_directory(
        "当前昵称",
        recorded_directory="旧账号目录",
        person_directory="   ",
      ),
    )

  def test_an_unmarked_account_behaves_exactly_as_before(self):
    """零影响保证：没挂人的账号必须与今天逐字一致。"""
    self.assertEqual(
      choose_owner_directory("昵称", recorded_directory="记录目录"),
      choose_owner_directory(
        "昵称",
        recorded_directory="记录目录",
        person_directory=None,
      ),
    )

  def test_the_person_folder_never_takes_the_owner_id_suffix(self):
    """这是归并成立的前提。

    同名消歧后缀是按账号加的。若它作用在人物目录上，同一个人的两个账号会各自
    得到 某人_合并_<账号A> 和 某人_合并_<账号B>，正好把要合并的东西又拆开。
    人物目录是人显式指定的，不需要消歧。
    """
    first = choose_owner_directory(
      "昵称",
      person_directory="某人_合并",
      owner_user_id="acc-A",
      owner_count=3,
    )
    second = choose_owner_directory(
      "昵称",
      person_directory="某人_合并",
      owner_user_id="acc-B",
      owner_count=3,
    )

    self.assertEqual("某人_合并", first)
    self.assertEqual(first, second)

  def test_an_over_long_person_folder_is_still_trimmed(self):
    """字节上限是路径本身的限制，人物目录一样受它约束。"""
    long_name = "长" * 200

    chosen = choose_owner_directory("昵称", person_directory=long_name)

    self.assertLessEqual(len(chosen.encode("utf-8")), 255)


class SafeDirectoryNameTest(unittest.TestCase):
  """人物目录是手输的，必须和昵称走同一套净化规则。

  昵称在成为路径之前会过 sanitize_text，人物目录原先直接进 Path：输入 a/b 会
  悄悄建出嵌套目录，输入 ../../.. 会写到媒体根目录之外，输入 . 会让所有作品
  平铺进公共根。同一条规则必须覆盖两者。
  """

  def test_a_path_separator_cannot_create_a_nested_folder(self):
    self.assertNotIn("/", safe_directory_name("a/b"))

  def test_a_parent_reference_cannot_escape_the_media_root(self):
    chosen = safe_directory_name("../../../tmp/escape")

    self.assertNotIn("/", chosen)
    self.assertNotIn("..", chosen)

  def test_a_lone_dot_does_not_collapse_into_the_parent(self):
    self.assertNotIn(".", safe_directory_name("."))

  def test_chinese_letters_digits_and_hash_survive(self):
    self.assertEqual("张三abc123#", safe_directory_name("张三abc123#"))

  def test_the_byte_limit_still_applies(self):
    self.assertLessEqual(len(safe_directory_name("长" * 200).encode("utf-8")), 255)

  def test_nothing_usable_yields_nothing(self):
    self.assertEqual("", safe_directory_name("   "))
    self.assertEqual("", safe_directory_name(None))


class PersonDirectoryIsSanitisedTest(unittest.TestCase):
  """净化必须发生在选目录这一步，手输的值不能绕过它。"""

  def test_a_dangerous_person_directory_is_neutralised(self):
    chosen = choose_owner_directory("昵称", person_directory="../../../tmp/x")

    self.assertNotIn("/", chosen)
    self.assertNotIn("..", chosen)

  def test_a_person_directory_that_sanitises_to_nothing_falls_through(self):
    """净化后什么都不剩，就该退回账号自己的目录，而不是落到空目录。"""
    chosen = choose_owner_directory(
      "昵称",
      recorded_directory="记录目录",
      person_directory="///",
    )

    self.assertEqual("记录目录", chosen)
