from datetime import datetime

from sqlalchemy import (
  CheckConstraint,
  ForeignKey,
  Index,
  String,
  UniqueConstraint,
  text,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER
from backend.src.database.orm.base import Base
from backend.src.database.orm.models.legacy import MYSQL_TABLE_OPTIONS


##
## >>============================= why not the `user` table =============================>>
##
##
## This repository already has a table called ``user``.  It is a Douyin profile
## - ``fan_ticket_count``, ``hotsoon_verified``, ``allow_be_located`` - written
## from platform payloads as a side effect of downloading.
##
## Somebody who signs in to this application is a different kind of thing
## entirely.  Rows of the first kind arrive automatically, from data this
## program does not control; a row of the second kind is created deliberately by
## whoever runs the deployment.  Giving the first a password column would mean
## every creator ever downloaded from becomes a potential login, and that a
## platform payload can touch a row that authentication depends on.
##
## So: a separate table, a separate name, and a test that fails if a password
## column ever appears on the platform one.
##


##
## Werkzeug's scrypt hash is ~160 characters - the method and its parameters,
## the salt and the derived key, all in one string.  255 leaves room for a
## future method without another migration; anything near bcrypt's 60 would
## truncate silently, and a truncated hash simply never matches again.
##
PASSWORD_HASH_LENGTH = 255

##
## Long enough not to be a constraint anybody meets, short enough that the
## column stays indexable under utf8mb4.
##
USERNAME_LENGTH = 190


class AppUserModel(Base):
  """Somebody who may sign in to this application.

  Deliberately minimal. Role is an identity fact; resource ownership remains
  represented by relation tables rather than columns on this row.
  """

  __tablename__ = "app_user"
  __table_args__ = (
    UniqueConstraint("username", name="uq_app_user_username"),
    CheckConstraint(
      "role IN ('{}', '{}')".format(ROLE_USER, ROLE_ADMIN),
      # Base's convention expands this to ``ck_app_user_role``.
      name="role",
    ),
    dict(MYSQL_TABLE_OPTIONS, comment="应用登录用户（与平台 user 表无关）"),
  )

  user_id: Mapped[int] = mapped_column(
    mysql.BIGINT(unsigned=True),
    primary_key=True,
    autoincrement=True,
  )

  ##
  ## Canonicalised before it ever gets here - see the authentication service.
  ## The database holds the canonical form so the UNIQUE means what it looks
  ## like it means: two people cannot hold "Alice" and "alice".
  ##
  username: Mapped[str] = mapped_column(String(USERNAME_LENGTH), nullable=False)

  ##
  ## Never a password.  The name is the reminder, and there is deliberately no
  ## column a plaintext one could be written into by mistake.
  ##
  password_hash: Mapped[str] = mapped_column(
    String(PASSWORD_HASH_LENGTH), nullable=False
  )

  role: Mapped[str] = mapped_column(
    String(16),
    nullable=False,
    server_default=text("'{}'".format(ROLE_USER)),
  )

  ##
  ## Disabled rather than deleted.  Deleting a user will one day take their
  ## downloads' provenance with it; refusing them a session does not.
  ##
  is_active: Mapped[bool] = mapped_column(
    mysql.TINYINT(unsigned=False), nullable=False, server_default=text("1")
  )

  created_at: Mapped[datetime] = mapped_column(
    mysql.DATETIME(fsp=3), nullable=False, server_default=text("CURRENT_TIMESTAMP(3)")
  )
  updated_at: Mapped[datetime] = mapped_column(
    mysql.DATETIME(fsp=3),
    nullable=False,
    server_default=text("CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)"),
  )


class AuthSessionModel(Base):
  """One signed-in browser.

  The browser holds a random opaque token.  This table holds only its SHA-256,
  which is what makes a stolen copy of the database useless for impersonation:
  a hash cannot be presented as a cookie, and the token cannot be recovered
  from it.

  Opaque rather than a signed payload on purpose.  A JWT would put the identity
  claim in the browser's hands and make revocation a second mechanism; a row
  that can simply be deleted is revocation.
  """

  __tablename__ = "auth_session"
  __table_args__ = (
    UniqueConstraint("token_hash", name="uq_auth_session_token_hash"),
    ##
    ## Sweeping expired sessions is the one query that touches every row, and
    ## it is the one that would otherwise scan the table.
    ##
    Index("ix_auth_session_expires_at", "expires_at"),
    Index("ix_auth_session_user_id", "user_id"),
    dict(MYSQL_TABLE_OPTIONS, comment="应用登录会话"),
  )

  session_id: Mapped[int] = mapped_column(
    mysql.BIGINT(unsigned=True),
    primary_key=True,
    autoincrement=True,
  )

  ##
  ## SHA-256, hex encoded: 64 characters, fixed.  No salt and no work factor,
  ## deliberately - this is not a password.  The token already carries far more
  ## entropy than any password, so the only thing a slow hash would buy is a
  ## slow lookup on every single request.
  ##
  token_hash: Mapped[str] = mapped_column(String(64), nullable=False)

  ##
  ## CASCADE, so deleting an account cannot leave a session behind that still
  ## points at a row which is no longer there.
  ##
  user_id: Mapped[int] = mapped_column(
    mysql.BIGINT(unsigned=True),
    ForeignKey("app_user.user_id", ondelete="CASCADE", name="fk_auth_session_user_id_app_user"),
    nullable=False,
  )

  created_at: Mapped[datetime] = mapped_column(
    mysql.DATETIME(fsp=3), nullable=False, server_default=text("CURRENT_TIMESTAMP(3)")
  )

  ##
  ## A fixed lifetime, decided when the session is created.  Not extended on
  ## use: a sliding window is a second rule about when a session dies, and this
  ## phase is better served by one that can be reasoned about in a sentence.
  ##
  expires_at: Mapped[datetime] = mapped_column(mysql.DATETIME(fsp=3), nullable=False)

  ##
  ## Recorded, never acted upon here.  It makes "which of my sessions is this"
  ## answerable later without turning it into an extension of the lifetime.
  ##
  last_seen_at: Mapped[datetime] = mapped_column(
    mysql.DATETIME(fsp=3), nullable=False, server_default=text("CURRENT_TIMESTAMP(3)")
  )
