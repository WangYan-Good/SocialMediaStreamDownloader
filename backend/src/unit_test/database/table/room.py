##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Extension>>
import yaml as yml

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.room                                  import RoomAttributeTable, \
                                                                             RoomPackMetaTable, \
                                                                             RoomPaidLiveDataTable, \
                                                                             RoomAuthTable, \
                                                                             RoomAdminUserIdTable, \
                                                                             RoomAdminUserOpenIdTable, \
                                                                             RoomAssistLabelTable, \
                                                                             FansGroupAdminUserIdTable, \
                                                                             FansGroupAdminUserOpenIdTable, \
                                                                             RoomSubscribeTable, \
                                                                             RoomShortTouchAreaConfigTable, \
                                                                             RoomShortTouchAreaConfigElementTable, \
                                                                             RoomShortTouchAreaConfigStrategyFeatWhitelistTable, \
                                                                             RoomTempStateConditionMapTable, \
                                                                             RoomTempStateGlobalConditionIgnoreStrategyTypeTable, \
                                                                             RoomTempStateGlobalConditionTable, \
                                                                             RoomRecordTable, \
                                                                             RoomTagTable, \
                                                                             RoomTopFansTable, \
                                                                             RoomUpperRightWidgetDataTable, \
                                                                             RoomVsRoleTable
from backend.src.base.log                                             import get_logger

##
## >>================================ room attribute table test method ===============================>>
##

##
## test: create room_attribute table
##
def test_create_room_attribute_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_attribute table
  ##
  room_attribute = RoomAttributeTable(db_instance=db)
  room_attribute.create()
  return

##
## test: drop room_attribute table
##
def test_drop_room_attribute_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop room_attribute table
  ##
  room_attribute = RoomAttributeTable(db)
  room_attribute.drop(confirm=True)
  return

##
## test: check if room_attribute table exists
##
def test_check_room_attribute_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## check if room attribute table exists
  ##
  room_attribute = RoomAttributeTable(db)
  if db.is_table_exist(room_attribute.get_name()):
    get_logger().info("{} table exists!".format(room_attribute.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_attribute.get_name()))
  return

##
## test: insert room attribute record
##
def test_insert_room_attribute(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## create room_attribute table if not exists
  ##
  room_attribute = RoomAttributeTable(db)
  
  sample_record = {
    "id": "7411524533301119798"
  }
  
  ##
  ## insert a sample room attribute record
  ##
  try:
    room_attribute.insert_record(sample_record)
    get_logger().info("sample room attribute record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample {} record: {}".format(room_attribute.get_name(), e))
    raise e

##
## test: delete room attribute record
##
def test_delete_room_attribute_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_attribute table if not exist
  ##
  room_attribute = RoomAttributeTable(db)
  
  ##
  ## delete a sample room attribute record
  ##
  sample_record = {
    'id':'7411524533301119798'
  }
  
  try:
    room_attribute.delete_record(sample_record)
    get_logger().info("sample room attribute record delete successfully")
  except Exception as e:
    get_logger().error("failed to delete sample room attribute record: {}".format(e))
    raise e    

##
## test: update room attribute record
##
def test_update_room_attribute_record(db:SocialMediaStreamDataBase) -> None:
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create room_attribute table if not exist
  ##
  room_attribute = RoomAttributeTable(db)
  sample_record = {
    'id':'7411524533301119798',
    'app_id':'1223456789'
  }
  
  ##
  ## update a sample room attribute record
  ##  
  try:
    room_attribute.update_record(sample_record)
    get_logger().info("sample room attribute record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample room attribute: {}".format(e))
    raise e
 
##
## test: get room attribute record
## 
def test_get_room_attribute_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_attribute table if not exist
  ##
  room_attribute = RoomAttributeTable(db)
  
  ##
  ## get a sample room attribute record
  ##
  sample_record = {
    'id':'7411524533301119798'
  }
  
  try:
    record = room_attribute.get_record(sample_record)
    if record:
      get_logger().info("sample room attribute record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample live record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room attribute record: {}".format(e))
    raise e
 
##
## >>================================ room pack meta table test method ===============================>>
##

##
## test: create table
##
def test_create_room_pack_meta_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room pack meta table
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  room_pack_meta.create()
  return

##
## test: drop table
##
def test_drop_room_pack_meta_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop room pack meta table
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  room_pack_meta.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_pack_meta_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_pack_meta = RoomPackMetaTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_pack_meta.get_name()):
    get_logger().info("{} table exists!".format(room_pack_meta.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_pack_meta.get_name()))
  return

