"""
Export migration SQL scripts per target table.

This script reads target table schemas from the reference table definition directory,
then exports data from the current database to per-table SQL files using the target
column order.
"""

from __future__ import annotations
##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

##<<Base>>
import pymysql

from datetime             import datetime
from pathlib              import Path
from typing               import Dict, Iterable, Iterator, Optional
from contextlib           import contextmanager
from dotenv               import load_dotenv

##<<Third-part>>
from backend.src.library.loglib                                  import get_logger
from backend.src.library.baselib                                 import get_dict_attr, load_yml
from backend.src.database.table.room_base                        import RoomBaseTable
from backend.src.database.table.live                             import LiveRecordTable
from backend.src.database.table.room_owner                       import RoomOwnerV2Table
from backend.src.database.social_media_stream_database           import SocialMediaStreamDataBase as smsd_v2
from backend.src.database.table.table_import                     import import_douyin_live_info_to_database
from backend.src.unit_test.database.migration.v1.table_export    import export_live_data as export_live_data_v1
from backend.src.unit_test.database.social_media_stream_database import SocialMediaStreamDataBase as smsd_v1

DEFAULT_BUILD_DIRS = [
  Path("config/build/douyin/live"),
  Path("/mnt/main/Service/SocialMediaStreamDownloader/config/build/douyin/live"),
]

RAW_SOURCE_TABLES = {
  "favorite_owner": ["owner_user_id", "platform"],
  "live_record": ["now", "platform", "owner_user_id", "room_id"],
  "share_url": ["owner_user_id"],
}

class TransactionConnectionProxy:
  """
  Transaction-safe connection proxy class.
  Provides a proxy layer over the real pymysql Connection so that intermediate
  calls to `connector.commit()` and `connector.close()` are intercepted and ignored
  during multi-table atomic migrations.
  事务安全连接代理类：拦截中途的 commit / close 等操作，交由外层事务管理器统一调度
  """
  def __init__(self, real_conn) -> None:
    self._real_conn = real_conn

  def cursor(self, *args, **kwargs):
    return self._real_conn.cursor(*args, **kwargs)

  def commit(self) -> None:
    ## Intercept inner commit during atomic transaction
    pass

  def rollback(self) -> None:
    ## Intercept inner rollback to keep transaction controlled by outer manager
    pass

  def close(self) -> None:
    ## Intercept close to prevent premature return to pooled connections
    pass

  def __enter__(self) -> TransactionConnectionProxy:
    return self

  def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    pass

  def __getattr__(self, name):
    return getattr(self._real_conn, name)


class TransactionDatabaseProxy:
  """
  Database proxy class that yields the single, transactional proxy connection
  across all insert_record calls, forcing table classes to operate inside
  a unified outer transaction block.
  数据库代理类：重写 get_connection 强制让所有子表使用相同的连接代理对象，实现原子事务
  """
  def __init__(self, real_db: smsd_v2, connection_proxy: TransactionConnectionProxy) -> None:
    self._real_db = real_db
    self._connection_proxy = connection_proxy

  @contextmanager
  def get_connection(self) -> Iterator[TransactionConnectionProxy]:
    yield self._connection_proxy

  def __getattr__(self, name):
    return getattr(self._real_db, name)


def get_raw_connection(conn) -> pymysql.connections.Connection:
  """
  Dynamically unwrap DBUtils proxies (SteadyDBConnection) to get the raw PyMySQL Connection.
  """
  raw = conn
  while hasattr(raw, "_con"):
    raw = raw._con
  return raw

