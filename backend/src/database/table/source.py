##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## data.room.owner.badge_image_list
## data.user.badge_image_list
##
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
## | Field             | Type             | Null | Key | Default | Extra | Topology                                   | Comment                   |
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
## | start_time        | timestamp        | NO   | PRI |         |       | "$.data.room.start_time"                   | 开始时间                   | 
## | platform          | varchar(20)      | NO   | PRI |         |       |           -                                | 平台                       |
## | room_id           | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                           | 直播间ID                   | 
## | badge_image_index | unsigned bigint  | NO   | PRI |         |       |                                            | 勋章图片索引               |
## | label             | varchar(20)      |      |     | NULL    |       |                                            |                           |
## | uri               | text             |      |     | NULL    |       | "$.data.room.owner.badge_image_list.x.uri" | 统一资源识别符             |
## +-------------------+------------------+------+-----+---------+-------+--------------------------------------------+---------------------------+
##
class BadgeImageTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __BADGE_IMAGE_TABLE_NAME       = 'badge_image'
  __BADGE_IMAGE_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'uri', 'label', 'badge_image_index']
  __BADGE_IMAGE_TABLE_PRI_KEY    = ['badge_image_index']
  __TABLE_AUTO_INCREMENT         = ['badge_image_index']
  __BADGE_IMAGE_TABLE_TUPLE      = {item:None for item in __BADGE_IMAGE_TABLE_HEADER}
  __SQL_CREATE_BADGE_IMAGE_TABLE = '''
                                   CREATE TABLE IF NOT EXISTS {} (
                                     start_time         timestamp    NOT NULL,
                                     platform           varchar(20)  NOT NULL,
                                     room_id            varchar(200) NOT NULL,
                                     badge_image_index  bigint       NOT NULL AUTO_INCREMENT,
                                     label              varchar(20)  DEFAULT NULL,
                                     uri                text         DEFAULT NULL,
                                     PRIMARY KEY (badge_image_index)
                                   )
                                   '''.format(__BADGE_IMAGE_TABLE_NAME)
  __SQL_DROP_BADGE_IMAGE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__BADGE_IMAGE_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__BADGE_IMAGE_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__BADGE_IMAGE_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__BADGE_IMAGE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__BADGE_IMAGE_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_BADGE_IMAGE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_BADGE_IMAGE_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

'''
  TBD: no related data type of pay_grade_icon
'''
##
## data.room.owner.pay_grade.grade_icon_list
##
## +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | Field                | Type              | Null | Key | Default | Extra | Topology                                                 | Comment              |
## +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
## | start_time           | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"                                 | 开始时间              | 
## | platform             | varchar(20)       | NO   | PRI |         |       |           -                                              | 平台                  |
## | room_id              | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                         | 直播间ID              | 
## | owner_user_id        | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                              | 账号作者ID            |
## | pay_grade_icon_index | unsigned bigint   | NO   | PRI |         |       |           -                                              | 索引号               |
## | pay_grade_icon       | TBD               |      |     | NULL    |       | "$.data.room.owner.pay_grade.grade_icon_list"            | 付费等级图标列表      |
## +----------------------+-------------------+------+-----+---------+-------+----------------------------------------------------------+----------------------+
##
class PayGradeIconTable(SocialMediaStreamDataTable):
  pass
"""
##
## >>=============================== attribute ===============================>>
##
  __PAY_GRADE_ICON_TABLE_NAME       = 'pay_grade_icon'
  __PAY_GRADE_ICON_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'owner_user_id', 'uri', 'version', 'pay_grade_icon_index', 'pay_grade_icon']
  __PAY_GRADE_ICON_TABLE_PRI_KEY    = ['pay_grade_icon_index']
  __TABLE_AUTO_INCREMENT            = ['pay_grade_icon_index']
  __PAY_GRADE_ICON_TABLE_TUPLE      = {item:None for item in __PAY_GRADE_ICON_TABLE_HEADER}
  __SQL_CREATE_PAY_GRADE_ICON_TABLE = '''
                                   CREATE TABLE IF NOT EXISTS {} (
                                     start_time         timestamp    NOT NULL,
                                     platform           varchar(20)  NOT NULL,
                                     room_id            varchar(200) NOT NULL,
                                     owner_user_id      varchar(200) NOT NULL,
                                     pay_grade_icon_index  bigint    NOT NULL AUTO_INCREMENT,
                                     version            varchar(20)  DEFAULT NULL,
                                     uri                text         DEFAULT NULL,
                                     pay_grade_icon     TBD          DEFAULT NULL,
                                     PRIMARY KEY (pay_grade_icon_index)
                                   )
                                   '''.format(__PAY_GRADE_ICON_TABLE_NAME)
  __SQL_DROP_PAY_GRADE_ICON_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__PAY_GRADE_ICON_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__PAY_GRADE_ICON_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__PAY_GRADE_ICON_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__PAY_GRADE_ICON_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__PAY_GRADE_ICON_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_PAY_GRADE_ICON_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_PAY_GRADE_ICON_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()
  """

