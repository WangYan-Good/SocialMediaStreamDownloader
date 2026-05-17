##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime import datetime as dat
from typing import Optional

## <<Third-Part>>
from backend.src.database.social_media_stream_database import SocialMediaStreamDataBase
from backend.src.database.table.stream import RoomStreamTable
from backend.src.base.log import get_logger
from backend.src.unit_test.test_db_config import get_test_db_config


def _require_db(db: Optional[SocialMediaStreamDataBase] = None) -> SocialMediaStreamDataBase:
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  return db


def test_create_room_stream_table(db: Optional[SocialMediaStreamDataBase] = None) -> None:
  dbi = _require_db(db)
  RoomStreamTable(dbi).create()


def test_check_room_stream_table_exists(db: Optional[SocialMediaStreamDataBase] = None) -> None:
  dbi = _require_db(db)
  table = RoomStreamTable(dbi)
  if dbi.is_table_exist(table.get_name()):
    get_logger().info("%s table exists", table.get_name())
  else:
    get_logger().warning("%s table not exists", table.get_name())


def test_room_stream_crud(db: Optional[SocialMediaStreamDataBase] = None) -> None:
  dbi = _require_db(db)
  table = RoomStreamTable(dbi)
  table.create()

  now = dat.now().replace(microsecond=0)
  record = {
    "platform": "douyin",
    "start_time": now,
    "room_id": "ut-room-stream-001",
    "default_resolution": "FULL_HD1",
    "stream_id": 691500607505433258,
    "stream_id_str": "691500607505433258",
    "provider": 1,
    "stream_control_type": 1,
  }

  table.insert_record(record, on_duplicate="ignore")

  got = table.get_record({
    "platform": "douyin",
    "start_time": now,
    "room_id": "ut-room-stream-001",
  })
  assert got and len(got) > 0
  assert got[0].get("default_resolution") == "FULL_HD1"

  table.update_record({
    "platform": "douyin",
    "start_time": now,
    "room_id": "ut-room-stream-001",
    "default_resolution": "HD1",
  })

  got_after = table.get_record({
    "platform": "douyin",
    "start_time": now,
    "room_id": "ut-room-stream-001",
  })
  assert got_after and len(got_after) > 0
  assert got_after[0].get("default_resolution") == "HD1"

  table.delete_record({
    "platform": "douyin",
    "start_time": now,
    "room_id": "ut-room-stream-001",
  })


def test_drop_room_stream_table(db: Optional[SocialMediaStreamDataBase] = None) -> None:
  dbi = _require_db(db)
  RoomStreamTable(dbi).drop(confirm=True)


if __name__ == "__main__":
  db = SocialMediaStreamDataBase(**get_test_db_config())
  test_create_room_stream_table(db)
  test_check_room_stream_table_exists(db)
  test_room_stream_crud(db)
  test_drop_room_stream_table(db)
