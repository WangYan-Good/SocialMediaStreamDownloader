##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from datetime                                                         import datetime as dat

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.stream                                import LiveStreamTable, \
                                                                             StreamCandidateResolutionTable, \
                                                                             StreamCompletePushUrlTable, \
                                                                             LiveCoreSdkDataTable, \
                                                                             LiveCoreSdkPullDataTable, \
                                                                             LiveCoreSdkPullFlvDataTable, \
                                                                             LiveCoreSdkPullHlsDataTable, \
                                                                             LiveCoreSdkPullDataOptionTable, \
                                                                             LiveCoreSdkPullQualityDataTable, \
                                                                             LiveCoreSdkPullDefaultQualityDataTable, \
                                                                             StreamPushUrlTable
from backend.src.base.log                                             import get_logger

##
## >>================================ live stream table test method ===============================>>
##

##
## test: create live_stream table
##
def test_create_live_stream_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_stream table
  ##
  live_stream = LiveStreamTable(db_instance=db)
  live_stream.create()
  return

##
## test: drop live_stream table
##
def test_drop_live_stream_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database is valid
  ##
  if db is None:
    get_logger().error("db_instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop live_stream table
  ##
  live_stream = LiveStreamTable(db)
  live_stream.drop(confirm=True)
  return

##
## test: check if live_stream table exists
##
def test_check_live_stream_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## check if live stream table exists
  ##
  live_stream = LiveStreamTable(db)
  if db.is_table_exist(live_stream.get_name()):
    get_logger().info("{} table exists!".format(live_stream.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_stream.get_name()))
  return

##
## test: insert live stream record
##
def test_insert_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid {} instance".format(type(db)))
    raise ValueError
  
  ##
  ## create live_stream table if not exists
  ##
  live_stream = LiveStreamTable(db)
  sample_record = {
    "id": "691500607505433258",
  }
  
  ##
  ## insert a sample live stream record
  ##
  try:
    live_stream.insert_record(sample_record, on_duplicate='ignore')
    get_logger().info("sample live stream record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample {} record: {}".format(live_stream.get_name(), e))
    raise e

##
## test: delete live stream record
##
def test_delete_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_stream table if not exist
  ##
  live_stream = LiveStreamTable(db)
  
  ##
  ## delete a sample live stream record
  ##
  sample_record = {
    'id':'691500607505433258'
  }
  
  try:
    live_stream.delete_record(sample_record)
    get_logger().info("sample live stream record delete successfully")
  except Exception as e:
    get_logger().error("failed to delete sample live stream record: {}".format(e))
    raise e

##
## test: update live stream record
##
def test_update_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  ##
  ## create live_stream table if not exist
  ##
  live_stream = LiveStreamTable(db)

  ##
  ## update a sample live stream record
  ##
  sample_record = {
    "id": "691500607505433258",
    "default_resolution":"FULL_HD1"
  }

  try:
    live_stream.update_record(sample_record)
    get_logger().info("sample live stream record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample live stream: {}".format(e))
    raise e

##
## test: get live stream record
##
def test_get_live_stream_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create live_stream table if not exist
  ##
  live_stream = LiveStreamTable(db)
  
  ##
  ## get a sample live stream record
  ##
  sample_record = {
    'id':'691500607505433258'
  }
  
  try:
    record = live_stream.get_record(sample_record)
    if record:
      get_logger().info("sample live stream record retrieved successfully: \n\t{}".format(record))
    else:
      get_logger().warning("sample live record not found")
  except Exception as e:
    get_logger().error("failed to retrieve sample live stream record: {}".format(e))
    raise e

##
## >>================================ stream candidate resolution table test method ===============================>>
##

def test_create_stream_candidate_resolution_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  stream_candidate_resolution_table = StreamCandidateResolutionTable(db_instance=db)
  stream_candidate_resolution_table.create()
  return

##
## test: drop table
##
def test_drop_stream_candidate_resolution_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  stream_candidate_resolution_table = StreamCandidateResolutionTable(db_instance=db)
  stream_candidate_resolution_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_stream_candidate_resolution_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  stream_candidate_resolution_table = StreamCandidateResolutionTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(stream_candidate_resolution_table.get_name()):
    get_logger().info("{} table exists!".format(stream_candidate_resolution_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(stream_candidate_resolution_table.get_name()))
  return

##
## test: insert record
##
def test_insert_stream_candidate_resolution_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_candidate_resolution = StreamCandidateResolutionTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_id': '691500607505433258',
    'resolution_index': 1
  }
  
  try:
    stream_candidate_resolution.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_stream_candidate_resolution_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_candidate_resolution = StreamCandidateResolutionTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_id': '691500607505433258',
    'resolution_index': 1
  }
  
  try:
    stream_candidate_resolution.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_stream_candidate_resolution_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_candidate_resolution = StreamCandidateResolutionTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_id': '691500607505433258',
    'resolution_index': 1,
    'candidate_resolution': 'FULL1_HLD'
  }
  
  try:
    stream_candidate_resolution.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_stream_candidate_resolution_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  stream_candidate_resolution = StreamCandidateResolutionTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'resolution_index': 1
  }
  
  try:
    record = stream_candidate_resolution.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(stream_candidate_resolution.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(stream_candidate_resolution.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(stream_candidate_resolution.get_name(), e))
    raise e

##
## >>================================ stream complete push url table test method ===============================>>
##

##
## >>================================ stream complete push url table test method ===============================>>
##
def test_create_stream_complete_push_url_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  stream_complete_push_url_table = StreamCompletePushUrlTable(db_instance=db)
  stream_complete_push_url_table.create()
  return

##
## test: drop table
##
def test_drop_stream_complete_push_url_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  stream_complete_push_url_table = StreamCompletePushUrlTable(db_instance=db)
  stream_complete_push_url_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_stream_complete_push_url_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  stream_complete_push_url_table = StreamCompletePushUrlTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(stream_complete_push_url_table.get_name()):
    get_logger().info("{} table exists!".format(stream_complete_push_url_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(stream_complete_push_url_table.get_name()))
  return

##
## test: insert record
##
def test_insert_stream_complete_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_complete_push_url = StreamCompletePushUrlTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_id': '691500607505433258'
  }
  
  try:
    stream_complete_push_url.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_stream_complete_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_complete_push_url = StreamCompletePushUrlTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_id': '691500607505433258',
    'complete_push_url_index': 1
  }
  
  try:
    stream_complete_push_url.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_stream_complete_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_complete_push_url = StreamCompletePushUrlTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_id': '691500607505433258',
    'complete_push_url_index': 1,
    'complete_push_url': 'TBD'
  }
  
  try:
    stream_complete_push_url.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_stream_complete_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  stream_complete_push_url = StreamCompletePushUrlTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'complete_push_url_index': 1
  }
  
  try:
    record = stream_complete_push_url.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(stream_complete_push_url.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(stream_complete_push_url.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(stream_complete_push_url.get_name(), e))
    raise e

##
## >>================================ live core sdk data table test method ===============================>>
##

def test_create_live_core_sdk_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  live_core_sdk_data_table = LiveCoreSdkDataTable(db_instance=db)
  live_core_sdk_data_table.create()
  return

##
## test: drop table
##
def test_drop_live_core_sdk_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  live_core_sdk_data_table = LiveCoreSdkDataTable(db_instance=db)
  live_core_sdk_data_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_live_core_sdk_data_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  live_core_sdk_data_table = LiveCoreSdkDataTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(live_core_sdk_data_table.get_name()):
    get_logger().info("{} table exists!".format(live_core_sdk_data_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_core_sdk_data_table.get_name()))
  return

##
## test: insert record
##
def test_insert_live_core_sdk_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_data = LiveCoreSdkDataTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_live_core_sdk_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_data = LiveCoreSdkDataTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_live_core_sdk_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_data = LiveCoreSdkDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'size': '2GB'
  }
  
  try:
    live_core_sdk_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_live_core_sdk_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  live_core_sdk_data = LiveCoreSdkDataTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = live_core_sdk_data.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(live_core_sdk_data.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(live_core_sdk_data.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(live_core_sdk_data.get_name(), e))
    raise e

##
## >>================================ live core sdk pull data table test method ===============================>>
##

def test_create_live_core_sdk_pull_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  live_core_sdk_pull_data_table = LiveCoreSdkPullDataTable(db_instance=db)
  live_core_sdk_pull_data_table.create()
  return

##
## test: drop table
##
def test_drop_live_core_sdk_pull_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  live_core_sdk_pull_data_table = LiveCoreSdkPullDataTable(db_instance=db)
  live_core_sdk_pull_data_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_live_core_sdk_pull_data_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  live_core_sdk_pull_data_table = LiveCoreSdkPullDataTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(live_core_sdk_pull_data_table.get_name()):
    get_logger().info("{} table exists!".format(live_core_sdk_pull_data_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_core_sdk_pull_data_table.get_name()))
  return

##
## test: insert record
##
def test_insert_live_core_sdk_pull_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_data = LiveCoreSdkPullDataTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_live_core_sdk_pull_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_data = LiveCoreSdkPullDataTable(db_instance=db)
  
  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_live_core_sdk_pull_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_data = LiveCoreSdkPullDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'version': '123456789'
  }
  
  try:
    live_core_sdk_pull_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_live_core_sdk_pull_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  live_core_sdk_pull_data = LiveCoreSdkPullDataTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = live_core_sdk_pull_data.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(live_core_sdk_pull_data.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(live_core_sdk_pull_data.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(live_core_sdk_pull_data.get_name(), e))
    raise e

##
## >>================================ live core sdk pull flv data table test method ===============================>>
##

def test_create_live_core_sdk_pull_flv_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  live_core_sdk_pull_flv_data_table = LiveCoreSdkPullFlvDataTable(db_instance=db)
  live_core_sdk_pull_flv_data_table.create()
  return

##
## test: drop table
##
def test_drop_live_core_sdk_pull_flv_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  live_core_sdk_pull_flv_data_table = LiveCoreSdkPullFlvDataTable(db_instance=db)
  live_core_sdk_pull_flv_data_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_live_core_sdk_pull_flv_data_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  live_core_sdk_pull_flv_data_table = LiveCoreSdkPullFlvDataTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(live_core_sdk_pull_flv_data_table.get_name()):
    get_logger().info("{} table exists!".format(live_core_sdk_pull_flv_data_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_core_sdk_pull_flv_data_table.get_name()))
  return

##
## test: insert record
##
def test_insert_live_core_sdk_pull_flv_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_flv_data = LiveCoreSdkPullFlvDataTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_flv_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_live_core_sdk_pull_flv_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_flv_data = LiveCoreSdkPullFlvDataTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'Flv_index': 1
  }
  
  try:
    live_core_sdk_pull_flv_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_live_core_sdk_pull_flv_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_flv_data = LiveCoreSdkPullFlvDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'Flv_index': 1,
    'Flv': '123456789'
  }
  
  try:
    live_core_sdk_pull_flv_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_live_core_sdk_pull_flv_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  live_core_sdk_pull_flv_data = LiveCoreSdkPullFlvDataTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'Flv_index': 1
  }
  
  try:
    record = live_core_sdk_pull_flv_data.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(live_core_sdk_pull_flv_data.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(live_core_sdk_pull_flv_data.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(live_core_sdk_pull_flv_data.get_name(), e))
    raise e

##
## >>================================ live core sdk pull flv data table test method ===============================>>
##

def test_create_live_core_sdk_pull_hls_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  live_core_sdk_pull_hls_data_table = LiveCoreSdkPullHlsDataTable(db_instance=db)
  live_core_sdk_pull_hls_data_table.create()
  return

##
## test: drop table
##
def test_drop_live_core_sdk_pull_hls_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  live_core_sdk_pull_hls_data_table = LiveCoreSdkPullHlsDataTable(db_instance=db)
  live_core_sdk_pull_hls_data_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_live_core_sdk_pull_hls_data_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  live_core_sdk_pull_hls_data_table = LiveCoreSdkPullHlsDataTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(live_core_sdk_pull_hls_data_table.get_name()):
    get_logger().info("{} table exists!".format(live_core_sdk_pull_hls_data_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_core_sdk_pull_hls_data_table.get_name()))
  return

##
## test: insert record
##
def test_insert_live_core_sdk_pull_hls_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_hls_data = LiveCoreSdkPullHlsDataTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_hls_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_live_core_sdk_pull_hls_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_hls_data = LiveCoreSdkPullHlsDataTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'Hls_index': 1
  }
  
  try:
    live_core_sdk_pull_hls_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_live_core_sdk_pull_hls_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_hls_data = LiveCoreSdkPullHlsDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'Hls_index': 1,
    'Hls': '123456789'
  }
  
  try:
    live_core_sdk_pull_hls_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_live_core_sdk_pull_hls_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  live_core_sdk_pull_hls_data = LiveCoreSdkPullHlsDataTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'Hls_index': 1
  }
  
  try:
    record = live_core_sdk_pull_hls_data.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(live_core_sdk_pull_hls_data.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(live_core_sdk_pull_hls_data.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(live_core_sdk_pull_hls_data.get_name(), e))
    raise e

##
## >>================================ live core sdk pull data option table test method ===============================>>
##

def test_create_live_core_sdk_pull_data_option_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  live_core_sdk_pull_data_option_table = LiveCoreSdkPullDataOptionTable(db_instance=db)
  live_core_sdk_pull_data_option_table.create()
  return

##
## test: drop table
##
def test_drop_live_core_sdk_pull_data_option_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  live_core_sdk_pull_data_option_table = LiveCoreSdkPullDataOptionTable(db_instance=db)
  live_core_sdk_pull_data_option_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_live_core_sdk_pull_data_option_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  live_core_sdk_pull_data_option_table = LiveCoreSdkPullDataOptionTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(live_core_sdk_pull_data_option_table.get_name()):
    get_logger().info("{} table exists!".format(live_core_sdk_pull_data_option_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_core_sdk_pull_data_option_table.get_name()))
  return

##
## test: insert record
##
def test_insert_live_core_sdk_pull_data_option_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_data_option = LiveCoreSdkPullDataOptionTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_data_option.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_live_core_sdk_pull_data_option_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_data_option = LiveCoreSdkPullDataOptionTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_data_option.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_live_core_sdk_pull_data_option_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_data_option = LiveCoreSdkPullDataOptionTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'vpass_default': True
  }
  
  try:
    live_core_sdk_pull_data_option.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_live_core_sdk_pull_data_option_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  live_core_sdk_pull_data_option = LiveCoreSdkPullDataOptionTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = live_core_sdk_pull_data_option.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(live_core_sdk_pull_data_option.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(live_core_sdk_pull_data_option.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(live_core_sdk_pull_data_option.get_name(), e))
    raise e

##
## >>================================ live core sdk pull quality data table test method ===============================>>
##

def test_create_live_core_sdk_pull_quality_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  live_core_sdk_pull_quality_data_table = LiveCoreSdkPullQualityDataTable(db_instance=db)
  live_core_sdk_pull_quality_data_table.create()
  return

##
## test: drop table
##
def test_drop_live_core_sdk_pull_quality_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  live_core_sdk_pull_quality_data_table = LiveCoreSdkPullQualityDataTable(db_instance=db)
  live_core_sdk_pull_quality_data_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_live_core_sdk_pull_quality_data_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  live_core_sdk_pull_quality_data_table = LiveCoreSdkPullQualityDataTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(live_core_sdk_pull_quality_data_table.get_name()):
    get_logger().info("{} table exists!".format(live_core_sdk_pull_quality_data_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_core_sdk_pull_quality_data_table.get_name()))
  return

##
## test: insert record
##
def test_insert_live_core_sdk_pull_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_quality_data = LiveCoreSdkPullQualityDataTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'quality_index': 1
  }
  
  try:
    live_core_sdk_pull_quality_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_live_core_sdk_pull_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_quality_data = LiveCoreSdkPullQualityDataTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'quality_index': 1
  }
  
  try:
    live_core_sdk_pull_quality_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_live_core_sdk_pull_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_quality_data = LiveCoreSdkPullQualityDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'quality_index': 1,
    'name': 'Luvvv'
  }
  
  try:
    live_core_sdk_pull_quality_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_live_core_sdk_pull_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  live_core_sdk_pull_quality_data = LiveCoreSdkPullQualityDataTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'start_time': dat.fromtimestamp(1740301577026/1000),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'quality_index': 1
  }
  
  try:
    record = live_core_sdk_pull_quality_data.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(live_core_sdk_pull_quality_data.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(live_core_sdk_pull_quality_data.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(live_core_sdk_pull_quality_data.get_name(), e))
    raise e

##
## >>================================ live core sdk pull default quality data table test method ===============================>>
##

def test_create_live_core_sdk_pull_default_quality_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  live_core_sdk_pull_default_quality_data_table = LiveCoreSdkPullDefaultQualityDataTable(db_instance=db)
  live_core_sdk_pull_default_quality_data_table.create()
  return

##
## test: drop table
##
def test_drop_live_core_sdk_pull_default_quality_data_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  live_core_sdk_pull_default_quality_data_table = LiveCoreSdkPullDefaultQualityDataTable(db_instance=db)
  live_core_sdk_pull_default_quality_data_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_live_core_sdk_pull_default_quality_data_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  live_core_sdk_pull_default_quality_data_table = LiveCoreSdkPullDefaultQualityDataTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(live_core_sdk_pull_default_quality_data_table.get_name()):
    get_logger().info("{} table exists!".format(live_core_sdk_pull_default_quality_data_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(live_core_sdk_pull_default_quality_data_table.get_name()))
  return

##
## test: insert record
##
def test_insert_live_core_sdk_pull_default_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_default_quality_data = LiveCoreSdkPullDefaultQualityDataTable(db_instance=db)

  ##
  ## insert a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_default_quality_data.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_live_core_sdk_pull_default_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_default_quality_data = LiveCoreSdkPullDefaultQualityDataTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    live_core_sdk_pull_default_quality_data.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_live_core_sdk_pull_default_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  live_core_sdk_pull_default_quality_data = LiveCoreSdkPullDefaultQualityDataTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'disable': 0
  }
  
  try:
    live_core_sdk_pull_default_quality_data.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_live_core_sdk_pull_default_quality_data_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  live_core_sdk_pull_default_quality_data = LiveCoreSdkPullDefaultQualityDataTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798'
  }
  
  try:
    record = live_core_sdk_pull_default_quality_data.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(live_core_sdk_pull_default_quality_data.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(live_core_sdk_pull_default_quality_data.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(live_core_sdk_pull_default_quality_data.get_name(), e))
    raise e

##
## >>================================ live core sdk pull default quality data table test method ===============================>>
##

def test_create_stream_push_url_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if db is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table
  ##
  stream_push_url_table = StreamPushUrlTable(db_instance=db)
  stream_push_url_table.create()
  return

##
## test: drop table
##
def test_drop_stream_push_url_table(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## drop table
  ##
  stream_push_url_table = StreamPushUrlTable(db_instance=db)
  stream_push_url_table.drop(confirm=True)
  return

##
## test: check if table exists
##
def test_check_stream_push_url_table_exists(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError

  stream_push_url_table = StreamPushUrlTable(db)

  ##
  ## check if table exists
  ##
  if db.is_table_exist(stream_push_url_table.get_name()):
    get_logger().info("{} table exists!".format(stream_push_url_table.get_name()))
  else:
    get_logger().info("{} table not exists!".format(stream_push_url_table.get_name()))
  return

##
## test: insert record
##
def test_insert_stream_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_push_url = StreamPushUrlTable(db_instance=db)

  ##
  ## insert a sample record
  ## 'push_url_index' auto increment
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_url_id': '691500607505433258',
    'push_url': 'abc'
  }
  
  try:
    stream_push_url.insert_record(sample_record)
    get_logger().info("sample record inserted successfully")
  except Exception as e:
    get_logger().error("failed to insert sample record: {}".format(e))
    raise e

##
## test: delete record
##
def test_delete_stream_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_push_url = StreamPushUrlTable(db_instance=db)

  ##
  ## delete a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_url_id': '691500607505433258',
    'push_url_index': 0
  }
  
  try:
    stream_push_url.delete_record(sample_record)
    get_logger().info("sample record deleted successfully")
  except Exception as e:
    get_logger().error("failed to delete sample record: {}".format(e))
    raise e

##
## test: update record
##
def test_update_stream_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exists
  ##
  stream_push_url = StreamPushUrlTable(db_instance=db)
  
  ##
  ## update a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_url_id': '691500607505433258',
    'push_url_index': 0,
    'push_url': 'TBD'
  }
  
  try:
    stream_push_url.update_record(sample_record)
    get_logger().info("sample record updated successfully")
  except Exception as e:
    get_logger().error("failed to update sample record: {}".format(e))
    raise e