##
## data.room.owner.user_dress_info.dress_own_ids
##
## +-----------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
## | Field           | Type              | Null | Key | Default | Extra | Topology                                          | Comment             |
## +-----------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
## | start_time      | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"                          | 开始时间             | 
## | platform        | varchar(20)       | NO   | PRI |         |       |           -                                       | 平台                 | 
## | room_id         | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                  | 直播间ID             | 
## | owner_user_id   | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                       | 直播间主播ID         |
## | dress_own_index | unsigned bigint   | NO   | PRI |         |       |           -                                       | 用户拥有的着装序号   | 
## | dress_own_id    | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.user_dress_info.dress_own_ids" | 用户拥有的着装ID     |
## +-----------------+-------------------+------+-----+---------+-------+---------------------------------------------------+---------------------+
##
class RoomOwnerUserDressOwnIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_NAME       = 'room_owner_user_dress_own_id'
  __ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'owner_user_id', 'dress_own_index', 'dress_own_id']
  __ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_PRI_KEY    = ['dress_own_index']
  __TABLE_AUTO_INCREMENT                          = ['dress_own_index']
  __ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_TUPLE      = {item:None for item in __ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_USER_DRESS_OWN_ID_TABLE = '''
                                                    CREATE TABLE IF NOT EXISTS {} (
                                                      start_time         timestamp     NOT NULL,
                                                      platform           varchar(20)   NOT NULL,
                                                      room_id            varchar(200)  NOT NULL,
                                                      owner_user_id      varchar(200)  NOT NULL,
                                                      dress_own_index    bigint        NOT NULL AUTO_INCREMENT,
                                                      dress_own_id       varchar(200)  DEFAULT NULL,
                                                      PRIMARY KEY (dress_own_index),
                                                      UNIQUE KEY unique_record (start_time, platform, room_id, owner_user_id, dress_own_id)
                                                    )
                                                    '''.format(__ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_NAME)
  __SQL_DROP_ROOM_OWNER_USER_DRESS_OWN_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_USER_DRESS_OWN_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_USER_DRESS_OWN_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_OWNER_USER_DRESS_OWN_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.user_dress_info.dress_wear_ids
##
## +------------------+-------------------+------+-----+---------+-------+----------------------------------------------------+---------------------+
## | Field            | Type              | Null | Key | Default | Extra | Topology                                           | Comment             |
## +------------------+-------------------+------+-----+---------+-------+----------------------------------------------------+---------------------+
## | start_time       | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"                           | 开始时间             | 
## | platform         | varchar(20)       | NO   | PRI |         |       |           -                                        | 平台                 | 
## | room_id          | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                   | 直播间ID             | 
## | owner_user_id    | varchar(200)      | NO   | PRI |         |       | "$.data.room.owner_user_id"                        | 直播间主播ID         |
## | dress_wear_index | unsigned bigint   | NO   | PRI |         |       |           -                                        | 用户穿戴的着装序号   | 
## | dress_wear_id    | varchar(200)      |      |     | NULL    |       | "$.data.room.owner.user_dress_info.dress_wear_ids" | 用户穿戴的着装ID     |
## +------------------+-------------------+------+-----+---------+-------+----------------------------------------------------+---------------------+
##
class RoomOwnerDressWearIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_OWNER_DRESS_WEAR_ID_TABLE_NAME       = 'room_owner_dress_wear_id'
  __ROOM_OWNER_DRESS_WEAR_ID_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'owner_user_id', 'dress_wear_index', 'dress_wear_id']
  __ROOM_OWNER_DRESS_WEAR_ID_TABLE_PRI_KEY    = ['dress_wear_index']
  __TABLE_AUTO_INCREMENT                      = ['dress_wear_index']
  __ROOM_OWNER_DRESS_WEAR_ID_TABLE_TUPLE      = {item:None for item in __ROOM_OWNER_DRESS_WEAR_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_OWNER_DRESS_WEAR_ID_TABLE = '''
                                                CREATE TABLE IF NOT EXISTS {} (
                                                  start_time         timestamp     NOT NULL,
                                                  platform           varchar(20)   NOT NULL,
                                                  room_id            varchar(200)  NOT NULL,
                                                  owner_user_id      varchar(200)  NOT NULL,
                                                  dress_wear_index   bigint        NOT NULL AUTO_INCREMENT,
                                                  dress_wear_id      varchar(200)  DEFAULT NULL,
                                                  PRIMARY KEY (dress_wear_index),
                                                  UNIQUE KEY unique_record (start_time, platform, room_id, owner_user_id, dress_wear_id)
                                                )
                                                '''.format(__ROOM_OWNER_DRESS_WEAR_ID_TABLE_NAME)
  __SQL_DROP_ROOM_OWNER_DRESS_WEAR_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_OWNER_DRESS_WEAR_ID_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_OWNER_DRESS_WEAR_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_OWNER_DRESS_WEAR_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_OWNER_DRESS_WEAR_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_OWNER_DRESS_WEAR_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_OWNER_DRESS_WEAR_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_OWNER_DRESS_WEAR_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.sharing_music_id_list
##
## +---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
## | Field               | Type             | Null | Key | Default | Extra | Topology                            | Comment              |
## +---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
## | start_time          | timestamp        | NO   | PRI |         |       | "$.data.room.start_time"            | 开始时间              | 
## | platform            | varchar(20)      | NO   | PRI |         |       |           -                         | 平台                  |
## | room_id             | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                    | 直播间ID              | 
## | sharing_music_index | unsigned bigint  | NO   | PRI |         |       |           -                         | 分享音乐ID序号        |
## | sharing_music_id    | varchar(200)     |      |     | NULL    |       | "$.data.room.sharing_music_id_list" | 分享音乐ID            | 
## +---------------------+------------------+------+-----+---------+-------+-------------------------------------+----------------------+
##
class RoomSharingMusicIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_SHARING_MUSIC_ID_TABLE_NAME       = 'room_sharing_music_id'
  __ROOM_SHARING_MUSIC_ID_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'sharing_music_index', 'sharing_music_id']
  __ROOM_SHARING_MUSIC_ID_TABLE_PRI_KEY    = ['sharing_music_index']
  __TABLE_AUTO_INCREMENT                   = ['sharing_music_index']
  __ROOM_SHARING_MUSIC_ID_TABLE_TUPLE      = {item:None for item in __ROOM_SHARING_MUSIC_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_SHARING_MUSIC_ID_TABLE = '''
                                              CREATE TABLE IF NOT EXISTS {} (
                                                start_time          timestamp     NOT NULL,
                                                platform            varchar(20)   NOT NULL,
                                                room_id             varchar(200)  NOT NULL,
                                                sharing_music_index bigint        NOT NULL AUTO_INCREMENT,
                                                sharing_music_id    varchar(200)  DEFAULT NULL,
                                                PRIMARY KEY (sharing_music_index),
                                                UNIQUE KEY unique_record (start_time, platform, room_id, sharing_music_id)
                                              )
                                              '''.format(__ROOM_SHARING_MUSIC_ID_TABLE_NAME)
  __SQL_DROP_ROOM_SHARING_MUSIC_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_SHARING_MUSIC_ID_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton pattern
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_SHARING_MUSIC_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_SHARING_MUSIC_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_SHARING_MUSIC_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_SHARING_MUSIC_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_SHARING_MUSIC_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_SHARING_MUSIC_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## picture
##
## +--------------+------------------+------+-----+---------+-------+-----------------------------------------+---------------------------+
## | Field        | Type             | Null | Key | Default | Extra | Topology                                | Comment                   |
## +--------------+------------------+------+-----+---------+-------+-----------------------------------------+---------------------------+
## | start_time   | timestamp        | NO   | PRI |         |       | "$.data.room.start_time"                | 开始时间                   | 
## | platform     | varchar(20)      | NO   | PRI |         |       |           -                             | 平台                       |
## | room_id      | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                        | 直播间ID                   | 
## | picture_index| unsigned bigint  | NO   | PRI |         |       | -                                       | 图片索引                   |
## | label        | varchar(50)      |      |     |         |       | -                                       | 图片标签                   |
## | avg_color    | varchar(7)       |      |     |         |       | "$.data.room.guide_button.avg_color"    | 平均颜色                   |
## | height       | unsigned int     |      |     |         |       | "$.data.room.guide_button.height"       | 高度                       |
## | image_type   | unsigned tinyint |      |     |         |       | "$.data.room.guide_button.image_type"   | 图片类型                   |
## | is_animated  | bool             |      |     |         |       | "$.data.room.guide_button.is_animated"  | 是否为动画                 |
## | open_web_url | text             |      |     |         |       | "$.data.room.guide_button.open_web_url" | 开放网页URL                |
## | uri          | text             |      |     |         |       | "$.data.room.guide_button.uri"          | 统一资源识别符             |
## | width        | unsigned int     |      |     |         |       | "$.data.room.guide_button.width"        | 宽度                      |
## +--------------+------------------+------+-----+---------+-------+-----------------------------------------+---------------------------+
##
class PictureTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __PICTURE_TABLE_NAME       = "picture"
  __PICTURE_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'picture_index', 'label', 'avg_color', 'height', 'image_type', 'is_animated', 'open_web_url', 'uri', 'width']
  __PICTURE_TABLE_PRI_KEY    = ['picture_index']
  __TABLE_AUTO_INCREMENT     = ['picture_index']
  __PICTURE_TABLE_TUPLE      = {item:None for item in __PICTURE_TABLE_HEADER}
  __SQL_CREATE_PICTURE_TABLE = '''
                               CREATE TABLE IF NOT EXISTS {} (
                                 start_time                      timestamp        NOT NULL,
                                 platform                        varchar(20)      NOT NULL,
                                 room_id                         varchar(200)     NOT NULL,
                                 picture_index                   bigint           NOT NULL AUTO_INCREMENT,
                                 label                           varchar(50)      DEFAULT NULL,
                                 avg_color                       varchar(7)       DEFAULT NULL,
                                 height                          int              DEFAULT NULL,
                                 image_type                      tinyint          DEFAULT NULL,
                                 is_animated                     bool             DEFAULT NULL,
                                 open_web_url                    text             DEFAULT NULL,
                                 uri                             text             DEFAULT NULL,
                                 width                           int              DEFAULT NULL,
                                 PRIMARY KEY (picture_index)
                               )
                               '''.format(__PICTURE_TABLE_NAME)
  __SQL_DROP_PICTURE_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__PICTURE_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__PICTURE_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__PICTURE_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__PICTURE_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__PICTURE_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_PICTURE_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_PICTURE_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## picture_flex_setting
