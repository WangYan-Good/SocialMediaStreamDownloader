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
