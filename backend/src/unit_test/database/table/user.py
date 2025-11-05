##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.user                                  import RoomOwnerTable, \
                                                                             FansClubTable, \
                                                                             FansClubAvailableGiftIdTable, \
                                                                             FansClubBadgeIconTable, \
                                                                             RoomOwnerUserAttrTable, \
                                                                             RoomAdminPrivilegeTable, \
                                                                             UserTable
from backend.src.base.log                                             import get_logger
from backend.src.library.databaselib                                  import create_table, is_table_exist, drop_table, \
                                                                             insert_record, delete_record, update_record, get_record
from backend.src.library.baselib                                      import set_dict_attr

##
## >>================================ room owner table test method ===============================>>
##
def test_room_owner_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  create_table(db, "room_owner")
  if is_table_exist(db, "room_owner"):
    get_logger().info("room_owner table exists!")
  else:
    get_logger().error("room_owner table not exists!")
    raise RuntimeError("room_owner table not exists after creation!")
  
  ##
  ## insert record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480'
  }
  try:
    insert_record(db, "room_owner", sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

  ##
  ## get record
  ##
  try:
    record = get_record(db, "room_owner", sample_record)
    if record:
      get_logger().info("sample room owner record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room owner record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room owner record: {}".format(e))
    raise e
  
  ##
  ## update record
  ##
  sample_record_update = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'city': 'Beijing'
  }
  try:
    update_record(db, "room_owner", sample_record_update)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e
  
  ##
  ## get updated record
  ##
  try:
    set_dict_attr(sample_record_update, "$.city", None)
    record = get_record(db, "room_owner", sample_record_update)
    if record:
      get_logger().info("updated room owner record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("updated room owner record not found")
  except Exception as e:
    get_logger().error("failed to retrieve updated room owner record: {}".format(e))
    raise e

  ##
  ## delete record
  ##
  try:
    delete_record(db, "room_owner", sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

  ##
  ## check if record is deleted
  ##
  try:
    record = get_record(db, "room_owner", sample_record)
    if record:
      get_logger().warning("sample room owner record still exists after deletion: \n\t{}".format(record))
    else:
      get_logger().info("sample room owner record not found after deletion")
  except Exception as e:
    get_logger().error("failed to verify deletion of sample room owner record: {}".format(e))
    raise e
  
  ##
  ## drop table
  ##
  drop_table(db, "room_owner")

  ##
  ## check if table is dropped
  ##
  if not is_table_exist(db, "room_owner"):
    get_logger().info("room_owner table dropped successfully")
  else:
    get_logger().warning("room_owner table still exists after deletion")

  return

##
## >>================================ own room flag table test method ===============================>>
##
def test_own_room_flag_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  create_table(db, "own_room_flag")
  if is_table_exist(db, "own_room_flag"):
    get_logger().info("own_room_flag table exists!")
  else:
    get_logger().error("own_room_flag table not exists!")
    raise RuntimeError("own_room_flag table not exists after creation!")
  
  ##
  ## insert record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'exist_flag_index': 1,
    'exist_flag': True
  }
  try:
    insert_record(db, "own_room_flag", sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e
  
  ##
  ## get record
  ##
  try:
    record = get_record(db, "own_room_flag", sample_record)
    if record:
      get_logger().info("sample own room flag record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample own room flag record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample own room flag record: {}".format(e))
    raise e
  
  ##
  ## update record
  ##
  sample_record_update = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'exist_flag_index': 1,
    'exist_flag': False
  }
  try:
    update_record(db, "own_room_flag", sample_record, sample_record_update)
    get_logger().info("sample own room flag record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample own room flag record: {}".format(e))
    raise e
  
  ##
  ## get updated record
  ##
  try:
    record = get_record(db, "own_room_flag", sample_record_update)
    if record:
      get_logger().info("updated own room flag record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("updated own room flag record not found")
  except Exception as e:
    get_logger().error("failed to retrieve updated own room flag record: {}".format(e))
    raise e
  
  ##
  ## delete record
  ##
  try:
    delete_record(db, "own_room_flag", sample_record)
    get_logger().info("sample own room flag record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample own room flag record: {}".format(e))
    raise e
  
  ##
  ## check if record is deleted
  ##
  try:
    record = get_record(db, "own_room_flag", sample_record)
    if record:
      get_logger().warning("sample own room flag record still exists after deletion: \n\t{}".format(record))
    else:
      get_logger().info("sample own room flag record not found after deletion")
  except Exception as e:
    get_logger().error("failed to verify deletion of sample own room flag record: {}".format(e))
    raise e
  
  ##
  ## drop table
  ##
  drop_table(db, "own_room_flag")

  ##
  ## check if table is dropped
  ##
  if not is_table_exist(db, "own_room_flag"):
    get_logger().info("own_room_flag table dropped successfully")
  else:
    get_logger().warning("own_room_flag table still exists after deletion")

  return

##
## >>================================ own room id table test method ===============================>>
##
def test_own_room_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  create_table(db, "own_room_id")
  if is_table_exist(db, "own_room_id"):
    get_logger().info("own_room_id table exists!")
  else:
    get_logger().error("own_room_id table not exists!")
    raise RuntimeError("own_room_id table not exists after creation!")
  
  ##
  ## insert record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id_index': 1,
    'room_id': '7411524533301119798'
  }
  try:
    insert_record(db, "own_room_id", sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e
  
  ##
  ## get record
  ##
  try:
    record = get_record(db, "own_room_id", sample_record)
    if record:
      get_logger().info("sample own room id record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample own room id record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample own room id record: {}".format(e))
    raise e
  
  ##
  ## update record
  ##
  sample_record_update = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id_index': 0,
    'room_id': '7411524533301119798'
  }
  try:
    update_record(db, "own_room_id", sample_record, sample_record_update)
    get_logger().info("sample own room id record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample own room id record: {}".format(e))
    raise e
  
  ##
  ## get updated record
  ##
  try:
    record = get_record(db, "own_room_id", sample_record_update)
    if record:
      get_logger().info("sample own room id record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample own room id record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample own room id record: {}".format(e))
    raise e
  
  ##
  ## delete record
  ##
  try:
    delete_record(db, "own_room_id", sample_record)
    get_logger().info("sample own room id record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample own room id record: {}".format(e))
    raise e
  
  ##
  ## check if record is deleted
  ##
  try:
    record = get_record(db, "own_room_id", sample_record)
    if record:
      get_logger().warning("sample own room id record still exists after deletion: \n\t{}".format(record))
    else:
      get_logger().info("sample own room id record not found after deletion")
  except Exception as e:
    get_logger().error("failed to verify deletion of sample own room id record: {}".format(e))
    raise e
  
  ##
  ## drop table
  ##
  drop_table(db, "own_room_id")

  ##
  ## check if table is dropped
  ##
  if not is_table_exist(db, "own_room_id"):
    get_logger().info("own_room_id table dropped successfully")
  else:
    get_logger().warning("own_room_id table still exists after deletion")
  return

##
## >>================================ room owner auth info table test method ===============================>>
##
def test_room_owner_auth_info_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  create_table(db, "room_owner_auth_info")
  if is_table_exist(db, "room_owner_auth_info"):
    get_logger().info("room_owner_auth_info table exists!")
  else:
    get_logger().error("room_owner_auth_info table not exists!")
    raise RuntimeError("room_owner_auth_info table not exists after creation!")
  
  ##
  ## insert record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798',
    'exist_authentication_info': True
  }
  try:
    insert_record(db, "room_owner_auth_info", sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e
  
  ##
  ## get record
  ##
  try:
    record = get_record(db, "room_owner_auth_info", sample_record)
    if record:
      get_logger().info("sample room owner auth info record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room owner auth info record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room owner auth info record: {}".format(e))
    raise e
  
  ##
  ## update record
  ##
  sample_record_update = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798',
    'exist_authentication_info': False
  }
  try:
    update_record(db, "room_owner_auth_info", sample_record_update)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e
  
  ##
  ## get updated record
  ##
  try:
    record = get_record(db, "room_owner_auth_info", sample_record)
    if record:
      get_logger().info("updated room owner auth info record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("updated room owner auth info record not found")
  except Exception as e:
    get_logger().error("failed to retrieve updated room owner auth info record: {}".format(e))
    raise e
  
  ##
  ## delete record
  ##
  try:
    set_dict_attr(sample_record, "$.exist_authentication_info", None)
    delete_record(db, "room_owner_auth_info", sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e
  
  ##
  ## check if record is deleted
  ##
  try:
    record = get_record(db, "room_owner_auth_info", sample_record)
    if record:
      get_logger().warning("sample room owner auth info record still exists after deletion: \n\t{}".format(record))
    else:
      get_logger().info("sample room owner auth info record not found after deletion")
  except Exception as e:
    get_logger().error("failed to verify deletion of sample room owner auth info record: {}".format(e))
    raise e
  
  ##
  ## drop table
  ##
  drop_table(db, "room_owner_auth_info")

  ##
  ## check if table is dropped
  ##
  if not is_table_exist(db, "room_owner_auth_info"):
    get_logger().info("room_owner_auth_info table dropped successfully")
  else:
    get_logger().warning("room_owner_auth_info table still exists after deletion")

  return

##
## >>================================ room owner auth level table test method ===============================>>
##
def test_room_owner_auth_level_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  create_table(db, "room_owner_auth_level")
  if is_table_exist(db, "room_owner_auth_level"):
    get_logger().info("room_owner_auth_level table exists!")
  else:
    get_logger().error("room_owner_auth_level table not exists!")
    raise RuntimeError("room_owner_auth_level table not exists after creation!")
  
  ##
  ## insert record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'level_index': 1,
    'level': 5
  }
  try:
    insert_record(db, "room_owner_auth_level", sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

  ##
  ## get record
  ##
  try:
    record = get_record(db, "room_owner_auth_level", sample_record)
    if record:
      get_logger().info("sample room owner auth level record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room owner auth level record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room owner auth level record: {}".format(e))
    raise e
  
  ##
  ## update record
  ##
  sample_record_update = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'level_index': 1,
    'level': 10
  }
  try:
    update_record(db, "room_owner_auth_level", sample_record_update)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e
  
  ##
  ## get updated record
  ##
  try:
    record = get_record(db, "room_owner_auth_level", sample_record)
    if record:
      get_logger().info("updated room owner auth level record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("updated room owner auth level record not found")
  except Exception as e:
    get_logger().error("failed to retrieve updated room owner auth level record: {}".format(e))
    raise e
  
  ##
  ## delete record
  ##
  try:
    delete_record(db, "room_owner_auth_level", sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e
  
  ##
  ## check if record is deleted
  ##
  try:
    record = get_record(db, "room_owner_auth_level", sample_record)
    if record:
      get_logger().warning("sample room owner auth level record still exists after deletion: \n\t{}".format(record))
    else:
      get_logger().info("sample room owner auth level record not found after deletion")
  except Exception as e:
    get_logger().error("failed to verify deletion of sample rroom owner auth level record: {}".format(e))
    raise e
  
  ##
  ## drop table
  ##
  drop_table(db, "room_owner_auth_level")

  ##
  ## check if table is dropped
  ##
  if not is_table_exist(db, "room_owner_auth_level"):
    get_logger().info("room_owner_auth_level table dropped successfully")
  else:
    get_logger().warning("room_owner_auth_level table still exists after deletion")

  return

##
## >>================================ fans club table test method ===============================>>
##
def test_fans_club_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  create_table(db, "fans_club")
  if is_table_exist(db, "fans_club"):
    get_logger().info("fans_club table exists!")
  else:
    get_logger().error("fans_club table not exists!")
    raise RuntimeError("fans_club table not exists after creation!")
  
  ##
  ## insert record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0'
  }
  try:
    insert_record(db, "fans_club", sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

  ##
  ## get record
  ##
  try:
    record = get_record(db, "fans_club", sample_record)
    if record:
      get_logger().info("sample fans club record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample fans club record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample fans club record: {}".format(e))
    raise e
  
  ##
  ## update record
  ##
  sample_record_update = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0',
    'badge_type': 0
  }
  try:
    update_record(db, "fans_club", sample_record_update)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e
  
  ##
  ## get updated record
  ##
  try:
    record = get_record(db, "fans_club", sample_record)
    if record:
      get_logger().info("updated fans club record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("updated fans club record not found")
  except Exception as e:
    get_logger().error("failed to retrieve updated fans club record: {}".format(e))
    raise e
  
  ##
  ## delete record
  ##
  try:
    delete_record(db, "fans_club", sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

  return

##
## >>================================ fans club available gift id table test method ===============================>>
##

##
## test: insert record
##
def test_insert_fans_club_available_gift_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0',
    'available_gift_index': 1
  }
  
  try:
    fans_club_available_gift_id.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_fans_club_available_gift_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0',
    'available_gift_index': 1
  }
  
  try:
    fans_club_available_gift_id.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_fans_club_available_gift_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0',
    'available_gift_index': 1,
    'available_gift_id': '123456789'
  }
  
  try:
    fans_club_available_gift_id.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## >>================================ fans club badge icon table test method ===============================>>
##

##
## test: insert record
##
def test_insert_fans_club_badge_icon_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club_badge_icon = FansClubBadgeIconTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480'
  }
  
  try:
    fans_club_badge_icon.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_fans_club_badge_icon_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club_badge_icon = FansClubBadgeIconTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'icon_index': 1
  }
  
  try:
    fans_club_badge_icon.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_fans_club_badge_icon_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club_badge_icon = FansClubBadgeIconTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0',
    'icon_index': 1,
    'icon_uri': 'webcast/aweme_pay_grade_2x_1_4.png'
  }
  
  try:
    fans_club_badge_icon.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## >>================================ room owner user attr table test method ===============================>>
