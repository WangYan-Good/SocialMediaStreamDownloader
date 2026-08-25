##<<Base>>
from datetime import datetime

##<<Extension>>
import pymysql

##<<Third-part>>
from backend.src.auth.errors import AuthUnavailable, DuplicateUsername


##
## Raw SQL against the same connection pool the rest of this project uses,
## rather than a second ORM session layer.
##
## Two tables and six statements do not need a mapper, and adding one here
## would mean authentication owned a database lifecycle nothing else shares.
##


class AuthRepository:
  """The two authentication tables, and nothing else.

  Every method turns a driver failure into ``AuthUnavailable``.  That is the
  whole reason this class exists as a seam: the service above must be able to
  tell "the database could not answer" from "the answer was no", and a pymysql
  exception reaching it would collapse the two.
  """

  def __init__(self, database):
    self._database = database

  ##
  ## >>============================= users =============================>>
  ##

  def find_user_by_username(self, username: str):
    row = self._one(
      "SELECT user_id, username, password_hash, is_active, role"
      " FROM app_user WHERE username = %s",
      (username,),
    )
    return self._as_user(row)

  def find_user_by_id(self, user_id: int):
    row = self._one(
      "SELECT user_id, username, password_hash, is_active, role"
      " FROM app_user WHERE user_id = %s",
      (user_id,),
    )
    return self._as_user(row)

  def insert_user(self, username: str, password_hash: str, role: str) -> int:
    try:
      with self._database.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(
            "INSERT INTO app_user (username, password_hash, role)"
            " VALUES (%s, %s, %s)",
            (username, password_hash, role),
          )
          new_id = cursor.lastrowid
        connector.commit()
      return int(new_id)
    except pymysql.err.IntegrityError as e:
      ##
      ## The UNIQUE index answering, which is the only reliable way to know:
      ## a check-then-insert can be passed by two concurrent creations.
      ##
      raise DuplicateUsername(username) from e
    except AuthUnavailable:
      raise
    except Exception as e:
      raise AuthUnavailable("authentication storage is unavailable") from e

  def set_user_role(self, user_id: int, role: str) -> bool:
    return self._write(
      "UPDATE app_user SET role = %s WHERE user_id = %s",
      (role, user_id),
    ) > 0

  ##
  ## >>============================= sessions =============================>>
  ##

  def insert_session(self, token_hash: str, user_id: int, expires_at: datetime) -> None:
    self._write(
      "INSERT INTO auth_session (token_hash, user_id, expires_at)"
      " VALUES (%s, %s, %s)",
      (token_hash, user_id, expires_at),
    )

  def find_session(self, token_hash: str):
    row = self._one(
      "SELECT token_hash, user_id, expires_at FROM auth_session WHERE token_hash = %s",
      (token_hash,),
    )
    if row is None:
      return None
    return {
      "token_hash": row[0],
      "user_id": int(row[1]),
      "expires_at": row[2],
    }

  def delete_session(self, token_hash: str) -> bool:
    return self._write(
      "DELETE FROM auth_session WHERE token_hash = %s", (token_hash,)
    ) > 0

  def touch_session(self, token_hash: str, seen_at: datetime) -> None:
    ##
    ## Recorded, and deliberately not an extension of the lifetime: expires_at
    ## is untouched, so a session still dies when it was always going to.
    ##
    self._write(
      "UPDATE auth_session SET last_seen_at = %s WHERE token_hash = %s",
      (seen_at, token_hash),
    )

  def delete_expired_sessions(self, now: datetime) -> int:
    return self._write("DELETE FROM auth_session WHERE expires_at <= %s", (now,))

  ##
  ## >>============================= plumbing =============================>>
  ##

  @staticmethod
  def _as_user(row):
    if row is None:
      return None
    return {
      "user_id": int(row[0]),
      "username": row[1],
      "password_hash": row[2],
      "is_active": bool(row[3]),
      "role": row[4],
    }

  def _one(self, statement: str, params: tuple):
    try:
      with self._database.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(statement, params)
          return cursor.fetchone()
    except Exception as e:
      raise AuthUnavailable("authentication storage is unavailable") from e

  def _write(self, statement: str, params: tuple) -> int:
    try:
      with self._database.get_connection() as connector:
        with connector.cursor() as cursor:
          cursor.execute(statement, params)
          affected = cursor.rowcount
        connector.commit()
      return int(affected)
    except Exception as e:
      raise AuthUnavailable("authentication storage is unavailable") from e