##
## test: insert record
##
def test_insert_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'cluster':'default',
    'dc':'lf',
    'env':'prod',
    'scene':'reflow_room_info(prod_single_dc/rpc/topo)'
  }
  
  try:
    room_pack_meta.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_pack_meta table if not exists
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  now = dat.fromtimestamp(1740301577026/1000.0)
  print(now)
  sample_record = {
    'now':now,
    'platform':'douyin',
    'room_id':'7411524533301119798'
  }
  
  try:
    room_pack_meta.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room_pack_meta table if not exists
  ##
  room_pack_meta = RoomPackMetaTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'cluster':'default',
    'dc':'lf',
    'env':'test',
    'scene':'reflow_room_info(prod_single_dc/rpc/topo)'
  }
  
  try:
    room_pack_meta.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_pack_meta_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_pack_meta = RoomPackMetaTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_pack_meta.get_record(sample_record)
    if record:
      get_logger().info("sample room pack meta record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room pack meta record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room pack meta record: {}".format(e))
    raise e
 
##
## >>================================ room paid live data test method ===============================>>
##

##
## test: create table
##
def test_create_room_paid_live_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room pack meta table
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  room_room_paid_live_data.create()
  return

##
## test: drop table
##
def test_drop_room_paid_live_data(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop room pack meta table
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  room_room_paid_live_data.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_paid_live_data_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_room_paid_live_data = RoomPaidLiveDataTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_room_paid_live_data.get_name()):
    get_logger().info("{} table exists!".format(room_room_paid_live_data.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_room_paid_live_data.get_name()))
  return

##
## test: insert record
##
def test_insert_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_room_paid_live_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798'
  }
  
  try:
    room_room_paid_live_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_paid_live_data = RoomPaidLiveDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'anchor_right':0,
    'need_delivery_notice':False,
    'view_right':0
  }
  
  try:
    room_paid_live_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_paid_live_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_paid_live_data = RoomPaidLiveDataTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_paid_live_data.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ room auth table test method ===============================>>
##

def test_create_room_auth_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create room auth table
  ##
  room_auth = RoomAuthTable(db_instance=db)
  room_auth.create()
  return

##
## test: drop table
##
def test_drop_room_auth_data(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop room pack meta table
  ##
  room_auth = RoomAuthTable(db_instance=db)
  room_auth.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_auth_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_auth = RoomAuthTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_auth.get_name()):
    get_logger().info("{} table exists!".format(room_auth.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_auth.get_name()))
  return

##
## test: insert record
##
def test_insert_room_auth_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_auth = RoomAuthTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_auth.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_auth_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_auth = RoomAuthTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798'
  }
  
  try:
    room_auth.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_auth_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_auth = RoomAuthTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'Chat':True,
    'Gift':False,
    'VSGift':0
  }
  
  try:
    room_auth.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_auth_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_auth = RoomAuthTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_auth.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ room admin user id table test method ===============================>>
##

def test_create_room_admin_user_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_admin_user_id = RoomAdminUserIdTable(db_instance=db)
  room_admin_user_id.create()
  return

##
## test: drop table
##
def test_drop_room_admin_user_id_data(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_admin_user_id = RoomAdminUserIdTable(db_instance=db)
  room_admin_user_id.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_admin_user_id_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_admin_user_id = RoomAdminUserIdTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_admin_user_id.get_name()):
    get_logger().info("{} table exists!".format(room_admin_user_id.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_admin_user_id.get_name()))
  return

##
## test: insert record
##
def test_insert_room_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_user_id = RoomAdminUserIdTable(db_instance=db)
  
  ##
  ## insert a sample record
  ## 'admin_user_id_index' auto increment
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_admin_user_id.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_user_id = RoomAdminUserIdTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798',
    'admin_user_id_index': 1
  }
  
  try:
    room_admin_user_id.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_user_id = RoomAdminUserIdTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'admin_user_id_index':1,
    'admin_user_id':'123456789'
  }
  
  try:
    room_admin_user_id.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_admin_user_id = RoomAdminUserIdTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'admin_user_id_index': 1
  }
  
  try:
    record = room_admin_user_id.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ room admin user open id table test method ===============================>>
##

def test_create_room_admin_user_open_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_admin_user_open_id = RoomAdminUserOpenIdTable(db_instance=db)
  room_admin_user_open_id.create()
  return

##
## test: drop table
##
def test_drop_room_admin_user_open_id_data(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_admin_user_open_id = RoomAdminUserOpenIdTable(db_instance=db)
  room_admin_user_open_id.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_admin_user_open_id_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_admin_user_open_id = RoomAdminUserOpenIdTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_admin_user_open_id.get_name()):
    get_logger().info("{} table exists!".format(room_admin_user_open_id.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_admin_user_open_id.get_name()))
  return

