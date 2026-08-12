from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint, String
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.database.orm.base import Base
from backend.src.database.orm.models.legacy import MYSQL_TABLE_OPTIONS


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
  ## Where this person's files go from now on, and the same kind of fact as
  ## share_url.directory_name: recorded, never derived.  Taking it from whichever
  ## account is marked "main" would move the landing place every time that mark
  ## moved, which is exactly the accident the post path already suffered once.
  ##
  directory_name: Mapped[Optional[str]] = mapped_column(String(100))

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
