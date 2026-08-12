"""Add person, person_account and person_collaboration.

Revision ID: 0004_person_identity
Revises: 0003_aweme_record

One real person may hold a main account, a spare and a matrix account at once,
and a photographer is the same kind of thing - they have accounts of their own,
which is where their work is downloaded from.  Nothing recorded that until now.

Pure DDL, nothing to backfill.  Nicknames cannot supply the relationships even
as a guess: of 1815 accounts there are 1785 distinct nicknames, and only 30
nicknames are shared by more than one account, so the same person's accounts
almost never share a name.  Every row here comes from someone marking it.

The collation is ``utf8mb4_0900_ai_ci``, matching every other table here.  It
is not cosmetic: ``person_account.owner_user_id`` is joined against
``share_url``, ``aweme_record`` and ``live_record``, and MySQL refuses to compare
strings of different collations - "Illegal mix of collations ... for operation
'='" - so a mismatch would fail every one of those queries at runtime.

No foreign key from ``person_account.owner_user_id`` to ``share_url``.  That
table is upserted by the download paths, and a constraint would make a marked
account impossible to clean up; no other table here cross-references it either.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0004_person_identity"
down_revision: Union[str, None] = "0003_aweme_record"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.create_table(
    "person",
    sa.Column(
      "person_id",
      mysql.INTEGER(unsigned=True),
      autoincrement=True,
      nullable=False,
    ),
    sa.Column("display_name", sa.String(length=100), nullable=False),
    ##
    ## Where this person's files go from now on.  Recorded, never derived:
    ## taking it from whichever account is marked "main" would move the landing
    ## place every time that mark moved.
    ##
    sa.Column("directory_name", sa.String(length=100), nullable=True),
    sa.Column("note", sa.String(length=500), nullable=True),
    sa.Column("created_at", mysql.TIMESTAMP(), nullable=True),
    sa.Column("updated_at", mysql.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint("person_id", name="pk_person"),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_0900_ai_ci",
  )

  op.create_table(
    "person_account",
    sa.Column("platform", sa.String(length=20), nullable=False),
    ##
    ## VARCHAR to match share_url.owner_user_id.  room_base stores the same id
    ## as BIGINT, and joining the two forces a CAST that discards every index;
    ## the 0002 migration documents what that cost.
    ##
    sa.Column("owner_user_id", sa.String(length=200), nullable=False),
    sa.Column("person_id", mysql.INTEGER(unsigned=True), nullable=False),
    ##
    ## Required.  Marking an account is a deliberate act and the role is part of
    ## it; "unset" only accumulates rows nobody later remembers how to fill.
    ##
    sa.Column("role", sa.String(length=20), nullable=False),
    ##
    ## Keyed on the account, not the pair: an account belongs to at most one
    ## person, which is the whole content of "this is their spare account".
    ##
    sa.PrimaryKeyConstraint(
      "platform",
      "owner_user_id",
      name="pk_person_account",
    ),
    sa.ForeignKeyConstraint(
      ["person_id"],
      ["person.person_id"],
      name="fk_person_account_person_id_person",
      ondelete="CASCADE",
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_0900_ai_ci",
  )
  op.create_index(
    "idx_person_account_person_id",
    "person_account",
    ["person_id"],
    unique=False,
  )

  op.create_table(
    "person_collaboration",
    sa.Column("photographer_id", mysql.INTEGER(unsigned=True), nullable=False),
    sa.Column("subject_id", mysql.INTEGER(unsigned=True), nullable=False),
    sa.Column("note", sa.String(length=500), nullable=True),
    ##
    ## Directed: one person can be both photographer and subject, and an
    ## undirected edge could not tell those two roles apart.
    ##
    sa.PrimaryKeyConstraint(
      "photographer_id",
      "subject_id",
      name="pk_person_collaboration",
    ),
    sa.ForeignKeyConstraint(
      ["photographer_id"],
      ["person.person_id"],
      name="fk_person_collaboration_photographer_id_person",
      ondelete="CASCADE",
    ),
    sa.ForeignKeyConstraint(
      ["subject_id"],
      ["person.person_id"],
      name="fk_person_collaboration_subject_id_person",
      ondelete="CASCADE",
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_0900_ai_ci",
  )
  op.create_index(
    "idx_person_collaboration_subject_id",
    "person_collaboration",
    ["subject_id"],
    unique=False,
  )


def downgrade() -> None:
  ##
  ## Children first: both carry a foreign key onto person.
  ##
  ## The indexes are not dropped separately.  MySQL keeps the index a foreign key
  ## needs and refuses to drop it while the constraint stands - "Cannot drop
  ## index ...: needed in a foreign key constraint" - and dropping the table
  ## removes its indexes anyway, so the explicit drops were both illegal and
  ## redundant.
  ##
  op.drop_table("person_collaboration")
  op.drop_table("person_account")
  op.drop_table("person")
