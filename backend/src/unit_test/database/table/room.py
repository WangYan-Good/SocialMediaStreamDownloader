##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database import SocialMediaStreamDataBase
from backend.src.database.table.room import (
  RoomStatsTable,
  RoomAdminUserIdTable,
  RoomAdminUserOpenIdTable,
  RoomDecoTable,
  FansGroupAdminUserIdTable,
  FansGroupAdminUserOpenIdTable,
)
from backend.src.base.log import get_logger
from backend.src.unit_test.test_db_config import get_test_db_config


def _require_db(db: SocialMediaStreamDataBase = None) -> None:
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError


def test_create_current_room_tables(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  RoomStatsTable(db).create()
  RoomAdminUserIdTable(db).create()
  RoomAdminUserOpenIdTable(db).create()
  RoomDecoTable(db).create()
  FansGroupAdminUserIdTable(db).create()
  FansGroupAdminUserOpenIdTable(db).create()


def test_check_current_room_tables_exist(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  tables = [
    RoomStatsTable(db),
    RoomAdminUserIdTable(db),
    RoomAdminUserOpenIdTable(db),
    RoomDecoTable(db),
    FansGroupAdminUserIdTable(db),
    FansGroupAdminUserOpenIdTable(db),
  ]
  for table in tables:
    exists = db.is_table_exist(table.get_name())
    if exists:
      get_logger().info("%s table exists", table.get_name())
    else:
      get_logger().warning("%s table not exists", table.get_name())


def test_room_stats_crud(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  table = RoomStatsTable(db)
  table.create()

  now = dat.now().replace(microsecond=123000)
  record = {
    "now": now,
    "platform": "douyin",
    "room_id": "ut-room-001",
    "comment_count": 1,
    "digg_count": 2,
  }
  table.insert_record(record, on_duplicate="ignore")

  got = table.get_record({"now": now, "platform": "douyin", "room_id": "ut-room-001"})
  assert got and len(got) > 0

  table.update_record({
    "now": now,
    "platform": "douyin",
    "room_id": "ut-room-001",
    "comment_count": 9,
  })

  table.delete_record({"now": now, "platform": "douyin", "room_id": "ut-room-001"})


def test_room_admin_user_id_crud(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  table = RoomAdminUserIdTable(db)
  table.create()

  table.insert_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "admin_user_id": "admin-u-1",
  }, on_duplicate="ignore")

  got = table.get_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "admin_user_id": "admin-u-1",
  })
  assert got and len(got) > 0

  index_value = got[0].get("index")
  assert index_value is not None

  table.update_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
    "admin_user_id": "admin-u-1-updated",
  })

  table.delete_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
  })


def test_room_admin_user_open_id_crud(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  table = RoomAdminUserOpenIdTable(db)
  table.create()

  table.insert_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "admin_user_open_id": "admin-open-1",
  }, on_duplicate="ignore")

  got = table.get_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "admin_user_open_id": "admin-open-1",
  })
  assert got and len(got) > 0

  index_value = got[0].get("index")
  assert index_value is not None

  table.update_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
    "admin_user_open_id": "admin-open-1-updated",
  })

  table.delete_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
  })


def test_room_deco_crud(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  table = RoomDecoTable(db)
  table.create()

  table.insert_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "deco_id": 123,
    "deco_type": 1,
    "content": "ut-deco",
  }, on_duplicate="ignore")

  got = table.get_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "deco_id": 123,
  })
  assert got and len(got) > 0

  deco_index = got[0].get("deco_index")
  assert deco_index is not None

  table.update_record({
    "deco_index": deco_index,
    "platform": "douyin",
    "room_id": "ut-room-001",
    "content": "ut-deco-updated",
  })

  table.delete_record({
    "deco_index": deco_index,
    "platform": "douyin",
    "room_id": "ut-room-001",
  })


def test_fans_group_admin_user_id_crud(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  table = FansGroupAdminUserIdTable(db)
  table.create()

  table.insert_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "fans_group_admin_user_id": "fans-admin-1",
  }, on_duplicate="ignore")

  got = table.get_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "fans_group_admin_user_id": "fans-admin-1",
  })
  assert got and len(got) > 0

  index_value = got[0].get("index")
  assert index_value is not None

  table.update_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
    "fans_group_admin_user_id": "fans-admin-1-updated",
  })

  table.delete_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
  })


def test_fans_group_admin_user_open_id_crud(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  table = FansGroupAdminUserOpenIdTable(db)
  table.create()

  table.insert_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "fans_group_admin_user_open_id": "fans-open-1",
  }, on_duplicate="ignore")

  got = table.get_record({
    "platform": "douyin",
    "room_id": "ut-room-001",
    "fans_group_admin_user_open_id": "fans-open-1",
  })
  assert got and len(got) > 0

  index_value = got[0].get("index")
  assert index_value is not None

  table.update_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
    "fans_group_admin_user_open_id": "fans-open-1-updated",
  })

  table.delete_record({
    "index": index_value,
    "platform": "douyin",
    "room_id": "ut-room-001",
  })

def test_drop_current_room_tables(db: SocialMediaStreamDataBase = None) -> None:
  _require_db(db)
  FansGroupAdminUserOpenIdTable(db).drop(confirm=True)
  FansGroupAdminUserIdTable(db).drop(confirm=True)
  RoomDecoTable(db).drop(confirm=True)
  RoomAdminUserOpenIdTable(db).drop(confirm=True)
  RoomAdminUserIdTable(db).drop(confirm=True)
  RoomStatsTable(db).drop(confirm=True)


if __name__ == "__main__":
  db = SocialMediaStreamDataBase(**get_test_db_config())

  test_create_current_room_tables(db)
  test_check_current_room_tables_exist(db)
  test_room_stats_crud(db)
  test_room_admin_user_id_crud(db)
  test_room_admin_user_open_id_crud(db)
  test_room_deco_crud(db)
  test_fans_group_admin_user_id_crud(db)
  test_fans_group_admin_user_open_id_crud(db)
  test_drop_current_room_tables(db)
