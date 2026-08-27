##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import threading
from datetime import datetime

## <<Extension>>
from flask import Blueprint, jsonify, request

## <<Third-Part>>
from backend.src.database.query.library import (
  LibraryFilterError,
  LibraryLiveFilter,
  LibraryPostFilter,
  LibraryRecordingFilter,
  LibraryQuery,
  MAX_PAGE_SIZE,
)
from backend.src.auth.roles import ROLE_ADMIN
from backend.src.database.table.share_url import DouyinShareUrlTable
from backend.src.library.baselib import get_dict_attr
from backend.src.service.media_asset import MediaAssetResolver
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger
from backend.src.web.auth_routes import (
  require_admin,
  require_authenticated,
  request_auth_context,
)


class LibraryUnavailable(RuntimeError):
  """Raised when the library cannot serve a request right now."""


def _isoformat(value):
  if isinstance(value, datetime):
    return value.isoformat(timespec="milliseconds")
  return value


def _serialize_post(row: dict) -> dict:
  ##
  ## Named field by field rather than passed through, so a column added to
  ## aweme_record later cannot start appearing in the api by accident.
  ##
  return {
    "platform": row.get("platform"),
    "aweme_id": row.get("aweme_id"),
    "owner_user_id": row.get("owner_user_id"),
    "sec_user_id": row.get("sec_user_id"),
    "nickname": row.get("nickname"),
    "directory_name": row.get("directory_name"),
    "person_id": row.get("person_id"),
    "person_display_name": row.get("person_display_name"),
    "aweme_type": row.get("aweme_type"),
    "desc": row.get("desc"),
    "create_time": _isoformat(row.get("create_time")),
    "downloaded_at": _isoformat(row.get("downloaded_at")),
    "media_count": row.get("media_count"),
    "saved_count": row.get("saved_count"),
    ##
    ## A string the downloader wrote at the time.  Nothing here checked whether
    ## that directory still exists, and nothing in this api will serve from it.
    ##
    "save_dir": row.get("save_dir"),
    "source": row.get("source"),
  }


def _serialize_user_post(row: dict) -> dict:
  """The downloaded work as a user resource, without filing internals."""
  return {
    "platform": row.get("platform"),
    # Retained only as the stable key of an existing database resource.
    "aweme_id": row.get("aweme_id"),
    "nickname": row.get("nickname"),
    "aweme_type": row.get("aweme_type"),
    "desc": row.get("desc"),
    "create_time": _isoformat(row.get("create_time")),
    "downloaded_at": _isoformat(row.get("downloaded_at")),
    "media_count": row.get("media_count"),
    "saved_count": row.get("saved_count"),
  }


def _serialize_live(row: dict) -> dict:
  ##
  ## No output path.  live_record has no such column, and deriving one from the
  ## room id or a directory convention would be a guess the interface would then
  ## present as a fact.
  ##
  return {
    "observed_at": _isoformat(row.get("observed_at")),
    "platform": row.get("platform"),
    "room_id": row.get("room_id"),
    "owner_user_id": row.get("owner_user_id"),
    "nickname": row.get("nickname"),
    "directory_name": row.get("directory_name"),
    "person_id": row.get("person_id"),
    "person_display_name": row.get("person_display_name"),
    "title": row.get("title"),
    "room_status": row.get("room_status"),
    "start_time": _isoformat(row.get("start_time")),
    "finish_time": _isoformat(row.get("finish_time")),
    "status_code": row.get("status_code"),
  }


