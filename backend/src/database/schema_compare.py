from dataclasses import dataclass, field
import re
from typing import Literal

from sqlalchemy import ForeignKeyConstraint, MetaData, String, UniqueConstraint, inspect
from sqlalchemy.engine import Engine

from backend.src.database.orm.models import Base, MANAGED_TABLE_NAMES


@dataclass(frozen=True)
class SchemaDifference:
  severity: Literal["error", "warning"]
  table: str
  object_type: str
  message: str


@dataclass
class SchemaReport:
  differences: list[SchemaDifference] = field(default_factory=list)

  @property
  def errors(self) -> tuple[SchemaDifference, ...]:
    return tuple(item for item in self.differences if item.severity == "error")

  @property
  def warnings(self) -> tuple[SchemaDifference, ...]:
    return tuple(item for item in self.differences if item.severity == "warning")

  @property
  def is_compatible(self) -> bool:
    return not self.errors

  def add_error(self, table: str, object_type: str, message: str) -> None:
    self.differences.append(
      SchemaDifference("error", table, object_type, message)
    )

  def add_warning(self, table: str, object_type: str, message: str) -> None:
    self.differences.append(
      SchemaDifference("warning", table, object_type, message)
    )

  @classmethod
  def with_error(cls, table: str, object_type: str, message: str):
    report = cls()
    report.add_error(table, object_type, message)
    return report

  def format_text(self) -> str:
    ordered = sorted(
      self.differences,
      key=lambda item: (item.table, item.severity, item.object_type, item.message),
    )
    return "\n".join(
      f"{item.table}: {item.severity}: {item.object_type}: {item.message}"
      for item in ordered
    )


def _type_description(type_) -> tuple:
  class_name = type_.__class__.__name__.lower()
  if class_name in {"varchar", "string"} or (
    isinstance(type_, String) and class_name not in {"text", "tinytext", "mediumtext"}
  ):
    return ("string", getattr(type_, "length", None))
  if class_name in {"tinytext", "mediumtext", "text"}:
    return (class_name,)
  if class_name in {"json"}:
    return ("json",)
  if class_name in {"timestamp", "datetime"}:
    return (class_name, getattr(type_, "fsp", None))
  if class_name in {"tinyint", "smallint", "integer", "int", "bigint"}:
    family = "integer" if class_name == "int" else class_name
    return (family, bool(getattr(type_, "unsigned", False)))
  return (class_name, str(type_).lower())


def _normalized_default(value) -> str | None:
  if value is None:
    return None
  normalized = str(value).strip().strip("'").strip('"').lower()
  while normalized.startswith("(") and normalized.endswith(")"):
    normalized = normalized[1:-1].strip()
  normalized = re.sub(r"current_timestamp\(\)", "current_timestamp", normalized)
  normalized = re.sub(r"\s+", " ", normalized)
  if normalized in {"false", "b'0'"}:
    return "0"
  if normalized in {"true", "b'1'"}:
    return "1"
  return normalized


def _named_columns(items, column_key="column_names") -> dict[str | None, tuple[str, ...]]:
  return {
    item.get("name"): tuple(item.get(column_key) or ())
    for item in items
  }


def _expected_foreign_keys(table) -> dict[str | None, tuple]:
  return {
    constraint.name: (
      tuple(column.name for column in constraint.columns),
      constraint.referred_table.name,
      tuple(element.column.name for element in constraint.elements),
    )
    for constraint in table.constraints
    if isinstance(constraint, ForeignKeyConstraint)
  }


def _actual_foreign_keys(items) -> dict[str | None, tuple]:
  return {
    item.get("name"): (
      tuple(item.get("constrained_columns") or ()),
      item.get("referred_table"),
      tuple(item.get("referred_columns") or ()),
    )
    for item in items
  }


def _compare_columns(report, table_name, table, reflected_columns):
  expected = {column.name: column for column in table.columns}
  actual = {column["name"]: column for column in reflected_columns}
  for column_name in sorted(expected.keys() - actual.keys()):
    report.add_error(table_name, "column", f"missing column {column_name}")
  for column_name in sorted(actual.keys() - expected.keys()):
    report.add_error(table_name, "column", f"extra column {column_name}")
  for column_name in sorted(expected.keys() & actual.keys()):
    expected_column = expected[column_name]
    actual_column = actual[column_name]
    expected_type = _type_description(expected_column.type)
    actual_type = _type_description(actual_column["type"])
    if expected_type != actual_type:
      detail = "type"
      if len(expected_type) > 1 and len(actual_type) > 1:
        if isinstance(expected_type[-1], bool) and expected_type[-1] != actual_type[-1]:
          detail = "unsigned type"
        elif expected_type[0] == actual_type[0]:
          detail = "type length or precision"
      report.add_error(
        table_name,
        "column",
        f"{column_name} {detail} differs: expected {expected_type}, found {actual_type}",
      )
    if expected_column.nullable != actual_column.get("nullable"):
      report.add_error(
        table_name,
        "column",
        f"{column_name} nullable differs: expected {expected_column.nullable}",
      )
    expected_default = _normalized_default(
      None if expected_column.server_default is None else expected_column.server_default.arg
    )
    actual_default = _normalized_default(actual_column.get("default"))
    if expected_default != actual_default:
      report.add_error(
        table_name,
        "column",
        f"{column_name} default differs: expected {expected_default}, found {actual_default}",
      )
    expected_autoincrement = expected_column.autoincrement is True
    actual_autoincrement = actual_column.get("autoincrement") is True
    if expected_autoincrement != actual_autoincrement:
      report.add_error(
        table_name,
        "column",
        f"{column_name} autoincrement differs: expected {expected_autoincrement}",
      )
    if expected_type[0] in {"string", "tinytext", "mediumtext", "text"}:
      table_options = table.dialect_options["mysql"]
      expected_charset = (
        getattr(expected_column.type, "charset", None) or table_options["charset"]
      )
      actual_charset = (
        actual_column.get("charset")
        or getattr(actual_column["type"], "charset", None)
      )
      if (
        actual_charset is not None
        and (expected_charset or "").lower() != actual_charset.lower()
      ):
        report.add_error(
          table_name,
          "column",
          f"{column_name} charset differs: expected {expected_charset}, found {actual_charset}",
        )
      expected_collation = (
        getattr(expected_column.type, "collation", None) or table_options["collate"]
      )
      actual_collation = (
        actual_column.get("collation")
        or getattr(actual_column["type"], "collation", None)
      )
      if (expected_collation or "").lower() != (actual_collation or "").lower():
        report.add_error(
          table_name,
          "column",
          f"{column_name} collation differs: expected {expected_collation}, found {actual_collation}",
        )


