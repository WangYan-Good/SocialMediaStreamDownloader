from alembic import context
from sqlalchemy.engine import Connection, Engine

from backend.src.database.orm.engine import create_schema_engine
from backend.src.database.orm.models import Base, MANAGED_TABLE_NAMES


target_metadata = Base.metadata


def include_managed_name(name, type_, parent_names):
  if type_ == "schema":
    return True
  if type_ == "table":
    return name == "alembic_version" or name in MANAGED_TABLE_NAMES
  table_name = parent_names.get("table_name")
  return table_name is None or table_name in MANAGED_TABLE_NAMES


def include_managed_object(object_, name, type_, reflected, compare_to):
  if type_ == "table":
    return name == "alembic_version" or name in MANAGED_TABLE_NAMES
  table = getattr(object_, "table", None)
  return table is None or table.name in MANAGED_TABLE_NAMES


def configure_context(**kwargs):
  context.configure(
    target_metadata=target_metadata,
    compare_type=True,
    compare_server_default=True,
    include_name=include_managed_name,
    include_object=include_managed_object,
    render_as_batch=False,
    **kwargs,
  )


def run_migrations_offline():
  configure_context(
    dialect_name="mysql",
    literal_binds=True,
  )
  with context.begin_transaction():
    context.run_migrations()


def run_with_connection(connection: Connection):
  configure_context(connection=connection)
  with context.begin_transaction():
    context.run_migrations()


def run_migrations_online():
  supplied_connection = context.config.attributes.get("connection")
  if isinstance(supplied_connection, Connection):
    run_with_connection(supplied_connection)
    return

  supplied_engine = context.config.attributes.get("engine")
  engine = supplied_engine
  owns_engine = not isinstance(engine, Engine)
  if owns_engine:
    engine = create_schema_engine(
      context.config.attributes.get("smsd_config"),
      context.config.attributes.get("database_name"),
    )
  try:
    with engine.connect() as connection:
      run_with_connection(connection)
  finally:
    if owns_engine:
      engine.dispose()


if context.is_offline_mode():
  run_migrations_offline()
else:
  run_migrations_online()
