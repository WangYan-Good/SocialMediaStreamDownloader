## <<Third-Part>>
from backend.src.database.social_media_stream_database import (
  SocialMediaStreamDataBase,
)
from backend.src.library.loglib import get_logger


class DouyinAwemeRecordTable(SocialMediaStreamDataBase):
##
## >>============================= attribute =============================>>
##
##
## aweme record table header
## +----------+----------+---------------+-------------+------------+------+
## | platform | aweme_id | owner_user_id | sec_user_id | aweme_type | desc |
## +----------+----------+---------------+-------------+------------+------+
## +-------------+---------------+-------------+-------------+----------+--------+
## | create_time | downloaded_at | media_count | saved_count | save_dir | source |
## +-------------+---------------+-------------+-------------+----------+--------+
##
## The managed schema lives in backend/src/database/orm/models/aweme.py and
## migration/versions/0003_aweme_record.py.  No DDL here: a second copy would
## have to be kept in step by hand and would drift from Alembic.
##
  __AWEME_RECORD_TABLE_NAME = "aweme_record"
  __AWEME_RECORD_TABLE_HEADER = [
    "platform",
    "aweme_id",
    "owner_user_id",
    "sec_user_id",
    "aweme_type",
    "desc",
    "create_time",
    "downloaded_at",
    "media_count",
    "saved_count",
    "save_dir",
    "source",
  ]
  __AWEME_RECORD_TABLE_TUPLE = {
    item: None for item in __AWEME_RECORD_TABLE_HEADER
  }

##
## >>============================= private method =============================>>
##
  def __init__(self, host: str, user: str, passwd: str, database: str):
    if hasattr(self, "_initialized") and self._initialized:
      return
    super().__init__(host, user, passwd, database)
    self._initialized = True

