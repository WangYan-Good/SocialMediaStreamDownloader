##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Third-Part>>
from backend.src.database.social_media_stream_database                import SocialMediaStreamDataBase
from backend.src.database.table.social_media_stream_db_table          import SocialMediaStreamDataTable

##
## room_stats
##
## +-------------------------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------+---------------------+
## | Field                               | Type              | Null | Key | Default | Extra | Topology                                                | Comment             |
## +-------------------------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------+---------------------+
## | now                                 | timestamp(3)      | NO   | PRI |         |       | "$.extra.now"                                           | 当前时间戳           |
## | platform                            | varchar(20)       | NO   | PRI |         |       |           -                                             | 平台                 |
## | room_id                             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                                        | 直播间 ID           |
## | comment_count                       | bigint            | YES  |     | 0       |       | "$.data.room.stats.comment_count"                       | 评论数              |
## | digg_count                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.digg_count"                          | 点赞数              |
## | dou_plus_promotion                  | tinytext          | YES  |     | NULL    |       | "$.data.room.stats.dou_plus_promotion"                  | Dou+ 推广           |
## | enter_count                         | bigint            | YES  |     | 0       |       | "$.data.room.stats.enter_count"                         | 进入数              |
## | fan_ticket                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.fan_ticket"                          | 粉丝票数量          |
## | follow_count                        | bigint            | YES  |     | 0       |       | "$.data.room.stats.follow_count"                        | 关注数              |
## | gift_uv_count                       | int               | YES  |     | 0       |       | "$.data.room.stats.gift_uv_count"                       | 礼物 UV 数          |
## | like_count                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.like_count"                          | 喜欢数              |
## | money                               | bigint            | YES  |     | 0       |       | "$.data.room.stats.money"                               | 金额                |
## | total_user                          | int               | YES  |     | 0       |       | "$.data.room.stats.total_user"                          | 总用户数            |
## | total_user_desp                     | text              | YES  |     | NULL    |       | "$.data.room.stats.total_user_desp"                     | 总用户描述          |
## | total_user_str                      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stats.total_user_str"                      | 总用户字符串        |
## | up_right_stats_str                  | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stats.up_right_stats_str"                  | 右上角统计字符串    |
## | up_right_stats_str_complete         | tinytext          | YES  |     | NULL    |       | "$.data.room.stats.up_right_stats_str_complete"         | 右上角统计完整字符串 |
## | user_count_str                      | varchar(100)      | YES  |     | NULL    |       | "$.data.room.stats.user_count_str"                      | 用户数量字符串      |
## | watermelon                          | bigint            | YES  |     | 0       |       | "$.data.room.stats.watermelon"                          | 西瓜                |
## | welfare_donation_amount             | bigint            | YES  |     | 0       |       | "$.data.room.stats.welfare_donation_amount"             | 福利捐赠金额         |
## | user_count_composition_city         | int               | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.city"         | 城市用户数           |
## | user_count_composition_my_follow    | bigint            | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.my_follow"    | 我的关注用户数       |
## | user_count_composition_other        | bigint            | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.other"        | 其他用户数           |
## | user_count_composition_video_detail | bigint            | YES  |     | 0       |       | "$.data.room.stats.user_count_composition.video_detail" | 视频详情用户数       |
## +-------------------------------------+-------------------+------+-----+---------+-------+---------------------------------------------------------+---------------------+
##
class RoomStatsTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_STATS_TABLE_NAME: str = 'room_stats'
  __ROOM_STATS_TABLE_HEADER: list[str] = [
    'now', 'platform', 'room_id',
    'comment_count', 'digg_count', 'dou_plus_promotion', 'enter_count', 'fan_ticket', 'follow_count',
    'gift_uv_count', 'like_count', 'money', 'total_user', 'total_user_desp', 'total_user_str',
    'up_right_stats_str', 'up_right_stats_str_complete', 'user_count_str', 'watermelon', 'welfare_donation_amount',
    'user_count_composition_city', 'user_count_composition_my_follow', 'user_count_composition_other',
    'user_count_composition_video_detail'
  ]
  __ROOM_STATS_TABLE_PRI_KEY: list[str] = ['now', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT: list[str] = []
  __ROOM_STATS_TABLE_TUPLE: dict[str, None] = {item:None for item in __ROOM_STATS_TABLE_HEADER}
  __SQL_CREATE_ROOM_STATS_TABLE: str = '''
                                   CREATE TABLE IF NOT EXISTS {} (
                                     `now`                               timestamp(3)  NOT NULL,
                                     platform                            varchar(20)   NOT NULL,
                                     room_id                             varchar(200)  NOT NULL,
                                     comment_count                       bigint        DEFAULT 0,
                                     digg_count                          bigint        DEFAULT 0,
                                     dou_plus_promotion                  tinytext      DEFAULT NULL,
                                     enter_count                         bigint        DEFAULT 0,
                                     fan_ticket                          bigint        DEFAULT 0,
                                     follow_count                        bigint        DEFAULT 0,
                                     gift_uv_count                       int           DEFAULT 0,
                                     like_count                          bigint        DEFAULT 0,
                                     money                               bigint        DEFAULT 0,
                                     total_user                          int           DEFAULT 0,
                                     total_user_desp                     text          DEFAULT NULL,
                                     total_user_str                      varchar(100)  DEFAULT NULL,
                                     up_right_stats_str                  varchar(100)  DEFAULT NULL,
                                     up_right_stats_str_complete         tinytext      DEFAULT NULL,
                                     user_count_str                      varchar(100)  DEFAULT NULL,
                                     watermelon                          bigint        DEFAULT 0,
                                     welfare_donation_amount             bigint        DEFAULT 0,
                                     user_count_composition_city         int           DEFAULT 0,
                                     user_count_composition_my_follow    bigint        DEFAULT 0,
                                     user_count_composition_other        bigint        DEFAULT 0,
                                     user_count_composition_video_detail bigint        DEFAULT 0,
                                     PRIMARY KEY (`now`, platform, room_id)
                                   )
                                   '''.format(__ROOM_STATS_TABLE_NAME)
  __SQL_DROP_ROOM_STATS_TABLE: str = 'DROP TABLE IF EXISTS {};'.format(__ROOM_STATS_TABLE_NAME)


##
## >>============================= private method =============================>>
##
  ##
  ## init method
  ##
  def __init__(self, db_instance:SocialMediaStreamDataBase) -> None:
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_STATS_TABLE_NAME

  ##
  ## get table header
  ##
  def get_header(self) -> list[str]:
    return self.__ROOM_STATS_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict[str, None]:
    return self.__ROOM_STATS_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list[str]:
    return self.__ROOM_STATS_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list[str]:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_STATS_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_STATS_TABLE

  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## $.data.room.admin_user_ids
##
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##| Field               | Type              | Null | Key | Default | Extra | Topology                     | Comment             |
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##| platform            | varchar(20)       | NO   | PRI |         |       |           -                  | 平台                 |
##| room_id             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"             | 直播间ID             |
##| index               | unsigned bigint   | NO   | PRI |         |       |           -                  | 直播间管理员ID序号    |
##| admin_user_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.admin_user_ids" | 直播间管理员用户ID    | 
##+---------------------+-------------------+------+-----+---------+-------+------------------------------+---------------------+
##
class RoomAdminUserIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ADMIN_USER_ID_TABLE_NAME       = 'room_admin_user_id'
  __ROOM_ADMIN_USER_ID_TABLE_HEADER     = ['platform',     'room_id',
                                           'index',        'admin_user_id'
                                           ]
  __ROOM_ADMIN_USER_ID_TABLE_PRI_KEY    = ['index', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT                = ['index']
  __ROOM_ADMIN_USER_ID_TABLE_TUPLE      = {item:None for item in __ROOM_ADMIN_USER_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_ADMIN_USER_ID_TABLE = '''
                                          CREATE TABLE IF NOT EXISTS {} (
                                            platform               varchar(20)  NOT NULL,
                                            room_id                varchar(200) NOT NULL,
                                            `index`                bigint       NOT NULL AUTO_INCREMENT,
                                            admin_user_id          varchar(200) DEFAULT NULL,
                                            PRIMARY KEY (`index`, platform, room_id),
                                            UNIQUE KEY unique_record (platform, room_id, admin_user_id)
                                          )
                                          '''.format(__ROOM_ADMIN_USER_ID_TABLE_NAME)
  __SQL_DROP_ROOM_ADMIN_USER_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_ADMIN_USER_ID_TABLE_NAME)


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
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_ADMIN_USER_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_ADMIN_USER_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_ADMIN_USER_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_ADMIN_USER_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_ADMIN_USER_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_ADMIN_USER_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## $.data.room.admin_user_open_ids
##
## +--------------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
## | Field                    | Type              | Null | Key | Default | Extra | Topology                          | Comment             |
## +--------------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
## | platform                 | varchar(20)       | NO   | PRI |         |       |           -                       | 平台                 | 
## | room_id                  | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                  | 直播间ID             |
## | index                    | unsigned bigint   | NO   | PRI |         |       |           -                       | 直播间管理员用户ID序号|
## | admin_user_open_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.admin_user_open_ids" | 直播间管理员用户ID    | 
## +--------------------------+-------------------+------+-----+---------+-------+-----------------------------------+---------------------+
##
class RoomAdminUserOpenIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME       = 'room_admin_user_open_id'
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER     = ['platform',          'room_id',
                                                'index',             'admin_user_open_id'
                                                ]
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY    = ['index', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT                     = ['index']
  __ROOM_ADMIN_USER_OPEN_ID_TABLE_TUPLE      = {item:None for item in __ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER}
  __SQL_CREATE_ROOM_ADMIN_USER_OPEN_ID_TABLE = '''
                                               CREATE TABLE IF NOT EXISTS {} (
                                                 platform                    varchar(20)  NOT NULL,
                                                 room_id                     varchar(200) NOT NULL,
                                                 `index`                     bigint       NOT NULL AUTO_INCREMENT,
                                                 admin_user_open_id          varchar(200) DEFAULT NULL,
                                                 PRIMARY KEY (`index`, platform, room_id),
                                                 UNIQUE KEY unique_record (platform, room_id, admin_user_open_id)
                                               )
                                               '''.format(__ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME)
  __SQL_DROP_ROOM_ADMIN_USER_OPEN_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME)


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
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_ADMIN_USER_OPEN_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_ADMIN_USER_OPEN_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## $.data.room.deco_list
##
## +-------------------+--------------+------+-----+---------+-------+--------------------------------+---------------------+
## | Field             | Type         | Null | Key | Default | Extra | Topology                       | Comment             |
## +-------------------+--------------+------+-----+---------+-------+--------------------------------+---------------------+
## | platform          | varchar(20)   | NO  | PRI |         |       |           -                    | 平台                 | 
## | room_id           | varchar(200) | NO   | PRI |         |       | "$.data.room.id"               | 直播间 ID           |
## | deco_index        | unsigned tinyint | NO | PRI |         |       | -                              | 装饰索引            |
## | deco_id           | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].id"  | 装饰 ID             |
## | deco_type         | unsigned tinyint | YES |  | NULL    |       | "$.data.room.deco_list[x].type"| 装饰类型            |
## | kind              | unsigned tinyint | YES | | NULL    |       | "$.data.room.deco_list[x].kind"| 种类                |
## | audit_text_color  | varchar(7)   | YES  |     | NULL    |       | "$.data.room.deco_list[x].audit_text_color" | 审核文本颜色 |
## | content           | tinytext     | YES  |     | NULL    |       | "$.data.room.deco_list[x].content" | 装饰内容         |
## | status            | unsigned tinyint | YES |  | 0       |       | "$.data.room.deco_list[x].status" | 状态             |
## | text_color        | varchar(7)   | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_color" | 文本颜色       |
## | text_size         | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_size" | 文本大小        |
## | position_x        | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].x"   | X 坐标               |
## | position_y        | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].y"   | Y 坐标               |
## | width             | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].w"   | 宽度                |
## | height            | unsigned int | YES  |     | NULL    |       | "$.data.room.deco_list[x].h"   | 高度                |
## | max_length        | unsigned tinyint | YES | | NULL | | "$.data.room.deco_list[x].max_length" | 最大长度        |
## | sub_type          | unsigned tinyint | YES | | NULL | | "$.data.room.deco_list[x].sub_type" | 子类型          |
## | text_image_adjustable_start_position | unsigned int | YES | | NULL | | "$.data.room.deco_list[x].text_image_adjustable_start_position" | 文本图片可调整开始位置 |
## | text_image_adjustable_end_position | unsigned int | YES | | NULL | | "$.data.room.deco_list[x].text_image_adjustable_end_position" | 文本图片可调整结束位置 |
## | input_rect        | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].input_rect" | 输入框矩形 (JSON) |
## | nine_patch_image  | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].nine_patch_image" | 九宫格图片 (JSON) |
## | reservation       | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].reservation" | 预约信息 (JSON)   |
## | text_font_config  | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_font_config" | 文本字体配置 (JSON) |
## | text_special_effects | json      | YES  |     | NULL    |       | "$.data.room.deco_list[x].text_special_effects" | 文本特效 (JSON) |
## | image_data        | json         | YES  |     | NULL    |       | "$.data.room.deco_list[x].image" | 图片数据 (JSON)   |
## +-------------------+--------------+------+-----+---------+-------+--------------------------------+---------------------+
## 
class RoomDecoTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __ROOM_DECO_TABLE_NAME       = 'room_deco'
  __ROOM_DECO_TABLE_HEADER     = ['platform',                             'room_id',                              'deco_index',                           'deco_id',
                                  'deco_type',                            'kind',                                 'audit_text_color',
                                  'content',                              'status',                               'text_color',
                                  'text_size',                            'position_x',                           'position_y',
                                  'width',                                'height',                               'max_length',
                                  'sub_type',                             'text_image_adjustable_start_position', 'text_image_adjustable_end_position',
                                  'input_rect',                           'nine_patch_image',                     'reservation',
                                  'text_font_config',                     'text_special_effects',                 'image_data'
                                  ]
  __ROOM_DECO_TABLE_PRI_KEY    = ['deco_index', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT       = ['deco_index']
  __ROOM_DECO_TABLE_TUPLE      = {item:None for item in __ROOM_DECO_TABLE_HEADER}
  __SQL_CREATE_ROOM_DECO_TABLE = '''
                                 CREATE TABLE IF NOT EXISTS {} (
                                   platform                             varchar(20)       NOT NULL,
                                   room_id                              varchar(200)      NOT NULL,
                                   deco_index                           tinyint unsigned  NOT NULL AUTO_INCREMENT,
                                   deco_id                              int unsigned      DEFAULT NULL,
                                   deco_type                            tinyint unsigned  DEFAULT NULL,
                                   kind                                 tinyint unsigned  DEFAULT NULL,
                                   audit_text_color                     varchar(7)        DEFAULT NULL,
                                   content                              tinytext          DEFAULT NULL,
                                   status                               tinyint unsigned  DEFAULT NULL,
                                   text_color                           varchar(7)        DEFAULT NULL, 
                                   text_size                            int unsigned      DEFAULT NULL,
                                   position_x                           int unsigned      DEFAULT NULL,
                                   position_y                           int unsigned      DEFAULT NULL,
                                   width                                int unsigned      DEFAULT NULL,
                                   height                               int unsigned      DEFAULT NULL,
                                   max_length                           tinyint unsigned  DEFAULT NULL,
                                   sub_type                             tinyint unsigned  DEFAULT NULL,
                                   text_image_adjustable_start_position int unsigned      DEFAULT NULL,
                                   text_image_adjustable_end_position   int unsigned      DEFAULT NULL,
                                   input_rect                           json              DEFAULT NULL,
                                   nine_patch_image                     json              DEFAULT NULL,
                                   reservation                          json              DEFAULT NULL,
                                   text_font_config                     json              DEFAULT NULL,
                                   text_special_effects                 json              DEFAULT NULL,
                                   image_data                           json              DEFAULT NULL,
                                   PRIMARY KEY (deco_index, platform, room_id),
                                   INDEX idx_deco_type (deco_type)
                                 )
                                 '''.format(__ROOM_DECO_TABLE_NAME)
  __SQL_DROP_ROOM_DECO_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__ROOM_DECO_TABLE_NAME)


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
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__ROOM_DECO_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__ROOM_DECO_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__ROOM_DECO_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__ROOM_DECO_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_ROOM_DECO_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_ROOM_DECO_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## $.data.room.fans_group_admin_user_ids
##
## +--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
## | Field                          | Type              | Null | Key | Default | Extra | Topology                                | Comment             |
## +--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
## | platform                       | varchar(20)       | NO   | PRI |         |       |           -                             | 平台                 |
## | room_id                        | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                        | 直播间ID             | 
## | index                          | unsigned bigint   | NO   | PRI |         |       |           -                             | 粉丝群管理员ID序号   |
## | fans_group_admin_user_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.fans_group_admin_user_ids" | 粉丝群管理员用户ID   |
## +--------------------------------+-------------------+------+-----+---------+-------+-----------------------------------------+---------------------+
##
class FansGroupAdminUserIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __FANS_GROUP_ADMIN_USER_ID_TABLE_NAME       = 'fans_group_admin_user_id'
  __FANS_GROUP_ADMIN_USER_ID_TABLE_HEADER     = ['platform',                'room_id',
                                                 'index',                   'fans_group_admin_user_id'
                                                 ]
  __FANS_GROUP_ADMIN_USER_ID_TABLE_PRI_KEY    = ['index', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT                      = ['index']
  __FANS_GROUP_ADMIN_USER_ID_TABLE_TUPLE      = {item:None for item in __FANS_GROUP_ADMIN_USER_ID_TABLE_HEADER}
  __SQL_CREATE_FANS_GROUP_ADMIN_USER_ID_TABLE = '''
                                                CREATE TABLE IF NOT EXISTS {} (
                                                  platform                          varchar(20)  NOT NULL,
                                                  room_id                           varchar(200) NOT NULL,
                                                  `index`                           bigint       NOT NULL AUTO_INCREMENT,
                                                  fans_group_admin_user_id          varchar(200) DEFAULT NULL,
                                                  PRIMARY KEY (`index`, platform, room_id),
                                                  UNIQUE KEY unique_record (platform, room_id, fans_group_admin_user_id)
                                                )
                                                '''.format(__FANS_GROUP_ADMIN_USER_ID_TABLE_NAME)
  __SQL_DROP_FANS_GROUP_ADMIN_USER_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__FANS_GROUP_ADMIN_USER_ID_TABLE_NAME)


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
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_FANS_GROUP_ADMIN_USER_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_FANS_GROUP_ADMIN_USER_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()

##
## $.data.room.fans_group_admin_user_open_ids
##
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
## | Field                               | Type              | Null | Key | Default | Extra | Topology                                     | Comment              |
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+----------------------+
## | platform                            | varchar(20)       | NO   | PRI |         |       |           -                                  | 平台                  |
## | room_id                             | varchar(200)      | NO   | PRI |         |       | "$.data.room.id"                             | 直播间ID              | 
## | index                               | unsigned bigint   | NO   | PRI |         |       |           -                                  | 粉丝群管理员OpenID序号 |
## | fans_group_admin_user_open_id       | varchar(200)      |      |     | NULL    |       | "$.data.room.fans_group_admin_user_open_ids" | 粉丝群管理员OpenID列表 |
## +-------------------------------------+-------------------+------+-----+---------+-------+----------------------------------------------+-----------------------+
##
class FansGroupAdminUserOpenIdTable(SocialMediaStreamDataTable):
##
## >>=============================== attribute ===============================>>
##
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME       = 'fans_group_admin_user_open_id'
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_HEADER     = ['platform',                     'room_id',
                                                      'index',                        'fans_group_admin_user_open_id'
                                                      ]
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY    = ['index', 'platform', 'room_id']
  __TABLE_AUTO_INCREMENT                           = ['index']
  __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_TUPLE      = {item:None for item in __FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_HEADER}
  __SQL_CREATE_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE = '''
                                                     CREATE TABLE IF NOT EXISTS {} (
                                                       platform                               varchar(20)  NOT NULL,
                                                       room_id                                varchar(200) NOT NULL,
                                                       `index`                                bigint       NOT NULL AUTO_INCREMENT,
                                                       fans_group_admin_user_open_id          varchar(200) DEFAULT NULL,
                                                       PRIMARY KEY (`index`, platform, room_id),
                                                       UNIQUE KEY unique_record (platform, room_id, fans_group_admin_user_open_id)
                                                     )
                                                     '''.format(__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME)
  __SQL_DROP_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE   = 'DROP TABLE IF EXISTS {};'.format(__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME)

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
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(db_instance)
    self._initialized = True

##
## >>============================= abstract method =============================>>
##
  ##
  ## get table name
  ##
  def get_name(self) -> str:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_NAME
  
  ##
  ## get table header
  ##
  def get_header(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_HEADER

  ##
  ## get table tuple
  ##
  def get_tuple(self) -> dict:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_TUPLE

  ##
  ## get table primary key
  ##
  def get_pri_key(self) -> list:
    return self.__FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE_PRI_KEY

  ##
  ## auto increment field
  ##
  def get_auto_increment_field(self) -> list:
    return self.__TABLE_AUTO_INCREMENT

  ##
  ## get SQL command of create table
  ##
  def get_create_sql_cmd(self) -> str:
    return self.__SQL_CREATE_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE

  ##
  ## get SQL command of drop table
  ##
  def get_drop_sql_cmd(self) -> str:
    return self.__SQL_DROP_FANS_GROUP_ADMIN_USER_OPEN_ID_TABLE
  
  ##
  ## verify table schema
  ## TODO
  ##
  def verify_table_schema(self) -> bool:
    return super().verify_table_schema()