##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.source                                import BadgeImageTable, \
                                                                             RoomOwnerDressWearIdTable, \
                                                                             RoomSharingMusicIdTable, \
                                                                             PictureTable, \
                                                                             PictureFlexSettingTable, \
                                                                             PictureTextSettingTable, \
                                                                             PictureUrlTable
from backend.src.base.log                                             import get_logger

##
## >>================================ room owner table test method ===============================>>
##

def test_create_badge_image_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  badge_image = BadgeImageTable(db_instance=db)
  badge_image.create()
  return

##
## test: drop table
##
def test_drop_badge_image_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  badge_image = BadgeImageTable(db_instance=db)
  badge_image.drop()
  return

##
## test: check if table exists
##
def test_check_badge_image_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  badge_image = BadgeImageTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(badge_image.get_name()):
    get_logger().info("{} table exists!".format(badge_image.get_name()))
  else:
    get_logger().info("{} table not exists!".format(badge_image.get_name()))
  return

##
## test: insert record
##
def test_insert_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  badge_image = BadgeImageTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'badge_image_index': 0,
    'version': '123456789',
    'uri': '1080x1080/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f'
  }
  
  try:
    badge_image.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  badge_image = BadgeImageTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'badge_image_index': 0
  }
  
  try:
    badge_image.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  badge_image = BadgeImageTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'badge_image_index': 0,
    'version': '123',
    'uri': '720x720/aweme-avatar/tos-cn-avt-0015_073398e34f18e2e545861a83f392ad9f'
  }
  
  try:
    badge_image.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_badge_image_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  badge_image = BadgeImageTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'badge_image_index': 0
  }
  
  try:
    record = badge_image.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(badge_image.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(badge_image.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(badge_image.get_name(), e))
    raise e

##
## >>================================ room owner dress wear id table test method ===============================>>
##

def test_create_room_owner_dress_wear_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_owner_dress_wear_id = RoomOwnerDressWearIdTable(db_instance=db)
  room_owner_dress_wear_id.create()
  return

##
## test: drop table
##
def test_drop_room_owner_dress_wear_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_owner_dress_wear_id = RoomOwnerDressWearIdTable(db_instance=db)
  room_owner_dress_wear_id.drop()
  return

##
## test: check if table exists
##
def test_check_room_owner_dress_wear_id_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_owner_dress_wear_id = RoomOwnerDressWearIdTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_owner_dress_wear_id.get_name()):
    get_logger().info("{} table exists!".format(room_owner_dress_wear_id.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_owner_dress_wear_id.get_name()))
  return

##
## test: insert record
##
def test_insert_room_owner_dress_wear_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner_dress_wear_id = RoomOwnerDressWearIdTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'dress_wear_index': 0
  }
  
  try:
    room_owner_dress_wear_id.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_owner_dress_wear_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner_dress_wear_id = RoomOwnerDressWearIdTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'dress_wear_index': 0
  }
  
  try:
    room_owner_dress_wear_id.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_owner_dress_wear_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_owner_dress_wear_id = RoomOwnerDressWearIdTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'dress_wear_index': 0,
    'dress_wear_id': '123456789'
  }
  
  try:
    room_owner_dress_wear_id.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_owner_dress_wear_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_owner_dress_wear_id = RoomOwnerDressWearIdTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'dress_wear_index': 0
  }
  
  try:
    record = room_owner_dress_wear_id.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_owner_dress_wear_id.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_owner_dress_wear_id.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_owner_dress_wear_id.get_name(), e))
    raise e

##
## >>================================ room sharing music id table test method ===============================>>
##

def test_create_room_sharing_music_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_sharing_music_id = RoomSharingMusicIdTable(db_instance=db)
  room_sharing_music_id.create()
  return

##
## test: drop table
##
def test_drop_room_sharing_music_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_sharing_music_id = RoomSharingMusicIdTable(db_instance=db)
  room_sharing_music_id.drop()
  return

##
## test: check if table exists
##
def test_check_room_sharing_music_id_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_sharing_music_id = RoomSharingMusicIdTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_sharing_music_id.get_name()):
    get_logger().info("{} table exists!".format(room_sharing_music_id.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_sharing_music_id.get_name()))
  return