##
## >>============================= sub class method =============================>>
##
  def get_aweme_record_table_name(self) -> str:
    return self.__AWEME_RECORD_TABLE_NAME

  def get_aweme_record_table_header(self) -> list:
    return self.__AWEME_RECORD_TABLE_HEADER

  def get_aweme_record_table_tuple(self) -> dict:
    return self.__AWEME_RECORD_TABLE_TUPLE

  def find_aweme_record(self, aweme_id: str, platform: str = "douyin"):
    """Return the recorded row for one post, or ``None``.

    Note what this is *not* for: deciding whether a post still needs downloading.
    ``media_count`` is only what one payload happened to expose, and the platform
    is not consistent about it - a response that omitted the cover would record a
    complete 2 of 2 and permanently suppress the cover.  The downloader compares
    the current plan against the files on disk instead.
    """
    if aweme_id is None:
      raise KeyError("aweme_id is required")
    sql = '''SELECT platform, aweme_id, media_count, saved_count, save_dir
             FROM   aweme_record
             WHERE  platform = %s AND aweme_id = %s;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, aweme_id))
          result = cursor.fetchall()
          if not result:
            return None
          return result[0]
    except Exception as e:
      get_logger().error(
        "query aweme record {} failed {}".format(aweme_id, e)
      )
      raise e

  def find_aweme_records(self, aweme_ids, platform: str = "douyin") -> dict:
    """Return ``{aweme_id: row}`` for the ids that have a record.

    One round trip for a whole page.  Marking nineteen list rows by calling
    ``find_aweme_record`` per row would be nineteen queries to answer one screen.
    """
    keys = [str(value).strip() for value in aweme_ids if str(value).strip()]
    if not keys:
      return {}
    ##
    ## Placeholders only - the values stay bound.  The count is what varies, so
    ## the string being built carries no data.
    ##
    placeholders = ", ".join(["%s"] * len(keys))
    sql = (
      "SELECT platform, aweme_id, media_count, saved_count, save_dir, "
      "downloaded_at FROM aweme_record WHERE platform = %s AND aweme_id IN ("
      + placeholders
      + ");"
    )
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, tuple([platform] + keys))
          return {
            row.get("aweme_id"): row
            for row in cursor.fetchall()
            if row.get("aweme_id") is not None
          }
    except Exception as e:
      get_logger().error("bulk aweme record lookup failed {}".format(e))
      raise e

  def find_owner_directory_name(self, owner_user_id: str):
    """Return the folder already in use for this owner, or ``None``.

    An owner who renames themselves would otherwise get a second folder, and the
    post files under the old name would stop being found - the same post would
    then be downloaded again into the new folder.  The live path avoids that the
    same way, so the two paths keep one folder per owner between them.

    One round trip rather than the live path's exists-then-read pair.
    """
    if owner_user_id is None:
      return None
    sql = '''SELECT directory_name
             FROM   share_url
             WHERE  owner_user_id = %s;
          '''
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql, (owner_user_id,))
        result = cursor.fetchall()
        if not result:
          return None
        recorded = result[0].get("directory_name")
        ##
        ## Older rows in this table carry the literal text "None" where a value
        ## was never set; post_share_url still shows it.  Treat that and the empty
        ## string as absent rather than creating a folder named "None".
        ##
        if not recorded or recorded == "None":
          return None
        return recorded

  def count_owners_using_directory_name(self, directory_name: str) -> int:
    """How many distinct owners are recorded under this folder name.

    Douyin does not require nicknames to be unique, so several accounts really do
    share one.  Measured on this database: 39 folder names cover more than one
    owner, four of them cover three.  Anything above 1 means the folder cannot
    identify its owner and the post path adds a discriminator.

    ``directory_name`` is not indexed, so this is a scan; at a few thousand rows
    that is cheaper than the migration an index would cost.
    """
    if not directory_name:
      return 0
    ##
    ## Blank owner ids are excluded.  A payload that omits author.uid used to
    ## produce a row keyed on the empty string, and counting that as an owner made
    ## a folder look shared when only one real account used it - which suppressed
    ## the discriminator entirely.
    ##
    sql = '''SELECT COUNT(DISTINCT owner_user_id) AS owners
             FROM   share_url
             WHERE  directory_name = %s
               AND  owner_user_id IS NOT NULL
               AND  owner_user_id <> '';
          '''
    with self.get_connection() as connector:
      with connector.cursor() as cursor:
        cursor.execute(sql, (directory_name,))
        result = cursor.fetchall()
        if not result:
          return 0
        return int(result[0].get("owners") or 0)

  def upsert_aweme_record(self, record: dict):
    """Write one post's outcome, replacing any earlier attempt at it.

    ``(platform, aweme_id)`` is the primary key, so a re-run updates the row it
    already has instead of adding a second one.
    """
    self.require_write_ready()
    if record.get("aweme_id") is None:
      raise KeyError("aweme_id is required")
    if record.get("platform") is None:
      raise KeyError("platform is required")

    sql = '''INSERT INTO aweme_record
               (platform, aweme_id, owner_user_id, sec_user_id, aweme_type,
                `desc`, create_time, downloaded_at, media_count, saved_count,
                save_dir, source)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE
               owner_user_id = VALUES(owner_user_id),
               sec_user_id   = VALUES(sec_user_id),
               aweme_type    = VALUES(aweme_type),
               `desc`        = VALUES(`desc`),
               create_time   = VALUES(create_time),
               downloaded_at = VALUES(downloaded_at),
               media_count   = VALUES(media_count),
               saved_count   = VALUES(saved_count),
               save_dir      = VALUES(save_dir),
               source        = VALUES(source);
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            sql,
            (
              record.get("platform"),
              record.get("aweme_id"),
              record.get("owner_user_id"),
              record.get("sec_user_id"),
              record.get("aweme_type"),
              record.get("desc"),
              record.get("create_time"),
              record.get("downloaded_at"),
              record.get("media_count"),
              record.get("saved_count"),
              record.get("save_dir"),
              record.get("source"),
            ),
          )
          connector.commit()
          get_logger().info(
            "record aweme {} saved {}/{}".format(
              record.get("aweme_id"),
              record.get("saved_count"),
              record.get("media_count"),
            )
          )
    except Exception as e:
      get_logger().error(
        "record aweme {} failed {}".format(record.get("aweme_id"), e)
      )
      raise e

  def upsert_post_owner(self, record: dict):
    """Keep one ``share_url`` row per owner, filling ``post_share_url``.

    The live path owns ``live_share_url`` on the same row, so this only ever
    writes the post column and the identity columns.  ``actived_count`` counts
    live sessions and is left alone.
    """
    self.require_write_ready()
    owner_user_id = record.get("owner_user_id")
    ##
    ## Blank is rejected as well as missing.  owner_user_id is the primary key, and
    ## a payload that omits author.uid arrives here as the empty string; inserting
    ## that creates a row no owner will ever match, which then miscounts the owners
    ## sharing a folder.
    ##
    if owner_user_id is None or not str(owner_user_id).strip():
      raise KeyError("owner_user_id is required")

    ##
    ## directory_name takes the stored value first, unlike every other column
    ## updated here.  The folder is where this owner's files already are, often
    ## put there by the live path long ago, so a rename must not move it - the
    ## nickname column is what tracks renames.  Written the other way round, the
    ## first post of a batch files correctly and then overwrites the record with
    ## today's nickname, sending every later post to a different folder.
    ##
    sql = '''INSERT INTO share_url
               (owner_user_id, sec_user_id, nickname, post_share_url,
                directory_name, user_status)
             VALUES (%s, %s, %s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE
               sec_user_id    = COALESCE(VALUES(sec_user_id), sec_user_id),
               nickname       = COALESCE(VALUES(nickname), nickname),
               post_share_url = COALESCE(VALUES(post_share_url), post_share_url),
               directory_name = COALESCE(directory_name, VALUES(directory_name));
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            sql,
            (
              record.get("owner_user_id"),
              record.get("sec_user_id"),
              record.get("nickname"),
              record.get("post_share_url"),
              record.get("directory_name"),
              record.get("user_status"),
            ),
          )
          connector.commit()
    except Exception as e:
      get_logger().error(
        "record post owner {} failed {}".format(
          record.get("owner_user_id"),
          e,
        )
      )
      raise e
