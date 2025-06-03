##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
from logging import debug, info, warning, error

## <<Extension>>

## <<Third-Part>>
from backend.src.database.social_media_stream_database import SocialMediaStreamDataBase
from backend.src.database.favorite_owner               import FavoriteOwnerTable
from backend.src.base.log                              import get_logger


class DouyinShareUrlTable(SocialMediaStreamDataBase):
##
## >>============================= attribute =============================>>
##

##
## douyin share url table header
## +---------------+-------------+-----------+----------------+----------------+----------------+-------------+---------------+
## | owner_user_id | sec_user_id | nickname  | post_share_url | live_share_url | directory_name | user_status | actived_count |
## +---------------+-------------+-----------+----------------+----------------+----------------+-------------+---------------+
##
  __DOUYIN_SHARE_URL_TABLE_NAME   = 'share_url'
  __DOUYIN_SHARE_URL_TABLE_HEADER = ['owner_user_id', 'sec_user_id', 'nickname', 'post_share_url', 'live_share_url', 'directory_name', 'user_status', 'actived_count']
  __DOUYIN_SHARE_URL_TABLE_TUPLE  = {item:None for item in __DOUYIN_SHARE_URL_TABLE_HEADER}
  __SQL_DROP_SHARE_URL_TABLE      = '''
                                    DROP TABLE share_url;
                                  '''
  __SQL_CREATE_SHARE_URL_TABLE    = '''
                                    CREATE TABLE share_url (
                                      sec_user_id       CHAR(200) NOT NULL PRIMARY KEY,
                                      nickname          CHAR(20),
                                      post_share_url    CHAR(100),
                                      live_share_url    CHAR(100),
                                      directory_name    CHAR(100),
                                      user_status       CHAR(100)
                                    )
                                  '''
