"""Give a recording an identity a crash recovery can replay without duplicating it.

Revision ID: 0011_recording_recovery_key
Revises: 0010_rbac_role_foundation

A future recovery journal re-presents a finished recording after a crash. The
journal is durable and the insert may already have succeeded, so the same entry
can arrive twice: once before the crash, once on restart. Without an identity
the database itself enforces, the second arrival inserts a second row and one
broadcast becomes two library resources.

``recovery_key`` is that identity, and the unique constraint is what makes it
one. A check-then-insert in application code cannot do this job - two processes
replaying the same journal can both pass the check - so the constraint is the
concurrency authority and the application only decides what to do when it
fires.

Nullable, and nothing is backfilled. Rows written before this migration have no
recovery identity and none can be invented for them: neither the row nor the
file on disk can establish one that a later replay could be trusted to match.
MySQL permits many NULLs under a unique constraint, so those rows stay legal and
ordinary recordings continue to be inserted without a key.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0011_recording_recovery_key"
down_revision: Union[str, None] = "0010_rbac_role_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RECOVERY_KEY_INDEX = "uq_recording_record_recovery_key"


def upgrade() -> None:
  op.add_column(
    "recording_record",
    sa.Column(
      "recovery_key",
      ##
      ## Fixed width because the value is: exactly 32 lowercase hex characters.
      ## ASCII with a binary collation so comparison is case sensitive and
      ## byte exact - under a case-insensitive collation two keys differing
      ## only in case would collide, and the constraint would refuse a replay
      ## that is not one.
      ##
      mysql.CHAR(length=32, charset="ascii", collation="ascii_bin"),
      nullable=True,
    ),
  )
  ##
  ## A unique index rather than a table constraint: MySQL implements a unique
  ## constraint as an index anyway, and naming the index keeps the downgrade
  ## unambiguous.
  ##
  op.create_index(
    RECOVERY_KEY_INDEX,
    "recording_record",
    ["recovery_key"],
    unique=True,
  )


def downgrade() -> None:
  op.drop_index(RECOVERY_KEY_INDEX, table_name="recording_record")
  op.drop_column("recording_record", "recovery_key")
