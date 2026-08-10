"""Add aweme_record for single-post downloads.

Revision ID: 0003_aweme_record
Revises: 0002_share_url_live_status_cache

Creates the table the post download path writes.  Pure DDL: nothing to backfill,
because no earlier version of this program recorded post downloads anywhere.

Author details are deliberately not duplicated here.  ``share_url`` already
carries an unused ``post_share_url`` column, and the post path fills that, so one
owner keeps one row there however many of their posts are fetched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0003_aweme_record"
down_revision: Union[str, None] = "0002_share_url_live_status_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
  op.create_table(
    "aweme_record",
    sa.Column("platform", sa.String(length=20), nullable=False),
    sa.Column("aweme_id", sa.String(length=64), nullable=False),
    ##
    ## VARCHAR to match share_url.owner_user_id; see 0002 for what casting
    ## between that and room_base's BIGINT costs.
    ##
    sa.Column("owner_user_id", sa.String(length=200), nullable=True),
    sa.Column("sec_user_id", sa.String(length=200), nullable=True),
    sa.Column("aweme_type", sa.String(length=20), nullable=True),
    sa.Column("desc", sa.String(length=500), nullable=True),
    sa.Column("create_time", mysql.TIMESTAMP(), nullable=True),
    sa.Column("downloaded_at", mysql.TIMESTAMP(fsp=3), nullable=False),
    ##
    ## media_count is what the run planned to fetch, which the media switches
    ## decide - not a count of what the post objectively holds.  saved_count is
    ## what landed, so saved_count < media_count marks a partial download.
    ##
    sa.Column("media_count", mysql.INTEGER(unsigned=True), nullable=False),
    sa.Column("saved_count", mysql.INTEGER(unsigned=True), nullable=False),
    sa.Column("save_dir", sa.String(length=500), nullable=True),
    sa.Column("source", sa.String(length=10), nullable=True),
    sa.PrimaryKeyConstraint(
      "platform",
      "aweme_id",
      name=op.f("pk_aweme_record"),
    ),
    mysql_charset="utf8mb4",
    mysql_collate="utf8mb4_0900_ai_ci",
    mysql_engine="InnoDB",
  )
  op.create_index(
    "idx_aweme_record_owner_user_id",
    "aweme_record",
    ["owner_user_id"],
    unique=False,
  )
  op.create_index(
    "idx_aweme_record_downloaded_at",
    "aweme_record",
    ["downloaded_at"],
    unique=False,
  )


def downgrade() -> None:
  op.drop_index("idx_aweme_record_downloaded_at", table_name="aweme_record")
  op.drop_index("idx_aweme_record_owner_user_id", table_name="aweme_record")
  op.drop_table("aweme_record")
