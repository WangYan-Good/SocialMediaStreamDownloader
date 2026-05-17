##
## import_export.py
## This module handles the table of the Social Media Stream Downloader (SMSD) database.
## It provides a data operation of table level in social_media_stream_downloader.
## Its operation includes import / export
##

##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from pathlib                                                          import   Path
import                                                                         glob

## <<Third-Part>>
from backend.src.library.baselib                                      import   load_yml, get_dict_attr, set_dict_attr, get_logger
from backend.src.database.social_media_stream_database                import   SocialMediaStreamDataBase
from backend.src.unit_test.test_db_config                             import   get_test_db_config
from backend.src.database.table.table_import                          import   import_douyin_live_info_to_database
from backend.src.database.table.table_export                          import   export_live_info_to_yml

##
## >>================================ table agent test method ===============================>>
##
def test_import_live_info_to_database(db: SocialMediaStreamDataBase, input_path: str) -> dict:
  ##
  ## load yml file
  ##
  data = load_yml(Path(input_path))
  if isinstance(data, dict) is False:
    raise ValueError(f"invalid yml root type: {type(data)}")
  
  ##
  ## parse living data
  ##
  living_data = get_dict_attr(data, "$.external_info")
  if isinstance(living_data, dict) is False:
    raise ValueError("missing or invalid $.external_info")

  room_id = get_dict_attr(living_data, "$.data.room.id")
  owner_user_id = get_dict_attr(living_data, "$.data.room.owner_user_id")
  start_time = get_dict_attr(living_data, "$.data.room.start_time")
  now = get_dict_attr(living_data, "$.extra.now")
  if room_id is None or owner_user_id is None:
    raise ValueError(f"missing required fields room.id/owner_user_id: room_id={room_id}, owner_user_id={owner_user_id}")
  
  ##
  ## import living data to database
  ##
  import_douyin_live_info_to_database(db, living_data)
  
  ##
  ## return identifier
  ##
  identifier = dict()
  set_dict_attr(identifier, "$.data.room.owner_user_id", owner_user_id, force=True)
  set_dict_attr(identifier, "$.data.room.id",            room_id,       force=True)
  set_dict_attr(identifier, "$.data.room.start_time",    start_time,    force=True)
  set_dict_attr(identifier, "$.extra.now",               now,           force=True)
  set_dict_attr(identifier, "$.import_locator.now",           now,                      force=True)
  set_dict_attr(identifier, "$.import_locator.platform",      "douyin",                 force=True)
  set_dict_attr(identifier, "$.import_locator.room_id",       str(room_id),               force=True)
  set_dict_attr(identifier, "$.import_locator.owner_user_id", str(owner_user_id),         force=True)
  set_dict_attr(identifier, "$.import_locator.start_time",    start_time if start_time is not None else 0, force=True)
  return identifier
  
def test_export_live_info_to_yml(db: SocialMediaStreamDataBase, output_path: str) -> None:
  
  ##
  ## parse living data
  ##
  living_data = dict()
  set_dict_attr(living_data, "$.data.room.owner_user_id", 58859666123,     force=True)
  set_dict_attr(living_data, "$.data.room.id",            7342521940575374106,  force=True)
  
  ##
  ## export living data to database
  ##
  export_live_info_to_yml(db, living_data, output_path)

if __name__ == "__main__":
  db = SocialMediaStreamDataBase(**get_test_db_config())

  imported_count = 0
  exported_count = 0
  failed_count = 0
  failed_files: list[str] = []
  
  ##
  ## text single file
  ##
  # file = '一汽_大众菏泽众志新能源.yml'
  # identifier = test_import_live_info_to_database(db, f'./config/build/douyin/live/{file}')
  # export_live_info_to_yml(db, identifier, f"./config/export/{file}")

  ##
  ## read all yml import files
  ## config/build/douyin/live
  ##
  input_path_list = sorted(glob.glob(os.path.join('./config/build/douyin/live', "*.yml")))
  for input_path in input_path_list:
    ##
    ## 获取文件名（不含扩展名）作为缓存变量名
    ##
    file_name = os.path.basename(input_path)
    get_logger().info(f"start to import {input_path} to database...")
    try:
      identifier = test_import_live_info_to_database(db, input_path)
      imported_count += 1
      get_logger().info(f"{input_path} import succeed")

      output_path = f"./config/export/{file_name}"
      export_live_info_to_yml(db, identifier, output_path)
      exported_count += 1
      get_logger().info(f"{file_name} export succeed")
    except Exception as e:
      failed_count += 1
      failed_files.append(file_name)
      get_logger().error(f"failed to process {input_path}: {e}")

  get_logger().info(
    "import summary: total=%s imported=%s exported=%s failed=%s",
    len(input_path_list),
    imported_count,
    exported_count,
    failed_count,
  )
  if failed_files:
    get_logger().warning("failed files: %s", ", ".join(failed_files))