##
## test: get record
## 
def test_get_stream_push_url_record(db:SocialMediaStreamDataBase = None):
  ##
  ## check if database instance is valid
  ##
  if db is None:
    get_logger().error("database instance is None, please provide a valid SocialMediaStreamDataBase instance")
    raise ValueError
  
  ##
  ## create table if not exist
  ##
  stream_push_url = StreamPushUrlTable(db_instance=db)

  ##
  ## get a sample record
  ##
  sample_record = {
    'now': dat.fromtimestamp(1740301577026/1000.0),
    'platform': 'douyin',
    'room_id': '7411524533301119798',
    'stream_url_id': '691500607505433258',
    'push_url_index': 0
  }
  
  try:
    record = stream_push_url.get_record(sample_record)
    if record:
      get_logger().info("sample {} record retrieved successfully: \n\t{}".format(stream_push_url.get_name(), record))
    else:
      get_logger().warning("sample {} record not found".format(stream_push_url.get_name()))
  except Exception as e:
    get_logger().error("failed to retrieve sample {} record: {}".format(stream_push_url.get_name(), e))
    raise e

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='192.168.1.12', user='wangyan', passwd='wuyu1998', database='social_media_stream_downloader')

  ##
  ## live stream table
  ##
  test_create_live_stream_table(db)
  test_check_live_stream_table_exists(db)
  test_insert_live_stream_record(db)
  test_get_live_stream_record(db)
  test_update_live_stream_record(db)
  test_get_live_stream_record(db)
  test_delete_live_stream_record(db)
  test_get_live_stream_record(db)
  test_drop_live_stream_table(db)
  test_check_live_stream_table_exists(db)

  ##
  ## stream candidate resolution
  ##
  test_create_stream_candidate_resolution_table(db)
  test_check_stream_candidate_resolution_table_exists(db)
  test_insert_stream_candidate_resolution_record(db)
  test_get_stream_candidate_resolution_record(db)
  test_update_stream_candidate_resolution_record(db)
  test_get_stream_candidate_resolution_record(db)
  test_delete_stream_candidate_resolution_record(db)
  test_get_stream_candidate_resolution_record(db)
  test_drop_stream_candidate_resolution_table(db)
  test_check_stream_candidate_resolution_table_exists(db)

  ##
  ## stream complete push url table
  ##
  test_create_stream_complete_push_url_table(db)
  test_check_stream_complete_push_url_table_exists(db)
  test_insert_stream_complete_push_url_record(db)
  test_get_stream_complete_push_url_record(db)
  test_update_stream_complete_push_url_record(db)
  test_get_stream_complete_push_url_record(db)
  test_delete_stream_complete_push_url_record(db)
  test_get_stream_complete_push_url_record(db)
  test_drop_stream_complete_push_url_table(db)
  test_check_stream_complete_push_url_table_exists(db)

  ##
  ## live core sdk data table
  ##
  test_create_live_core_sdk_data_table(db)
  test_check_live_core_sdk_data_table_exists(db)
  test_insert_live_core_sdk_data_record(db)
  test_get_live_core_sdk_data_record(db)
  test_update_live_core_sdk_data_record(db)
  test_get_live_core_sdk_data_record(db)
  test_delete_live_core_sdk_data_record(db)
  test_get_live_core_sdk_data_record(db)
  test_drop_live_core_sdk_data_table(db)
  test_check_live_core_sdk_data_table_exists(db)

  ##
  ## live core sdk pull data table
  ##
  test_create_live_core_sdk_pull_data_table(db)
  test_check_live_core_sdk_pull_data_table_exists(db)
  test_insert_live_core_sdk_pull_data_record(db)
  test_get_live_core_sdk_pull_data_record(db)
  test_update_live_core_sdk_pull_data_record(db)
  test_get_live_core_sdk_pull_data_record(db)
  test_delete_live_core_sdk_pull_data_record(db)
  test_get_live_core_sdk_pull_data_record(db)
  test_drop_live_core_sdk_pull_data_table(db)
  test_check_live_core_sdk_pull_data_table_exists(db)

  ##
  ## live core sdk pull flv data table
  ##
  test_create_live_core_sdk_pull_flv_data_table(db)
  test_check_live_core_sdk_pull_flv_data_table_exists(db)
  test_insert_live_core_sdk_pull_flv_data_record(db)
  test_get_live_core_sdk_pull_flv_data_record(db)
  test_update_live_core_sdk_pull_flv_data_record(db)
  test_get_live_core_sdk_pull_flv_data_record(db)
  test_delete_live_core_sdk_pull_flv_data_record(db)
  test_get_live_core_sdk_pull_flv_data_record(db)
  test_drop_live_core_sdk_pull_flv_data_table(db)
  test_check_live_core_sdk_pull_flv_data_table_exists(db)

  ##
  ## live core sdk pull hls data table
  ##
  test_create_live_core_sdk_pull_hls_data_table(db)
  test_check_live_core_sdk_pull_hls_data_table_exists(db)
  test_insert_live_core_sdk_pull_hls_data_record(db)
  test_get_live_core_sdk_pull_hls_data_record(db)
  test_update_live_core_sdk_pull_hls_data_record(db)
  test_get_live_core_sdk_pull_hls_data_record(db)
  test_delete_live_core_sdk_pull_hls_data_record(db)
  test_get_live_core_sdk_pull_hls_data_record(db)
  test_drop_live_core_sdk_pull_hls_data_table(db)
  test_check_live_core_sdk_pull_hls_data_table_exists(db)

  ##
  ## live core sdk pull data option table
  ##
  test_create_live_core_sdk_pull_data_option_table(db)
  test_check_live_core_sdk_pull_data_option_table_exists(db)
  test_insert_live_core_sdk_pull_data_option_record(db)
  test_get_live_core_sdk_pull_data_option_record(db)
  test_update_live_core_sdk_pull_data_option_record(db)
  test_get_live_core_sdk_pull_data_option_record(db)
  test_delete_live_core_sdk_pull_data_option_record(db)
  test_get_live_core_sdk_pull_data_option_record(db)
  test_drop_live_core_sdk_pull_data_option_table(db)
  test_check_live_core_sdk_pull_data_option_table_exists(db)

  ##
  ## live core sdk pull quality data table
  ##
  test_create_live_core_sdk_pull_quality_data_table(db)
  test_check_live_core_sdk_pull_quality_data_table_exists(db)
  test_insert_live_core_sdk_pull_quality_data_record(db)
  test_get_live_core_sdk_pull_quality_data_record(db)
  test_update_live_core_sdk_pull_quality_data_record(db)
  test_get_live_core_sdk_pull_quality_data_record(db)
  test_delete_live_core_sdk_pull_quality_data_record(db)
  test_get_live_core_sdk_pull_quality_data_record(db)
  test_drop_live_core_sdk_pull_quality_data_table(db)
  test_check_live_core_sdk_pull_quality_data_table_exists(db)

  ##
  ## live core sdk pull default quality data table
  ##
  test_create_live_core_sdk_pull_default_quality_data_table(db)
  test_check_live_core_sdk_pull_default_quality_data_table_exists(db)
  test_insert_live_core_sdk_pull_default_quality_data_record(db)
  test_get_live_core_sdk_pull_default_quality_data_record(db)
  test_update_live_core_sdk_pull_default_quality_data_record(db)
  test_get_live_core_sdk_pull_default_quality_data_record(db)
  test_delete_live_core_sdk_pull_default_quality_data_record(db)
  test_get_live_core_sdk_pull_default_quality_data_record(db)
  test_drop_live_core_sdk_pull_default_quality_data_table(db)
  test_check_live_core_sdk_pull_default_quality_data_table_exists(db)

  ##
  ## stream push url table
  ##
  test_create_stream_push_url_table(db)
  test_check_stream_push_url_table_exists(db)
  test_insert_stream_push_url_record(db)
  test_get_stream_push_url_record(db)
  test_update_stream_push_url_record(db)
  test_get_stream_push_url_record(db)
  test_delete_stream_push_url_record(db)
  test_get_stream_push_url_record(db)
  test_drop_stream_push_url_table(db)
  test_check_stream_push_url_table_exists(db)