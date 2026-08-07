import importlib
import unittest

from sqlalchemy.pool import NullPool


def load_orm_modules():
  try:
    engine_module = importlib.import_module("backend.src.database.orm.engine")
    base_module = importlib.import_module("backend.src.database.orm.base")
  except ModuleNotFoundError as exc:
    raise AssertionError("ORM database foundation is not implemented") from exc
  return engine_module, base_module


class OrmEngineTest(unittest.TestCase):
  def database_config(self):
    return {
      "database": {
        "enable": True,
        "host": "db.internal",
        "port": 3307,
        "username": "smsd_user",
        "password": "p@ss/word",
        "name": "smsd",
      }
    }

  def test_build_database_url_preserves_special_characters(self):
    engine_module, _ = load_orm_modules()

    url = engine_module.build_database_url(self.database_config())

    self.assertEqual(url.drivername, "mysql+pymysql")
    self.assertEqual(url.username, "smsd_user")
    self.assertEqual(url.password, "p@ss/word")
    self.assertEqual(url.host, "db.internal")
    self.assertEqual(url.port, 3307)
    self.assertEqual(url.database, "smsd")
    self.assertEqual(url.query, {"charset": "utf8mb4"})
    self.assertNotIn("p@ss/word", url.render_as_string(hide_password=True))

  def test_database_name_can_be_overridden_for_migration_tests(self):
    engine_module, _ = load_orm_modules()

    url = engine_module.build_database_url(
      self.database_config(), database_name="smsd_migration_test_012345abcdef"
    )

    self.assertEqual(url.database, "smsd_migration_test_012345abcdef")

  def test_engine_is_lazy_and_uses_no_persistent_pool(self):
    engine_module, _ = load_orm_modules()

    engine = engine_module.create_schema_engine(self.database_config())
    try:
      self.assertIsInstance(engine.pool, NullPool)
      self.assertEqual(engine.url.host, "db.internal")
    finally:
      engine.dispose()

  def test_declarative_base_has_stable_constraint_names(self):
    _, base_module = load_orm_modules()

    self.assertEqual(
      base_module.Base.metadata.naming_convention,
      {
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
      },
    )


if __name__ == "__main__":
  unittest.main()