##
## test: insert record
##
def test_insert_room_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_user_open_id = RoomAdminUserOpenIdTable(db_instance=db)
  
  ##
  ## insert a sample record
  ## 'admin_user_open_index': auto increment
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_admin_user_open_id.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_user_open_id = RoomAdminUserOpenIdTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798',
    'admin_user_open_id_index': 1
  }
  
  try:
    room_admin_user_open_id.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_admin_user_open_id = RoomAdminUserOpenIdTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'admin_user_open_id_index':1,
    'admin_user_open_id':'123456789'
  }
  
  try:
    room_admin_user_open_id.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_admin_user_open_id = RoomAdminUserOpenIdTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'admin_user_open_id_index':1
  }
  
  try:
    record = room_admin_user_open_id.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ room assist label table test method ===============================>>
##

def test_create_room_assist_label_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_assist_label = RoomAssistLabelTable(db_instance=db)
  room_assist_label.create()
  return

##
## test: drop table
##
def test_drop_room_assist_label_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_assist_label = RoomAssistLabelTable(db_instance=db)
  room_assist_label.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_assist_label_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_assist_label = RoomAssistLabelTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_assist_label.get_name()):
    get_logger().info("{} table exists!".format(room_assist_label.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_assist_label.get_name()))
  return

##
## test: insert record
##
def test_insert_room_assist_label_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_assist_label = RoomAssistLabelTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_assist_label.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_assist_label_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_assist_label = RoomAssistLabelTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798',
    'assist_label_index': 1
  }
  
  try:
    room_assist_label.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_assist_label_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_assist_label = RoomAssistLabelTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'assist_label_index':1,
    'assist_label':'owner'
  }
  
  try:
    room_assist_label.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_assist_label_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_assist_label = RoomAssistLabelTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'assist_label_index': 1
  }
  
  try:
    record = room_assist_label.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ fans group admin user id test method ===============================>>
##

def test_create_fans_group_admin_user_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db_instance=db)
  fans_group_admin_user_id.create()
  return

##
## test: drop table
##
def test_drop_fans_group_admin_user_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db_instance=db)
  fans_group_admin_user_id.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_fans_group_admin_user_id_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(fans_group_admin_user_id.get_name()):
    get_logger().info("{} table exists!".format(fans_group_admin_user_id.get_name()))
  else:
    get_logger().info("{} table not exists!".format(fans_group_admin_user_id.get_name()))
  return

##
## test: insert record
##
def test_insert_fans_group_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    fans_group_admin_user_id.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_fans_group_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798',
    'fans_group_admin_user_id_index':1
  }
  
  try:
    fans_group_admin_user_id.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_fans_group_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'fans_group_admin_user_id_index':1,
    'fans_group_admin_user_id':'123456789'
  }
  
  try:
    fans_group_admin_user_id.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_fans_group_admin_user_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  fans_group_admin_user_id = FansGroupAdminUserIdTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'fans_group_admin_user_id_index':1
  }
  
  try:
    record = fans_group_admin_user_id.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ fans group admin user open id test method ===============================>>
##

def test_create_fans_group_admin_user_open_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db_instance=db)
  fans_group_admin_user_open_id.create()
  return

##
## test: drop table
##
def test_drop_fans_group_admin_user_open_id_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db_instance=db)
  fans_group_admin_user_open_id.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_fans_group_admin_user_open_id_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(fans_group_admin_user_open_id.get_name()):
    get_logger().info("{} table exists!".format(fans_group_admin_user_open_id.get_name()))
  else:
    get_logger().info("{} table not exists!".format(fans_group_admin_user_open_id.get_name()))
  return

##
## test: insert record
##
def test_insert_fans_group_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    fans_group_admin_user_open_id.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_fans_group_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now':dat.fromtimestamp(1740301577026/1000.0),
    'platform':'douyin',
    'room_id':'7411524533301119798',
    'fans_group_admin_user_open_id_index': 1
  }
  
  try:
    fans_group_admin_user_open_id.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_fans_group_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'fans_group_admin_user_open_id_index':1,
    'fans_group_admin_user_open_id':'123456789'
  }
  
  try:
    fans_group_admin_user_open_id.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_fans_group_admin_user_open_id_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  fans_group_admin_user_open_id = FansGroupAdminUserOpenIdTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'fans_group_admin_user_open_id_index': 1
  }
  
  try:
    record = fans_group_admin_user_open_id.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ room subscribe table test method ===============================>>
##

def test_create_room_subscribe_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_subscribe = RoomSubscribeTable(db_instance=db)
  room_subscribe.create()
  return

##
## test: drop table
##
def test_drop_room_subscribe_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_subscribe = RoomSubscribeTable(db_instance=db)
  room_subscribe.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_subscribe_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_subscribe = RoomSubscribeTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_subscribe.get_name()):
    get_logger().info("{} table exists!".format(room_subscribe.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_subscribe.get_name()))
  return

