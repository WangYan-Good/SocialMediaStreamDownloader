from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Index, PrimaryKeyConstraint, String, UniqueConstraint, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.database.orm.base import Base
from backend.src.database.orm.models.legacy import MYSQL_TABLE_OPTIONS


class RoomStatsModel(Base):
  __tablename__ = "room_stats"
  __table_args__ = (
    PrimaryKeyConstraint('now', 'platform', 'room_id'),
    dict(MYSQL_TABLE_OPTIONS),
  )

  now: Mapped[datetime] = mapped_column(mysql.TIMESTAMP(fsp=3), nullable=False)
  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[str] = mapped_column(String(200), nullable=False)
  comment_count: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  digg_count: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  dou_plus_promotion: Mapped[Optional[str]] = mapped_column(mysql.TINYTEXT(), nullable=True)
  enter_count: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  fan_ticket: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  follow_count: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  gift_uv_count: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=False), nullable=True, server_default=text("0"))
  like_count: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  money: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  total_user: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=False), nullable=True, server_default=text("0"))
  total_user_desp: Mapped[Optional[str]] = mapped_column(mysql.TEXT(), nullable=True)
  total_user_str: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
  up_right_stats_str: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
  up_right_stats_str_complete: Mapped[Optional[str]] = mapped_column(mysql.TINYTEXT(), nullable=True)
  user_count_str: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
  watermelon: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  welfare_donation_amount: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  user_count_composition_city: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=False), nullable=True, server_default=text("0"))
  user_count_composition_my_follow: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  user_count_composition_other: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))
  user_count_composition_video_detail: Mapped[Optional[int]] = mapped_column(mysql.BIGINT(unsigned=False), nullable=True, server_default=text("0"))


class RoomAdminUserIdModel(Base):
  __tablename__ = "room_admin_user_id"
  __table_args__ = (
    PrimaryKeyConstraint('index', 'platform', 'room_id'),
    UniqueConstraint('platform', 'room_id', 'admin_user_id', name="unique_record"),
    dict(MYSQL_TABLE_OPTIONS),
  )

  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[str] = mapped_column(String(200), nullable=False)
  index: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=False), nullable=False, autoincrement=True)
  admin_user_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class RoomAdminUserOpenIdModel(Base):
  __tablename__ = "room_admin_user_open_id"
  __table_args__ = (
    PrimaryKeyConstraint('index', 'platform', 'room_id'),
    UniqueConstraint('platform', 'room_id', 'admin_user_open_id', name="unique_record"),
    dict(MYSQL_TABLE_OPTIONS),
  )

  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[str] = mapped_column(String(200), nullable=False)
  index: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=False), nullable=False, autoincrement=True)
  admin_user_open_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class RoomDecoModel(Base):
  __tablename__ = "room_deco"
  __table_args__ = (
    PrimaryKeyConstraint('deco_index', 'platform', 'room_id'),
    Index("idx_deco_type", 'deco_type'),
    dict(MYSQL_TABLE_OPTIONS),
  )

  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[str] = mapped_column(String(200), nullable=False)
  deco_index: Mapped[int] = mapped_column(mysql.TINYINT(unsigned=True), nullable=False, autoincrement=True)
  deco_id: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  deco_type: Mapped[Optional[int]] = mapped_column(mysql.TINYINT(unsigned=True), nullable=True)
  kind: Mapped[Optional[int]] = mapped_column(mysql.TINYINT(unsigned=True), nullable=True)
  audit_text_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
  content: Mapped[Optional[str]] = mapped_column(mysql.TINYTEXT(), nullable=True)
  status: Mapped[Optional[int]] = mapped_column(mysql.TINYINT(unsigned=True), nullable=True)
  text_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
  text_size: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  position_x: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  position_y: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  width: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  height: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  max_length: Mapped[Optional[int]] = mapped_column(mysql.TINYINT(unsigned=True), nullable=True)
  sub_type: Mapped[Optional[int]] = mapped_column(mysql.TINYINT(unsigned=True), nullable=True)
  text_image_adjustable_start_position: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  text_image_adjustable_end_position: Mapped[Optional[int]] = mapped_column(mysql.INTEGER(unsigned=True), nullable=True)
  input_rect: Mapped[Optional[Any]] = mapped_column(mysql.JSON(), nullable=True)
  nine_patch_image: Mapped[Optional[Any]] = mapped_column(mysql.JSON(), nullable=True)
  reservation: Mapped[Optional[Any]] = mapped_column(mysql.JSON(), nullable=True)
  text_font_config: Mapped[Optional[Any]] = mapped_column(mysql.JSON(), nullable=True)
  text_special_effects: Mapped[Optional[Any]] = mapped_column(mysql.JSON(), nullable=True)
  image_data: Mapped[Optional[Any]] = mapped_column(mysql.JSON(), nullable=True)


class FansGroupAdminUserIdModel(Base):
  __tablename__ = "fans_group_admin_user_id"
  __table_args__ = (
    PrimaryKeyConstraint('index', 'platform', 'room_id'),
    UniqueConstraint('platform', 'room_id', 'fans_group_admin_user_id', name="unique_record"),
    dict(MYSQL_TABLE_OPTIONS),
  )

  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[str] = mapped_column(String(200), nullable=False)
  index: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=False), nullable=False, autoincrement=True)
  fans_group_admin_user_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class FansGroupAdminUserOpenIdModel(Base):
  __tablename__ = "fans_group_admin_user_open_id"
  __table_args__ = (
    PrimaryKeyConstraint('index', 'platform', 'room_id'),
    UniqueConstraint('platform', 'room_id', 'fans_group_admin_user_open_id', name="unique_record"),
    dict(MYSQL_TABLE_OPTIONS),
  )

  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  room_id: Mapped[str] = mapped_column(String(200), nullable=False)
  index: Mapped[int] = mapped_column(mysql.BIGINT(unsigned=False), nullable=False, autoincrement=True)
  fans_group_admin_user_open_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