@contextmanager
def record_migration_transaction(destination_db: smsd_v2):
  """
  Record Migration Transaction context manager.
  Ensures that all insertions and updates triggered for a single record
  are bound to the same Connection, running within a single Transaction block.
  If any table insertion raises an exception, the entire record's table synchronization is
  rolled back instantly and the exception is propagated to stop the main pipeline.
  单条记录原子同步上下文管理器：
  1. 保证单条记录对应的所有子表操作在同一个 Connection 下运行；
  2. 禁用 autocommit，只在整个同步完成时一次性 commit；
  3. 若抛出任何异常，立即 rollback 回滚，不留下任何脏数据，并向外抛出异常中断迁移。
  """
  with destination_db.get_connection() as real_conn:
    conn_proxy = TransactionConnectionProxy(real_conn)
    db_proxy   = TransactionDatabaseProxy(destination_db, conn_proxy)
    try:
      ##
      ## Turn off autocommit on the database connection so transaction is explicitly started.
      ## 事务控制：禁用 autocommit
      ##
      get_raw_connection(real_conn).autocommit(False)
      yield db_proxy
      ##
      ## Commit transaction when imports for this single record complete successfully.
      ## 成功后提交整体事务
      ##
      get_raw_connection(real_conn).commit()
    except Exception as e:
      import traceback
      get_logger().error(f"Failed to synchronize table records, rolling back transaction: {e}\n{traceback.format_exc()}")
      try:
        get_raw_connection(real_conn).rollback()
      except Exception as rollback_err:
        get_logger().error(f"Database transaction rollback failed: {rollback_err}\n{traceback.format_exc()}")
      raise e

def _normalize_live_info(data: dict) -> dict:
  ## Some exported yml files wrap the original live response in external_info.
  ## table_import expects the original live response shape, so unwrap it here.
  if data is None:
    return {}
  if isinstance(data, dict) and isinstance(data.get("external_info"), dict):
    return data.get("external_info")
  return data

def _iter_yml_files(build_dirs: Iterable[Path]) -> Iterable[Path]:
  """
  Multiple build directories may point to overlapping files; de-duplicate by
  resolved path while keeping a deterministic traversal order.
  """
  seen = set()
  for build_dir in build_dirs:
    build_dir = build_dir.expanduser()
    if not build_dir.exists():
      get_logger().warning(f"Build directory {build_dir} does not exist, skipped.")
      continue
    for path in sorted(build_dir.rglob("*.yml"), key=lambda item: str(item)):
      resolved = path.resolve()
      if resolved in seen:
        continue
      seen.add(resolved)
      yield path

def _live_record_key_from_live_info(data: dict) -> Optional[dict]:
  """
  live_record is the migration boundary. All yml/source imports must first
  resolve this destination primary key so existing destination rows can win.
  """
  try:
    now_ms        = get_dict_attr(data, "$.extra.now")
    room_id       = get_dict_attr(data, "$.data.room.id")
    owner_user_id = get_dict_attr(data, "$.data.room.owner_user_id")
    if now_ms in (None, "") or room_id in (None, "") or owner_user_id in (None, ""):
      return None
    return {
      "now": datetime.fromtimestamp(float(now_ms) / 1000.0),
      "platform": "douyin",
      "owner_user_id": str(owner_user_id),
      "room_id": str(room_id),
    }
  except Exception as e:
    get_logger().warning(f"Build live_record key failed: {e}")
    return None

def _live_record_exists(destination_db: smsd_v2, key: dict) -> bool:
  """
  Check if the live_record identified by the key already exists in destination.
  """
  with destination_db.get_connection() as conn:
    with conn.cursor() as cursor:
      cursor.execute(
        """
        SELECT 1
        FROM live_record
        WHERE now = %s AND platform = %s AND owner_user_id = %s AND room_id = %s
        LIMIT 1
        """,
        (key["now"], key["platform"], key["owner_user_id"], key["room_id"])
      )
      return cursor.fetchone() is not None

def _destination_room_base_exists(destination_db: smsd_v2, key: dict) -> bool:
  """
  Check if the room_base identified by the key already exists in destination.
  """
  with destination_db.get_connection() as conn:
    with conn.cursor() as cursor:
      cursor.execute(
        """
        SELECT 1
        FROM room_base
        WHERE now = %s AND id = %s AND owner_user_id = %s
        LIMIT 1
        """,
        (key["now"], key["room_id"], key["owner_user_id"]),
      )
      return cursor.fetchone() is not None

def _classify_yml_migration_action(destination_db: smsd_v2, key: dict) -> str:
  """
  Decide how a yml record should be applied to destination.
  add: live_record does not exist.
  update: live_record exists but core room_base detail is missing.
  skip: live_record and room_base already exist.
  """
  if not _live_record_exists(destination_db, key):
    return "add"
  if not _destination_room_base_exists(destination_db, key):
    return "update"
  return "skip"