##
## test: insert record
##
def test_insert_room_subscribe_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_subscribe = RoomSubscribeTable(db_instance=db)
  
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
    room_subscribe.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_subscribe_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_subscribe = RoomSubscribeTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480'
  }
  
  try:
    room_subscribe.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_subscribe_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_subscribe = RoomSubscribeTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'owner_user_id': '2700838411446480',
    'is_member': True,
    'level': 100
  }
  
  try:
    room_subscribe.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_subscribe_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_subscribe = RoomSubscribeTable(db)
  
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
    record = room_subscribe.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ room short touch area config table test method ===============================>>
##

def test_create_room_short_touch_area_config_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_short_touch_area_config = RoomShortTouchAreaConfigTable(db_instance=db)
  room_short_touch_area_config.create()
  return

##
## test: drop table
##
def test_drop_room_short_touch_area_config_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_short_touch_area_config = RoomShortTouchAreaConfigTable(db_instance=db)
  room_short_touch_area_config.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_short_touch_area_config_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_short_touch_area_config = RoomShortTouchAreaConfigTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_short_touch_area_config.get_name()):
    get_logger().info("{} table exists!".format(room_short_touch_area_config.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_short_touch_area_config.get_name()))
  return

##
## test: insert record
##
def test_insert_room_short_touch_area_config_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config = RoomShortTouchAreaConfigTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_short_touch_area_config.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_short_touch_area_config_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config = RoomShortTouchAreaConfigTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_short_touch_area_config.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_short_touch_area_config_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config = RoomShortTouchAreaConfigTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'forbidden_types_map': '{"type1": true, "type2": false}',
  }
  
  try:
    room_short_touch_area_config.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_short_touch_area_config_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_short_touch_area_config = RoomShortTouchAreaConfigTable(db)
  
  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_short_touch_area_config.get_record(sample_record)
    if record:
      get_logger().info("sample room paid live data record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample room paid live data record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample room paid live data record: {}".format(e))
    raise e

##
## >>================================ room short touch area config element table test method ===============================>>
##

def test_create_room_short_touch_area_config_element_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_short_touch_area_config_element = RoomShortTouchAreaConfigElementTable(db_instance=db)
  room_short_touch_area_config_element.create()
  return

##
## test: drop table
##
def test_drop_room_short_touch_area_config_element_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_short_touch_area_config_element = RoomShortTouchAreaConfigElementTable(db_instance=db)
  room_short_touch_area_config_element.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_short_touch_area_config_element_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_short_touch_area_config_element = RoomShortTouchAreaConfigElementTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_short_touch_area_config_element.get_name()):
    get_logger().info("{} table exists!".format(room_short_touch_area_config_element.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_short_touch_area_config_element.get_name()))
  return

##
## test: insert record
##
def test_insert_room_short_touch_area_config_element_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config_element = RoomShortTouchAreaConfigElementTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_short_touch_area_config_element.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_short_touch_area_config_element_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config_element = RoomShortTouchAreaConfigElementTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'element_index': 1
  }
  
  try:
    room_short_touch_area_config_element.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_short_touch_area_config_element_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config_element = RoomShortTouchAreaConfigElementTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'element_index': 1,
    'priority': 1,
    'type': 3
  }
  
  try:
    room_short_touch_area_config_element.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_short_touch_area_config_element_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_short_touch_area_config_element = RoomShortTouchAreaConfigElementTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_short_touch_area_config_element.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_short_touch_area_config_element.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_short_touch_area_config_element.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_short_touch_area_config_element.get_name(), e))
    raise e

##
## >>================================ room short touch area config strategy feat whitelist table test method ===============================>>
##

def test_create_room_short_touch_area_config_strategy_feat_whitelist_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_short_touch_area_config_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db_instance=db)
  room_short_touch_area_config_strategy_feat_whitelist.create()
  return

##
## test: drop table
##
def test_drop_room_short_touch_area_config_strategy_feat_whitelist_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_short_touch_area_config_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db_instance=db)
  room_short_touch_area_config_strategy_feat_whitelist.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_short_touch_area_config_strategy_feat_whitelist_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_short_touch_area_config_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_short_touch_area_config_strategy_feat_whitelist.get_name()):
    get_logger().info("{} table exists!".format(room_short_touch_area_config_strategy_feat_whitelist.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_short_touch_area_config_strategy_feat_whitelist.get_name()))
  return

##
## test: insert record
##
def test_insert_room_short_touch_area_config_strategy_feat_whitelist_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_short_touch_area_config_strategy_feat_whitelist.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_short_touch_area_config_strategy_feat_whitelist_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'whitelist_index': 1
  }
  
  try:
    room_short_touch_area_config_strategy_feat_whitelist.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_short_touch_area_config_strategy_feat_whitelist_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_short_touch_area_config_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'whitelist_index': 1,
    'whitelist_tag': 'abc'
  }
  
  try:
    room_short_touch_area_config_strategy_feat_whitelist.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_short_touch_area_config_strategy_feat_whitelist_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_short_touch_area_config_strategy_feat_whitelist = RoomShortTouchAreaConfigStrategyFeatWhitelistTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'whitelist_index': 1
  }
  
  try:
    record = room_short_touch_area_config_strategy_feat_whitelist.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_short_touch_area_config_strategy_feat_whitelist.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_short_touch_area_config_strategy_feat_whitelist.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_short_touch_area_config_strategy_feat_whitelist.get_name(), e))
    raise e