def _serialize_recording(row: dict) -> dict:
  """Persistent recording metadata safe for both USER and ADMIN lists."""
  return {
    "recording_id": row.get("recording_id"),
    "platform": row.get("platform"),
    "room_id": row.get("room_id"),
    "title": row.get("title"),
    "nickname": row.get("nickname"),
    "started_at": _isoformat(row.get("started_at")),
    "finished_at": _isoformat(row.get("finished_at")),
    "created_at": _isoformat(row.get("created_at")),
  }


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _success(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


class LibraryRuntime:
  """Lazily wires the library query to the configured database.

  Nothing is opened until a request arrives, so the server still starts on a
  machine whose database is down - and browsing the library never constructs a
  platform client, because the library never talks to a platform.
  """

  def __init__(self, config_loader=load_config, database_factory=None) -> None:
    self._config_loader = config_loader
    self._database_factory = database_factory
    self._lock = threading.Lock()
    self._config = None
    self._query = None

  def _settings(self) -> dict:
    if self._config is None:
      self._config = self._config_loader()
    return self._config

  def asset_resolver(self) -> MediaAssetResolver:
    """The filesystem reader, bound to the configured download root.

    Configuration is the authority on where downloads live - not the container
    layout. ``/app/downloads`` is where the compose file happens to mount a
    volume; a host install may legitimately point ``download.save_path``
    somewhere else entirely, and this must follow it.

    Read through a callable rather than captured, so a reloaded configuration
    is honoured without rebuilding the runtime.
    """
    return MediaAssetResolver(
      lambda: get_dict_attr(self._settings(), "$.download.save_path")
    )

  def page_size_limit(self) -> int:
    limit = get_dict_attr(self._settings(), "$.library.page_size_limit")
    return MAX_PAGE_SIZE if limit is None else int(limit)

  def query(self) -> LibraryQuery:
    settings = self._settings()
    if get_dict_attr(settings, "$.database.enable") is not True:
      ##
      ## Refused before any connection is attempted.  "The database is off" is a
      ## different answer from "there is nothing here", and the page must be
      ## able to tell them apart.
      ##
      raise LibraryUnavailable("媒体库需要启用数据库")

    with self._lock:
      if self._query is None:
        factory = self._database_factory
        if factory is None:
          factory = DouyinShareUrlTable
        try:
          database = factory(
            host=get_dict_attr(settings, "$.database.host"),
            user=get_dict_attr(settings, "$.database.username"),
            passwd=get_dict_attr(settings, "$.database.password"),
            database=get_dict_attr(settings, "$.database.name"),
          )
        except Exception as e:
          get_logger().warning("library database unavailable: {}".format(e))
          raise LibraryUnavailable("数据库暂时不可用")
        self._query = LibraryQuery(database)
      return self._query


def build_library_blueprint(runtime: LibraryRuntime = None) -> Blueprint:
  runtime = runtime if runtime is not None else LibraryRuntime()
  blueprint = Blueprint("library", __name__, url_prefix="/api")

  @blueprint.route("/library/posts", methods=["GET"])
  @require_authenticated
  def list_posts():
    try:
      post_filter = LibraryPostFilter.from_mapping(
        request.args, runtime.page_size_limit()
      )
      context = request_auth_context()
      if context.user.role == ROLE_ADMIN:
        page = runtime.query().posts(post_filter)
        serializer = _serialize_post
      else:
        page = runtime.query().posts_for_user(
          context.user.user_id, post_filter
        )
        serializer = _serialize_user_post
    except LibraryFilterError as e:
      return _error(str(e), 400)
    except LibraryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      ##
      ## Logged in full, reported as nothing: a driver error carries the host,
      ## the user and sometimes the statement, none of which belongs in a
      ## browser.
      ##
      get_logger().error("library post listing failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    return _success(
      {
        "total": page.total,
        "page": page.page,
        "page_size": page.page_size,
        "items": [serializer(row) for row in page.items],
      }
    )

  @blueprint.route("/library/recordings", methods=["GET"])
  @require_authenticated
  def list_recordings():
    try:
      recording_filter = LibraryRecordingFilter.from_mapping(
        request.args, runtime.page_size_limit()
      )
      context = request_auth_context()
      if context.user.role == ROLE_ADMIN:
        page = runtime.query().recordings(recording_filter)
      else:
        page = runtime.query().recordings_for_user(
          context.user.user_id, recording_filter
        )
    except LibraryFilterError as e:
      return _error(str(e), 400)
    except LibraryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      get_logger().error("library recording listing failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    return _success(
      {
        "total": page.total,
        "page": page.page,
        "page_size": page.page_size,
        "items": [_serialize_recording(row) for row in page.items],
      }
    )

  @blueprint.route("/library/lives", methods=["GET"])
  @require_admin
  def list_lives():
    try:
      live_filter = LibraryLiveFilter.from_mapping(
        request.args, runtime.page_size_limit()
      )
      page = runtime.query().lives(live_filter)
    except LibraryFilterError as e:
      return _error(str(e), 400)
    except LibraryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      get_logger().error("library live listing failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    return _success(
      {
        "total": page.total,
        "page": page.page,
        "page_size": page.page_size,
        "items": [_serialize_live(row) for row in page.items],
      }
    )


  ##
  ## >>--------------------------- media assets ---------------------------<<
  ##
  ##
  ## What is on disk right now, for one resource the caller is allowed to see.
  ##
  ## The ordering below is the security property, not an implementation detail:
  ##
  ##     authenticate -> scoped database lookup -> only then, the filesystem
  ##
  ## A request for somebody else's resource fails at the lookup and never
  ## reaches the resolver at all - so it cannot be used to probe which paths
  ## exist on this host, and cannot be timed to learn whether a post is there.
  ## ``test_media_asset_routes`` asserts the resolver is untouched on that path.
  ##
  ## Neither route serves bytes. They answer what exists; delivering it is a
  ## later phase with its own boundary to draw.
  ##
  def _asset_payload(resource: dict, discovery) -> dict:
    return {
      "resource": resource,
      "storage_state": discovery.storage_state.value,
      "assets": [asset.as_dict() for asset in discovery.assets],
    }

  @blueprint.route("/library/posts/<platform>/<aweme_id>/assets", methods=["GET"])
  @require_authenticated
  def post_assets(platform, aweme_id):
    try:
      context = request_auth_context()
      query = runtime.query()
      ##
      ## The scope comes from the session. No query parameter widens it, and
      ## there is deliberately none to pass.
      ##
      if context.user.role == ROLE_ADMIN:
        row = query.post(platform, aweme_id)
      else:
        row = query.post_for_user(context.user.user_id, platform, aweme_id)
    except LibraryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      get_logger().error("library post asset lookup failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    if row is None:
      ##
      ## One answer for "no such post", "not yours" and "belongs to nobody".
      ## Any difference between them would confirm the post exists.
      ##
      return _error("资源不存在", 404)

    discovery = runtime.asset_resolver().post_assets(
      row.get("save_dir"), platform, aweme_id
    )
    return _success(
      _asset_payload(
        {"kind": "post", "platform": platform, "aweme_id": aweme_id},
        discovery,
      )
    )

  @blueprint.route(
    "/library/recordings/<int:recording_id>/assets", methods=["GET"]
  )
  @require_authenticated
  def recording_assets(recording_id):
    try:
      context = request_auth_context()
      query = runtime.query()
      if context.user.role == ROLE_ADMIN:
        row = query.recording(recording_id)
      else:
        row = query.recording_for_user(context.user.user_id, recording_id)
    except LibraryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      get_logger().error("library recording asset lookup failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    if row is None:
      return _error("资源不存在", 404)

    discovery = runtime.asset_resolver().recording_asset(
      row.get("output_path"), recording_id
    )
    return _success(
      _asset_payload(
        {"kind": "recording", "recording_id": recording_id},
        discovery,
      )
    )

  return blueprint
