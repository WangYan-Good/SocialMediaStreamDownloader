"""Give the application an identity of its own.

The revision id is kept short on purpose: ``alembic_version.version_num`` is
VARCHAR(32), and a longer id fails at the moment the migration tries to record
itself - after the DDL has already run.

Revision ID: 0007_authentication_foundation
Revises: 0006_person_main_unique

Two tables, and nothing touched.

``app_user`` is somebody who may sign in.  It is emphatically not the existing
``user`` table, which is a Douyin profile - ``fan_ticket_count``,
``hotsoon_verified``, ``allow_be_located`` - written from platform payloads as
a side effect of downloading.  Those rows arrive automatically, from data this
program does not control; putting a password column on them would make every
creator ever downloaded from into a potential login, and would let a platform
payload write to a row authentication depends on.  So the application identity
gets its own table, and this migration deliberately alters nothing that
already exists.

``auth_session`` is one signed-in browser.  The browser holds a random opaque
token; this table holds only its SHA-256.  That asymmetry is the point: a copy
of the database - a backup, a dump, a support session - cannot be turned into
a session cookie, because a hash cannot be presented as one and the token
cannot be recovered from it.

Opaque rather than a signed payload.  A JWT would hand the identity claim to
the browser and make revoking one a second mechanism bolted on afterwards; a
row that can be deleted is already revocation.

Nothing is backfilled.  There are no accounts to migrate - the first one is
created deliberately, through the CLI, by whoever runs the deployment.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0007_authentication_foundation"
down_revision: Union[str, None] = "0006_person_main_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


##
## Matching the rest of the schema rather than the SQLAlchemy defaults, so a
## table created here compares equal to one created by the ORM at start-up.
##
TABLE_OPTIONS = {
  "mysql_engine": "InnoDB",
  "mysql_charset": "utf8mb4",
  "mysql_collate": "utf8mb4_0900_ai_ci",
}


def upgrade() -> None:
  op.create_table(
    "app_user",
    sa.Column("user_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    ##
    ## Canonicalised by the service before it arrives, so this UNIQUE means
    ## what it appears to mean: "Alice" and "alice" are one account, not two.
    ##
    sa.Column("username", sa.String(length=190), nullable=False),
    ##
    ## Wide enough for Werkzeug's scrypt output, which is ~160 characters of
    ## method, parameters, salt and derived key.  A column sized for bcrypt's
    ## 60 would truncate it, and a truncated hash never matches again.
    ##
    sa.Column("password_hash", sa.String(length=255), nullable=False),
    ##
    ## Disabled rather than deleted.  Refusing somebody a session does not
    ## disturb anything their account is referenced by.
    ##
    sa.Column(
      "is_active",
      mysql.TINYINT(unsigned=False),
      server_default=sa.text("1"),
      nullable=False,
    ),
    sa.Column(
      "created_at",
      mysql.DATETIME(fsp=3),
      server_default=sa.text("CURRENT_TIMESTAMP(3)"),
      nullable=False,
    ),
    sa.Column(
      "updated_at",
      mysql.DATETIME(fsp=3),
      server_default=sa.text("CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint("user_id", name="pk_app_user"),
    sa.UniqueConstraint("username", name="uq_app_user_username"),
    comment="应用登录用户（与平台 user 表无关）",
    **TABLE_OPTIONS,
  )

  op.create_table(
    "auth_session",
    sa.Column("session_id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
    ##
    ## SHA-256, hex encoded: 64 characters, fixed width.  No salt and no work
    ## factor, deliberately - this is not a password.  The token carries far
    ## more entropy than any password could, so a slow hash would buy nothing
    ## and cost a slow lookup on every authenticated request.
    ##
    sa.Column("token_hash", sa.String(length=64), nullable=False),
    sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
    sa.Column(
      "created_at",
      mysql.DATETIME(fsp=3),
      server_default=sa.text("CURRENT_TIMESTAMP(3)"),
      nullable=False,
    ),
    sa.Column("expires_at", mysql.DATETIME(fsp=3), nullable=False),
    sa.Column(
      "last_seen_at",
      mysql.DATETIME(fsp=3),
      server_default=sa.text("CURRENT_TIMESTAMP(3)"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint("session_id", name="pk_auth_session"),
    sa.UniqueConstraint("token_hash", name="uq_auth_session_token_hash"),
    ##
    ## CASCADE: deleting an account must not leave a session pointing at a row
    ## that is no longer there - which is either an orphan that still
    ## authenticates or a crash on every request, depending on how the lookup
    ## happens to be written.
    ##
    sa.ForeignKeyConstraint(
      ["user_id"],
      ["app_user.user_id"],
      name="fk_auth_session_user_id_app_user",
      ondelete="CASCADE",
    ),
    comment="应用登录会话",
    **TABLE_OPTIONS,
  )

  ##
  ## Sweeping expired sessions is the one query that would otherwise scan the
  ## whole table.
  ##
  op.create_index("ix_auth_session_expires_at", "auth_session", ["expires_at"])
  op.create_index("ix_auth_session_user_id", "auth_session", ["user_id"])


def downgrade() -> None:
  ##
  ## The tables, and only the tables.
  ##
  ## Dropping the indexes first looks tidier and is wrong: MySQL uses
  ## ``ix_auth_session_user_id`` to back the foreign key on ``user_id``, and
  ## refuses to drop an index a constraint still needs -
  ##
  ##     (1553, "Cannot drop index 'ix_auth_session_user_id': needed in a
  ##      foreign key constraint")
  ##
  ## ``DROP TABLE`` takes the indexes with it, so there is nothing to do by
  ## hand. This is the kind of thing only a real MySQL can say - the source
  ## reads perfectly either way.
  ##
  ## Sessions before users: a foreign key cannot outlive the table it points
  ## at, so dropping app_user first fails on any database that enforces it.
  ##
  op.drop_table("auth_session")
  op.drop_table("app_user")
