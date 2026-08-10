import importlib
import unittest

from sqlalchemy.dialects import mysql


CORE_TABLES = frozenset({"share_url", "favorite_owner", "live_record"})
PRIMARY_ENTITY_TABLES = frozenset({"room_base", "room_owner_v2", "user"})
ROOM_EXTENSION_TABLES = frozenset(
  {
    "room_stats",
    "room_admin_user_id",
    "room_admin_user_open_id",
    "room_deco",
    "fans_group_admin_user_id",
    "fans_group_admin_user_open_id",
  }
)


def load_models():
  try:
    return importlib.import_module("backend.src.database.orm.models")
  except ModuleNotFoundError as exc:
    raise AssertionError("ORM production models are not implemented") from exc


class OrmModelTest(unittest.TestCase):
  def test_core_models_register_the_expected_tables(self):
    models = load_models()

    self.assertTrue(CORE_TABLES.issubset(models.MANAGED_TABLE_NAMES))
    self.assertTrue(CORE_TABLES.issubset(models.Base.metadata.tables))

  def test_share_url_schema_matches_the_existing_contract(self):
    models = load_models()
    table = models.Base.metadata.tables["share_url"]

    self.assertEqual(
      [
        "owner_user_id",
        "sec_user_id",
        "nickname",
        "post_share_url",
        "live_share_url",
        "directory_name",
        "user_status",
        "actived_count",
        "last_live_status",
        "last_checked_at",
        "last_room_id",
      ],
      list(table.columns.keys()),
    )
    self.assertEqual(["owner_user_id"], [item.name for item in table.primary_key])
    self.assertEqual(
      [
        "idx_nickname",
        "idx_share_url_actived_count",
        "idx_share_url_last_checked_at",
      ],
      sorted(item.name for item in table.indexes),
    )
    self.assertIsInstance(table.c.actived_count.type, mysql.INTEGER)
    self.assertTrue(table.c.actived_count.type.unsigned)
    self.assertEqual("0", str(table.c.actived_count.server_default.arg))

    self.assertIsInstance(table.c.last_live_status.type, mysql.TINYINT)
    self.assertTrue(table.c.last_live_status.type.unsigned)
    self.assertTrue(table.c.last_live_status.nullable)
    self.assertIsInstance(table.c.last_checked_at.type, mysql.TIMESTAMP)
    self.assertEqual(3, table.c.last_checked_at.type.fsp)
    self.assertTrue(table.c.last_checked_at.nullable)
    self.assertEqual(200, table.c.last_room_id.type.length)
    self.assertTrue(table.c.last_room_id.nullable)

  def test_favorite_owner_uses_the_existing_composite_key(self):
    models = load_models()
    table = models.Base.metadata.tables["favorite_owner"]

    self.assertEqual(
      ["owner_user_id", "platform"],
      [item.name for item in table.primary_key],
    )
    self.assertIsInstance(table.c.score.type, mysql.TINYINT)
    self.assertTrue(table.c.score.type.unsigned)
    self.assertEqual("0", str(table.c.score.server_default.arg))

  def test_live_record_schema_preserves_timestamp_precision_and_key_order(self):
    models = load_models()
    table = models.Base.metadata.tables["live_record"]

    self.assertEqual(
      [
        "now",
        "platform",
        "room_id",
        "owner_user_id",
        "user_id",
        "start_time",
        "finish_time",
        "status_code",
      ],
      list(table.columns.keys()),
    )
    self.assertEqual(
      ["now", "platform", "owner_user_id", "room_id"],
      [item.name for item in table.primary_key],
    )
    self.assertIsInstance(table.c.now.type, mysql.TIMESTAMP)
    self.assertEqual(3, table.c.now.type.fsp)
    self.assertIsInstance(table.c.status_code.type, mysql.TINYINT)
    self.assertTrue(table.c.status_code.type.unsigned)

  def test_core_tables_use_the_existing_mysql_options(self):
    models = load_models()

    for table_name in CORE_TABLES:
      options = models.Base.metadata.tables[table_name].dialect_options["mysql"]
      self.assertEqual("InnoDB", options["engine"])
      self.assertEqual("utf8mb4", options["charset"])
      self.assertEqual("utf8mb4_0900_ai_ci", options["collate"])

  def test_primary_entity_models_extend_the_managed_table_set(self):
    models = load_models()
    expected = CORE_TABLES | PRIMARY_ENTITY_TABLES

    self.assertTrue(expected.issubset(models.MANAGED_TABLE_NAMES))
    self.assertTrue(expected.issubset(models.Base.metadata.tables))

  def test_room_base_preserves_columns_key_index_and_dialect_types(self):
    models = load_models()
    table = models.Base.metadata.tables["room_base"]

    self.assertEqual(168, len(table.columns))
    self.assertEqual(
      ["now", "id", "start_time"],
      [item.name for item in table.primary_key],
    )
    self.assertEqual(
      {"idx_room_base_id_start_time": ["id", "start_time"]},
      {index.name: [column.name for column in index.columns] for index in table.indexes},
    )
    self.assertIsInstance(table.c.now.type, mysql.TIMESTAMP)
    self.assertEqual(3, table.c.now.type.fsp)
    self.assertIsInstance(table.c.title.type, mysql.TINYTEXT)
    self.assertIsInstance(table.c.cover.type, mysql.JSON)
    self.assertTrue(table.c.status.type.unsigned)
    self.assertEqual("0", str(table.c.status.server_default.arg))

  def test_room_owner_preserves_columns_indexes_comment_and_dialect_types(self):
    models = load_models()
    table = models.Base.metadata.tables["room_owner_v2"]

    self.assertEqual(114, len(table.columns))
    self.assertEqual(["room_id"], [item.name for item in table.primary_key])
    self.assertEqual({"idx_nickname", "idx_user_id"}, {item.name for item in table.indexes})
    self.assertEqual("主播信息表", table.comment)
    self.assertIsInstance(table.c.avatar_large.type, mysql.JSON)
    self.assertIsInstance(table.c.owner_device_id.type, mysql.BIGINT)
    self.assertTrue(table.c.gender.type.unsigned)
    self.assertEqual("CURRENT_TIMESTAMP", str(table.c.created_at.server_default.arg))

  def test_user_preserves_columns_key_comment_and_dialect_types(self):
    models = load_models()
    table = models.Base.metadata.tables["user"]

    self.assertEqual(100, len(table.columns))
    self.assertEqual(["id"], [item.name for item in table.primary_key])
    self.assertEqual("用户信息表", table.comment)
    self.assertIsInstance(table.c.badge_image_list.type, mysql.JSON)
    self.assertIsInstance(table.c.bg_img_url.type, mysql.TEXT)
    self.assertTrue(table.c.age_range.type.unsigned)
    self.assertEqual(
      "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
      str(table.c.updated_at.server_default.arg),
    )

  def test_managed_table_set_is_complete(self):
    models = load_models()
    expected = CORE_TABLES | PRIMARY_ENTITY_TABLES | ROOM_EXTENSION_TABLES

    self.assertEqual(expected, models.MANAGED_TABLE_NAMES)
    self.assertEqual(expected, frozenset(models.Base.metadata.tables))

  def test_room_stats_preserves_the_existing_contract(self):
    models = load_models()
    table = models.Base.metadata.tables["room_stats"]

    self.assertEqual(24, len(table.columns))
    self.assertEqual(
      ["now", "platform", "room_id"],
      [item.name for item in table.primary_key],
    )
    self.assertIsInstance(table.c.now.type, mysql.TIMESTAMP)
    self.assertEqual(3, table.c.now.type.fsp)
    self.assertIsInstance(table.c.user_count_composition_city.type, mysql.INTEGER)

  def test_repeated_room_member_tables_preserve_keys_and_unique_record(self):
    models = load_models()
    cases = {
      "room_admin_user_id": "admin_user_id",
      "room_admin_user_open_id": "admin_user_open_id",
      "fans_group_admin_user_id": "fans_group_admin_user_id",
      "fans_group_admin_user_open_id": "fans_group_admin_user_open_id",
    }

    for table_name, member_column in cases.items():
      with self.subTest(table=table_name):
        table = models.Base.metadata.tables[table_name]
        self.assertEqual(4, len(table.columns))
        self.assertEqual(
          ["index", "platform", "room_id"],
          [item.name for item in table.primary_key],
        )
        self.assertTrue(table.c.index.autoincrement)
        constraint = next(
          item for item in table.constraints if item.name == "unique_record"
        )
        self.assertEqual(
          ["platform", "room_id", member_column],
          [item.name for item in constraint.columns],
        )

  def test_room_deco_preserves_columns_key_index_and_json_fields(self):
    models = load_models()
    table = models.Base.metadata.tables["room_deco"]

    self.assertEqual(25, len(table.columns))
    self.assertEqual(
      ["deco_index", "platform", "room_id"],
      [item.name for item in table.primary_key],
    )
    self.assertEqual({"idx_deco_type"}, {item.name for item in table.indexes})
    self.assertTrue(table.c.deco_index.autoincrement)
    self.assertIsInstance(table.c.image_data.type, mysql.JSON)


if __name__ == "__main__":
  unittest.main()