def _compare_table_objects(report, inspector, table_name, table):
  actual_pk = tuple(
    inspector.get_pk_constraint(table_name).get("constrained_columns") or ()
  )
  expected_pk = tuple(column.name for column in table.primary_key)
  if actual_pk != expected_pk:
    report.add_error(
      table_name,
      "primary_key",
      f"columns differ: expected {expected_pk}, found {actual_pk}",
    )

  expected_fks = _expected_foreign_keys(table)
  actual_fks = _actual_foreign_keys(inspector.get_foreign_keys(table_name))
  if expected_fks != actual_fks:
    report.add_error(table_name, "foreign_key", "foreign keys differ")

  expected_uniques = {
    constraint.name: tuple(column.name for column in constraint.columns)
    for constraint in table.constraints
    if isinstance(constraint, UniqueConstraint)
  }
  actual_unique_items = inspector.get_unique_constraints(table_name)
  actual_uniques = _named_columns(actual_unique_items)
  if expected_uniques != actual_uniques:
    report.add_error(table_name, "unique_constraint", "unique constraints differ")

  unique_index_names = {
    item.get("duplicates_index") or item.get("name")
    for item in actual_unique_items
  }
  actual_indexes = {
    item.get("name"): (
      tuple(item.get("column_names") or ()),
      bool(item.get("unique", False)),
    )
    for item in inspector.get_indexes(table_name)
    if item.get("name") not in unique_index_names
  }
  expected_indexes = {
    index.name: (
      tuple(column.name for column in index.columns),
      bool(index.unique),
    )
    for index in table.indexes
  }
  if expected_indexes != actual_indexes:
    report.add_error(table_name, "index", "indexes differ")

  expected_comment = table.comment
  actual_comment = inspector.get_table_comment(table_name).get("text")
  if expected_comment != actual_comment:
    report.add_error(table_name, "comment", "table comment differs")

  expected_options = table.dialect_options["mysql"]
  actual_options = inspector.get_table_options(table_name)
  option_pairs = (
    ("engine", expected_options["engine"], actual_options.get("mysql_engine")),
    (
      "charset",
      expected_options["charset"],
      actual_options.get("mysql_charset") or actual_options.get("mysql_default charset"),
    ),
    ("collation", expected_options["collate"], actual_options.get("mysql_collate")),
  )
  for object_type, expected_value, actual_value in option_pairs:
    if (expected_value or "").lower() != (actual_value or "").lower():
      report.add_error(
        table_name,
        object_type,
        f"expected {expected_value}, found {actual_value}",
      )


def _mysql_column_details(engine: Engine) -> dict[tuple[str, str], dict]:
  dialect = getattr(engine, "dialect", None)
  if getattr(dialect, "name", None) != "mysql":
    return {}
  with engine.connect() as connection:
    rows = connection.exec_driver_sql(
      "SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME, EXTRA "
      "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE()"
    ).mappings()
    return {
      (row["TABLE_NAME"], row["COLUMN_NAME"]): {
        "charset": row["CHARACTER_SET_NAME"],
        "collation": row["COLLATION_NAME"],
        "autoincrement": "auto_increment" in (row["EXTRA"] or "").lower(),
      }
      for row in rows
    }


def compare_managed_schema(
  engine: Engine,
  metadata: MetaData = Base.metadata,
) -> SchemaReport:
  inspector = inspect(engine)
  report = SchemaReport()
  reflected_names = frozenset(inspector.get_table_names())
  managed_names = frozenset(MANAGED_TABLE_NAMES)
  mysql_column_details = _mysql_column_details(engine)

  for table_name in sorted(managed_names - reflected_names):
    report.add_error(table_name, "table", f"missing managed table {table_name}")
  for table_name in sorted(reflected_names - managed_names - {"alembic_version"}):
    report.add_warning(table_name, "table", "unmanaged table")

  for table_name in sorted(managed_names & reflected_names):
    table = metadata.tables[table_name]
    reflected_columns = []
    for column in inspector.get_columns(table_name):
      reflected_column = dict(column)
      reflected_column.update(
        mysql_column_details.get((table_name, column["name"]), {})
      )
      reflected_columns.append(reflected_column)
    _compare_columns(report, table_name, table, reflected_columns)
    _compare_table_objects(report, inspector, table_name, table)
  return report


__all__ = [
  "SchemaDifference",
  "SchemaReport",
  "compare_managed_schema",
]
