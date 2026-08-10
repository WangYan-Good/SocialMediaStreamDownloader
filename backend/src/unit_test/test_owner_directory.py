import unittest

from backend.src.platform.douyin.douyin_owner_directory import (
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