##
## >>================================ room temp state condition map table test method ===============================>>
##

def test_create_room_temp_state_condition_map_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db_instance=db)
  room_temp_state_condition_map.create()
  return

##
## test: drop table
##
def test_drop_room_temp_state_condition_map_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db_instance=db)
  room_temp_state_condition_map.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_temp_state_condition_map_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_temp_state_condition_map.get_name()):
    get_logger().info("{} table exists!".format(room_temp_state_condition_map.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_temp_state_condition_map.get_name()))
  return

##
## test: insert record
##
def test_insert_room_temp_state_condition_map_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_temp_state_condition_map.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_temp_state_condition_map_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'map_index': 1
  }
  
  try:
    room_temp_state_condition_map.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_temp_state_condition_map_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'map_index': 1,
    'minimum_gap': 1,
    'priority': 2,
    'strategy_type': 3
  }
  
  try:
    room_temp_state_condition_map.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_temp_state_condition_map_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_temp_state_condition_map = RoomTempStateConditionMapTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'map_index': 1
  }
  
  try:
    record = room_temp_state_condition_map.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_temp_state_condition_map.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_temp_state_condition_map.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_temp_state_condition_map.get_name(), e))
    raise e

##
## >>================================ room temp state global condition ignore strategy type table test method ===============================>>
##

def test_create_room_temp_state_global_condition_ignore_strategy_type_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db_instance=db)
  room_temp_state_global_condition_ignore_strategy_type.create()
  return

##
## test: drop table
##
def test_drop_room_temp_state_global_condition_ignore_strategy_type_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db_instance=db)
  room_temp_state_global_condition_ignore_strategy_type.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_temp_state_global_condition_ignore_strategy_type_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_temp_state_global_condition_ignore_strategy_type.get_name()):
    get_logger().info("{} table exists!".format(room_temp_state_global_condition_ignore_strategy_type.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_temp_state_global_condition_ignore_strategy_type.get_name()))
  return

##
## test: insert record
##
def test_insert_room_temp_state_global_condition_ignore_strategy_type_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_temp_state_global_condition_ignore_strategy_type.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_temp_state_global_condition_ignore_strategy_type_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_temp_state_global_condition_ignore_strategy_type.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_temp_state_global_condition_ignore_strategy_type_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'strategy_type': 2
  }
  
  try:
    room_temp_state_global_condition_ignore_strategy_type.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_temp_state_global_condition_ignore_strategy_type_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_temp_state_global_condition_ignore_strategy_type = RoomTempStateGlobalConditionIgnoreStrategyTypeTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_temp_state_global_condition_ignore_strategy_type.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_temp_state_global_condition_ignore_strategy_type.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_temp_state_global_condition_ignore_strategy_type.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_temp_state_global_condition_ignore_strategy_type.get_name(), e))
    raise e

##
## >>================================ room temp state global condition table test method ===============================>>
##

def test_create_room_temp_state_global_condition_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db_instance=db)
  room_temp_state_global_condition.create()
  return

##
## test: drop table
##
def test_drop_room_temp_state_global_condition_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db_instance=db)
  room_temp_state_global_condition.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_temp_state_global_condition_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_temp_state_global_condition.get_name()):
    get_logger().info("{} table exists!".format(room_temp_state_global_condition.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_temp_state_global_condition.get_name()))
  return

##
## test: insert record
##
def test_insert_room_temp_state_global_condition_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db_instance=db)
  
  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_temp_state_global_condition.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_temp_state_global_condition_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_temp_state_global_condition.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_temp_state_global_condition_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'allow_count': 4,
    'duration_gap': 100
  }
  
  try:
    room_temp_state_global_condition.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_temp_state_global_condition_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_temp_state_global_condition = RoomTempStateGlobalConditionTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_temp_state_global_condition.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_temp_state_global_condition.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_temp_state_global_condition.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_temp_state_global_condition.get_name(), e))
    raise e

##
## >>================================ room record table test method ===============================>>
##

def test_create_room_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_record = RoomRecordTable(db_instance=db)
  room_record.create()
  return

##
## test: drop table
##
def test_drop_room_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_record = RoomRecordTable(db_instance=db)
  room_record.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_record_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  room_record = RoomRecordTable(db)
  
  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_record.get_name()):
    get_logger().info("{} table exists!".format(room_record.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_record.get_name()))
  return

