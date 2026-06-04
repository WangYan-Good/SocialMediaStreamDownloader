##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>

## <<Extension>>

## <<Third-Part>>
from backend.src.database.social_media_stream_database       import SocialMediaStreamDataBase
from backend.src.base.log                                    import get_logger


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
  __SQL_CREATE_SHARE_URL_TABLE    = '''
                                    CREATE TABLE IF NOT EXISTS {} (
                                      owner_user_id     VARCHAR(200) NOT NULL,
                                      sec_user_id       VARCHAR(200) DEFAULT NULL,
                                      nickname          VARCHAR(50)  DEFAULT NULL,
                                      post_share_url    VARCHAR(100) DEFAULT NULL,
                                      live_share_url    VARCHAR(100) DEFAULT NULL,
                                      directory_name    VARCHAR(100) DEFAULT NULL,
                                      user_status       VARCHAR(100) DEFAULT NULL,
                                      actived_count     INT UNSIGNED NOT NULL DEFAULT 0,
                                      PRIMARY KEY (owner_user_id),
                                      INDEX idx_nickname (nickname)
                                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                                  '''.format(__DOUYIN_SHARE_URL_TABLE_NAME)
  __SQL_DROP_SHARE_URL_TABLE      = '''
                                    DROP TABLE IF EXISTS {};
                                  '''.format(__DOUYIN_SHARE_URL_TABLE_NAME)
##
## >>============================= private method =============================>>
##
  def __init__(self, host:str, user:str, passwd:str, database:str):
    if hasattr(self, '_initialized') and self._initialized:
        return
    super().__init__(host, user, passwd, database)
    self._initialized = True

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
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
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
                get_logger().info("update {} success".format([item for item in df_result_record]))
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
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
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
                get_logger().info("update owner_user_id:{} live_share_url:{} success".format(db_record[0], record["live_share_url"]))
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
      ##
      ## execute sql & receive result
      ##
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
          result = cursor.fetchall()
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
      ##
      ## execute sql & receive result
      ##
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
          result = cursor.fetchall()
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
      ##
      ## execute sql & receive result
      ##
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
          result = cursor.fetchall()
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
      ##
      ## execute sql & receive result
      ##
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
          result = cursor.fetchall()
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
      ##
      ## execute sql & receive result
      ##
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
          result = cursor.fetchall()
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
              WHERE owner_user_id = %s;
            '''
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (owner_user_id,))
          db_record = cursor.fetchone()

      if db_record is None:
        get_logger().warning("owner_user_id {} not found, skip increment".format(owner_user_id))
        return

      if isinstance(db_record, dict):
        current_count = int(db_record.get("actived_count", 0))
      else:
        current_count = int(db_record[1])

      increment_sql = '''
                      UPDATE share_url
                      SET actived_count = %s
                      WHERE owner_user_id = %s
                    '''
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(increment_sql, (current_count + 1, owner_user_id))
          connector.commit()
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
          and favorite_owner.platform = "douyin"
          and share_url.user_status != "已注销"
          order by favorite_owner.score desc;
          '''
    ##
    ## execute sql & receive result
    ##
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
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
            where platform = "douyin"
            )  and user_status != "已注销"
          order by actived_count;
          '''
    ##
    ## execute sql & receive result
    ##
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
    return result

  ##
  ## check if the douyin platform favorite owner score record is exist
  ##
  def is_owner_score_record_exist(self, owner_user_id:str, platform:str="douyin") -> bool:
    sql = '''
          select owner_user_id
          from favorite_owner 
          where owner_user_id = "{}"
          and platform = "{}"
          '''.format(owner_user_id, platform)
    ##
    ## execute sql & receive result
    ##
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
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
    ##
    ## execute sql & commit
    ##
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql)
        connector.commit()
    return True

  ##
  ## get douyin platform favorite owner score
  ##
  def get_owner_score_by_user_id(self, owner_user_id:str, platform:str="douyin") -> int:
    sql = '''
          select score
          from favorite_owner 
          where owner_user_id = "{}"
          and platform = "{}"
          '''.format(owner_user_id, platform)
    ##
    ## execute sql & receive result
    ##
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql)
        result = cursor.fetchall()
    if len(result) != 0:
      return result[0][0]
    else:
      raise ValueError("ERROR: get owner score failed, owner_user_id: {}".format(owner_user_id))

  ##
  ## update douyin platform favorite owner score
  ##
  def update_owner_score(self, owner_user_id:str, score:int, platform:str="douyin"):
    sql = '''
          update favorite_owner
          set score = {}
          where owner_user_id = "{}"
          and platform = "{}"
          '''.format(score, owner_user_id, platform)
    ##
    ## execute sql & commit
    ##
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql)
        connector.commit()
    return True