##

##
## test: insert record
##
def test_insert_room_owner_user_attr_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner_user_attr = RoomOwnerUserAttrTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_owner_user_attr.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_owner_user_attr_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner_user_attr = RoomOwnerUserAttrTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_owner_user_attr.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_owner_user_attr_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner_user_attr = RoomOwnerUserAttrTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798',
    'is_admin': True,
    'is_super_admin':True
  }
  
  try:
    room_owner_user_attr.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## >>================================ room admin privilege table test method ===============================>>
##

##
## test: insert record
##
def test_insert_room_admin_privilege_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_privilege = RoomAdminPrivilegeTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_admin_privilege.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_admin_privilege_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_privilege = RoomAdminPrivilegeTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798',
    'admin_privilege_index': 1
  }
  
  try:
    room_admin_privilege.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_admin_privilege_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_privilege = RoomAdminPrivilegeTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798',
    'admin_privilege_index': 1,
    'admin_privilege':'TBD'
  }
  
  try:
    room_admin_privilege.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## >>================================ user table test method ===============================>>
##

##
## test: insert record
##
def test_insert_user_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  user = UserTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'id': '2700838411446480'
  }
  
  try:
    user.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_user_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  user = UserTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'id': '2700838411446480'
  }
  
  try:
    user.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_user_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  user = UserTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'id': '2700838411446480',
    'gender': 0
  }
  
  try:
    user.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='127.0.0.1', user='admin', passwd='admin', database='test_social_media_stream_downloader')

  ##
  ## room owner table
  ##
  test_room_owner_table(db)

  ##
  ## own room flag table
  ## 
  test_own_room_flag_table(db)

  ##
  ## own room id table
  ##
  test_own_room_id_table(db)

  ##
  ## room owner auth info table
  ##
  test_room_owner_auth_info_table(db)

  ##
  ## room owner auth level table
  ##
  test_room_owner_auth_level_table(db)

  ##
  ## fans club table
  ##
  test_fans_club_table(db)

  ##
  ## fans club available gift id table
  ##
  test_create_fans_club_available_gift_id_table(db)
  test_check_fans_club_available_gift_id_exists(db)
  test_insert_fans_club_available_gift_id_record(db)
  test_get_fans_club_available_gift_id_record(db)
  test_update_fans_club_available_gift_id_record(db)
  test_get_fans_club_available_gift_id_record(db)
  test_delete_fans_club_available_gift_id_record(db)
  test_get_fans_club_available_gift_id_record(db)
  test_drop_fans_club_available_gift_id_table(db)
  test_check_fans_club_available_gift_id_exists(db)

  ##
  ## fans club badge icon table
  ##
  test_create_fans_club_badge_icon_table(db)
  test_check_fans_club_badge_icon_exists(db)
  test_insert_fans_club_badge_icon_record(db)
  test_get_fans_club_badge_icon_record(db)
  test_update_fans_club_badge_icon_record(db)
  test_get_fans_club_badge_icon_record(db)
  test_delete_fans_club_badge_icon_record(db)
  test_get_fans_club_badge_icon_record(db)
  test_drop_fans_club_badge_icon_table(db)
  test_check_fans_club_badge_icon_exists(db)

  ##
  ## room owner user attr table
  ##
  test_create_room_owner_user_attr_table(db)
  test_check_room_owner_user_attr_exists(db)
  test_insert_room_owner_user_attr_record(db)
  test_get_room_owner_user_attr_record(db)
  test_update_room_owner_user_attr_record(db)
  test_get_room_owner_user_attr_record(db)
  test_delete_room_owner_user_attr_record(db)
  test_get_room_owner_user_attr_record(db)
  test_drop_room_owner_user_attr_table(db)
  test_check_room_owner_user_attr_exists(db)

  ##
  ## room admin privilege table
  ##
  test_create_room_admin_privilege_table(db)
  test_check_room_admin_privilege_exists(db)
  test_insert_room_admin_privilege_record(db)
  test_get_room_admin_privilege_record(db)
  test_update_room_admin_privilege_record(db)
  test_get_room_admin_privilege_record(db)
  test_delete_room_admin_privilege_record(db)
  test_get_room_admin_privilege_record(db)
  test_drop_room_admin_privilege_table(db)
  test_check_room_admin_privilege_exists(db)

  ##
  ## user table
  ##
  test_create_user_table(db)
  test_check_user_exists(db)
  test_insert_user_record(db)
  test_get_user_record(db)
  test_update_user_record(db)
  test_get_user_record(db)
  test_delete_user_record(db)
  test_get_user_record(db)
  test_drop_user_table(db)
  test_check_user_exists(db)

  ##
  ## room owner author stats table
  ##
  create_table(db, "room_owner_author_stats")
  is_table_exist(db, "room_owner_author_stats")
  # test_insert_room_owner_author_stats_record(db)
  # test_get_room_owner_author_stats_record(db)
  # test_update_room_owner_author_stats_record(db)
  # test_get_room_owner_author_stats_record(db)
  # test_delete_room_owner_author_stats_record(db)
  # test_get_room_owner_author_stats_record(db)
  drop_table(db, "room_owner_author_stats")
  is_table_exist(db, "room_owner_author_stats")