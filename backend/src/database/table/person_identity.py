## <<Third-Part>>
from backend.src.database.orm.models.person import ACCOUNT_ROLES
from backend.src.database.social_media_stream_database import (
  SocialMediaStreamDataBase,
)
from backend.src.library.loglib import get_logger


PLATFORM = "douyin"


class UnknownRole(ValueError):
  """Raised when an account is attached with a role nobody defined.

  Its own type so a caller can turn it into a field-level message rather than a
  generic failure: the user picked something from a list, and the list is short.
  """


class DouyinPersonIdentityTable(SocialMediaStreamDataBase):
  """Reads and writes the three tables that record who an account belongs to.

  A person is created on demand.  An account nobody marked has no row here, and
  every path that consults this table has to behave exactly as it did before -
  that is what keeps the feature at zero effect until it is actually used.
  """

##
## >>============================= people =============================>>
##
  def create_person(
    self,
    display_name: str,
    directory_name: str = None,
    note: str = None,
  ) -> int:
    """Create a person and return the new id."""
    if not isinstance(display_name, str) or not display_name.strip():
      raise ValueError("display_name is required")

    sql = '''INSERT INTO person (display_name, directory_name, note)
             VALUES (%s, %s, %s);
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            sql,
            (display_name.strip(), directory_name, note),
          )
          new_id = cursor.lastrowid
          connector.commit()
    except Exception as e:
      get_logger().error("create person {} failed: {}".format(display_name, e))
      raise e
    return new_id

  def update_person(
    self,
    person_id: int,
    display_name: str = None,
    directory_name: str = None,
    note: str = None,
  ) -> None:
    """Update only the fields that were named.

    Renaming a folder must not blank a note that nobody mentioned, so unnamed
    fields are left out of the statement rather than written as ``None``.
    """
    if display_name is None and directory_name is None and note is None:
      return

    ##
    ## One fixed statement with COALESCE rather than a SET clause assembled from
    ## the fields that were named.  Same effect - an unmentioned field keeps its
    ## stored value - without building SQL text at runtime, which is the line
    ## test_sql_construction_invariant draws: only identifiers may ever be
    ## interpolated, everything else binds.  share_url's upsert reads the same
    ## way, so the two stay recognisable as one idiom.
    ##
    sql = '''UPDATE person
             SET display_name   = COALESCE(%s, display_name),
                 directory_name = COALESCE(%s, directory_name),
                 note           = COALESCE(%s, note)
             WHERE person_id = %s;
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            sql,
            (display_name, directory_name, note, person_id),
          )
          connector.commit()
    except Exception as e:
      get_logger().error("update person {} failed: {}".format(person_id, e))
      raise e

  def delete_person(self, person_id: int) -> None:
    """Delete a person.

    Their account attachments and collaborations go with them through the
    foreign keys' cascade, so this deliberately issues one statement rather than
    clearing the children by hand - two places to keep in step is one too many.
    """
    sql = "DELETE FROM person WHERE person_id = %s;"
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (person_id,))
          connector.commit()
    except Exception as e:
      get_logger().error("delete person {} failed: {}".format(person_id, e))
      raise e

  def list_persons(self) -> list:
    """Every person, with how many accounts each holds.

    A LEFT JOIN so somebody created a moment ago, before any account was
    attached, still appears - that is the ordinary order of the operation.
    """
    sql = '''SELECT p.person_id, p.display_name, p.directory_name, p.note,
                    COUNT(pa.owner_user_id) AS account_count
             FROM person AS p
             LEFT JOIN person_account AS pa ON pa.person_id = p.person_id
             GROUP BY p.person_id, p.display_name, p.directory_name, p.note
             ORDER BY p.display_name;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql)
          rows = cursor.fetchall() or []
    except Exception as e:
      get_logger().error("list persons failed: {}".format(e))
      raise e

    return [
      {
        "person_id": row[0],
        "display_name": row[1],
        "directory_name": row[2],
        "note": row[3],
        "account_count": row[4],
      }
      for row in rows
    ]

  def search_accounts(self, keyword: str, limit: int = 30) -> list:
    """Find accounts by nickname or id, reporting who each already belongs to.

    A search rather than a list: there are more than eighteen hundred accounts,
    which no picker can show.  Each result carries its current person so that
    attaching one somewhere else is a visible move rather than a silent one.
    """
    if not isinstance(keyword, str) or not keyword.strip():
      return []

    pattern = "%{}%".format(keyword.strip())
    sql = '''SELECT s.owner_user_id, s.nickname, s.directory_name,
                    pa.person_id, pa.role
             FROM share_url AS s
             LEFT JOIN person_account AS pa
               ON pa.owner_user_id = s.owner_user_id AND pa.platform = %s
             WHERE s.nickname LIKE %s OR s.owner_user_id LIKE %s
             ORDER BY s.nickname
             LIMIT %s;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (PLATFORM, pattern, pattern, int(limit)))
          rows = cursor.fetchall() or []
    except Exception as e:
      get_logger().error("search accounts for {} failed: {}".format(keyword, e))
      raise e

    return [
      {
        "owner_user_id": row[0],
        "nickname": row[1],
        "directory_name": row[2],
        "person_id": row[3],
        "role": row[4],
      }
      for row in rows
    ]

