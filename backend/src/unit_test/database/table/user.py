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

##
## >>================================ room owner table test method ===============================>>
##

def test_create_room_owner_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_owner = RoomOwnerTable(db_instance=db)
  room_owner.create()
  return

##
## test: drop table
##
def test_drop_room_owner_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_owner = RoomOwnerTable(db_instance=db)
  room_owner.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_owner_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_owner = RoomOwnerTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_owner.get_name()):
    get_logger().info("{} table exists!".format(room_owner.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_owner.get_name()))
  return

##
## test: insert record
##
def test_insert_room_owner_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner = RoomOwnerTable(db_instance=db)
  
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
    room_owner.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_owner_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner = RoomOwnerTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798',
    'owner_user_id': '2700838411446480'
  }
  
  try:
    room_owner.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_owner_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner = RoomOwnerTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'webcast_uid': 'MS4wLjMljH3nsEUH1oduoEHICOyLO_mi_GCJdTJEys1TI9mE8kaaf7-cX-5cj3yS5qMPbqI',
    'web_rid':'827868393976'
  }
  
  try:
    room_owner.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_owner_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_owner = RoomOwnerTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480'
  }
  
  try:
    record = room_owner.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ fans club table test method ===============================>>
##

def test_create_fans_club_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  fans_club = FansClubTable(db_instance=db)
  fans_club.create()
  return

##
## test: drop table
##
def test_drop_fans_club_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  fans_club = FansClubTable(db_instance=db)
  fans_club.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_fans_club_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  fans_club = FansClubTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(fans_club.get_name()):
    get_logger().info("{} table exists!".format(fans_club.get_name()))
  else:
    get_logger().info("{} table not exists!".format(fans_club.get_name()))
  return

##
## test: insert record
##
def test_insert_fans_club_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club = FansClubTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0'
  }
  
  try:
    fans_club.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_fans_club_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club = FansClubTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0'
  }
  
  try:
    fans_club.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_fans_club_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_club = FansClubTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0',
    'badge_type': 0
  }
  
  try:
    fans_club.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_fans_club_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  fans_club = FansClubTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0'
  }
  
  try:
    record = fans_club.get_record(sample_record)
    if record:
      get_logger().info("sample record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample record: {}".format(e))
    raise e

##
## >>================================ fans club available gift id table test method ===============================>>
##

def test_create_fans_club_available_gift_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db_instance=db)
  fans_club_available_gift_id.create()
  return

##
## test: drop table
##
def test_drop_fans_club_available_gift_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db_instance=db)
  fans_club_available_gift_id.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_fans_club_available_gift_id_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(fans_club_available_gift_id.get_name()):
    get_logger().info("{} table exists!".format(fans_club_available_gift_id.get_name()))
  else:
    get_logger().info("{} table not exists!".format(fans_club_available_gift_id.get_name()))
  return

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
    'owner_user_id': '2700838411446480',
    'anchor_id': '0'
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
## test: get record
## 
def test_get_fans_club_available_gift_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  fans_club_available_gift_id = FansClubAvailableGiftIdTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'anchor_id': '0',
    'available_gift_index': 1
  }
  
  try:
    record = fans_club_available_gift_id.get_record(sample_record)
    if record:
      get_logger().info("sample record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample record: {}".format(e))
    raise e

##
## >>================================ fans club badge icon table test method ===============================>>
##

def test_create_fans_club_badge_icon_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  fans_club_badge_icon = FansClubBadgeIconTable(db_instance=db)
  fans_club_badge_icon.create()
  return