def _ensure_destination_live_tables(destination_db: smsd_v2) -> None:
  """
  Create the core destination tables before using table_import. Raw table
  migration below still creates its own legacy/non-yml tables as needed.
  """
  LiveRecordTable(destination_db).create(verify_schema=True)
  RoomBaseTable(destination_db).create(verify_schema=True)
  RoomOwnerV2Table(destination_db).create(verify_schema=True)

def _live_record_key_from_source_row(row: dict) -> Optional[dict]:
  """
  Extract the live_record key from a source row.
  """
  now_value = row.get("now")
  platform = row.get("platform")
  owner_user_id = row.get("owner_user_id")
  room_id = row.get("room_id")
  if now_value in (None, "") or platform in (None, "") or owner_user_id in (None, "") or room_id in (None, ""):
    return None
  return {
    "now": now_value,
    "platform": str(platform),
    "owner_user_id": str(owner_user_id),
    "room_id": str(room_id),
  }

def _migrate_raw_favorite_owner_table(
  source_db: smsd_v1,
  destination_db: smsd_v2
) -> int:
  """
  Migrate favorite_owner rows from source to destination db.
  """
  inserted = 0
  ##
  ## all rows should be 1:1 migrated without any check
  ## so we can directly migrate without extra filtering.
  ##
  with source_db.get_connection() as source_conn:
    with source_conn.cursor() as source_cursor:
      source_cursor.execute("SELECT * FROM favorite_owner")
      for row in source_cursor.fetchall():
        owner_user_id = row.get("owner_user_id")
        if owner_user_id in (None, ""):
          raise ValueError(f"Invalid favorite_owner owner_user_id: {row}")

        with destination_db.get_connection() as dest_conn:
          with dest_conn.cursor() as dest_cursor:
            dest_cursor.execute(
              """
              INSERT IGNORE INTO favorite_owner (owner_user_id, platform, score)
              VALUES (%s, %s, %s)
              """,
              (owner_user_id, row.get("platform"), row.get("score", 0))
            )
          dest_conn.commit()
          inserted += 1
  return inserted

def _migrate_raw_share_url_table(
  source_db: smsd_v1,
  destination_db: smsd_v2
) -> int:
  """
  Migrate share_url rows from source to destination db.
  """
  inserted = 0
  with source_db.get_connection() as source_conn:
    with source_conn.cursor() as source_cursor:
      source_cursor.execute("SELECT * FROM share_url")
      for row in source_cursor.fetchall():
        owner_user_id = row.get("owner_user_id")
        if owner_user_id in (None, ""):
          raise ValueError(f"Invalid share_url owner_user_id: {row}")

        with destination_db.get_connection() as dest_conn:
          with dest_conn.cursor() as dest_cursor:
            dest_cursor.execute(
              """
              INSERT IGNORE INTO share_url (
                owner_user_id, sec_user_id, nickname, post_share_url, live_share_url,
                directory_name, user_status, actived_count
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
              """,
              (
                owner_user_id,
                row.get("sec_user_id"),
                row.get("nickname"),
                row.get("post_share_url"),
                row.get("live_share_url"),
                row.get("directory_name"),
                row.get("user_status"),
                row.get("actived_count", 0),
              )
            )
          dest_conn.commit()
          inserted += 1

  return inserted

def _migrate_non_yml_tables_for_live_record(
  source_db: smsd_v1,
  destination_db: smsd_v2
):
  """
  Migrate non-yml tables related to a live_record identified by the source row.
  For each related table, if the source record has valid owner_user_id and platform,
  migrate the corresponding rows from the source database to the destination database.
  """

  ##
  ## Migrate favorite_owner rows for this live_record's owner_user_id and platform.
  ##
  try:
    inserted = _migrate_raw_favorite_owner_table(source_db, destination_db)
  except Exception as e:
    raise e
  get_logger().info(f"Migrated favorite_owner rows: inserted={inserted}")


  ##
  ## Migrate share_url rows for this live_record's owner_user_id.
  ##
  try:
    inserted = _migrate_raw_share_url_table(source_db, destination_db)
  except Exception as e:
    raise e
  get_logger().info(f"Migrated share_url rows: inserted={inserted}")

