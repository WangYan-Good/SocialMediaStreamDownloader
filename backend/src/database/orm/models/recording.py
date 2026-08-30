from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, text
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
    ##
    ## The identity a crash recovery replays against.  Unique so the database
    ## itself refuses a second row for the same replayed recording - a
    ## check-then-insert in application code cannot do that job, because two
    ## processes replaying the same journal can both pass the check.
    ##
    ## Declared as a constraint rather than a unique Index because that is how
    ## MySQL reflects it, and the schema comparison reads reflection.
    ##
    UniqueConstraint(
      "recovery_key",
      name="uq_recording_record_recovery_key",
    ),
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
  ##
  ## Nullable, and never backfilled: rows written before recovery existed have
  ## no identity a replay could be trusted to match, and MySQL permits many
  ## NULLs under a unique index so they stay legal.
  ##
  ## ``ascii_bin`` so comparison is byte exact - under a case-insensitive
  ## collation two keys differing only in case would collide.
  ##
  recovery_key: Mapped[Optional[str]] = mapped_column(
    mysql.CHAR(length=32, charset="ascii", collation="ascii_bin"),
    nullable=True,
  )