##
## >>============================= private method =============================>>
##
  def __init__(self, host:str, user:str, passwd:str, database:str):
    super().__init__(host, user, passwd, database)

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##
  ##
  ## get share url table name
  ##
  def get_share_url_table_name(self) -> str:
    return self.__DOUYIN_SHARE_URL_TABLE_NAME
  
  ##
  ## get share url table header
  ##
  def get_share_url_table_header(self) -> list:
    return self.__DOUYIN_SHARE_URL_TABLE_HEADER
  
  ##
  ## get share url table tuple
  ##
  def get_share_url_table_tuple(self) -> dict:
    return self.__DOUYIN_SHARE_URL_TABLE_TUPLE
  
  ##
  ## update live share url record
  ##
  def update_live_share_url_record(self, record:dict):
    try:
      db_result_record = list()
      ##
      ## check if the primary key is exist
      ##
      if record.get("owner_user_id") is None:
        raise KeyError
      
      ##
      ## check if the record is exist in database
      ##
      sql = '''SELECT owner_user_id, nickname, live_share_url, user_status
              FROM   share_url
              WHERE  owner_user_id = "{}";
            '''.format(record.get("owner_user_id"))
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      if len(result) != 0:
        ##
        ## the record is exist in database
        ## next: insert it if live share url is None
        ##
        for db_record in result:
          ##
          ## flag for difference
          ##
          df_result_record = [item for item in db_record]
          different = False
          
          ##
          ## update nickname when the nickname is different
          ##
          if db_record[1] != record.get("nickname"):
            df_result_record[1] = record.get("nickname")
            different = True

          ##
          ## update the record when the record is None
          ##
          if db_record[2] is None:
            df_result_record[2] = record.get("live_share_url")
            different = True
            
          ##
          ## update user status when the user status is different
          ##
          if db_record[3] != record.get("user_status"):
            df_result_record[3] = record.get("user_status")
            different = True

          ##
          ## update the record
          ##
          if different:
            update_sql = '''
                          UPDATE share_url
                          SET nickname = "{}", live_share_url = "{}", user_status = "{}"
                          WHERE owner_user_id = "{}";
                          '''.format(df_result_record[1], df_result_record[2], df_result_record[3], df_result_record[0])
            cursor.execute(update_sql)
            connector.commit()
            print("INFO: update {} success".format([item for item in df_result_record]))
            
      else:
        ##
        ## the record is not exist in database
        ## next: insert it into database
        ##
        insert_sql = '''
                      INSERT INTO share_url (owner_user_id, sec_user_id, nickname, post_share_url, live_share_url, directory_name, user_status) VALUES (
                        "{}",
                        "{}", 
                        "{}", 
                        '{}',
                        "{}", 
                        "{}", 
                        "{}"
                      );
                     '''.format(record.get("owner_user_id"), record.get("sec_user_id"), record.get("nickname"), record.get("post_share_url"), record.get("live_share_url"), record.get("directory_name"), record.get("user_status"))
        cursor.execute(insert_sql)
        connector.commit()
        get_logger().info("insert record {} success".format([item for item in record.values()]))
      connector.close()
    except Exception as e:
      get_logger().error("insert live share url {} failed {}".format(record["live_share_url"], e))
      raise e
  
  ##
  ## create a share url record
  ##
  def insert_live_share_url_record(self, record:dict):
    try:        
      ##
      ## check if the primary key is exist
      ##
      if record.get("owner_user_id") is None:
        raise KeyError
      
      ##
      ## check if the record is exist in database
      ##
      sql = '''SELECT owner_user_id, live_share_url
              FROM   share_url
              WHERE  owner_user_id = "{}";
            '''.format(record.get("owner_user_id"))
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      if len(result) != 0:
        ##
        ## the record is exist in database
        ## next: insert it if live share url is None
        ##
        for db_record in result:
          ##
          ## update the record when the record is None
          ##
          if db_record[1] is None:
            update_sql = '''
                          UPDATE share_url
                          SET live_share_url = "{}"
                          WHERE owner_user_id = "{}";
                          '''.format(record.get("live_share_url"), db_record[0])
            cursor.execute(update_sql)
            connector.commit()
            connector.close()
            get_logger().info("update owner_user_id:{} live_share_url:{} success".format(db_record[0], record["live_share_url"]))
          else:
            pass
      else:
        ##
        ## the record is not exist in database
        ## next: insert it into database
        ## actived_count: default 0, uncessary to insert
        ##
        insert_sql = '''
                      INSERT INTO share_url (owner_user_id, sec_user_id, nickname, post_share_url, live_share_url, directory_name, user_status) VALUES (
                        "{}",
                        "{}", 
                        "{}", 
                        '{}',
                        "{}", 
                        "{}", 
                        "{}"
                      );
                     '''.format(record.get("owner_user_id"), record.get("sec_user_id"), record.get("nickname"), record.get("post_share_url"), record.get("live_share_url"), record.get("directory_name"), record.get("user_status"))
        cursor.execute(insert_sql)
        connector.commit()
        connector.close()
        get_logger().info("insert record {} success".format([item for item in record.values()]))
    except Exception as e:
      get_logger().error("insert live share url {} failed {}".format(record["live_share_url"], e))
      raise e

  ##
  ## check if the douyin user is recorded
  ##
  def is_live_share_url_record_exist (self, live_share_url:str) -> bool:
    try:
      sql = '''
              SELECT live_share_url 
              FROM share_url
              WHERE live_share_url = "{}";
            '''.format(live_share_url)
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      connector.close()
      if len(result) != 0:
        return True
      else:
        return False
    except Exception as e:
      get_logger().error("search live share url {} failed {}".format(live_share_url, e))
      raise e

  ##
  ## get the owner directory name from database
  ##
  def get_owner_directory_name_by_live_share_url(self, live_share_url:str) -> str:
    try:
      sql = '''
              SELECT directory_name
              FROM share_url
              WHERE live_share_url = "{}";
            '''.format(live_share_url)
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      connector.close()
      if len(result) != 0:
        return result[0][0]
      else:
        return None
    except Exception as e:
      get_logger().error("search owner directory name {} failed {}".format(live_share_url, e))
      raise e

  ##
  ## get the owner nickname from database
  ##
  def get_directory_name_by_owner_user_id(self, owner_user_id:str) -> str:
    try:
      sql = '''
              SELECT directory_name
              FROM share_url
              WHERE owner_user_id = "{}";
            '''.format(owner_user_id)
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      connector.close()
      if len(result) != 0:
        return result[0][0]
      else:
        return None
    except Exception as e:
      get_logger().error("search owner directory name {} failed {}".format(owner_user_id, e))
      raise e

  ##
  ## get the owner nickname from database
  ##
  def get_owner_nickname_by_live_share_url(self, live_share_url:str) -> str:
    try:
      sql = '''
              SELECT nickname
              FROM share_url
              WHERE live_share_url = "{}";
            '''.format(live_share_url)
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      connector.close()
      if len(result) != 0:
        return result[0][0]
      else:
        return None
    except Exception as e:
      get_logger().error("search owner nickname {} failed {}".format(live_share_url, e))
      raise e

  ##
  ## check if the douyin owner is recorded
  ##
  def is_owner_user_id_record_exist(self, owner_user_id:str) -> bool:
    try:
      sql = '''
              SELECT owner_user_id 
              FROM share_url
              WHERE owner_user_id = "{}";
            '''.format(owner_user_id)
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      connector.close()
      if len(result) != 0:
        return True
      else:
        return False
    except Exception as e:
      get_logger().error("search owner user id {} failed {}".format(owner_user_id, e))
      raise e

  ##
  ## increment live actived count
  ##
  def increment_live_actived_count(self, owner_user_id:str):
    try:
      
      ##
      ## check if the input is valid
      ##
      if owner_user_id is None:
        raise KeyError
      
      ##
      ## construct sql to access database for actived_count
      ##
      sql = '''
              SELECT owner_user_id, actived_count
              FROM share_url
              WHERE owner_user_id = "{}";
            '''.format(owner_user_id)
      ##
      ## execute sql & receive result
      ##
      connector = self.get_db_connector()
      cursor = connector.cursor()
      cursor.execute(sql)
      result = cursor.fetchall()
      connector.close()
      
      ##
      ## handle the result
      ##
      if len(result) == 0:
        pass
      else:
        for db_record in result:
          ##
          ## construct sql
          ##
          increment_sql = '''
                            UPDATE share_url
                            SET actived_count = {}
                            WHERE owner_user_id = "{}"
                          '''.format(db_record[1]+1, db_record[0])
                          
          ##
          ## execute sql
          ##
          connector = self.get_db_connector()
          cursor = connector.cursor()
          cursor.execute(increment_sql)
          connector.commit()
          connector.close()
          get_logger().info("increment actived count succeed!")
    except Exception as e:
      get_logger().error("increment actived count failed {}".format(e))

  ##
  ## get douyin platform favorite owner live url
  ##
  def get_douyin_favorite_live_url(self) -> list:
    sql = '''
          select share_url.live_share_url
          from share_url, favorite_owner
          where share_url.owner_user_id = favorite_owner.owner_user_id
          and share_url.user_status != "已注销"
          order by favorite_owner.score desc;
          '''
    connector = self.get_db_connector()
    cursor = connector.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    connector.close()
    return result
  
  ##
  ## get douyin platform general owner live url
  ##
  def get_douyin_non_favorite_live_url(self) -> list:
    sql = '''
          select live_share_url
          from share_url 
          where owner_user_id not in (
            select owner_user_id 
            from favorite_owner
            )  and user_status != "已注销"
          order by actived_count;
          '''
    connector = self.get_db_connector()
    cursor = connector.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    connector.close()
    return result

  ##
  ## check if the douyin platform favorite owner score record is exist
  ##
  def is_owner_score_record_exist(self, owner_user_id:str) -> bool:
    sql = '''
          select owner_user_id
          from favorite_owner 
          where owner_user_id = "{}"
          '''.format(owner_user_id)
    connector = self.get_db_connector()
    cursor = connector.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    connector.close()
    if len(result) != 0:
      return True
    else:
      return False

  ##
  ## insert douyin platform favorite owner score
  ##
  def insert_owner_score(self, owner_user_id:str, platform:str="douyin", score:int=0):
    sql = '''
          insert into favorite_owner (owner_user_id, platform, score)
          values ("{}", "{}", {})
          '''.format(owner_user_id, platform, score)
    connector = self.get_db_connector()
    cursor = connector.cursor()
    cursor.execute(sql)
    connector.commit()
    connector.close()
    return True

  ##
  ## get douyin platform favorite owner score
  ##
  def get_owner_score_by_user_id(self, owner_user_id:str) -> int:
    sql = '''
          select score
          from favorite_owner 
          where owner_user_id = "{}"
          '''.format(owner_user_id)
    connector = self.get_db_connector()
    cursor = connector.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    connector.close()
    if len(result) != 0:
      return result[0][0]
    else:
      raise ValueError("ERROR: get owner score failed, owner_user_id: {}".format(owner_user_id))

  ##
  ## update douyin platform favorite owner score
  ##
  def update_owner_score(self, owner_user_id:str, score:int):
    sql = '''
          update favorite_owner
          set score = {}
          where owner_user_id = "{}"
          '''.format(score, owner_user_id)
    connector = self.get_db_connector()
    cursor = connector.cursor()
    cursor.execute(sql)
    connector.commit()
    connector.close()
    return True