##
## >>============================= accounts =============================>>
##
  def attach_account(
    self,
    platform: str,
    owner_user_id: str,
    person_id: int,
    role: str,
  ) -> None:
    """Record that an account belongs to a person, in the given role.

    Upserts on the account rather than inserting.  An account belongs to at most
    one person, and re-attaching is the ordinary way to correct a mistake, so a
    second attach has to move the account rather than leave it under two people.
    """
    if role not in ACCOUNT_ROLES:
      raise UnknownRole(
        "role must be one of {}, got {!r}".format(ACCOUNT_ROLES, role)
      )

    sql = '''INSERT INTO person_account
               (platform, owner_user_id, person_id, role)
             VALUES (%s, %s, %s, %s)
             ON DUPLICATE KEY UPDATE
               person_id = VALUES(person_id),
               role      = VALUES(role);
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, owner_user_id, person_id, role))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "attach account {} to person {} failed: {}".format(
          owner_user_id,
          person_id,
          e,
        )
      )
      raise e

  def detach_account(self, platform: str, owner_user_id: str) -> None:
    """Unmark an account.

    Its downloads fall back to the account's own recorded folder, which is what
    makes a mis-marked account recoverable.
    """
    sql = '''DELETE FROM person_account
             WHERE platform = %s AND owner_user_id = %s;
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, owner_user_id))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "detach account {} failed: {}".format(owner_user_id, e)
      )
      raise e

##
## >>============================= directory =============================>>
##
  def find_person_directory_name(
    self,
    owner_user_id: str,
    platform: str = PLATFORM,
  ):
    """Return the folder this account's person files under, or ``None``.

    ``None`` covers all three ways there is no answer - the account is not
    marked, its person has no folder recorded, or that folder is blank - because
    the caller does the same thing in every one of them: fall back to what it
    did before people existed.
    """
    sql = '''SELECT p.directory_name
             FROM person_account AS pa
             JOIN person AS p ON p.person_id = pa.person_id
             WHERE pa.platform = %s AND pa.owner_user_id = %s
             LIMIT 1;
          '''
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (platform, owner_user_id))
          row = cursor.fetchone()
    except Exception as e:
      get_logger().error(
        "look up person directory for {} failed: {}".format(owner_user_id, e)
      )
      raise e

    if not row:
      return None
    found = row[0] if not isinstance(row, dict) else row.get("directory_name")
    if not isinstance(found, str) or not found.strip():
      return None
    return found

##
## >>============================= collaboration =============================>>
##
  def add_collaboration(
    self,
    photographer_id: int,
    subject_id: int,
    note: str = None,
  ) -> None:
    """Record that a photographer works with a subject.

    Directed, so the pair is stored as given.  A person photographing themselves
    is rejected: the row would carry no information and would make "who did this
    person shoot" answer with themselves.
    """
    if photographer_id == subject_id:
      raise ValueError("a person cannot be recorded as photographing themselves")

    sql = '''INSERT INTO person_collaboration
               (photographer_id, subject_id, note)
             VALUES (%s, %s, %s)
             ON DUPLICATE KEY UPDATE
               note = COALESCE(VALUES(note), note);
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (photographer_id, subject_id, note))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "record collaboration {} -> {} failed: {}".format(
          photographer_id,
          subject_id,
          e,
        )
      )
      raise e

  def remove_collaboration(self, photographer_id: int, subject_id: int) -> None:
    sql = '''DELETE FROM person_collaboration
             WHERE photographer_id = %s AND subject_id = %s;
          '''
    self.require_write_ready()
    try:
      with self.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(sql, (photographer_id, subject_id))
          connector.commit()
    except Exception as e:
      get_logger().error(
        "remove collaboration {} -> {} failed: {}".format(
          photographer_id,
          subject_id,
          e,
        )
      )
      raise e
