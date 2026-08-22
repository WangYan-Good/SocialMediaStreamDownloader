from datetime import datetime
from typing import Optional

from sqlalchemy import (
  Computed,
  ForeignKey,
  Index,
  PrimaryKeyConstraint,
  String,
  UniqueConstraint,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.database.orm.base import Base
from backend.src.database.orm.models.legacy import MYSQL_TABLE_OPTIONS


##
## How "at most one main per person" is expressed to the database.
##
## MySQL has no partial index, so the rule is carried by a generated column that
## is the person's id for a main row and NULL for every other role, plus an
## ordinary UNIQUE.  MySQL allows any number of NULLs in a unique index, which
## gives 0-or-1 without saying anything at all about how many spares or matrix
## accounts a person holds.
##
## The string must stay identical to ``MAIN_PROJECTION`` in migration 0006:
## these two and the DDL MySQL ends up holding are one fact, and the schema
## comparison at start-up is what notices if they drift.
##
MAIN_PROJECTION = "CASE WHEN role = 'main' THEN person_id ELSE NULL END"
MAIN_UNIQUE_NAME = "uq_person_account_main_person"


##
## Which account a person holds this one as.  Stored as a string rather than a
## database enum, matching user_status and video_quality elsewhere; the values
## are checked in the application layer where the error can name the field.
##
ROLE_MAIN = "main"
ROLE_ALT = "alt"
ROLE_MATRIX = "matrix"
ACCOUNT_ROLES = (ROLE_MAIN, ROLE_ALT, ROLE_MATRIX)


class PersonModel(Base):
  """A real person, independent of any platform account.

  Someone may hold a main account, a spare and a matrix account at once, and a
  photographer is the same kind of thing - they have accounts of their own,
  which is where their work is downloaded from.  So there is no separate
  photographer table: a photographer is a person who appears on the left of a
  collaboration.  Splitting them would store one human twice, and renaming,
  re-filing or marking a spare account would then have to be done in both
  places.

  Rows are created on demand.  An account that was never marked has no row here
  and behaves exactly as it did before this table existed.
  """

  __tablename__ = "person"
  __table_args__ = (MYSQL_TABLE_OPTIONS,)

  person_id: Mapped[int] = mapped_column(
    mysql.INTEGER(unsigned=True),
    primary_key=True,
    autoincrement=True,
  )

  display_name: Mapped[str] = mapped_column(String(100), nullable=False)

  ##
  ## No folder of their own.  If a person exists then one of their accounts is
  ## the main one, and its share_url.directory_name already says where their
  ## files live; a copy here would only be somewhere for the two to disagree.
  ##
  note: Mapped[Optional[str]] = mapped_column(String(500))

  created_at: Mapped[Optional[datetime]] = mapped_column(mysql.TIMESTAMP())
  updated_at: Mapped[Optional[datetime]] = mapped_column(mysql.TIMESTAMP())


class PersonAccountModel(Base):
  """Which person an account belongs to.

  The primary key is the account, not the pair.  An account belongs to at most
  one person - that is the whole content of "this is the same person's spare
  account" - and keying on the pair would let one account hang under two people,
  leaving "whose account is this?" unanswerable.

  ``owner_user_id`` deliberately carries no foreign key to ``share_url``.  That
  table is upserted by the download paths, and a constraint here would make a
  marked account impossible to clean up; no other table in this database
  cross-references it either.
  """

  __tablename__ = "person_account"
  __table_args__ = (
    PrimaryKeyConstraint("platform", "owner_user_id"),
    Index("idx_person_account_person_id", "person_id"),
    ##
    ## The last line of defence for "at most one main per person".
    ##
    ## The service already refuses a second main, in a transaction and holding
    ## the person's row, and that is what produces a 409 somebody can act on.
    ## This is for the writes it never sees - a repair script, a console, a
    ## future path that forgets - because with two mains ``find_person_folder``
    ## joins on ``role = 'main'`` and takes LIMIT 1 with no ordering, so the
    ## folder a person's downloads land in becomes whichever row came back.
    ##
    UniqueConstraint("main_person_id", name=MAIN_UNIQUE_NAME),
    MYSQL_TABLE_OPTIONS,
  )

  platform: Mapped[str] = mapped_column(String(20), nullable=False)

  ##
  ## VARCHAR to match share_url.owner_user_id.  room_base stores the same id as
  ## BIGINT, and joining the two forces a CAST that discards every index; the
  ## 0002 migration documents what that cost.
  ##
  owner_user_id: Mapped[str] = mapped_column(String(200), nullable=False)

  person_id: Mapped[int] = mapped_column(
    mysql.INTEGER(unsigned=True),
    ForeignKey("person.person_id", ondelete="CASCADE"),
    nullable=False,
  )

  ##
  ## Required.  Marking an account is a deliberate act and the role is part of
  ## it; allowing "unset" only accumulates rows nobody later remembers how to
  ## fill.  How many accounts share a role is not constrained - which one is the
  ## main account is a judgement call, and nothing depends on it because the
  ## folder comes from the person, not from the main account.
  ##
  role: Mapped[str] = mapped_column(String(20), nullable=False)

  ##
  ## Generated, never written.  A column the application could set would be a
  ## second place for "is this the main account" to live, and the two would
  ## disagree the first time one was updated without the other.
  ##
  ## VIRTUAL rather than STORED: it is derived from two columns of its own row,
  ## so materialising it would cost space to store what MySQL can read for free,
  ## and a virtual column is still indexable in MySQL 8.
  ##
  main_person_id: Mapped[Optional[int]] = mapped_column(
    mysql.INTEGER(unsigned=True),
    Computed(MAIN_PROJECTION, persisted=False),
    nullable=True,
  )


class PersonCollaborationModel(Base):
  """A photographer works with a subject.

  Directed, because one person can be both: a photographer who also streams
  appears on the left of one row and the right of another, and an undirected
  edge could not tell those apart.

  Recorded between people rather than against individual posts.  Marking 1547
  posts one by one, and every new post after them, costs more than the precision
  is worth here; a pair is marked once.
  """

  __tablename__ = "person_collaboration"
  __table_args__ = (
    PrimaryKeyConstraint("photographer_id", "subject_id"),
    Index("idx_person_collaboration_subject_id", "subject_id"),
    MYSQL_TABLE_OPTIONS,
  )

  photographer_id: Mapped[int] = mapped_column(
    mysql.INTEGER(unsigned=True),
    ForeignKey("person.person_id", ondelete="CASCADE"),
    nullable=False,
  )
  subject_id: Mapped[int] = mapped_column(
    mysql.INTEGER(unsigned=True),
    ForeignKey("person.person_id", ondelete="CASCADE"),
    nullable=False,
  )

  note: Mapped[Optional[str]] = mapped_column(String(500))
