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
    ## one linear chain, one head: 0001 -> ... -> 0006 -> 0007
    ##
    self.assertEqual(
      "0007_authentication_foundation",
      scripts.get_current_head(),
    )
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
    moved = scripts.get_revision("0005_drop_person_directory")
    self.assertEqual("0004_person_identity", moved.down_revision)
    main_unique = scripts.get_revision("0006_person_main_unique")
    self.assertEqual("0005_drop_person_directory", main_unique.down_revision)
    authentication = scripts.get_revision("0007_authentication_foundation")
    self.assertEqual("0006_person_main_unique", authentication.down_revision)

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

  def main_constraint_source(self) -> str:
    config = self.load_factory()(unified_config())
    return (
      Path(config.get_main_option("script_location"))
      / "versions"
      / "0006_person_main_unique.py"
    ).read_text(encoding="utf-8")

  def test_the_main_constraint_migration_adds_a_generated_column_and_unique(self):
    """MySQL 没有 partial index，"只在 role='main' 的行里唯一"只能写成
    生成列 + 普通 UNIQUE：main 行取 person_id，其余取 NULL，而 MySQL 的
    唯一索引允许任意多个 NULL——正好是「0 个或 1 个，绝不能 2 个」。
    """
    source = self.main_constraint_source()
    upgrade = source.split("def upgrade()", 1)[1].split("def downgrade()", 1)[0]

    ##
    ## The names are module constants so the migration, the model and MySQL all
    ## hold one spelling; asserted against the whole file for that reason.
    ##
    self.assertIn('COLUMN_NAME = "main_person_id"', source)
    self.assertIn('INDEX_NAME = "uq_person_account_main_person"', source)
    self.assertIn("CASE WHEN role = 'main' THEN person_id ELSE NULL END", source)
    self.assertIn("Computed", upgrade)
    self.assertIn("unique=True", upgrade)
    ##
    ## VIRTUAL, not STORED: derived from two columns of its own row, so there is
    ## nothing to gain by materialising it.
    ##
    self.assertIn("persisted=False", upgrade)

  def test_it_refuses_to_run_on_data_that_already_has_two_mains(self):
    """迁移不能替用户挑哪个 main 该留下。

    那是业务数据，删掉或降级任何一个都可能是错的。所以先查、查到就明确失败，
    并报出冲突的 person_id 让人去处理——不静默改数据。
    """
    source = self.main_constraint_source()
    upgrade = source.split("def upgrade()", 1)[1].split("def downgrade()", 1)[0]

    ##
    ## 先检测，再加约束：顺序反了就会先撞上 UNIQUE，报出一个只有数据库看得懂
    ## 的错，用户不知道是哪几个人物出了问题。
    ##
    self.assertLess(
      upgrade.index("_DUPLICATE_MAINS"), upgrade.index("op.add_column")
    )
    self.assertLess(
      upgrade.index("raise RuntimeError"), upgrade.index("op.create_index")
    )
    ##
    ## 报出的是「哪几个 person 有几个 main」，不是数据库自己的重复键消息
    ##
    self.assertIn("GROUP BY person_id", source)
    self.assertIn("HAVING COUNT(*) > 1", source)
    self.assertIn("person_id={} has {} main accounts", upgrade)
    ##
    ## 不得自动修数据
    ##
    self.assertNotIn("UPDATE person_account", upgrade)
    self.assertNotIn("DELETE FROM person_account", upgrade)

  def test_the_main_constraint_downgrade_removes_both(self):
    source = self.main_constraint_source()
    downgrade = source.split("def downgrade()", 1)[1]

    self.assertIn("drop_index", downgrade)
    self.assertIn("drop_column", downgrade)
    ##
    ## Index before column: MySQL will not drop a column an index still refers
    ## to.
    ##
    self.assertLess(downgrade.index("drop_index"), downgrade.index("drop_column"))
    ##
    ## 回滚只撤销 schema，不动业务数据
    ##
    self.assertNotIn("DELETE", downgrade.upper())
    self.assertNotIn("drop_table", downgrade)

  def test_the_main_constraint_revision_follows_the_last_one(self):
    source = self.main_constraint_source()

    self.assertIn('down_revision: Union[str, None] = "0005_drop_person_directory"', source)

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

  def test_every_revision_id_fits_the_version_column(self):
    """alembic_version.version_num 是 VARCHAR(32)。

    超长的 id 不会在写脚本时报错，而是在迁移执行完 DDL、准备记录自己那一刻
    失败——库结构已经改了，版本号却没记上。只有真跑一次才会撞见。
    """
    config = self.load_factory()(unified_config())
    scripts = ScriptDirectory.from_config(config)

    for revision in scripts.walk_revisions():
      self.assertLessEqual(
        len(revision.revision),
        32,
        "revision id 超过 32 字符: {}".format(revision.revision),
      )

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


