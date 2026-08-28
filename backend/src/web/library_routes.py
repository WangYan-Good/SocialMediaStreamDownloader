##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import threading
from datetime import datetime

## <<Extension>>
from flask import Blueprint, jsonify, request, send_file

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
from backend.src.service.media_asset import SECURE_OPEN_SUPPORTED, MediaAssetResolver
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger
from backend.src.web.auth_routes import (
  require_admin,
  require_authenticated,
  request_auth_context,
)
from backend.src.web.wire import recording_id_to_wire


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
    ##
    ## Text, not a number.  The column is BIGINT UNSIGNED and a browser parses a
    ## JSON number as a double, so an identity sent as a number would be rounded
    ## before any code here could be blamed for it.
    ##
    "recording_id": recording_id_to_wire(row.get("recording_id")),
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
      ##
      ## Serialized here rather than after the boundary: a row whose identity
      ## cannot be spelled is refused by ``recording_id_to_wire``, and that
      ## refusal has to be answered in this endpoint's own words instead of
      ## escaping as an unhandled exception.
      ##
      items = [_serialize_recording(row) for row in page.items]
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
        "items": items,
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

  ##
  ## The scoped lookup, in one place.
  ##
  ## Metadata and download must authorize identically, and the surest way to
  ## keep them identical is for there to be one implementation rather than two
  ## that agree today. Each returns either the row or a ready response, so a
  ## caller cannot forget to check.
  ##
  def _authorized_post_row(platform, aweme_id):
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
      return None, _error(str(e), 503)
    except Exception as e:
      get_logger().error("library post asset lookup failed: {}".format(e))
      return None, _error("服务器内部错误，请稍后重试", 500)

    if row is None:
      ##
      ## One answer for "no such post", "not yours" and "belongs to nobody".
      ## Any difference between them would confirm the post exists.
      ##
      return None, _error("资源不存在", 404)
    return row, None

  def _authorized_recording_row(recording_id):
    try:
      context = request_auth_context()
      query = runtime.query()
      if context.user.role == ROLE_ADMIN:
        row = query.recording(recording_id)
      else:
        row = query.recording_for_user(context.user.user_id, recording_id)
    except LibraryUnavailable as e:
      return None, _error(str(e), 503)
    except Exception as e:
      get_logger().error("library recording asset lookup failed: {}".format(e))
      return None, _error("服务器内部错误，请稍后重试", 500)

    if row is None:
      return None, _error("资源不存在", 404)
    return row, None

  @blueprint.route("/library/posts/<platform>/<aweme_id>/assets", methods=["GET"])
  @require_authenticated
  def post_assets(platform, aweme_id):
    row, refusal = _authorized_post_row(platform, aweme_id)
    if refusal is not None:
      return refusal

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
    row, refusal = _authorized_recording_row(recording_id)
    if refusal is not None:
      return refusal

    discovery = runtime.asset_resolver().recording_asset(
      row.get("output_path"), recording_id
    )
    return _success(
      _asset_payload(
        ##
        ## The same spelling the list used.  One endpoint answering with a
        ## number and another with a string would be two contracts for one
        ## identity, and a browser could not compare them.
        ##
        {"kind": "recording", "recording_id": recording_id_to_wire(recording_id)},
        discovery,
      )
    )

  ##
  ## >>------------------------- media delivery -------------------------<<
  ##
  ##
  ## The bytes. Every request walks the full length of the boundary:
  ##
  ##     authenticate
  ##       -> scoped database lookup for the PARENT resource
  ##         -> only now, the filesystem
  ##           -> rediscover what is on disk right now
  ##             -> match the requested id against THAT
  ##               -> open it through the root, refusing every symlink
  ##                 -> fstat the descriptor that was actually opened
  ##                   -> stream that open file
  ##
  ## No step may be skipped for a request that "already" listed the asset. The
  ## listing is a description of a moment that has passed; the file may since
  ## have been deleted, replaced, or turned into a link pointing anywhere. An
  ## asset id names a file - it never grants access to one.
  ##
  ## There is deliberately no path anywhere in this section, and no route that
  ## takes one.
  ##
  def _deliver(opened):
    """Stream an already-open media file as an attachment.

    The file object is passed to ``send_file`` rather than a path. A path would
    be re-opened by name, which would discard the secure walk that produced
    this descriptor and reintroduce the race it exists to close.
    """
    response = send_file(
      opened.stream,
      mimetype=opened.asset.media_type,
      ##
      ## Always an attachment, images included. Nothing this server stores is
      ## rendered inline in this phase, so no media can become a vector for
      ## anything the browser would execute or embed.
      ##
      as_attachment=True,
      ##
      ## Werkzeug builds the header - including the RFC 5987 encoding a Chinese
      ## file name needs, and the escaping that stops a crafted name from
      ## injecting one. Hand-formatting this header is how that goes wrong.
      ##
      download_name=opened.asset.name,
      ##
      ## No Range handling in this phase. Conditional responses would advertise
      ## byte-range support that has not been designed yet, which is how a
      ## download endpoint quietly becomes a player transport.
      ##
      conditional=False,
      ##
      ## No entity tag. Computing one means reading the file to hash it, and
      ## the asset id is a name, not a content digest - using it here would
      ## claim a guarantee it does not make.
      ##
      etag=False,
      last_modified=None,
    )

    ##
    ## From the descriptor, not from the earlier listing. The file may have
    ## grown since discovery, and Content-Length must describe what is actually
    ## being sent.
    ##
    response.headers["Content-Length"] = str(opened.size_bytes)
    ##
    ## Private media must not be retained by any cache between here and the
    ## browser - a shared proxy holding one user's video would serve it to the
    ## next person who asked.
    ##
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"

    ##
    ## The descriptor is released when the response is done with it, whether it
    ## completed, failed, or the client hung up mid-stream. A server that runs
    ## for weeks cannot leak one per download.
    ##
    response.call_on_close(opened.close)
    return response

  @blueprint.route(
    "/library/posts/<platform>/<aweme_id>/assets/<asset_id>/download",
    methods=["GET"],
  )
  @require_authenticated
  def post_asset_download(platform, aweme_id, asset_id):
    row, refusal = _authorized_post_row(platform, aweme_id)
    if refusal is not None:
      return refusal

    if not SECURE_OPEN_SUPPORTED:
      ##
      ## This host cannot make the guarantee the walk depends on. Serving the
      ## file through a plain open would look identical and be a different
      ## promise, so it refuses instead. Metadata still works.
      ##
      return _error("文件暂时不可用", 503)

    try:
      opened = runtime.asset_resolver().open_post_asset(
        row.get("save_dir"), platform, aweme_id, asset_id
      )
    except Exception as e:
      get_logger().error("post asset open failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    if opened is None:
      ##
      ## Unknown id, an id from another post, a file deleted since it was
      ## listed, a name that is now a symlink. One answer: the difference
      ## between them is a description of this host's filesystem.
      ##
      return _error("资源或文件不存在", 404)

    return _deliver(opened)

  @blueprint.route(
    "/library/recordings/<int:recording_id>/assets/<asset_id>/download",
    methods=["GET"],
  )
  @require_authenticated
  def recording_asset_download(recording_id, asset_id):
    row, refusal = _authorized_recording_row(recording_id)
    if refusal is not None:
      return refusal

    if not SECURE_OPEN_SUPPORTED:
      return _error("文件暂时不可用", 503)

    try:
      opened = runtime.asset_resolver().open_recording_asset(
        row.get("output_path"), recording_id, asset_id
      )
    except Exception as e:
      get_logger().error("recording asset open failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    if opened is None:
      return _error("资源或文件不存在", 404)

    return _deliver(opened)

  return blueprint
