from backend.src.database.orm.base import Base
from backend.src.database.orm.models.aweme import AwemeRecordModel
from backend.src.database.orm.models.legacy import FavoriteOwnerModel, ShareUrlModel
from backend.src.database.orm.models.live import LiveRecordModel
from backend.src.database.orm.models.room import (
  FansGroupAdminUserIdModel,
  FansGroupAdminUserOpenIdModel,
  RoomAdminUserIdModel,
  RoomAdminUserOpenIdModel,
  RoomDecoModel,
  RoomStatsModel,
)
from backend.src.database.orm.models.room_base import RoomBaseModel
from backend.src.database.orm.models.room_owner import RoomOwnerModel
from backend.src.database.orm.models.user import UserModel


MANAGED_TABLE_NAMES = frozenset(
  {
    AwemeRecordModel.__tablename__,
    ShareUrlModel.__tablename__,
    FavoriteOwnerModel.__tablename__,
    LiveRecordModel.__tablename__,
    FansGroupAdminUserIdModel.__tablename__,
    FansGroupAdminUserOpenIdModel.__tablename__,
    RoomAdminUserIdModel.__tablename__,
    RoomAdminUserOpenIdModel.__tablename__,
    RoomBaseModel.__tablename__,
    RoomDecoModel.__tablename__,
    RoomOwnerModel.__tablename__,
    RoomStatsModel.__tablename__,
    UserModel.__tablename__,
  }
)


__all__ = [
  "AwemeRecordModel",
  "Base",
  "FavoriteOwnerModel",
  "FansGroupAdminUserIdModel",
  "FansGroupAdminUserOpenIdModel",
  "LiveRecordModel",
  "MANAGED_TABLE_NAMES",
  "RoomAdminUserIdModel",
  "RoomAdminUserOpenIdModel",
  "RoomBaseModel",
  "RoomDecoModel",
  "RoomOwnerModel",
  "RoomStatsModel",
  "ShareUrlModel",
  "UserModel",
]
