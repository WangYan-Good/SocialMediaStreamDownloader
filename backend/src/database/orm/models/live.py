from datetime import datetime
from typing import Optional

from sqlalchemy import PrimaryKeyConstraint, String
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.database.orm.base import Base
from backend.src.database.orm.models.legacy import MYSQL_TABLE_OPTIONS


class LiveRecordModel(Base):
  __tablename__ = "live_record"
  __table_args__ = (
    PrimaryKeyConstraint("now", "platform", "owner_user_id", "room_id"),
    MYSQL_TABLE_OPTIONS,
  )

  now: Mapped[datetime] = mapped_column(mysql.TIMESTAMP(fsp=3), nullable=False)
  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[str] = mapped_column(String(200), nullable=False)
  owner_user_id: Mapped[str] = mapped_column(String(200), nullable=False)
  user_id: Mapped[Optional[str]] = mapped_column(String(200))
  start_time: Mapped[Optional[datetime]] = mapped_column(mysql.TIMESTAMP())
  finish_time: Mapped[Optional[datetime]] = mapped_column(mysql.TIMESTAMP())
  status_code: Mapped[Optional[int]] = mapped_column(mysql.TINYINT(unsigned=True))