def migrate_source_live_records_to_destination(
  source_db: smsd_v1,
  destination_db: smsd_v2,
) -> Dict[str, int]:
  """
  Phase 1: migrate source DB by live_record as the primary boundary.
  """
  source_total_live_records      = 0
  source_imported_count          = 0
  raw_live_record_imported_count = 0
  source_skipped_existing_count  = 0

  with source_db.get_connection() as source_conn:
    with source_conn.cursor() as source_cursor:
      ##
      ## migrate live record related data
      ##
      source_cursor.execute("SELECT * FROM live_record")
      while True:
        row = source_cursor.fetchone()
        if row is None:
          break
        source_total_live_records += 1
        key = _live_record_key_from_source_row(row)
        if key is None:
          get_logger().warning(f"Skip source live_record without key: {row}")
          continue

        get_logger().info(
          f">> Phase1 source migration now={key.get('now')} platform={key.get('platform')} owner_user_id={key.get('owner_user_id')} room_id={key.get('room_id')}"
        )

        ##
        ## Step 1: migrate source row if destination missing.
        ##
        if not _live_record_exists(destination_db, key):
          ##
          ## Step 1a: migrate Douyin live_record if destination missing.
          ##
          if str(key.get("platform")) == "douyin":
            data = export_live_data_v1(source_db, row, None)
            get_logger().info(
              f">> Phase1 source import now={row.get('now')} room_id={row.get('room_id')} owner_user_id={row.get('owner_user_id')}"
            )

            ##
            ## Use table_import for Douyin records to populate v2 rich tables.
            ##
            with record_migration_transaction(destination_db) as tx_db:
              import_douyin_live_info_to_database(tx_db, data)
            source_imported_count += 1
            get_logger().info(
              f"<< Phase1 source imported now={row.get('now')} room_id={row.get('room_id')} owner_user_id={row.get('owner_user_id')}"
            )
          else:
              raw_live_record_imported_count += 1
              get_logger().info(
                f"<< Phase1 non-douyin live_record inserted now={row.get('now')} room_id={row.get('room_id')} owner_user_id={row.get('owner_user_id')}"
              )
        else:
          source_skipped_existing_count += 1

        get_logger().info(
          f"<< Finished Phase1 source migration now={key.get('now')} platform={key.get('platform')} owner_user_id={key.get('owner_user_id')} room_id={key.get('room_id')}"
        )
        
      ##
      ## Step 2: migrate related non-yml tables for this source record.
      ##         favorite_owner and share_url layout are not changed between v1 and v2. 
      ##         we can directly migrate rows from source to destination.
      ##
      _migrate_non_yml_tables_for_live_record(source_db, destination_db)

  return {
    "source_total_live_records": source_total_live_records,
    "source_imported_count": source_imported_count,
    "raw_live_record_imported_count": raw_live_record_imported_count,
    "source_skipped_existing_count": source_skipped_existing_count,
  }

def migrate_yml_files_to_destination(
  destination_db: smsd_v2,
  build_dirs: Iterable[Path],
) -> Dict[str, int]:
  """
  Phase 2: scan yml files and decide add/update/skip by destination state.
  """
  yml_total_count   = 0
  yml_add_count     = 0
  yml_update_count  = 0
  yml_skip_count    = 0
  yml_invalid_count = 0
  yml_failed_count  = 0

  for yml_path in _iter_yml_files(build_dirs):
    yml_total_count += 1
    try:
      data = _normalize_live_info(load_yml(yml_path))
      key = _live_record_key_from_live_info(data)
    except Exception as e:
      yml_invalid_count += 1
      get_logger().warning(f"Skip unreadable yml {yml_path}: {e}")
      continue

    if key is None:
      yml_invalid_count += 1
      get_logger().warning(f"Skip yml without valid live_record key: {yml_path}")
      continue

    action = _classify_yml_migration_action(destination_db, key)
    if action == "skip":
      yml_skip_count += 1
      continue

    try:
      get_logger().info(
        f">> Phase2 yml {action} file={yml_path} now={key.get('now')} platform={key.get('platform')} owner_user_id={key.get('owner_user_id')} room_id={key.get('room_id')}"
      )
      with record_migration_transaction(destination_db) as tx_db:
        import_douyin_live_info_to_database(tx_db, data)
      if action == "add":
        yml_add_count += 1
      else:
        yml_update_count += 1
      get_logger().info(
        f"<< Phase2 yml {action} success file={yml_path} now={key.get('now')} platform={key.get('platform')} owner_user_id={key.get('owner_user_id')} room_id={key.get('room_id')}"
      )
    except Exception as e:
      yml_failed_count += 1
      get_logger().error(f"Phase2 yml {action} failed file={yml_path}: {e}")
      raise e

  return {
    "yml_total_count": yml_total_count,
    "yml_add_count": yml_add_count,
    "yml_update_count": yml_update_count,
    "yml_skip_count": yml_skip_count,
    "yml_invalid_count": yml_invalid_count,
    "yml_failed_count": yml_failed_count,
  }