##
## +--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
## | Field              | Type             | Null | Key | Default | Extra | Topology                                     | Comment                   |
## +--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
## | start_time         | timestamp        | NO   | PRI |         |       | "$.data.room.start_time"                     | 开始时间                   | 
## | platform           | varchar(20)      | NO   | PRI |         |       |           -                                  | 平台                       |
## | room_id            | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                             | 直播间ID                   | 
## | label              | varchar(50)      |      |     |         |       | -                                            | 图片标签                   |
## | uri                | text             |      |     | NULL    |       | "$.data.room.guide_button.uri"               | 统一资源识别符             |
## | flex_setting_index | unsigned bigint  | NO   | PRI |         |       | -                                            | 弹性设置序号               |
## | flex_setting       | tinytext         |      |     | NULL    |       | "$.data.room.guide_button.flex_setting_list" | 弹性设置                   |
## +--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
##
class PictureFlexSettingTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __PICTURE_FLEX_SETTING_TABLE_NAME       = "picture_flex_setting"
  __PICTURE_FLEX_SETTING_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'label', 'uri', 'flex_setting_index', 'flex_setting']
  __PICTURE_FLEX_SETTING_TABLE_PRI_KEY    = ['flex_setting_index']
  __TABLE_AUTO_INCREMENT                  = ['flex_setting_index']
  __PICTURE_FLEX_SETTING_TABLE_TUPLE      = {item:None for item in __PICTURE_FLEX_SETTING_TABLE_HEADER}
  __SQL_CREATE_PICTURE_FLEX_SETTING_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              start_time                      timestamp        NOT NULL,
                                              platform                        varchar(20)      NOT NULL,
                                              room_id                         varchar(200)     NOT NULL,
                                              label                           varchar(50)      DEFAULT NULL,
                                              uri                             text             DEFAULT NULL,
                                              flex_setting_index              bigint           NOT NULL AUTO_INCREMENT,
                                              flex_setting                    tinytext         DEFAULT NULL,
                                              PRIMARY KEY (flex_setting_index)
                                            )
                                            '''.format(__PICTURE_FLEX_SETTING_TABLE_NAME)
  __SQL_DROP_PICTURE_FLEX_SETTING_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__PICTURE_FLEX_SETTING_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__PICTURE_FLEX_SETTING_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__PICTURE_FLEX_SETTING_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__PICTURE_FLEX_SETTING_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__PICTURE_FLEX_SETTING_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_PICTURE_FLEX_SETTING_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_PICTURE_FLEX_SETTING_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## picture_text_setting
##
## +--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
## | Field              | Type             | Null | Key | Default | Extra | Topology                                     | Comment                   |
## +--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
## | start_time         | timestamp        | NO   | PRI |         |       | "$.data.room.start_time"                     | 开始时间                   | 
## | platform           | varchar(20)      | NO   | PRI |         |       |           -                                  | 平台                       |
## | room_id            | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                             | 直播间ID                   | 
## | label              | varchar(50)      |      |     |         |       | -                                            | 图片标签                   |
## | uri                | text             |      |     | NULL    |       | "$.data.room.guide_button.uri"               | 统一资源识别符             |
## | text_setting_index | unsigned bigint  | NO   | PRI |         |       | -                                            | 文本设置序号               |
## | text_setting       | tinytext         |      |     | NULL    |       | "$.data.room.guide_button.text_setting_list" | 文本设置                   |
## +--------------------+------------------+------+-----+---------+-------+----------------------------------------------+---------------------------+
##
class PictureTextSettingTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __PICTURE_TEXT_SETTING_TABLE_NAME       = "picture_text_setting"
  __PICTURE_TEXT_SETTING_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'label', 'uri', 'text_setting_index', 'text_setting']
  __PICTURE_TEXT_SETTING_TABLE_PRI_KEY    = ['text_setting_index']
  __TABLE_AUTO_INCREMENT                  = ['text_setting_index']
  __PICTURE_TEXT_SETTING_TABLE_TUPLE      = {item:None for item in __PICTURE_TEXT_SETTING_TABLE_HEADER}
  __SQL_CREATE_PICTURE_TEXT_SETTING_TABLE = '''
                                            CREATE TABLE IF NOT EXISTS {} (
                                              start_time                      timestamp        NOT NULL,
                                              platform                        varchar(20)      NOT NULL,
                                              room_id                         varchar(200)     NOT NULL,
                                              label                           varchar(50)      DEFAULT NULL,
                                              uri                             text             DEFAULT NULL,
                                              text_setting_index              bigint           NOT NULL AUTO_INCREMENT,
                                              text_setting                    tinytext         DEFAULT NULL,
                                              PRIMARY KEY (text_setting_index)
                                            )
                                            '''.format(__PICTURE_TEXT_SETTING_TABLE_NAME)
  __SQL_DROP_PICTURE_TEXT_SETTING_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__PICTURE_TEXT_SETTING_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__PICTURE_TEXT_SETTING_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__PICTURE_TEXT_SETTING_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__PICTURE_TEXT_SETTING_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__PICTURE_TEXT_SETTING_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_PICTURE_TEXT_SETTING_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_PICTURE_TEXT_SETTING_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## picture_url
##
## +-------------+------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
## | Field       | Type             | Null | Key | Default | Extra | Topology                            | Comment                   |
## +-------------+------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
## | start_time  | timestamp        | NO   | PRI |         |       | "$.data.room.start_time"            | 开始时间                   | 
## | platform    | varchar(20)      | NO   | PRI |         |       |           -                         | 平台                       |
## | room_id     | varchar(200)     | NO   | PRI |         |       | "$.data.room.id"                    | 直播间ID                   | 
## | label       | varchar(50)      |      |     |         |       | -                                   | 图片标签                   |
## | uri         | text             |      |     | NULL    |       | "$.data.room.guide_button.uri"      | 统一资源识别符             |
## | url_index   | unsigned bigint  | NO   | PRI |         |       | -                                   | url索引号                 |
## | url         | text             |      |     | NULL    |       | "$.data.room.guide_button.url_list" | url                       |
## +-------------+------------------+------+-----+---------+-------+-------------------------------------+---------------------------+
##
class PictureUrlTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __PICTURE_URL_TABLE_NAME       = "picture_url"
  __PICTURE_URL_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'label', 'uri', 'url_index', 'url']
  __PICTURE_URL_TABLE_PRI_KEY    = ['url_index']
  __TABLE_AUTO_INCREMENT         = ['url_index']
  __PICTURE_URL_TABLE_TUPLE      = {item:None for item in __PICTURE_URL_TABLE_HEADER}
  __SQL_CREATE_PICTURE_URL_TABLE = '''
                                   CREATE TABLE IF NOT EXISTS {} (
                                     start_time                      timestamp        NOT NULL,
                                     platform                        varchar(20)      NOT NULL,
                                     room_id                         varchar(200)     NOT NULL,
                                     label                           varchar(50)      DEFAULT NULL,
                                     uri                             text             DEFAULT NULL,
                                     url_index                       bigint           NOT NULL AUTO_INCREMENT,
                                     url                             text             DEFAULT NULL,
                                     PRIMARY KEY (url_index)
                                   )
                                   '''.format(__PICTURE_URL_TABLE_NAME)
  __SQL_DROP_PICTURE_URL_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__PICTURE_URL_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__PICTURE_URL_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__PICTURE_URL_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__PICTURE_URL_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__PICTURE_URL_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_PICTURE_URL_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_PICTURE_URL_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## data.room.owner.badge_image_list.content
##
## +------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------------+---------------------------+
## | Field            | Type              | Null | Key | Default | Extra | Topology                                                      | Comment                   |
## +------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------------+---------------------------+
## | start_time       | timestamp         | NO   | PRI |         |       | "$.data.room.start_time"                                      | 开始时间                   | 
## | platform         | varchar(20)       | NO   | PRI |         |       |           -                                                   | 平台                       |
## | room_id          | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                              | 直播间ID                   | 
## | uri_index        | unsigned bigint   | NO   | PRI |         |       |                      -                                        | 统一资源识别符索引          |
## | label            | varchar(50)       |      |     |         |       | -                                                             | 图片标签                   |
## | uri              | text              |      |     | NULL    |       | "$.data.room.owner.badge_image_list.uri"                      | 统一资源识别符             |
## | alternative_text | text              |      |     | NULL    |       | "$.data.room.owner.badge_image_list.content.alternative_text" | 替代文本                  |
## | font_color       | varchar(7)        |      |     | NULL    |       | "$.data.room.owner.badge_image_list.content.font_color"       | 字体颜色                  |
## | level            | unsigned smallint |      |     | NULL    |       | "$.data.room.owner.badge_image_list.content.level"            | 等级                      |
## | name             | varchar(50)       |      |     | NULL    |       | "$.data.room.owner.badge_image_list.content.name"             | 名称                      |
## +------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------------+---------------------------+
##
class PictureContentTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __PICTURE_CONTENT_TABLE_NAME       = "picture_content"
  __PICTURE_CONTENT_TABLE_HEADER     = ['start_time', 'platform', 'room_id', 'uri_index', 'label', 'uri', 'alternative_text', 'font_color', 'level', 'name']
  __PICTURE_CONTENT_TABLE_PRI_KEY    = ['uri_index']
  __TABLE_AUTO_INCREMENT             = ['uri_index']
  __PICTURE_CONTENT_TABLE_TUPLE      = {item:None for item in __PICTURE_CONTENT_TABLE_HEADER}
  __SQL_CREATE_PICTURE_CONTENT_TABLE = '''
                                       CREATE TABLE IF NOT EXISTS {} (
                                         start_time                      timestamp        NOT NULL,
                                         platform                        varchar(20)      NOT NULL,
                                         room_id                         varchar(200)     NOT NULL,
                                         uri_index                       bigint           NOT NULL AUTO_INCREMENT,
                                         label                           varchar(50)      DEFAULT NULL,
                                         uri                             text             DEFAULT NULL,
                                         alternative_text                text             DEFAULT NULL,
                                         font_color                      varchar(7)       DEFAULT NULL,
                                         level                           smallint         DEFAULT NULL,
                                         name                            varchar(50)      DEFAULT NULL,
                                         PRIMARY KEY (uri_index)
                                       )
                                       '''.format(__PICTURE_CONTENT_TABLE_NAME)
  __SQL_DROP_PICTURE_CONTENT_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__PICTURE_CONTENT_TABLE_NAME)

##
## >>============================= private method =============================>>
##
  ##
  ## singleton mode
  ##
  def __new__(cls, *args, **kwargs):
    return super().__new__(cls, *args, **kwargs)

  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase = None) -> None:
    super().__init__(db_instance)

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__PICTURE_CONTENT_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__PICTURE_CONTENT_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__PICTURE_CONTENT_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__PICTURE_CONTENT_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_PICTURE_CONTENT_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_PICTURE_CONTENT_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()
