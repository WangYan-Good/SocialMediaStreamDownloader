from backend.src.database.orm.base import Base
from backend.src.database.orm.models.app_user import AppUserModel, AuthSessionModel
from backend.src.database.orm.models.aweme import (
  AppUserAwemeRecordModel,
  AwemeRecordModel,
)
from backend.src.database.orm.models.legacy import FavoriteOwnerModel, ShareUrlModel
from backend.src.database.orm.models.live import LiveRecordModel
from backend.src.database.orm.models.person import (
  ACCOUNT_ROLES,
  PersonAccountModel,
  PersonCollaborationModel,
  PersonModel,
)
from backend.src.database.orm.models.recording import RecordingRecordModel
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
    ##
    ## The application's own identity tables.  Listed here so alembic
    ## autogenerate and the start-up schema comparison both see them - a
    ## table missing from this set is one the comparison cannot notice
    ## drifting, and one autogenerate would offer to drop.
    ##
    AppUserModel.__tablename__,
    AuthSessionModel.__tablename__,
    AppUserAwemeRecordModel.__tablename__,
    AwemeRecordModel.__tablename__,
    ShareUrlModel.__tablename__,
    FavoriteOwnerModel.__tablename__,
    LiveRecordModel.__tablename__,
    RecordingRecordModel.__tablename__,
    PersonModel.__tablename__,
    PersonAccountModel.__tablename__,
    PersonCollaborationModel.__tablename__,
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
  "ACCOUNT_ROLES",
  "AppUserModel",
  "AuthSessionModel",
  "AppUserAwemeRecordModel",
  "AwemeRecordModel",
  "Base",
  "FavoriteOwnerModel",
  "FansGroupAdminUserIdModel",
  "FansGroupAdminUserOpenIdModel",
  "LiveRecordModel",
  "MANAGED_TABLE_NAMES",
  "PersonAccountModel",
  "PersonCollaborationModel",
  "PersonModel",
  "RecordingRecordModel",
  "RoomAdminUserIdModel",
  "RoomAdminUserOpenIdModel",
  "RoomBaseModel",
  "RoomDecoModel",
  "RoomOwnerModel",
  "RoomStatsModel",
  "ShareUrlModel",
  "UserModel",
]