class TestAuthenticationMigrationShape(unittest.TestCase):
  """The authentication migration, read as source.

  Source-level rather than executed, for the same reason the person tests
  above are: a real MySQL is not always reachable, and the shape of the DDL is
  worth holding either way.  ``test_auth_migration_mysql`` runs it for real
  where a database exists.
  """

  def source(self) -> str:
    revision_path = (
      Path(__file__).resolve().parents[1]
      / "database"
      / "migration"
      / "versions"
      / "0007_authentication_foundation.py"
    )
    return revision_path.read_text(encoding="utf-8")

  def test_it_follows_the_last_revision(self):
    self.assertIn(
      'down_revision: Union[str, None] = "0006_person_main_unique"',
      self.source(),
    )

  def test_it_creates_both_identity_tables(self):
    source = self.source()

    self.assertIn('op.create_table(\n    "app_user"', source)
    self.assertIn('op.create_table(\n    "auth_session"', source)

  def test_it_leaves_every_platform_table_alone(self):
    ##
    ## The one thing this migration must not do.  ``user`` here is the Douyin
    ## profile table; a migration that altered it would be changing data this
    ## program downloads rather than data it owns.
    ##
    source = self.source()

    for platform_table in (
      '"user"',
      '"share_url"',
      '"aweme_record"',
      '"live_record"',
      '"person"',
      '"person_account"',
    ):
      for mutation in ("op.drop_table(", "op.alter_column(", "op.add_column("):
        self.assertNotIn(mutation + platform_table, source)

  def test_it_stores_a_hash_and_never_a_raw_token(self):
    source = self.source()

    self.assertIn('"token_hash"', source)
    for forbidden in ('"session_token"', '"raw_token"'):
      self.assertNotIn(forbidden, source)

  def test_the_session_points_at_the_application_user_and_cascades(self):
    source = self.source()

    self.assertIn("app_user.user_id", source)
    self.assertIn('ondelete="CASCADE"', source)

  def test_the_downgrade_removes_only_what_the_upgrade_added(self):
    source = self.source()
    downgrade = source[source.index("def downgrade()") :]

    self.assertIn('op.drop_table("auth_session")', downgrade)
    self.assertIn('op.drop_table("app_user")', downgrade)
    ##
    ## The platform table survives a downgrade, which is the same rule as above
    ## read from the other direction.
    ##
    self.assertNotIn('op.drop_table("user")', downgrade)

  def test_the_downgrade_does_not_drop_indexes_by_hand(self):
    ##
    ## MySQL uses ix_auth_session_user_id to back the foreign key on user_id
    ## and refuses to drop an index a constraint still needs, so an explicit
    ## drop_index before drop_table fails with 1553. DROP TABLE removes them
    ## anyway.
    ##
    ## Held here as well as in the MySQL test because this reads as harmless
    ## tidying, and the source gives no hint that it is not.
    ##
    source = self.source()
    downgrade = source[source.index("def downgrade()") :]

    self.assertNotIn("op.drop_index(", downgrade)

  def test_the_session_is_dropped_before_the_user_it_references(self):
    ##
    ## A foreign key cannot outlive the table it points at.  Dropping app_user
    ## first fails on any database that enforces the constraint.
    ##
    source = self.source()
    downgrade = source[source.index("def downgrade()") :]

    self.assertLess(
      downgrade.index('op.drop_table("auth_session")'),
      downgrade.index('op.drop_table("app_user")'),
    )
