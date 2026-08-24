"""Link application users to downloaded post records.

Revision ID: 0008_app_user_aweme_ownership
Revises: 0007_authentication_foundation

The resource row stays global and deduplicated by ``(platform, aweme_id)``.
This relation is the many-to-many ownership fact; historical rows are not
backfilled because the existing database cannot prove who requested them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0008_app_user_aweme_ownership"
down_revision: Union[str, None] = "0007_authentication_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_OPTIONS = {
  "mysql_engine": "InnoDB",
  "mysql_charset": "utf8mb4",
  "mysql_collate": "utf8mb4_0900_ai_ci",
}


def upgrade() -> None:
  op.create_table(
    "app_user_aweme_record",
    sa.Column(
      "app_user_id",
      mysql.BIGINT(unsigned=True),
      nullable=False,
    ),
    sa.Column("platform", sa.String(length=20), nullable=False),
    sa.Column("aweme_id", sa.String(length=64), nullable=False),
    sa.Column(
      "linked_at",
      mysql.DATETIME(fsp=3),
      server_default=sa.text("CURRENT_TIMESTAMP(3)"),
      nullable=False,
    ),
    sa.PrimaryKeyConstraint(
      "app_user_id",
      "platform",
      "aweme_id",
      name="pk_app_user_aweme_record",
    ),
    sa.ForeignKeyConstraint(
      ["app_user_id"],
      ["app_user.user_id"],
      name="fk_app_user_aweme_record_app_user",
      ondelete="CASCADE",
    ),
    sa.ForeignKeyConstraint(
      ["platform", "aweme_id"],
      ["aweme_record.platform", "aweme_record.aweme_id"],
      name="fk_app_user_aweme_record_aweme_record",
      ondelete="CASCADE",
    ),
    **TABLE_OPTIONS,
  )
  op.create_index(
    "ix_app_user_aweme_record_aweme",
    "app_user_aweme_record",
    ["platform", "aweme_id"],
  )


def downgrade() -> None:
  op.drop_table("app_user_aweme_record")