##
## >>================================ test method ===============================>>
##

##
## test：create a database table
##
def test_create_share_url_table():
  ##
  ## test for connect to database
  ##
  try:
    db = DouyinShareUrlTable(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    connector = db.get_db_connector()
    cursor = connector.cursor()
    sql = '''
            CREATE TABLE share_url (
              owner_user_id     CHAR(200) NOT NULL PRIMARY KEY,
              sec_user_id       CHAR(200),
              nickname          CHAR(20),
              post_share_url    CHAR(100),
              live_share_url    CHAR(100),
              directory_name    CHAR(100),
              user_status       CHAR(100)
            )
          '''
    cursor.execute(sql)
    get_logger().info("test create database table success")
    connector.close()
  except Exception as e:
    get_logger().error("test create database table failed {}".format(e))

##
## test：drop a database table
##
def test_drop_db_table():  
  ##
  ## test for connect to database
  ##
  try:
    db = DouyinShareUrlTable(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    connector = db.get_db_connector()
    cursor = connector.cursor()
    sql = '''
            DROP TABLE share_url;
          '''
    cursor.execute(sql)
    get_logger().info("test drop database table success")
    connector.close()
  except Exception as e:
    get_logger().error("test drop database table failed {}".format(e))

##
## test：insert a record to database table
##
def test_insert_record():
  record = dict()
  record["owner_user_id"]  = "58859666123"
  record["sec_user_id"]    = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
  record["nickname"]       = "\u2728\u7C73\u5F00\u6717\u7EFF\u841D\u2728"
  record["post_share_url"] = "https://v.douyin.com/iYkvSmAw/"
  record["live_share_url"] = "https://v.douyin.com/iFemNNTW/"
  record["directory_name"] = "_\u7C73\u5F00\u6717\u7EFF\u841D_"
  record["user_status"]    = "正常"

  try:
    db = DouyinShareUrlTable(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    db.insert_live_share_url_record(record)
  except Exception as e:
    get_logger().error("insert a record failed {}".format(e))

##
## test: search recode from table
##
def test_search_record_from_table():
  try:
    db = DouyinShareUrlTable(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    url = "https://v.douyin.com/ikRBs7Sy/"
    if db.is_live_share_url_record_exist(url) is True:
      get_logger().info("live share url {} is exist".format(url))
  except Exception as e:
    get_logger().error("search records from table failed {}".format(e))
    raise e

def test_increment_actived_count():
  try:
    owner_user_id = "55262425391"
    db = DouyinShareUrlTable(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    db.increment_live_actived_count(owner_user_id)      
  except Exception as e:
    pass
  
##
## test: increment actived count
##
def test_increment_actived_count():
  try:
    owner_user_id = "55262425391"
    db = DouyinShareUrlTable(host='127.0.0.1', user='admin', passwd='admin', database='social_media_stream_downloader')
    db.increment_live_actived_count(owner_user_id)      
  except Exception as e:
    pass
  
class DouyinLiveRecordTable (SocialMediaStreamDataBase):
##
## >>============================= attribute =============================>>
##

##
## douyin live record table header
## +---------------+-------------+-----------+----------------+----------------+----------------+-------------+---------------+
## | room_id | like_count | nickname  | post_share_url | live_share_url | directory_name | user_status | actived_count |
## +---------------+-------------+-----------+----------------+----------------+----------------+-------------+---------------+
##

##
## >>============================= private method =============================>>
##

##
## >>============================= abstract method =============================>>
##

##
## >>============================= sub class method =============================>>
##

##
## >>================================ test method ===============================>>
##
  pass

'''
# MySQL 数据库表设计：抖音直播数据存储

基于提供的 YAML 文件，我设计了一套 MySQL 数据库表结构来存储抖音直播相关数据。这套设计考虑了数据关系、查询效率和扩展性。

## 1. 核心表结构

### 1.1 直播间表 (live_rooms)

```sql
CREATE TABLE `live_rooms` (
  `id` bigint(20) NOT NULL COMMENT '直播间ID',
  `id_str` varchar(64) NOT NULL COMMENT '直播间ID字符串',
  `title` varchar(255) DEFAULT NULL COMMENT '直播间标题',
  `status` tinyint(4) DEFAULT 0 COMMENT '直播状态：1-直播中，2-已结束',
  `create_time` int(11) DEFAULT NULL COMMENT '创建时间戳',
  `start_time` int(11) DEFAULT NULL COMMENT '开始时间戳',
  `finish_time` int(11) DEFAULT NULL COMMENT '结束时间戳',
  `stream_close_time` int(11) DEFAULT NULL COMMENT '流关闭时间',
  `like_count` int(11) DEFAULT 0 COMMENT '点赞数',
  `user_count` int(11) DEFAULT 0 COMMENT '观看人数',
  `total_user` int(11) DEFAULT 0 COMMENT '总观看人数',
  `app_id` int(11) DEFAULT NULL COMMENT '应用ID',
  `live_id` int(11) DEFAULT NULL COMMENT '直播ID',
  `stream_id` bigint(20) DEFAULT NULL COMMENT '流ID',
  `stream_id_str` varchar(64) DEFAULT NULL COMMENT '流ID字符串',
  `anchor_share_text` text DEFAULT NULL COMMENT '主播分享文本',
  `share_url` varchar(512) DEFAULT NULL COMMENT '分享URL',
  `location` varchar(255) DEFAULT NULL COMMENT '位置信息',
  `city` varchar(100) DEFAULT NULL COMMENT '城市',
  `cover_url` varchar(512) DEFAULT NULL COMMENT '封面URL',
  `cover_avg_color` varchar(20) DEFAULT NULL COMMENT '封面平均颜色',
  `introduction` text DEFAULT NULL COMMENT '直播间介绍',
  `short_title` varchar(255) DEFAULT NULL COMMENT '短标题',
  `video_feed_tag` varchar(100) DEFAULT NULL COMMENT '视频标签',
  `has_commerce_goods` tinyint(1) DEFAULT 0 COMMENT '是否有电商商品',
  `live_type_normal` tinyint(1) DEFAULT 0 COMMENT '是否普通直播',
  `live_type_audio` tinyint(1) DEFAULT 0 COMMENT '是否音频直播',
  `live_type_linkmic` tinyint(1) DEFAULT 0 COMMENT '是否连麦直播',
  `replay` tinyint(1) DEFAULT 0 COMMENT '是否回放',
  `comment_count` int(11) DEFAULT 0 COMMENT '评论数',
  `digg_count` int(11) DEFAULT 0 COMMENT '点赞数',
  `follow_count` int(11) DEFAULT 0 COMMENT '关注数',
  `finish_reason` tinyint(4) DEFAULT 0 COMMENT '结束原因',
  `orientation` tinyint(4) DEFAULT 0 COMMENT '屏幕方向',
  `layout` tinyint(4) DEFAULT 0 COMMENT '布局类型',
  `cell_style` tinyint(4) DEFAULT 0 COMMENT '单元格样式',
  `base_category` int(11) DEFAULT 0 COMMENT '基础分类',
  `category` int(11) DEFAULT 0 COMMENT '分类',
  `client_version` int(11) DEFAULT NULL COMMENT '客户端版本',
  `os_type` tinyint(4) DEFAULT NULL COMMENT '操作系统类型',
  `create_scene` varchar(100) DEFAULT NULL COMMENT '创建场景',
  `is_virtual_anchor` tinyint(1) DEFAULT 0 COMMENT '是否虚拟主播',
  `enable_room_perspective` tinyint(1) DEFAULT 0 COMMENT '是否启用房间透视',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`),
  KEY `idx_owner_id` (`owner_user_id`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_stream_id` (`stream_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间表';
```

### 1.2 主播表 (live_anchors)

```sql
CREATE TABLE `live_anchors` (
  `id` bigint(20) NOT NULL COMMENT '主播ID',
  `id_str` varchar(64) NOT NULL COMMENT '主播ID字符串',
  `sec_uid` varchar(128) NOT NULL COMMENT '安全用户ID',
  `nickname` varchar(255) DEFAULT NULL COMMENT '昵称',
  `display_id` varchar(100) DEFAULT NULL COMMENT '显示ID',
  `short_id` bigint(20) DEFAULT NULL COMMENT '短ID',
  `signature` text DEFAULT NULL COMMENT '签名',
  `avatar_large` varchar(512) DEFAULT NULL COMMENT '大头像URL',
  `avatar_medium` varchar(512) DEFAULT NULL COMMENT '中头像URL',
  `avatar_thumb` varchar(512) DEFAULT NULL COMMENT '小头像URL',
  `gender` tinyint(4) DEFAULT 0 COMMENT '性别：0-未知，1-男，2-女',
  `verified` tinyint(1) DEFAULT 0 COMMENT '是否认证',
  `verified_content` varchar(255) DEFAULT NULL COMMENT '认证内容',
  `verified_reason` varchar(255) DEFAULT NULL COMMENT '认证原因',
  `location_city` varchar(100) DEFAULT NULL COMMENT '所在城市',
  `follower_count` int(11) DEFAULT 0 COMMENT '粉丝数',
  `follower_count_str` varchar(50) DEFAULT NULL COMMENT '粉丝数字符串',
  `following_count` int(11) DEFAULT 0 COMMENT '关注数',
  `following_count_str` varchar(50) DEFAULT NULL COMMENT '关注数字符串',
  `level` int(11) DEFAULT 1 COMMENT '等级',
  `pay_grade_level` int(11) DEFAULT 0 COMMENT '付费等级',
  `authorization_info` tinyint(4) DEFAULT 0 COMMENT '授权信息',
  `with_commerce_permission` tinyint(1) DEFAULT 0 COMMENT '是否有电商权限',
  `with_fusion_shop_entry` tinyint(1) DEFAULT 0 COMMENT '是否有融合店铺入口',
  `web_rid` varchar(100) DEFAULT NULL COMMENT '网页房间ID',
  `webcast_uid` varchar(255) DEFAULT NULL COMMENT '直播用户ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sec_uid` (`sec_uid`),
  KEY `idx_nickname` (`nickname`),
  KEY `idx_short_id` (`short_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='主播表';
```

### 1.3 直播流表 (live_streams)

```sql
CREATE TABLE `live_streams` (
  `id` bigint(20) NOT NULL COMMENT '流ID',
  `id_str` varchar(64) NOT NULL COMMENT '流ID字符串',
  `room_id` bigint(20) NOT NULL COMMENT '关联的房间ID',
  `stream_provider` tinyint(4) DEFAULT 0 COMMENT '流提供商',
  `stream_orientation` tinyint(4) DEFAULT 1 COMMENT '流方向',
  `default_resolution` varchar(20) DEFAULT NULL COMMENT '默认分辨率',
  `candidate_resolution` varchar(255) DEFAULT NULL COMMENT '候选分辨率',
  `flv_pull_url` text DEFAULT NULL COMMENT 'FLV拉流URL',
  `hls_pull_url` text DEFAULT NULL COMMENT 'HLS拉流URL',
  `rtmp_pull_url` text DEFAULT NULL COMMENT 'RTMP拉流URL',
  `rtmp_push_url` text DEFAULT NULL COMMENT 'RTMP推流URL',
  `stream_control_type` tinyint(4) DEFAULT 0 COMMENT '流控制类型',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_room_id` (`room_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播流表';
```

### 1.4 直播管理员表 (live_room_admins)

```sql
CREATE TABLE `live_room_admins` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `room_id` bigint(20) NOT NULL COMMENT '直播间ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_room_user` (`room_id`, `user_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间管理员表';
```

### 1.5 直播统计数据表 (live_room_stats)

```sql
CREATE TABLE `live_room_stats` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `room_id` bigint(20) NOT NULL COMMENT '直播间ID',
  `like_count` int(11) DEFAULT 0 COMMENT '点赞数',
  `digg_count` int(11) DEFAULT 0 COMMENT '点赞数',
  `comment_count` int(11) DEFAULT 0 COMMENT '评论数',
  `follow_count` int(11) DEFAULT 0 COMMENT '关注数',
  `user_count` int(11) DEFAULT 0 COMMENT '观看人数',
  `total_user` int(11) DEFAULT 0 COMMENT '总观看人数',
  `fan_ticket` int(11) DEFAULT 0 COMMENT '粉丝票数',
  `money` int(11) DEFAULT 0 COMMENT '金额(分)',
  `gift_uv_count` int(11) DEFAULT 0 COMMENT '礼物UV数',
  `record_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_room_time` (`room_id`, `record_time`),
  KEY `idx_record_time` (`record_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间统计数据表';
```

## 2. 扩展表结构

### 2.1 直播标签表 (live_tags)

```sql
CREATE TABLE `live_tags` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_name` varchar(100) NOT NULL COMMENT '标签名称',
  `tag_type` tinyint(4) DEFAULT 0 COMMENT '标签类型',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tag_name` (`tag_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播标签表';
```

### 2.2 直播间标签关联表 (live_room_tags)

```sql
CREATE TABLE `live_room_tags` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `room_id` bigint(20) NOT NULL COMMENT '直播间ID',
  `tag_id` int(11) NOT NULL COMMENT '标签ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_room_tag` (`room_id`, `tag_id`),
  KEY `idx_tag_id` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间标签关联表';
```

### 2.3 直播分享记录表 (live_share_records)

```sql
CREATE TABLE `live_share_records` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `room_id` bigint(20) NOT NULL COMMENT '直播间ID',
  `share_url` varchar(512) NOT NULL COMMENT '分享URL',
  `share_platform` varchar(50) DEFAULT NULL COMMENT '分享平台',
  `share_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分享时间',
  `share_user_id` bigint(20) DEFAULT NULL COMMENT '分享用户ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_room_id` (`room_id`),
  KEY `idx_share_user` (`share_user_id`),
  KEY `idx_share_time` (`share_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播分享记录表';
```

## 3. 使用建议

1. **数据分区**：对于直播统计数据表(live_room_stats)，可以按时间进行分区，提高查询效率。

2. **索引优化**：根据实际查询模式，可能需要添加更多复合索引。

3. **分表策略**：对于大型平台，可以考虑按主播ID或时间范围进行分表。

4. **数据归档**：对于历史直播数据，可以设计归档策略，将不活跃数据移到归档表。

5. **缓存层**：高频访问的数据如直播间基本信息，可以使用Redis缓存。

这套设计涵盖了从直播间基本信息、主播信息、流信息到统计数据的完整存储需求，可以根据实际业务场景进行调整和扩展。
'''

##
## >>================================ main method ===============================>>
##
if __name__ == "__main__":
  ##
  ## test for connect to database
  ##
  # test_create_db_table()
  # test_drop_db_table()
  # test_insert_record()
  # test_search_record_from_table()
  # test_increment_actived_count()
  # test_create_favorite_owner_table()
  pass