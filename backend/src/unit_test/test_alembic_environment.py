from pathlib import Path
import unittest

from alembic.script import ScriptDirectory


EXPECTED_TABLES = frozenset(
  {
    "share_url",
    "favorite_owner",
    "live_record",
    "room_base",
    "room_owner_v2",
    "user",
    "room_stats",
    "room_admin_user_id",
    "room_admin_user_open_id",
    "room_deco",
    "fans_group_admin_user_id",
    "fans_group_admin_user_open_id",
  }
)


def unified_config():
  return {
    "database": {
      "host": "127.0.0.1",
      "port": 3306,
      "username": "smsd",
      "password": "not-written-to-alembic-config",
      "name": "smsd",
    }
  }


class AlembicEnvironmentTest(unittest.TestCase):
  def load_factory(self):
    try:
      from backend.src.database.migration import make_alembic_config
    except ModuleNotFoundError as exc:
      raise AssertionError("Alembic environment is not implemented") from exc
    return make_alembic_config

  def test_config_contains_no_database_url(self):
    config = self.load_factory()(unified_config())

    self.assertIsNone(config.get_main_option("sqlalchemy.url") or None)
    self.assertEqual(unified_config(), config.attributes["smsd_config"])
    self.assertIsNone(config.attributes["database_name"])

  def test_baseline_has_one_head_and_no_parent(self):
    config = self.load_factory()(unified_config())
    scripts = ScriptDirectory.from_config(config)

    ##
    ## one linear chain, one head: 0001 -> 0002 -> 0003 -> 0004
    ##
    self.assertEqual("0004_person_identity", scripts.get_current_head())
    baseline = scripts.get_revision("0001_initial_schema")
    self.assertIsNone(baseline.down_revision)
    live_status_cache = scripts.get_revision("0002_share_url_live_status_cache")
    self.assertEqual("0001_initial_schema", live_status_cache.down_revision)
    aweme_record = scripts.get_revision("0003_aweme_record")
    self.assertEqual(
      "0002_share_url_live_status_cache",
      aweme_record.down_revision,
    )
    person_identity = scripts.get_revision("0004_person_identity")
    self.assertEqual("0003_aweme_record", person_identity.down_revision)

  def test_the_person_migration_creates_all_three_tables_and_drops_them(self):
    """纯 DDL，无回填——此前没有任何版本记录过这些关系。"""
    config = self.load_factory()(unified_config())
    revision_path = (
      Path(config.get_main_option("script_location"))
      / "versions"
      / "0004_person_identity.py"
    )
    source = revision_path.read_text(encoding="utf-8")
    upgrade = source.split("def upgrade()", 1)[1].split("def downgrade()", 1)[0]
    downgrade = source.split("def downgrade()", 1)[1]

    self.assertEqual(3, upgrade.count("op.create_table("))
    for table_name in ("person", "person_account", "person_collaboration"):
      self.assertIn('"{}",'.format(table_name), upgrade)
      self.assertIn('op.drop_table("{}")'.format(table_name), downgrade)
    ##
    ## 无回填：此前没有任何版本记录过这些关系
    ##
    self.assertNotIn("op.drop_table", upgrade)
    self.assertNotIn("op.execute", upgrade)
    ##
    ## downgrade 不得显式删索引。MySQL 会保留外键所需的索引并拒绝删除
    ## （"Cannot drop index ...: needed in a foreign key constraint"），
    ## 而删表本就会带走它的索引——真实往返测出来的，文本断言看不出。
    ##
    self.assertNotIn("op.drop_index", downgrade)

  def test_baseline_is_an_explicit_immutable_snapshot(self):
    config = self.load_factory()(unified_config())
    revision_path = Path(config.get_main_option("script_location")) / "versions" / "0001_initial_schema.py"
    source = revision_path.read_text(encoding="utf-8")
    upgrade = source.split("def upgrade()", 1)[1].split("def downgrade()", 1)[0]

    self.assertEqual(12, upgrade.count("op.create_table("))
    for table_name in EXPECTED_TABLES:
      self.assertTrue(
        f'op.create_table("{table_name}"' in upgrade
        or f"op.create_table('{table_name}'" in upgrade
      )
    self.assertNotIn("op.drop_table", upgrade)
    self.assertNotIn("Base.metadata.create_all", source)
    self.assertNotIn("v1", source.lower())

  def test_the_person_migration_matches_the_databases_collation(self):
    """排序规则必须与被 join 的表一致。

    person_account.owner_user_id 要和 share_url / aweme_record / live_record
    对比，MySQL 拒绝比较不同排序规则的字符串（Illegal mix of collations），
    所以写错会让这些查询在运行时全部失败——假游标测不出来，只有真库会报。
    """
    config = self.load_factory()(unified_config())
    source = (
      Path(config.get_main_option("script_location"))
      / "versions"
      / "0004_person_identity.py"
    ).read_text(encoding="utf-8")

    self.assertEqual(3, source.count('mysql_collate="utf8mb4_0900_ai_ci"'))
    self.assertNotIn("utf8mb4_unicode_ci", source)

  def test_environment_filters_unmanaged_tables(self):
    config = self.load_factory()(unified_config())
    env_source = (
      Path(config.get_main_option("script_location")) / "env.py"
    ).read_text(encoding="utf-8")

    self.assertIn("MANAGED_TABLE_NAMES", env_source)
    self.assertIn("include_name=include_managed_name", env_source)
    self.assertIn('dialect_name="mysql"', env_source)


if __name__ == "__main__":
  unittest.main()
