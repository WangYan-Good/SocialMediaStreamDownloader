"""Let the database refuse a second main account for one person.

The revision id is kept short on purpose: ``alembic_version.version_num`` is
VARCHAR(32), and a longer id fails at the moment the migration tries to record
itself - after the DDL has already run.

Revision ID: 0006_person_main_unique
Revises: 0005_drop_person_directory

The application already refuses a second main.  It does so inside one
transaction, holding the person's row, and answers the user a 409 they can act
on - and that stays exactly where it is, because a database error is not a
sentence anybody wants to read.

What the application cannot do is speak for a write it never sees.  A repair
script, a console session, a future code path that forgets: any of them can put
two ``role = 'main'`` rows under one ``person_id``, and nothing downstream is
prepared for that.  ``find_person_folder`` joins on ``role = 'main'`` and takes
``LIMIT 1`` with no ordering, so with two mains the folder a person's downloads
land in becomes whichever row the server happened to return - it can differ
between two calls, and the sub-accounts get aligned to one of them.

MySQL has no partial index, so "unique among the rows where role = 'main'"
cannot be written directly.  It is spelled instead as a generated column that is
the person's id for a main and NULL for everything else, plus an ordinary
UNIQUE.  MySQL permits any number of NULLs in a unique index, which gives
exactly the shape wanted:

    0 mains  ->  no non-NULL value        -> allowed
    1 main   ->  one non-NULL value       -> allowed
    2 mains  ->  the same value twice     -> refused

and leaves alt and matrix entirely uncounted, which matters: a person really may
hold five spares.

The column is VIRTUAL rather than STORED.  It is derived from two columns in its
own row, so there is nothing to gain by materialising it, and a virtual column
costs no row space while still being indexable in MySQL 8.

``role`` is compared with ``=`` under this table's ``utf8mb4_0900_ai_ci``
collation, so a row written as ``'MAIN'`` counts as a main here.  That is
deliberate and matches every other query in this codebase - ``find_person_folder``
and ``align_accounts_to_main`` both say ``role = 'main'`` - so a case-variant row
cannot slip past this constraint while still being treated as the main
everywhere else.

Nothing is backfilled and nothing is repaired.  See ``upgrade`` for why.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0006_person_main_unique"
down_revision: Union[str, None] = "0005_drop_person_directory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "uq_person_account_main_person"
COLUMN_NAME = "main_person_id"

##
## Written out rather than built, so the expression in the migration, the one on
## the model and the one MySQL ends up holding are all the same string.
##
MAIN_PROJECTION = "CASE WHEN role = 'main' THEN person_id ELSE NULL END"

_DUPLICATE_MAINS = sa.text(
  "SELECT person_id, COUNT(*) AS main_count "
  "FROM person_account "
  "WHERE role = 'main' "
  "GROUP BY person_id "
  "HAVING COUNT(*) > 1 "
  "ORDER BY person_id"
)


def upgrade() -> None:
  ##
  ## Checked before the constraint is added, and refused rather than repaired.
  ##
  ## Which of two mains is the real one is a fact about somebody's accounts that
  ## nothing here knows.  Demoting the wrong one is silent and expensive: the
  ## folder every other account of that person files under moves to the survivor,
  ## and the previous value is not written down anywhere afterwards.  So this
  ## stops and says who is affected, and a person decides.
  ##
  ## Doing it in this order also means the failure is legible.  Adding the index
  ## first would produce MySQL's own duplicate-key message, which names one
  ## arbitrary row and not the people who need looking at.
  ##
  duplicates = op.get_bind().execute(_DUPLICATE_MAINS).fetchall()
  if duplicates:
    listed = ", ".join(
      "person_id={} has {} main accounts".format(row[0], row[1])
      for row in duplicates
    )
    raise RuntimeError(
      "cannot enforce one main account per person: {}. "
      "Resolve these by hand - decide which account is the main one and change "
      "the others to alt or matrix - then run the migration again. "
      "Nothing has been modified.".format(listed)
    )

  op.add_column(
    "person_account",
    sa.Column(
      COLUMN_NAME,
      mysql.INTEGER(unsigned=True),
      sa.Computed(MAIN_PROJECTION, persisted=False),
      nullable=True,
    ),
  )
  op.create_index(INDEX_NAME, "person_account", [COLUMN_NAME], unique=True)


def downgrade() -> None:
  ##
  ## The index first: MySQL will not drop a column an index still refers to.
  ##
  ## Schema only.  Rows are left exactly as they are - a database that could
  ## hold two mains again is the state this revision was applied *from*, and
  ## deleting somebody's account to get back there would be absurd.
  ##
  op.drop_index(INDEX_NAME, table_name="person_account")
  op.drop_column("person_account", COLUMN_NAME)
