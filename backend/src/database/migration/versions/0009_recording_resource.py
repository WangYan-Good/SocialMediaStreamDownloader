"""Persist one catalog resource for each completed live recording execution.

Revision ID: 0009_recording_resource
Revises: 0008_app_user_aweme_ownership

No live observation or historical file is backfilled: neither the existing
tables nor the filesystem can prove which media file belongs to which past
execution.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0009_recording_resource"
down_revision: Union[str, None] = "0008_app_user_aweme_ownership"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_OPTIONS = {
  "mysql_engine": "InnoDB",
  "mysql_charset": "utf8mb4",
  "mysql_collate": "utf8mb4_0900_ai_ci",
}


def upgrade() -> None:
  op.create_table(
    "recording_record",
    sa.Column(
      "recording_id",
      mysql.BIGINT(unsigned=True),
      autoincrement=True,
      nullable=False,
    ),
    sa.Column("app_user_id", mysql.BIGINT(unsigned=True), nullable=True),
    sa.Column("platform", sa.String(length=20), nullable=False),
    sa.Column("room_id", sa.String(length=200), nullable=True),
    sa.Column("owner_user_id", sa.String(length=200), nullable=True),
    sa.Column("title", sa.String(length=500), nullable=True),
    sa.Column("protocol", sa.String(length=20), nullable=True),
    sa.Column("output_path", sa.String(length=1000), nullable=False),
    sa.Column("started_at", mysql.DATETIME(fsp=3), nullable=True),
    sa.Column("finished_at", mysql.DATETIME(fsp=3), nullable=True),
    sa.Column("source", sa.String(length=20), nullable=False),
    sa.Column(
      "created_at",
      mysql.DATETIME(fsp=3),
      server_default=sa.text("CURRENT_TIMESTAMP(3)"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint("recording_id", name="pk_recording_record"),
    sa.ForeignKeyConstraint(
      ["app_user_id"],
      ["app_user.user_id"],
      name="fk_recording_record_app_user",
      ondelete="SET NULL",
    ),
    **TABLE_OPTIONS,
  )
  op.create_index(
    "ix_recording_record_app_user_finished",
    "recording_record",
    ["app_user_id", "finished_at"],
  )
  op.create_index(
    "ix_recording_record_owner_user_id",
    "recording_record",
    ["owner_user_id"],
  )
  op.create_index(
    "ix_recording_record_finished_at",
    "recording_record",
    ["finished_at"],
  )


def downgrade() -> None:
  op.drop_table("recording_record")
