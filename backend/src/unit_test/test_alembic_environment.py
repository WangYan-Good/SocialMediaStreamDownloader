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

    self.assertEqual("0001_initial_schema", scripts.get_current_head())
    revision = scripts.get_revision("0001_initial_schema")
    self.assertIsNone(revision.down_revision)

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
