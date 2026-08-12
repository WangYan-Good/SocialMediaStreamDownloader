"""Drop person.directory_name.

The revision id is kept short on purpose: ``alembic_version.version_num`` is
VARCHAR(32), and a longer id fails at the moment the migration tries to record
itself - after the DDL has already run.

Revision ID: 0005_drop_person_directory
Revises: 0004_person_identity

A person does not need a folder of their own.  If a person exists then one of
their accounts is the main one, and that account's ``share_url.directory_name``
is already the fact of where their files live.  Holding a second copy on
``person`` only created somewhere for the two to disagree - and they would, the
moment either was edited without the other.

Every account of a person now resolves to the main account's folder, and the
sub-accounts' own rows are kept equal to it, so the database gives one answer.

Nothing is backfilled.  The column was added in 0004 and released without a way
to reach it that did not also set the main account's folder, so any value here
is either absent or a duplicate of the one being kept.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_drop_person_directory"
down_revision: Union[str, None] = "0004_person_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.drop_column("person", "directory_name")


def downgrade() -> None:
  op.add_column(
    "person",
    sa.Column("directory_name", sa.String(length=100), nullable=True),
  )
