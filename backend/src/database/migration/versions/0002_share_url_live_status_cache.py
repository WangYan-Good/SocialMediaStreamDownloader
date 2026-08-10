"""Cache the most recent known live status on share_url.

Revision ID: 0002_share_url_live_status_cache
Revises: 0001_initial_schema

Adds the three columns the download-history filter reads (``last_live_status``,
``last_checked_at``, ``last_room_id``) plus the two indexes backing its sort keys,
then backfills them from the newest ``room_base`` snapshot per owner.

The backfill deliberately avoids ``UPDATE share_url JOIN room_base``.
``room_base.owner_user_id`` is BIGINT while ``share_url.owner_user_id`` is
VARCHAR(200), so joining the two tables forces a CAST that discards every index and
re-materialises the grouped derived table once per driving row.  Measured on a
database with 7,538 share_url rows and 29,679 room_base rows, that shape took
1,074,546 ms (17.9 minutes).  Computing the per-owner maximum in Python from a
single sequential scan and applying batched primary-key updates keeps the same
result in a few seconds.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0002_share_url_live_status_cache"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


##
## Number of owners updated per round trip during the backfill.
##
_BACKFILL_BATCH_SIZE = 500


def _latest_snapshot_per_owner(connection) -> dict:
  """Return ``{owner_user_id: (snapshot_at, status, room_id)}`` from room_base.

  One sequential scan, maximum resolved in Python.  ``owner_user_id`` is coerced to
  ``str`` because room_base stores it as BIGINT while share_url stores VARCHAR.
  """
  latest: dict = {}
  result = connection.execute(
    sa.text(
      "SELECT owner_user_id, `now`, `status`, `id` "
      "FROM room_base "
      "WHERE owner_user_id IS NOT NULL"
    )
  )
  for owner_user_id, snapshot_at, status, room_id in result:
    if snapshot_at is None:
      continue
    key = str(owner_user_id)
    previous = latest.get(key)
    if previous is None or snapshot_at > previous[0]:
      latest[key] = (snapshot_at, status, room_id)
  return latest


def _backfill(connection) -> None:
  inspector = sa.inspect(connection)
  if "room_base" not in inspector.get_table_names():
    return

  latest = _latest_snapshot_per_owner(connection)
  if not latest:
    return

  statement = sa.text(
    "UPDATE share_url "
    "SET last_live_status = :status, "
    "    last_checked_at  = :checked_at, "
    "    last_room_id     = :room_id "
    "WHERE owner_user_id = :owner_user_id"
  )

  batch: list = []
  for owner_user_id, (snapshot_at, status, room_id) in latest.items():
    batch.append(
      {
        "owner_user_id": owner_user_id,
        "status": None if status is None else int(status),
        "checked_at": snapshot_at,
        "room_id": None if room_id is None else str(room_id),
      }
    )
    if len(batch) >= _BACKFILL_BATCH_SIZE:
      connection.execute(statement, batch)
      batch = []

  if batch:
    connection.execute(statement, batch)


def upgrade() -> None:
  op.add_column(
    "share_url",
    sa.Column("last_live_status", mysql.TINYINT(unsigned=True), nullable=True),
  )
  op.add_column(
    "share_url",
    sa.Column("last_checked_at", mysql.TIMESTAMP(fsp=3), nullable=True),
  )
  op.add_column(
    "share_url",
    sa.Column("last_room_id", sa.String(length=200), nullable=True),
  )
  op.create_index(
    "idx_share_url_last_checked_at", "share_url", ["last_checked_at"], unique=False
  )
  op.create_index(
    "idx_share_url_actived_count", "share_url", ["actived_count"], unique=False
  )

  _backfill(op.get_bind())


def downgrade() -> None:
  op.drop_index("idx_share_url_actived_count", table_name="share_url")
  op.drop_index("idx_share_url_last_checked_at", table_name="share_url")
  op.drop_column("share_url", "last_room_id")
  op.drop_column("share_url", "last_checked_at")
  op.drop_column("share_url", "last_live_status")