##
## test: insert record
##
def test_insert_room_sharing_music_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_sharing_music_id = RoomSharingMusicIdTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'sharing_music_index': 0
  }
  
  try:
    room_sharing_music_id.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_sharing_music_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_sharing_music_id = RoomSharingMusicIdTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'sharing_music_index': 0
  }
  
  try:
    room_sharing_music_id.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_sharing_music_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_sharing_music_id = RoomSharingMusicIdTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'sharing_music_index': 0,
    'sharing_music_id': '123456789'
  }
  
  try:
    room_sharing_music_id.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_sharing_music_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_sharing_music_id = RoomSharingMusicIdTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'sharing_music_index': 0
  }
  
  try:
    record = room_sharing_music_id.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_sharing_music_id.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_sharing_music_id.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_sharing_music_id.get_name(), e))
    raise e

##
## >>================================ picture table test method ===============================>>
##

def test_create_picture_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  picture_table = PictureTable(db_instance=db)
  picture_table.create()
  return

##
## test: drop table
##
def test_drop_picture_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  picture_table = PictureTable(db_instance=db)
  picture_table.drop()
  return

##
## test: check if table exists
##
def test_check_picture_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  picture_table = PictureTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(picture_table.get_name()):
    get_logger().info("{} table exists!".format(picture_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(picture_table.get_name()))
  return

##
## test: insert record
##
def test_insert_picture_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture = PictureTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'picture_index': 0
  }
  
  try:
    picture.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_picture_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture = PictureTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'picture_index': 0
  }
  
  try:
    picture.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_picture_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture = PictureTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'picture_index': 0,
    'height': 15,
    'width': 20
  }
  
  try:
    picture.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_picture_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  picture = PictureTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'picture_index': 0
  }
  
  try:
    record = picture.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(picture.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(picture.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(picture.get_name(), e))
    raise e

##
## >>================================ picture flex setting table test method ===============================>>
##

def test_create_picture_flex_setting_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  picture_flex_setting_table = PictureFlexSettingTable(db_instance=db)
  picture_flex_setting_table.create()
  return

##
## test: drop table
##
def test_drop_picture_flex_setting_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  picture_flex_setting_table = PictureFlexSettingTable(db_instance=db)
  picture_flex_setting_table.drop()
  return

##
## test: check if table exists
##
def test_check_picture_flex_setting_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  picture_flex_setting_table = PictureFlexSettingTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(picture_flex_setting_table.get_name()):
    get_logger().info("{} table exists!".format(picture_flex_setting_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(picture_flex_setting_table.get_name()))
  return

##
## test: insert record
##
def test_insert_picture_flex_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_flex_setting = PictureFlexSettingTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'flex_setting_index': 0
  }
  
  try:
    picture_flex_setting.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_picture_flex_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_flex_setting = PictureFlexSettingTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'flex_setting_index': 0
  }
  
  try:
    picture_flex_setting.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_picture_flex_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_flex_setting = PictureFlexSettingTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'flex_setting_index': 0,
    'uri': 'xxx',
    'flex_setting': 'TBD'
  }
  
  try:
    picture_flex_setting.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_picture_flex_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  picture_flex_setting = PictureFlexSettingTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'flex_setting_index': 0
  }
  
  try:
    record = picture_flex_setting.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(picture_flex_setting.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(picture_flex_setting.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(picture_flex_setting.get_name(), e))
    raise e

##
## >>================================ picture text setting table test method ===============================>>
##

def test_create_picture_text_setting_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  picture_text_setting_table = PictureTextSettingTable(db_instance=db)
  picture_text_setting_table.create()
  return

##
## test: drop table
##
def test_drop_picture_text_setting_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  picture_text_setting_table = PictureTextSettingTable(db_instance=db)
  picture_text_setting_table.drop()
  return

##
## test: check if table exists
##
def test_check_picture_text_setting_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  picture_text_setting_table = PictureTextSettingTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(picture_text_setting_table.get_name()):
    get_logger().info("{} table exists!".format(picture_text_setting_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(picture_text_setting_table.get_name()))
  return

##
## test: insert record
##
def test_insert_picture_text_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_text_setting = PictureTextSettingTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'text_setting_index': 0
  }
  
  try:
    picture_text_setting.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_picture_text_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_text_setting = PictureTextSettingTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'text_setting_index': 0
  }
  
  try:
    picture_text_setting.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_picture_text_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_text_setting = PictureTextSettingTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'text_setting_index': 0,
    'uri': 'xxx',
    'text_setting': 'TBD'
  }
  
  try:
    picture_text_setting.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_picture_text_setting_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  picture_text_setting = PictureTextSettingTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'text_setting_index': 0
  }
  
  try:
    record = picture_text_setting.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(picture_text_setting.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(picture_text_setting.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(picture_text_setting.get_name(), e))
    raise e

##
## >>================================ picture url table test method ===============================>>
##

def test_create_picture_url_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  picture_url_table = PictureUrlTable(db_instance=db)
  picture_url_table.create()
  return

##
## test: drop table
##
def test_drop_picture_url_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  picture_url_table = PictureUrlTable(db_instance=db)
  picture_url_table.drop()
  return

##
## test: check if table exists
##
def test_check_picture_url_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  picture_url_table = PictureUrlTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(picture_url_table.get_name()):
    get_logger().info("{} table exists!".format(picture_url_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(picture_url_table.get_name()))
  return

##
## test: insert record
##
def test_insert_picture_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_url = PictureUrlTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'url_index': 0
  }
  
  try:
    picture_url.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_picture_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_url = PictureUrlTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'url_index': 0
  }
  
  try:
    picture_url.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_picture_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  picture_url = PictureUrlTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'url_index': 0,
    'uri': 'xxx',
    'url': 'TBD'
  }
  
  try:
    picture_url.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_picture_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  picture_url = PictureUrlTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'url_index': 0
  }
  
  try:
    record = picture_url.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(picture_url.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(picture_url.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(picture_url.get_name(), e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  """
  ##
  ## room owner table
  ##
  test_create_badge_image_table(db)
  test_check_badge_image_exists(db)
  test_insert_badge_image_record(db)
  test_get_badge_image_record(db)
  test_update_badge_image_record(db)
  test_get_badge_image_record(db)
  test_delete_badge_image_record(db)
  test_get_badge_image_record(db)
  test_drop_badge_image_table(db)
  test_check_badge_image_exists(db)

  ##
  ## room owner dress wear id table
  ##
  test_create_room_owner_dress_wear_id_table(db)
  test_check_room_owner_dress_wear_id_exists(db)
  test_insert_room_owner_dress_wear_id_record(db)
  test_get_room_owner_dress_wear_id_record(db)
  test_update_room_owner_dress_wear_id_record(db)
  test_get_room_owner_dress_wear_id_record(db)
  test_delete_room_owner_dress_wear_id_record(db)
  test_get_room_owner_dress_wear_id_record(db)
  test_drop_room_owner_dress_wear_id_table(db)
  test_check_room_owner_dress_wear_id_exists(db)

  ##
  ## room sharing music id table
  ##
  test_create_room_sharing_music_id_table(db)
  test_check_room_sharing_music_id_exists(db)
  test_insert_room_sharing_music_id_record(db)
  test_get_room_sharing_music_id_record(db)
  test_update_room_sharing_music_id_record(db)
  test_get_room_sharing_music_id_record(db)
  test_delete_room_sharing_music_id_record(db)
  test_get_room_sharing_music_id_record(db)
  test_drop_room_sharing_music_id_table(db)
  test_check_room_sharing_music_id_exists(db)

  ##
  ## picture
  ##
  test_create_picture_table(db)
  test_check_picture_exists(db)
  test_insert_picture_record(db)
  test_get_picture_record(db)
  test_update_picture_record(db)
  test_get_picture_record(db)
  test_delete_picture_record(db)
  test_get_picture_record(db)
  test_drop_picture_table(db)
  test_check_picture_exists(db)

  ##
  ## picture flex setting table
  ##
  test_create_picture_flex_setting_table(db)
  test_check_picture_flex_setting_exists(db)
  test_insert_picture_flex_setting_record(db)
  test_get_picture_flex_setting_record(db)
  test_update_picture_flex_setting_record(db)
  test_get_picture_flex_setting_record(db)
  test_delete_picture_flex_setting_record(db)
  test_get_picture_flex_setting_record(db)
  test_drop_picture_flex_setting_table(db)
  test_check_picture_flex_setting_exists(db)

  ##
  ## picture text setting table
  ##
  test_create_picture_text_setting_table(db)
  test_check_picture_text_setting_exists(db)
  test_insert_picture_text_setting_record(db)
  test_get_picture_text_setting_record(db)
  test_update_picture_text_setting_record(db)
  test_get_picture_text_setting_record(db)
  test_delete_picture_text_setting_record(db)
  test_get_picture_text_setting_record(db)
  test_drop_picture_text_setting_table(db)
  test_check_picture_text_setting_exists(db)

  ##
  ## picture url table
  ##
  test_create_picture_url_table(db)
  test_check_picture_url_exists(db)
  test_insert_picture_url_record(db)
  test_get_picture_url_record(db)
  test_update_picture_url_record(db)
  test_get_picture_url_record(db)
  test_delete_picture_url_record(db)
  test_get_picture_url_record(db)
  test_drop_picture_url_table(db)
  test_check_picture_url_exists(db)
  """