def migrate_database_destination_first(
  source_db: smsd_v1,
  destination_db: smsd_v2,
  build_dirs: Iterable[Path] = None
) -> None:
  ##
  ## Two-phase migration order by live_record:
  ## 1. Source DB migration by live_record as the main boundary.
  ## 2. Scan yml files and decide add/update/skip by destination state.
  ##
  build_dirs = DEFAULT_BUILD_DIRS if build_dirs is None else build_dirs
  _ensure_destination_live_tables(destination_db)

  phase1_stats = migrate_source_live_records_to_destination(source_db, destination_db)
  phase2_stats = migrate_yml_files_to_destination(destination_db, build_dirs)

  get_logger().info(
    "Two-phase migration summary: "
    f"phase1_source_live_record={phase1_stats['source_total_live_records']}, "
    f"phase1_source_imported={phase1_stats['source_imported_count']}, "
    f"phase1_source_skipped_existing={phase1_stats['source_skipped_existing_count']}, "
    f"phase1_raw_live_record_imported={phase1_stats['raw_live_record_imported_count']}, "
    f"phase2_yml_total={phase2_stats['yml_total_count']}, "
    f"phase2_yml_add={phase2_stats['yml_add_count']}, "
    f"phase2_yml_update={phase2_stats['yml_update_count']}, "
    f"phase2_yml_skip={phase2_stats['yml_skip_count']}, "
    f"phase2_yml_invalid={phase2_stats['yml_invalid_count']}, "
    f"yml_failed={phase2_stats['yml_failed_count']}, "
    "policy=yml_update_when_live_record_exists_but_room_base_missing."
  )

def main() -> None:
  ##
  ## Parse arguments
  ##
  destination_db_name = os.getenv("MYSQL_DB_NAME", "social_media_stream_downloader")
  destination_db_host = os.getenv("MYSQL_HOST", "localhost")
  destination_db_port = int(os.getenv("MYSQL_PORT", "3306"))
  destination_db_user = os.getenv("MYSQL_USER", "root")
  destination_db_passwd = os.getenv("MYSQL_PASSWORD", "")
  
  source_db_name = os.getenv("SOURCE_MYSQL_DB_NAME", "social_media_stream_downloader")
  source_db_host = os.getenv("SOURCE_MYSQL_HOST", "localhost")
  source_db_port = int(os.getenv("SOURCE_MYSQL_PORT", "3306"))
  source_db_user = os.getenv("SOURCE_MYSQL_USER", "root")
  source_db_passwd = os.getenv("SOURCE_MYSQL_PASSWORD", "")

  ##
  ## connect to source database
  ##
  source_db = smsd_v1(
    host=source_db_host,
    user=source_db_user,
    passwd=source_db_passwd,
    database=source_db_name
  )
  with source_db.get_connection() as conn:
    with conn.cursor() as cursor:
      cursor.execute("SELECT VERSION()")
      version = cursor.fetchone()
      print(f"Connected to source database: {source_db_user}@{source_db_host}:{source_db_port}/{source_db_name} | version={version}")

  ##
  ## connect to destination database
  ##
  destination_db = smsd_v2(
    host=destination_db_host,
    user=destination_db_user,
    passwd=destination_db_passwd,
    database=destination_db_name
  )
  with destination_db.get_connection() as conn:
    with conn.cursor() as cursor:
      cursor.execute("SELECT VERSION()")
      version = cursor.fetchone()
      print(f"Connected to destination database: {destination_db_user}@{destination_db_host}:{destination_db_port}/{destination_db_name} | version={version}")
  ##
  ## 1. import saved yml files under build to destination database
  ## 2. migrate data from source database to destination database
  ##  
  try:  
    migrate_database_destination_first(source_db, destination_db)
  except Exception as e:
    get_logger().error(f"Error occurred during migration: {e}")
    raise e

if __name__ == "__main__":
  load_dotenv()
  main()