##
## test: drop table
##
def test_drop_fans_club_badge_icon_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  fans_club_badge_icon = FansClubBadgeIconTable(db_instance=db)
  fans_club_badge_icon.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_fans_club_badge_icon_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  fans_club_badge_icon = FansClubBadgeIconTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(fans_club_badge_icon.get_name()):
    get_logger().info("{} table exists!".format(fans_club_badge_icon.get_name()))
  else:
    get_logger().info("{} table not exists!".format(fans_club_badge_icon.get_name()))
  return

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
## test: get record
## 
def test_get_fans_club_badge_icon_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  fans_club_badge_icon = FansClubBadgeIconTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'icon_index': 1
  }
  
  try:
    record = fans_club_badge_icon.get_record(sample_record)
    if record:
      get_logger().info("sample record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample record: {}".format(e))
    raise e

##
## >>================================ room owner user attr table test method ===============================>>
##

def test_create_room_owner_user_attr_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_owner_user_attr = RoomOwnerUserAttrTable(db_instance=db)
  room_owner_user_attr.create()
  return

##
## test: drop table
##
def test_drop_room_owner_user_attr_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_owner_user_attr = RoomOwnerUserAttrTable(db_instance=db)
  room_owner_user_attr.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_owner_user_attr_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_owner_user_attr = RoomOwnerUserAttrTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_owner_user_attr.get_name()):
    get_logger().info("{} table exists!".format(room_owner_user_attr.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_owner_user_attr.get_name()))
  return

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
## test: get record
## 
def test_get_room_owner_user_attr_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_owner_user_attr = RoomOwnerUserAttrTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_owner_user_attr.get_record(sample_record)
    if record:
      get_logger().info("sample record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample record: {}".format(e))
    raise e

##
## >>================================ room admin privilege table test method ===============================>>
##

def test_create_room_admin_privilege_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_admin_privilege = RoomAdminPrivilegeTable(db_instance=db)
  room_admin_privilege.create()
  return

##
## test: drop table
##
def test_drop_room_admin_privilege_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_admin_privilege = RoomAdminPrivilegeTable(db_instance=db)
  room_admin_privilege.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_admin_privilege_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_admin_privilege = RoomAdminPrivilegeTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_admin_privilege.get_name()):
    get_logger().info("{} table exists!".format(room_admin_privilege.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_admin_privilege.get_name()))
  return

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
## test: get record
## 
def test_get_room_admin_privilege_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_admin_privilege = RoomAdminPrivilegeTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'owner_user_id': '2700838411446480',
    'room_id': '7411524533301119798',
    'admin_privilege_index': 1
  }
  
  try:
    record = room_admin_privilege.get_record(sample_record)
    if record:
      get_logger().info("sample record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample record: {}".format(e))
    raise e

##
## >>================================ user table test method ===============================>>
##

def test_create_user_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  user = UserTable(db_instance=db)
  user.create()
  return

##
## test: drop table
##
def test_drop_user_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  user = UserTable(db_instance=db)
  user.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_user_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  user = UserTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(user.get_name()):
    get_logger().info("{} table exists!".format(user.get_name()))
  else:
    get_logger().info("{} table not exists!".format(user.get_name()))
  return

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
## test: get record
## 
def test_get_user_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  user = UserTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'id': '2700838411446480'
  }
  
  try:
    record = user.get_record(sample_record)
    if record:
      get_logger().info("sample record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample record: {}".format(e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')

  ##
  ## room owner table
  ##
  test_create_room_owner_table(db)
  test_check_room_owner_exists(db)
  test_insert_room_owner_record(db)
  test_get_room_owner_record(db)
  test_update_room_owner_record(db)
  test_get_room_owner_record(db)
  test_delete_room_owner_record(db)
  test_get_room_owner_record(db)
  test_drop_room_owner_table(db)
  test_check_room_owner_exists(db)

  ##
  ## fans club table
  ##
  test_create_fans_club_table(db)
  test_check_fans_club_exists(db)
  test_insert_fans_club_record(db)
  test_get_fans_club_record(db)
  test_update_fans_club_record(db)
  test_get_fans_club_record(db)
  test_delete_fans_club_record(db)
  test_get_fans_club_record(db)
  test_drop_fans_club_table(db)
  test_check_fans_club_exists(db)

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