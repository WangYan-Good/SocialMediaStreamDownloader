from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.database.orm.base import Base
from backend.src.database.orm.models.legacy import MYSQL_TABLE_OPTIONS


class RecordingRecordModel(Base):
  """One persistent media resource produced by one recording execution."""

  __tablename__ = "recording_record"
  __table_args__ = (
    Index(
      "ix_recording_record_app_user_finished",
      "app_user_id",
      "finished_at",
    ),
    Index("ix_recording_record_owner_user_id", "owner_user_id"),
    Index("ix_recording_record_finished_at", "finished_at"),
    MYSQL_TABLE_OPTIONS,
  )

  recording_id: Mapped[int] = mapped_column(
    mysql.BIGINT(unsigned=True),
    primary_key=True,
    autoincrement=True,
  )
  app_user_id: Mapped[Optional[int]] = mapped_column(
    mysql.BIGINT(unsigned=True),
    ForeignKey(
      "app_user.user_id",
      name="fk_recording_record_app_user",
      ondelete="SET NULL",
    ),
  )
  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[Optional[str]] = mapped_column(String(200))
  owner_user_id: Mapped[Optional[str]] = mapped_column(String(200))
  title: Mapped[Optional[str]] = mapped_column(String(500))
  protocol: Mapped[Optional[str]] = mapped_column(String(20))
  output_path: Mapped[str] = mapped_column(String(1000), nullable=False)
  started_at: Mapped[Optional[datetime]] = mapped_column(mysql.DATETIME(fsp=3))
  finished_at: Mapped[Optional[datetime]] = mapped_column(mysql.DATETIME(fsp=3))
  source: Mapped[str] = mapped_column(String(20), nullable=False)
  created_at: Mapped[datetime] = mapped_column(
    mysql.DATETIME(fsp=3),
    nullable=False,
    server_default=text("CURRENT_TIMESTAMP(3)"),
  )
