from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKeyConstraint, Index, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.database.orm.base import Base
from backend.src.database.orm.models.legacy import MYSQL_TABLE_OPTIONS


class AwemeRecordModel(Base):
  """One row per downloaded post.

  Shaped like ``live_record``: one row per event rather than a snapshot of
  platform state.  The primary key is the dedup key - re-submitting the same
  link finds the existing row instead of downloading a second copy.

  Author details are not repeated here.  They live on ``share_url``, which the
  post path fills through ``post_share_url``, so one owner keeps one row there
  no matter how many of their posts are downloaded.
  """

  __tablename__ = "aweme_record"
  __table_args__ = (
    PrimaryKeyConstraint("platform", "aweme_id"),
    Index("idx_aweme_record_owner_user_id", "owner_user_id"),
    Index("idx_aweme_record_downloaded_at", "downloaded_at"),
    MYSQL_TABLE_OPTIONS,
  )

  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  aweme_id: Mapped[str] = mapped_column(String(64), nullable=False)

  ##
  ## VARCHAR to match share_url.owner_user_id.  room_base stores the same id as
  ## BIGINT, and joining the two forces a CAST that discards every index; the
  ## 0002 migration documents what that cost.
  ##
  owner_user_id: Mapped[Optional[str]] = mapped_column(String(200))
  sec_user_id: Mapped[Optional[str]] = mapped_column(String(200))

  aweme_type: Mapped[Optional[str]] = mapped_column(String(20))
  desc: Mapped[Optional[str]] = mapped_column(String(500))
  create_time: Mapped[Optional[datetime]] = mapped_column(mysql.TIMESTAMP())
  downloaded_at: Mapped[datetime] = mapped_column(
    mysql.TIMESTAMP(fsp=3),
    nullable=False,
  )

  ##
  ## media_count is how many files the run *planned* to fetch, which the media
  ## switches decide - it is not a count of what the post objectively holds.
  ## saved_count below it is what actually landed, so saved_count < media_count
  ## marks a partial download that a re-run can finish.
  ##
  media_count: Mapped[int] = mapped_column(
    mysql.INTEGER(unsigned=True),
    nullable=False,
  )
  saved_count: Mapped[int] = mapped_column(
    mysql.INTEGER(unsigned=True),
    nullable=False,
  )

  save_dir: Mapped[Optional[str]] = mapped_column(String(500))

  ##
  ## Which route answered: "api" or "html".  Kept so the rate at which the
  ## signed API stops working is observable from the data.
  ##
  source: Mapped[Optional[str]] = mapped_column(String(10))


class AppUserAwemeRecordModel(Base):
  """Many-to-many visibility of recorded posts for application users."""

  __tablename__ = "app_user_aweme_record"
  __table_args__ = (
    PrimaryKeyConstraint(
      "app_user_id",
      "platform",
      "aweme_id",
      name="pk_app_user_aweme_record",
    ),
    ForeignKeyConstraint(
      ["app_user_id"],
      ["app_user.user_id"],
      name="fk_app_user_aweme_record_app_user",
      ondelete="CASCADE",
    ),
    ForeignKeyConstraint(
      ["platform", "aweme_id"],
      ["aweme_record.platform", "aweme_record.aweme_id"],
      name="fk_app_user_aweme_record_aweme_record",
      ondelete="CASCADE",
    ),
    ##
    ## The primary key starts with app_user_id, so it cannot back the composite
    ## child side of the aweme FK.  Keep this explicit instead of relying on a
    ## MySQL-created index whose name and lifecycle differ by server version.
    ##
    Index("ix_app_user_aweme_record_aweme", "platform", "aweme_id"),
    MYSQL_TABLE_OPTIONS,
  )

  app_user_id: Mapped[int] = mapped_column(
    mysql.BIGINT(unsigned=True), nullable=False
  )
  platform: Mapped[str] = mapped_column(String(20), nullable=False)
  aweme_id: Mapped[str] = mapped_column(String(64), nullable=False)
  linked_at: Mapped[datetime] = mapped_column(
    mysql.DATETIME(fsp=3),
    nullable=False,
    server_default=text("CURRENT_TIMESTAMP(3)"),
  )
