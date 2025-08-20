##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.room                                  import RoomAttributeTable, \
                                                                             RoomPackMetaTable, \
                                                                             RoomPaidLiveDataTable, \
                                                                             RoomAuthTable, \
                                                                             RoomAdminUserIdTable, \
                                                                             RoomAdminUserOpenIdTable, \
                                                                             RoomAssistLabelTable, \
                                                                             FansGroupAdminUserIdTable
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
  room_attribute.drop()
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
  room_pack_meta.drop()
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
  room_room_paid_live_data.drop()
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
  room_auth.drop()
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
  room_admin_user_id.drop()
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
    'room_id':'7411524533301119798'
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
    'admin_user_id_index':0,
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
    'room_id': '7411524533301119798'
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
  room_admin_user_open_id.drop()
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
    'room_id':'7411524533301119798'
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
    'admin_user_open_index':0,
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
    'room_id': '7411524533301119798'
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
  room_assist_label.drop()
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
    'room_id':'7411524533301119798'
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
    'assist_label_index':0,
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
    'room_id': '7411524533301119798'
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
  fans_group_admin_user_id.drop()
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
    'room_id':'7411524533301119798'
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
    'fans_group_admin_user_id_index':0,
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
    'room_id': '7411524533301119798'
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
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')
  """
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
  
  ##
  ## room assist label table
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
  """