##
## test: insert record
##
def test_insert_room_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_record = RoomRecordTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'id': '7411524533301119798'
  }
  
  try:
    room_record.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_record = RoomRecordTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'id': '7411524533301119798'
  }
  
  try:
    room_record.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_record = RoomRecordTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'id': '7411524533301119798',
    'room_like_count': 14873,
    'stream_id': '691500607505433258'
  }
  
  try:
    room_record.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_room_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_record = RoomRecordTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'id': '7411524533301119798'
  }
  
  try:
    record = room_record.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_record.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_record.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_record.get_name(), e))
    raise e

"""
##
## >>================================ room record table test method ===============================>>
##

def test_create_room_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_record = RoomRecordTable(db_instance=db)
  room_record.create()
  return

##
## test: drop table
##
def test_drop_room_record_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_record = RoomRecordTable(db_instance=db)
  room_record.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_record_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  room_record = RoomRecordTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_record.get_name()):
    get_logger().info("{} table exists!".format(room_record.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_record.get_name()))
  return

##
## test: insert record
##
def test_insert_room_record_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_record = RoomRecordTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_record.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_record_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_record = RoomRecordTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_record.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_record_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_record = RoomRecordTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'status': 1
  }
  
  try:
    room_record.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
##
def test_get_room_record_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_record = RoomRecordTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = room_record.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_record.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_record.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_record.get_name(), e))
    raise e
"""
##
## >>================================ room tag table test method ===============================>>
##

def test_create_room_tag_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_tag = RoomTagTable(db_instance=db)
  room_tag.create()
  return

##
## test: drop table
##
def test_drop_room_tag_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_tag = RoomTagTable(db_instance=db)
  room_tag.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_tag_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  room_tag = RoomTagTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_tag.get_name()):
    get_logger().info("{} table exists!".format(room_tag.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_tag.get_name()))
  return

##
## test: insert record
##
def test_insert_room_tag_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_tag = RoomTagTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_tag.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_tag_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_tag = RoomTagTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'tag_index': 1
  }
  
  try:
    room_tag.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_tag_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_tag = RoomTagTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'tag_index': 1,
    'tag': 'helloworld'
  }
  
  try:
    room_tag.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
##
def test_get_room_tag_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_tag = RoomTagTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'tag_index': 1
  }
  
  try:
    record = room_tag.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_tag.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_tag.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_tag.get_name(), e))
    raise e

##
## >>================================ room top fans table test method ===============================>>
##

def test_create_room_top_fans_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  room_top_fans = RoomTopFansTable(db_instance=db)
  room_top_fans.create()
  return

##
## test: drop table
##
def test_drop_room_top_fans_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  room_top_fans = RoomTopFansTable(db_instance=db)
  room_top_fans.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_room_top_fans_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  room_top_fans = RoomTopFansTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(room_top_fans.get_name()):
    get_logger().info("{} table exists!".format(room_top_fans.get_name()))
  else:
    get_logger().info("{} table not exists!".format(room_top_fans.get_name()))
  return

##
## test: insert record
##
def test_insert_room_top_fans_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_top_fans = RoomTopFansTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    room_top_fans.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_room_top_fans_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_top_fans = RoomTopFansTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'fans_index': 1
  }
  
  try:
    room_top_fans.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_room_top_fans_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  room_top_fans = RoomTopFansTable(db_instance=db)

  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'fans_index': 1,
    'top_fans': 'TBD'
  }
  
  try:
    room_top_fans.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
