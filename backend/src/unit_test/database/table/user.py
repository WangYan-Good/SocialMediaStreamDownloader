##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat
import json
from typing                                                           import Optional, Any, Dict

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.user                                  import UserTable
from backend.src.library.loglib                                       import get_logger
from backend.src.unit_test.test_db_config                             import get_test_db_config

SAMPLE_USER_ID = '2700838411446480'

##
## >>================================ user table test method ===============================>>
##

##
## test: create user table
##
def test_create_user_table(db: Optional[SocialMediaStreamDataBase] = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create user table
  ##
  user = UserTable(db_instance=db)
  user.create()
  return

##
## test: drop user table
##
def test_drop_user_table(db: Optional[SocialMediaStreamDataBase] = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## drop user table
  ##
  user = UserTable(db_instance=db)
  user.drop(confirm=True)
  return

##
## test: check if user table exists
##
def test_check_user_table_exists(db: Optional[SocialMediaStreamDataBase] = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  user = UserTable(db)

  ##
  ## check if user table exists
  ##
  if db.is_table_exist(user.get_name()):
    get_logger().info("{} table exists!".format(user.get_name()))
  else:
    get_logger().info("{} table not exists!".format(user.get_name()))
  return

##
## test: insert user record
##
def test_insert_user_record(db: Optional[SocialMediaStreamDataBase] = None):
  """
  Test inserting a user record into the user table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create user table if not exists
  ##
  user = UserTable(db_instance=db)

  ##
  ## insert a sample user record
  ##
  sample_user: Dict[str, Any] = {
    'id': SAMPLE_USER_ID,
    'nickname': 'Lvuuu',
    'display_id': '30266029732',
    'sec_uid': 'MS4wLjABAAAA3REn4Oekpt-zrnovTqTVWrTPkevbUHRJZRX2td0l_EdDr8Zgzk1HlnNgKHEyguTr',
    'user_open_id': '',
    'status': 1,
    'gender': 2,
    'city': '常德',
    'signature': 'unit test user signature',
    'verified': True,
    'verified_reason': '',
    'follow_status': 0,
    'is_follower': False,
    'is_following': False,
    'fan_ticket_count': 0,
    'pay_score': 0,
    'with_commerce_permission': True,
    'with_fusion_shop_entry': True,
    'with_car_management_permission': False,
    'badge_image_list': json.dumps([]),
    'badge_image_list_v2': json.dumps([]),
    'media_badge_image_list': json.dumps([]),
    'new_real_time_icons': json.dumps([]),
    'real_time_icons': json.dumps([]),
    'top_fans': json.dumps([]),
    'commerce_webcast_config_ids': json.dumps([]),
    'can_view_webcast_private': 0,
    'webcast_private': 0,
    'webcast_nick': '',
    'hide_by_room': 0,
    'link_mask': 0,
    'created_at': dat.fromtimestamp(1714227431),
    'updated_at': dat.fromtimestamp(1740042739)
  }

  try:
    inserted_id = user.insert_record(sample_user)
    assert inserted_id >= 0
    get_logger().info("sample user record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample user record: {}".format(e))
    raise e

##
## test: get user record
##
def test_get_user_record(db: Optional[SocialMediaStreamDataBase] = None):
  """
  Test getting a user record from the user table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create user table if not exists
  ##
  user = UserTable(db_instance=db)

  ##
  ## get record by id
  ##
  try:
    record = user.get_record({'id': SAMPLE_USER_ID})
    if isinstance(record, list) and len(record) > 0 and isinstance(record[0], dict):
      row = record[0]
      assert row.get('id') == SAMPLE_USER_ID
      get_logger().info("user record found: {}".format(row))
    else:
      get_logger().info("user record not found")
      raise AssertionError("user record not found")
  except Exception as e:
    get_logger().error("failed to get user record: {}".format(e))
    raise e

##
## test: update user record
##
def test_update_user_record(db: Optional[SocialMediaStreamDataBase] = None):
  """
  Test updating a user record in the user table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create user table if not exists
  ##
  user = UserTable(db_instance=db)

  ##
  ## update a sample user record
  ##
  update_data: Dict[str, Any] = {
    'id': SAMPLE_USER_ID,
    'status': 2,
    'nickname': 'Lvuuu-updated',
    'updated_at': dat.now()
  }

  try:
    affected_rows = user.update_record(update_data)
    assert affected_rows >= 0
    get_logger().info("user record updated successfully")
  except Exception as e:
    get_logger().error("failed to update user record: {}".format(e))
    raise e

  ##
  ## validate update result
  ##
  try:
    record = user.get_record({'id': SAMPLE_USER_ID})
    assert isinstance(record, list)
    assert len(record) > 0
    assert isinstance(record[0], dict)
    assert record[0].get('status') == 2
    assert record[0].get('nickname') == 'Lvuuu-updated'
  except Exception as e:
    get_logger().error("failed to validate updated user record: {}".format(e))
    raise e

##
## test: delete user record
##
def test_delete_user_record(db: Optional[SocialMediaStreamDataBase] = None):
  """
  Test deleting a user record from the user table.
  """
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create user table if not exists
  ##
  user = UserTable(db_instance=db)

  ##
  ## delete record by id
  ##
  try:
    deleted_rows = user.delete_record({'id': SAMPLE_USER_ID})
    assert deleted_rows >= 0
    get_logger().info("user record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete user record: {}".format(e))
    raise e

  ##
  ## validate delete result
  ##
  try:
    record = user.get_record({'id': SAMPLE_USER_ID})
    assert isinstance(record, list)
    assert len(record) == 0
  except Exception as e:
    get_logger().error("failed to validate deleted user record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(**get_test_db_config())

  ##
  ## user table
  ##
  test_check_user_table_exists(db)
  test_create_user_table(db)
  test_insert_user_record(db)
  test_check_user_table_exists(db)
  test_get_user_record(db)
  test_update_user_record(db)
  test_delete_user_record(db)
  test_drop_user_table(db)
  test_check_user_table_exists(db)
