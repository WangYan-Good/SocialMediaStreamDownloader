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
  
  ##
  ## parse living data
  ##
  living_data = get_dict_attr(data, "$.external_info")
  
  ##
  ## import living data to database
  ##
  import_douyin_live_info_to_database(db, living_data)
  
  ##
  ## return identifier
  ##
  identifier = dict()
  set_dict_attr(identifier, "$.data.room.owner_user_id", get_dict_attr(living_data, "$.data.room.owner_user_id"),     force=True)
  set_dict_attr(identifier, "$.data.room.id",            get_dict_attr(living_data, "$.data.room.id"),                force=True)
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
  db = SocialMediaStreamDataBase(host='localhost', user='admin', passwd='admin', database='social_media_stream_downloader')
  
  ##
  ## text single file
  ##
  # file = '西瓜皮_2.yml'
  # identifier = test_import_live_info_to_database(db, f'./config/build/douyin/live/{file}')
  # export_live_info_to_yml(db, identifier, f"./config/export/{file}")

  ##
  ## read all yml import files
  ## config/build/douyin/live
  ##
  input_path_list = glob.glob(os.path.join('./config/build/douyin/live', "*.yml"))
  for input_path in input_path_list:
    ##
    ## 获取文件名（不含扩展名）作为缓存变量名
    ##
    file_name = os.path.basename(input_path)
    cache_key = os.path.splitext(file_name)[0]  # 去掉 .yml 后缀

    identifier = test_import_live_info_to_database(db, input_path)
    get_logger().info(f"{input_path} import succeed")
    export_live_info_to_yml(db, identifier, f"./config/export/{file_name}")
    get_logger().info(f"{file_name}  export succeed")