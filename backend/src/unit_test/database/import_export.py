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

## <<Third-Part>>
from backend.src.library.baselib                                      import   load_yml, get_dict_attr, set_dict_attr
from backend.src.database.social_media_stream_database                import   SocialMediaStreamDataBase
from backend.src.database.table.table_import                          import   import_douyin_live_info_to_database
from backend.src.database.table.table_export                          import   export_live_info_to_yml

##
## >>================================ table agent test method ===============================>>
##
def test_import_live_info_to_database(db: SocialMediaStreamDataBase, input_path: str) -> None:
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
  
def test_export_live_info_to_yml(db: SocialMediaStreamDataBase, output_path: str) -> None:
  
  ##
  ## parse living data
  ##
  living_data = dict()
  set_dict_attr(living_data, "$.data.room.owner_user_id", 2700838411446480,     force=True)
  set_dict_attr(living_data, "$.data.room.id",            7362550606306773794,  force=True)
  
  ##
  ## export living data to database
  ##
  export_live_info_to_yml(db, living_data, output_path)

if __name__ == "__main__":
  db = SocialMediaStreamDataBase(host='localhost', user='wangyan', passwd='wuyu1998', database='test_social_media_stream_downloader')
  input_path = './docs/design/Lvuuu.yml'
  output_path = './config/export/Lvuuu.yml'
  # test_import_live_info_to_database(db, input_path)
  test_export_live_info_to_yml(db, output_path)