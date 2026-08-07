from copy import deepcopy
import unittest
from unittest.mock import patch

from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects import mysql

from backend.src.database.orm.models import Base


class FakeInspector:
  def __init__(self):
    self.tables = list(Base.metadata.tables)
    self.columns = {}
    self.primary_keys = {}
    self.foreign_keys = {}
    self.uniques = {}
    self.indexes = {}
    self.comments = {}
    self.options = {}
    for table_name, table in Base.metadata.tables.items():
      options = table.dialect_options["mysql"]
      self.columns[table_name] = []
      for column in table.columns:
        reflected_type = deepcopy(column.type)
        if hasattr(reflected_type, "collation"):
          reflected_type.collation = (
            getattr(column.type, "collation", None) or options["collate"]
          )
        if hasattr(reflected_type, "charset"):
          reflected_type.charset = (
            getattr(column.type, "charset", None) or options["charset"]
          )
        self.columns[table_name].append({
          "name": column.name,
          "type": reflected_type,
          "nullable": column.nullable,
          "default": None if column.server_default is None else str(column.server_default.arg),
          "autoincrement": column.autoincrement is True,
        })
      self.primary_keys[table_name] = {
        "name": table.primary_key.name,
        "constrained_columns": [column.name for column in table.primary_key],
      }
      self.foreign_keys[table_name] = [
        {
          "name": constraint.name,
          "constrained_columns": [column.name for column in constraint.columns],
          "referred_table": constraint.referred_table.name,
          "referred_columns": [element.column.name for element in constraint.elements],
        }
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
      ]
      self.uniques[table_name] = [
        {
          "name": constraint.name,
          "column_names": [column.name for column in constraint.columns],
        }
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
      ]
      self.indexes[table_name] = [
        {
          "name": index.name,
          "column_names": [column.name for column in index.columns],
          "unique": index.unique,
        }
        for index in table.indexes
      ]
      self.comments[table_name] = {"text": table.comment}
      self.options[table_name] = {
        "mysql_engine": options["engine"],
        "mysql_default charset": options["charset"],
        "mysql_collate": options["collate"],
      }

  def get_table_names(self):
    return self.tables

  def get_columns(self, table_name):
    return self.columns[table_name]

  def get_pk_constraint(self, table_name):
    return self.primary_keys[table_name]

  def get_foreign_keys(self, table_name):
    return self.foreign_keys[table_name]

  def get_unique_constraints(self, table_name):
    return self.uniques[table_name]

  def get_indexes(self, table_name):
    return self.indexes[table_name]

  def get_table_comment(self, table_name):
    return self.comments[table_name]

  def get_table_options(self, table_name):
    return self.options[table_name]


class SchemaCompareTest(unittest.TestCase):
  def load_api(self):
    try:
      from backend.src.database.schema_compare import (
        SchemaReport,
        compare_managed_schema,
      )
    except ModuleNotFoundError as exc:
      raise AssertionError("schema comparator is not implemented") from exc
    return SchemaReport, compare_managed_schema

  def compare(self, inspector):
    _, compare_managed_schema = self.load_api()
    with patch("backend.src.database.schema_compare.inspect", return_value=inspector):
      return compare_managed_schema(object())

  def test_report_classifies_errors_and_warnings_without_credentials(self):
    SchemaReport, _ = self.load_api()
    report = SchemaReport()
    report.add_error("room_base", "column", "missing column id")
    report.add_warning("legacy_v1", "table", "unmanaged table")

    self.assertFalse(report.is_compatible)
    self.assertEqual(1, len(report.errors))
    self.assertEqual(1, len(report.warnings))
    self.assertNotIn("password", report.format_text().lower())

  def test_matching_schema_is_compatible_and_unmanaged_table_warns(self):
    inspector = FakeInspector()
    inspector.tables.extend(["alembic_version", "legacy_v1"])
    report = self.compare(inspector)

    self.assertTrue(report.is_compatible)
    self.assertEqual(["legacy_v1"], [item.table for item in report.warnings])

  def test_missing_managed_table_is_an_error(self):
    inspector = FakeInspector()
    inspector.tables.remove("live_record")
    report = self.compare(inspector)

    self.assertFalse(report.is_compatible)
    self.assertIn(("live_record", "table"), {(item.table, item.object_type) for item in report.errors})

  def test_columns_compare_presence_type_unsigned_nullable_and_default(self):
    inspector = FakeInspector()
    inspector.columns["share_url"].pop(1)
    inspector.columns["share_url"].append(
      {"name": "unexpected", "type": mysql.INTEGER(), "nullable": True, "default": None}
    )
    actived = next(item for item in inspector.columns["share_url"] if item["name"] == "actived_count")
    actived.update(type=mysql.INTEGER(unsigned=False), nullable=True, default="7")
    report = self.compare(inspector)

    messages = "\n".join(item.message for item in report.errors)
    self.assertIn("missing column sec_user_id", messages)
    self.assertIn("extra column unexpected", messages)
    self.assertIn("unsigned", messages)
    self.assertIn("nullable", messages)
    self.assertIn("default", messages)

  def test_columns_compare_autoincrement_and_effective_collation(self):
    inspector = FakeInspector()
    member_index = next(
      item for item in inspector.columns["room_admin_user_id"]
      if item["name"] == "index"
    )
    member_index["autoincrement"] = False
    live_url = next(
      item for item in inspector.columns["share_url"]
      if item["name"] == "live_share_url"
    )
    live_url["type"].collation = "utf8mb4_bin"

    report = self.compare(inspector)

    messages = "\n".join(item.message for item in report.errors)
    self.assertIn("index autoincrement differs", messages)
    self.assertIn("live_share_url collation differs", messages)

  def test_key_constraint_and_index_differences_are_errors(self):
    inspector = FakeInspector()
    inspector.primary_keys["live_record"]["constrained_columns"] = ["now"]
    inspector.foreign_keys["live_record"].append(
      {
        "name": "unexpected_fk",
        "constrained_columns": ["room_id"],
        "referred_table": "share_url",
        "referred_columns": ["owner_user_id"],
      }
    )
    inspector.uniques["room_admin_user_id"] = []
    inspector.indexes["share_url"].append(
      {"name": "unexpected_index", "column_names": ["sec_user_id"], "unique": False}
    )
    report = self.compare(inspector)

    object_types = {item.object_type for item in report.errors}
    self.assertTrue({"primary_key", "foreign_key", "unique_constraint", "index"}.issubset(object_types))

  def test_mysql_options_and_comment_are_compared(self):
    inspector = FakeInspector()
    inspector.options["user"] = {
      "mysql_engine": "MyISAM",
      "mysql_default charset": "latin1",
      "mysql_collate": "latin1_swedish_ci",
    }
    inspector.comments["user"] = {"text": "wrong"}
    report = self.compare(inspector)

    object_types = [item.object_type for item in report.errors if item.table == "user"]
    self.assertEqual(["charset", "collation", "comment", "engine"], sorted(object_types))

  def test_formatted_output_is_deterministic(self):
    SchemaReport, _ = self.load_api()
    report = SchemaReport()
    report.add_warning("z_table", "table", "later")
    report.add_error("a_table", "column", "first")

    lines = report.format_text().splitlines()
    self.assertIn("a_table", lines[0])
    self.assertIn("z_table", lines[1])


if __name__ == "__main__":
  unittest.main()
