from typing import Optional

from sqlalchemy import Index, String, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.database.orm.base import Base


MYSQL_TABLE_OPTIONS = {
  "mysql_engine": "InnoDB",
  "mysql_charset": "utf8mb4",
  "mysql_collate": "utf8mb4_0900_ai_ci",
}


class ShareUrlModel(Base):
  __tablename__ = "share_url"
  __table_args__ = (
    Index("idx_nickname", "nickname"),
    MYSQL_TABLE_OPTIONS,
  )

  owner_user_id: Mapped[str] = mapped_column(String(200), primary_key=True)
  sec_user_id: Mapped[Optional[str]] = mapped_column(String(200))
  nickname: Mapped[Optional[str]] = mapped_column(String(50))
  post_share_url: Mapped[Optional[str]] = mapped_column(String(100))
  live_share_url: Mapped[Optional[str]] = mapped_column(String(100))
  directory_name: Mapped[Optional[str]] = mapped_column(String(100))
  user_status: Mapped[Optional[str]] = mapped_column(String(100))
  actived_count: Mapped[int] = mapped_column(
    mysql.INTEGER(unsigned=True),
    nullable=False,
    server_default=text("0"),
  )


class FavoriteOwnerModel(Base):
  __tablename__ = "favorite_owner"
  __table_args__ = MYSQL_TABLE_OPTIONS

  owner_user_id: Mapped[str] = mapped_column(String(200), primary_key=True)
  platform: Mapped[str] = mapped_column(String(20), primary_key=True)
  score: Mapped[int] = mapped_column(
    mysql.TINYINT(unsigned=True),
    nullable=False,
    server_default=text("0"),
  )