##
def test_get_room_top_fans_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  room_top_fans = RoomTopFansTable(db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'fans_index': 1
  }
  
  try:
    record = room_top_fans.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(room_top_fans.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(room_top_fans.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(room_top_fans.get_name(), e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')

  ##
  ## room attribute table
  ##
  test_create_room_attribute_table(db)
  test_check_room_attribute_table_exists(db)
  test_insert_room_attribute(db)
  test_update_room_attribute_record(db)
  test_get_room_attribute_record(db)
  test_delete_room_attribute_record(db)
  test_drop_room_attribute_table(db)
  test_check_room_attribute_table_exists(db)
  
  ##
  ## room pack meta table
  ##
  test_create_room_pack_meta_table(db)
  test_check_room_pack_meta_table_exists(db)
  test_insert_room_pack_meta_record(db)
  test_update_room_pack_meta_record(db)
  test_get_room_pack_meta_record(db)
  test_delete_room_pack_meta_record(db)
  test_drop_room_pack_meta_table(db)
  test_check_room_pack_meta_table_exists(db)
  
  ##
  ## room paid live data table
  ##
  test_create_room_paid_live_data_table(db)
  test_check_room_paid_live_data_exists(db)
  test_insert_room_paid_live_data_record(db)
  test_update_room_paid_live_data_record(db)
  test_get_room_paid_live_data_record(db)
  test_delete_room_paid_live_data_record(db)
  test_drop_room_paid_live_data(db)
  test_check_room_paid_live_data_exists(db)

  ##
  ## room auth table
  ##
  test_create_room_auth_table(db)
  test_check_room_auth_exists(db)
  test_insert_room_auth_record(db)
  test_delete_room_auth_record(db)
  test_update_room_auth_record(db)
  test_get_room_auth_record(db)
  test_drop_room_auth_data(db)
  test_check_room_auth_exists(db)

  ##
  ## RoomTabTable
  ## TBD
  ##

  ##
  ## room admin user id table
  ##
  test_create_room_admin_user_id_table(db)
  test_check_room_admin_user_id_exists(db)
  test_insert_room_admin_user_id_record(db)
  test_get_room_admin_user_id_record(db)
  test_update_room_admin_user_id_record(db)
  test_get_room_admin_user_id_record(db)
  test_delete_room_admin_user_id_record(db)
  test_get_room_admin_user_id_record(db)
  test_drop_room_admin_user_id_data(db)
  test_check_room_admin_user_id_exists(db)

  ##
  ## room admin user open id table
  ##
  test_create_room_admin_user_open_id_table(db)
  test_insert_room_admin_user_open_id_record(db)
  test_get_room_admin_user_open_id_record(db)
  test_update_room_admin_user_open_id_record(db)
  test_get_room_admin_user_open_id_record(db)
  test_delete_room_admin_user_open_id_record(db)
  test_get_room_admin_user_open_id_record(db)
  test_check_room_admin_user_open_id_exists(db)
  test_drop_room_admin_user_open_id_data(db)
  test_check_room_admin_user_open_id_exists(db)
  """
  ##
  ## room assist label table
  ## TBD
  ##
  test_create_room_assist_label_table(db)
  test_check_room_assist_label_exists(db)
  test_insert_room_assist_label_record(db)
  test_get_room_assist_label_record(db)
  test_update_room_assist_label_record(db)
  test_get_room_assist_label_record(db)
  test_delete_room_assist_label_record(db)
  test_get_room_assist_label_record(db)
  test_drop_room_assist_label_table(db)
  test_check_room_assist_label_exists(db)
  
  ##
  ## room deco table
  ## TBD
  ##
  """

  ##
  ## fans group admin user id table
  ##
  test_create_fans_group_admin_user_id_table(db)
  test_check_fans_group_admin_user_id_exists(db)
  test_insert_fans_group_admin_user_id_record(db)
  test_get_fans_group_admin_user_id_record(db)
  test_update_fans_group_admin_user_id_record(db)
  test_get_fans_group_admin_user_id_record(db)
  test_delete_fans_group_admin_user_id_record(db)
  test_get_fans_group_admin_user_id_record(db)
  test_drop_fans_group_admin_user_id_table(db)
  test_check_fans_group_admin_user_id_exists(db)

  ##
  ## fans group admin user open id table
  ##
  test_create_fans_group_admin_user_open_id_table(db)
  test_check_fans_group_admin_user_open_id_exists(db)
  test_insert_fans_group_admin_user_open_id_record(db)
  test_get_fans_group_admin_user_open_id_record(db)
  test_update_fans_group_admin_user_open_id_record(db)
  test_get_fans_group_admin_user_open_id_record(db)
  test_delete_fans_group_admin_user_open_id_record(db)
  test_get_fans_group_admin_user_open_id_record(db)
  test_drop_fans_group_admin_user_open_id_table(db)
  test_check_fans_group_admin_user_open_id_exists(db)

  ##
  ## room subscribe table
  ##
  test_create_room_subscribe_table(db)
  test_check_room_subscribe_exists(db)
  test_insert_room_subscribe_record(db)
  test_get_room_subscribe_record(db)
  test_update_room_subscribe_record(db)
  test_get_room_subscribe_record(db)
  test_delete_room_subscribe_record(db)
  test_get_room_subscribe_record(db)
  test_drop_room_subscribe_table(db)
  test_check_room_subscribe_exists(db)

  ##
  ## room short touch area config table
  ##
  test_create_room_short_touch_area_config_table(db)
  test_check_room_short_touch_area_config_exists(db)
  test_insert_room_short_touch_area_config_record(db)
  test_get_room_short_touch_area_config_record(db)
  test_update_room_short_touch_area_config_record(db)
  test_get_room_short_touch_area_config_record(db)
  test_delete_room_short_touch_area_config_record(db)
  test_get_room_short_touch_area_config_record(db)
  test_drop_room_short_touch_area_config_table(db)
  test_check_room_short_touch_area_config_exists(db)

  ##
  ## room short touch area config element table
  ##
  test_create_room_short_touch_area_config_element_table(db)
  test_check_room_short_touch_area_config_element_exists(db)
  test_insert_room_short_touch_area_config_element_record(db)
  test_get_room_short_touch_area_config_element_record(db)
  test_update_room_short_touch_area_config_element_record(db)
  test_get_room_short_touch_area_config_element_record(db)
  test_delete_room_short_touch_area_config_element_record(db)
  test_get_room_short_touch_area_config_element_record(db)
  test_drop_room_short_touch_area_config_element_table(db)
  test_check_room_short_touch_area_config_element_exists(db)

  ##
  ## room short touch area config strategy feat whitelist table
  ##
  test_create_room_short_touch_area_config_strategy_feat_whitelist_table(db)
  test_check_room_short_touch_area_config_strategy_feat_whitelist_exists(db)
  test_insert_room_short_touch_area_config_strategy_feat_whitelist_record(db)
  test_get_room_short_touch_area_config_strategy_feat_whitelist_record(db)
  test_update_room_short_touch_area_config_strategy_feat_whitelist_record(db)
  test_get_room_short_touch_area_config_strategy_feat_whitelist_record(db)
  test_delete_room_short_touch_area_config_strategy_feat_whitelist_record(db)
  test_get_room_short_touch_area_config_strategy_feat_whitelist_record(db)
  test_drop_room_short_touch_area_config_strategy_feat_whitelist_table(db)
  test_check_room_short_touch_area_config_strategy_feat_whitelist_exists(db)

  ##
  ## room temp state condition map
  ##
  test_create_room_temp_state_condition_map_table(db)
  test_check_room_temp_state_condition_map_exists(db)
  test_insert_room_temp_state_condition_map_record(db)
  test_get_room_temp_state_condition_map_record(db)
  test_update_room_temp_state_condition_map_record(db)
  test_get_room_temp_state_condition_map_record(db)
  test_delete_room_temp_state_condition_map_record(db)
  test_get_room_temp_state_condition_map_record(db)
  test_drop_room_temp_state_condition_map_table(db)
  test_check_room_temp_state_condition_map_exists(db)

  ##
  ## room temp state global condition ignore strategy type table
  ##
  test_create_room_temp_state_global_condition_ignore_strategy_type_table(db)
  test_check_room_temp_state_global_condition_ignore_strategy_type_exists(db)
  test_insert_room_temp_state_global_condition_ignore_strategy_type_record(db)
  test_get_room_temp_state_global_condition_ignore_strategy_type_record(db)
  test_update_room_temp_state_global_condition_ignore_strategy_type_record(db)
  test_get_room_temp_state_global_condition_ignore_strategy_type_record(db)
  test_delete_room_temp_state_global_condition_ignore_strategy_type_record(db)
  test_get_room_temp_state_global_condition_ignore_strategy_type_record(db)
  test_drop_room_temp_state_global_condition_ignore_strategy_type_table(db)
  test_check_room_temp_state_global_condition_ignore_strategy_type_exists(db)

  ##
  ## room temp state global condition table
  ##
  test_create_room_temp_state_global_condition_table(db)
  test_check_room_temp_state_global_condition_exists(db)
  test_insert_room_temp_state_global_condition_record(db)
  test_get_room_temp_state_global_condition_record(db)
  test_update_room_temp_state_global_condition_record(db)
  test_get_room_temp_state_global_condition_record(db)
  test_delete_room_temp_state_global_condition_record(db)
  test_get_room_temp_state_global_condition_record(db)
  test_drop_room_temp_state_global_condition_table(db)
  test_check_room_temp_state_global_condition_exists(db)

  ##
  ## room record table
  ##
  test_create_room_record_table(db)
  test_check_room_record_exists(db)
  test_insert_room_record(db)
  test_get_room_record(db)
  test_update_room_record(db)
  test_get_room_record(db)
  test_delete_room_record(db)
  test_get_room_record(db)
  test_drop_room_record_table(db)
  test_check_room_record_exists(db)

  ##
  ## room tag table
  ##
  test_create_room_tag_table(db)
  test_check_room_tag_exists(db)
  test_insert_room_tag_record(db)
  test_get_room_tag_record(db)
  test_update_room_tag_record(db)
  test_get_room_tag_record(db)
  test_delete_room_tag_record(db)
  test_get_room_tag_record(db)
  test_drop_room_tag_table(db)
  test_check_room_tag_exists(db)

  """
  ##
  ## TODO: room top fans table
  ##
  test_create_room_top_fans_table(db)
  test_check_room_top_fans_exists(db)
  test_insert_room_top_fans_record(db)
  test_get_room_top_fans_record(db)
  test_update_room_top_fans_record(db)
  test_get_room_top_fans_record(db)
  test_delete_room_top_fans_record(db)
  test_get_room_top_fans_record(db)
  test_drop_room_top_fans_table(db)
  test_check_room_top_fans_exists(db)
  """