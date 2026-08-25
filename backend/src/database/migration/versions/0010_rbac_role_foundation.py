"""Add the application role fact without granting anybody administrator access.

Revision ID: 0010_rbac_role_foundation
Revises: 0009_recording_resource

Every existing account becomes ``user``. Administrator access is granted only
through the operator CLI after this migration; no row is inferred or promoted.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_rbac_role_foundation"
down_revision: Union[str, None] = "0009_recording_resource"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROLE_CONSTRAINT = "ck_app_user_role"


def upgrade() -> None:
  op.add_column(
    "app_user",
    sa.Column(
      "role",
      sa.String(length=16),
      server_default=sa.text("'user'"),
      nullable=False,
    ),
  )
  op.create_check_constraint(
    op.f(ROLE_CONSTRAINT),
    "app_user",
    "role IN ('user', 'admin')",
  )


def downgrade() -> None:
  op.drop_constraint(op.f(ROLE_CONSTRAINT), "app_user", type_="check")
  op.drop_column("app_user", "role")
