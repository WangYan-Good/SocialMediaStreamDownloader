##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.room_base                             import RoomBaseTable
from backend.src.base.log                                             import get_logger

##
## >>================================ room_base table test method ===============================>>
##

##
## test: create room_base table
##
def test_create_room_base_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_base table
  ##
  room_base = RoomBaseTable(db_instance=db)
  room_base.create()
  return

##
## test: drop room_base table
##
def test_drop_room_base_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## drop room_base table
  ##
  room_base = RoomBaseTable(db_instance=db)
  room_base.drop(confirm=True)
  return

##
## test: check if room_base table exists
##
def test_check_room_base_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  room_base = RoomBaseTable(db)

  ##
  ## check if room_base table exists
  ##
  if db.is_table_exist(room_base.get_name()):
    get_logger().info("{} table exists!".format(room_base.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_base.get_name()))
  return

##
## test: insert room_base record
##
def test_insert_room_base_record(db:SocialMediaStreamDataBase = None):
  """
  Test inserting a room_base record into the room_base table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_base table if not exists
  ##
  room_base = RoomBaseTable(db_instance=db)

  ##
  ## insert a sample room record
  ##
  sample_room = {
    'id': '7362550606306773794',
    'id_str': '7362550606306773794',
    'title': '直播五分钟',
    'status': 4,
    'owner_user_id': 2700838411446480,
    'create_time': 1714227431000,
    'start_time': 1714227435000,
    'finish_time': 1714232860000,
    'app_id': 1128,
    'client_version': 290600,
    'orientation': 0,
    'os_type': 1,
    'layout': 0,
    'stream_id': 691500607505433258,
    'like_count': 14873,
    'user_count': 0,
    'popularity': 0,
    'sell_goods': False,
    'has_commerce_goods': True,
    'is_replay': False,
    'live_type_normal': True,
    'live_type_audio': False,
    'live_type_linkmic': False,
    'live_type_official': False,
    'linkmic_layout': 1,
    'acquaintance_status': 0,
    'finish_reason': 1,
    'room_audit_status': 0,
    'mosaic_status': 0,
    'luckymoney_num': 0,
    'web_count': 0,
    'danmaku_detail': 0,
    'webcast_comment_tcs': 0,
    'cover_data': {
      'avg_color': '#F1FFEB',
      'uri': 'webcast-cover/7310930480756017947',
      'url_list': [
        'https://p11-webcast-sign.douyinpic.com/webcast-cover/7310930480756017947~tplv-qz53dukwul-common-resize:0:0.image',
        'https://p3-webcast-sign.douyinpic.com/webcast-cover/7310930480756017947~tplv-qz53dukwul-common-resize:0:0.image'
      ],
      'width': 0,
      'height': 0,
      'image_type': 0,
      'is_animated': False
    },
    'extra_data': {
      'create_scene': '',
      'ecom_live_shop_v2': 0,
      'ecom_live_start_with_cart': False,
      'facial_unrecognised': 0,
      'geo_block': 0,
      'is_sandbox': False,
      'is_virtual_anchor': False,
      'realtime_replay_enabled': False,
      'vr_type': 0,
      'vs_type': 0
    },
    'admin_user_ids': [572164301142046, 98105276094, 1877579610464923],
    'filter_words': [],
    'tags': [],
    'created_at': dat.fromtimestamp(1714227431),
    'updated_at': dat.fromtimestamp(1714232860)
  }

  try:
    room_base.insert_record(sample_room)
    get_logger().info("sample room_base record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample room_base record: {}".format(e))
    raise e

##
## test: get room_base record
##
def test_get_room_base_record(db:SocialMediaStreamDataBase = None):
  """
  Test getting a room_base record from the room_base table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_base table if not exists
  ##
  room_base = RoomBaseTable(db_instance=db)

  ##
  ## get record by id
  ##
  try:
    record = room_base.get_record({'id': '7362550606306773794'})
    if record:
      get_logger().info("room_base record found: {}".format(record))
    else:
      get_logger().info("room_base record not found")
  except Exception as e:
    get_logger().error("failed to get room_base record: {}".format(e))
    raise e

##
## test: update room_base record
##
def test_update_room_base_record(db:SocialMediaStreamDataBase = None):
  """
  Test updating a room_base record in the room_base table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_base table if not exists
  ##
  room_base = RoomBaseTable(db_instance=db)

  ##
  ## update a sample room record
  ##
  update_data = {
    'status': 2,
    'like_count': 15000,
    'user_count': 100,
    'updated_at': dat.now()
  }

  try:
    room_base.update_record(update_data, {'id': '7362550606306773794'})
    get_logger().info("room_base record updated successfully")
  except Exception as e:
    get_logger().error("failed to update room_base record: {}".format(e))
    raise e

##
## test: delete room_base record
##
def test_delete_room_base_record(db:SocialMediaStreamDataBase = None):
  """
  Test deleting a room_base record from the room_base table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_base table if not exists
  ##
  room_base = RoomBaseTable(db_instance=db)

  ##
  ## delete record by id
  ##
  try:
    room_base.delete_record({'id': '7362550606306773794'})
    get_logger().info("room_base record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete room_base record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='127.0.0.1', user='admin', passwd='admin', database='test_social_media_stream_downloader')

  ##
  ## room_base table
  ##
  test_check_room_base_table_exists(db)
  test_create_room_base_table(db)
  test_insert_room_base_record(db)
  test_check_room_base_table_exists(db)
  test_get_room_base_record(db)
  test_update_room_base_record(db)
  test_delete_room_base_record(db)
  test_drop_room_base_table(db)
  test_check_room_base_table_exists(db)
