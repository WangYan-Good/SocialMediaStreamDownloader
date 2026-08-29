##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Base>>
import io
import threading
import time
from datetime import datetime

## <<Extension>>
from flask import Blueprint, Response, jsonify, request, send_file

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
from backend.src.service.media_range import BoundedRangeReader
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
  ##
  ## >>--------------------------- byte ranges ---------------------------<<
  ##
  ##
  ## Range exists here for one reason: a download of a large recording that was
  ## interrupted should be able to continue rather than start again.
  ##
  ## Everything about it happens *after* the boundary above. The window is
  ## resolved against the size reported by ``fstat`` on the descriptor that was
  ## actually opened - never against a size remembered from a listing, and never
  ## before the file has been proven. A Range header changes which bytes are
  ## sent and nothing else: not who may ask, not which file is found, not
  ## whether the filesystem is touched at all.
  ##
  ## Only one range. Multiple ranges would mean ``multipart/byteranges``, which
  ## is a second body format to get right for a case no download client sends;
  ## a request for several is answered with the whole representation instead.
  ##
  def _published_tag(opened):
    """The entity tag for these bytes, or ``None`` when none may be claimed.

    Not the asset id. That names a file - parent identity plus file name - and
    is deliberately unchanged when a file is replaced with different content.
    Resuming against it would splice the tail of a new file onto the head of an
    old one and call the result a download.

    ``None`` while the representation is too recently written for a timestamp
    to have noticed a change. An entity tag without a ``W/`` prefix *is* a
    strong validator as far as HTTP is concerned, and RFC 9110 §8.8.1 requires
    a server that cannot meet that standard to say so. Sending an unmarked tag
    here would be the header asserting a guarantee the mechanism behind it does
    not provide.

    Withheld rather than marked weak. A weak tag could not satisfy ``If-Range``
    either - §13.1.3 requires a strong comparison - so it would be a second
    kind of state to carry for no gain, and these responses are already
    ``no-store``, so there is no cache that wants one.
    """
    if not opened.version.is_strong_at(time.time_ns()):
      return None
    return opened.version.entity_tag

  def _suffix_length(start):
    """The suffix-length of a ``bytes=-N`` request, or ``None`` for other forms.

    Read from the header text rather than from the parsed pair, because the
    parse cannot tell these two apart::

        bytes=-0   ->  (0, None)
        bytes=0-   ->  (0, None)

    The sign is lost on an integer zero, and the two spellings mean opposite
    things: the first asks for the last nothing bytes, the second for
    everything from the first byte on. Only the leading ``-`` distinguishes
    them, so that one character is what gets looked at.

    Syntax is still entirely Werkzeug's - this runs only after it has accepted
    the header, agreed the unit is ``bytes``, and produced exactly one range.
    """
    spec = request.headers.get("Range", "").partition("=")[2].strip()
    if not spec.startswith("-"):
      return None
    ##
    ## ``-3`` parses to a start of -3; ``-0`` to a start of 0. Both are the
    ## suffix-length once the sign has served its purpose.
    ##
    return abs(start)

  def _requested_range(complete_length):
    """Which single window this request asked for, if any.

    Returns ``("full", None)`` when the whole representation should be sent,
    ``("partial", (start, end))`` for a satisfiable single range, and
    ``("unsatisfiable", None)`` when a byte range was asked for and cannot be
    answered.

    Werkzeug parses the header - a hand-written parser would have to get
    syntax, units, overflow and clamping right, and every one of those is a
    place to be wrong in a way that reads bytes nobody asked for.

    What it does *not* decide is what a suffix range means when it is longer
    than the file, or when it is zero. ``range_for_length`` refuses the first
    and accepts the second; RFC 9110 §14.1.2 says the opposite of both. The
    helper is a tool, not this server's contract, so those two cases are
    normalized below - narrowly, and only after parsing has succeeded.
    """
    requested = request.range
    if requested is None:
      ##
      ## No Range at all, or one malformed enough that the parser declined it.
      ## A malformed header is not an error to report - the client simply gets
      ## the whole file, which is always a correct answer to a GET.
      ##
      return "full", None

    if requested.units != "bytes":
      ##
      ## Some other unit. Nothing else is implemented, and ignoring an
      ## unsupported unit is what the standard asks for.
      ##
      return "full", None

    if len(requested.ranges) != 1:
      ##
      ## Several ranges. Answering properly means multipart/byteranges; the
      ## whole representation is a valid response and is what gets sent.
      ##
      return "full", None

    if complete_length == 0:
      ##
      ## Nothing to take a window of. RFC 9110 §14.2 permits ignoring Range
      ## when the selected representation has no content, and that is the only
      ## coherent answer here: a 206 would need a Content-Range describing a
      ## window of an empty file, and there is no such thing to describe.
      ##
      return "full", None

    start, _ = requested.ranges[0]
    suffix = _suffix_length(start)
    if suffix is not None:
      if suffix == 0:
        ##
        ## "The last zero bytes" cannot be satisfied - there is no such window.
        ## §14.1.2 makes a suffix range satisfiable only for a non-zero
        ## suffix-length.
        ##
        return "unsatisfiable", None
      if suffix >= complete_length:
        ##
        ## More tail than the file has, so the tail is the whole file. §14.1.2:
        ## "if the selected representation is shorter than the specified
        ## suffix-length, the entire representation is used."
        ##
        return "partial", (0, complete_length)
      return "partial", (complete_length - suffix, complete_length)

    window = requested.range_for_length(complete_length)
    if window is None:
      ##
      ## Asked for bytes that are not there.
      ##
      return "unsatisfiable", None
    return "partial", window

  def _honours_if_range(opened):
    """Whether a conditional resume may proceed.

    ``If-Range`` is a client saying "continue only if this is still the same
    thing I was downloading". If it is not, the honest answer is the whole of
    the current representation - never the tail of it, which the client would
    append to bytes from a file that no longer exists.
    """
    condition = request.headers.get("If-Range")
    if condition is None:
      return True

    published = _published_tag(opened)
    if published is None:
      ##
      ## No strong validator exists for this representation, so nothing can
      ## satisfy the condition. Whatever the client is quoting, it was not a
      ## promise this server is currently in a position to keep - and §13.1.3
      ## requires a strong comparison, which there is nothing to compare with.
      ##
      return False

    ##
    ## Only strong entity tags are honoured. The date form would have to rest
    ## on modification time, whose one-second resolution cannot distinguish a
    ## file replaced moments after it was read - precisely the case that
    ## corrupts a resume. An unrecognised condition falls back to the whole
    ## representation, which is always safe.
    ##
    return condition.strip() == '"{}"'.format(published)

  def _common_headers(response, opened):
    response.headers["Accept-Ranges"] = "bytes"
    tag = _published_tag(opened)
    if tag is not None:
      ##
      ## Set through the header API so the quoting is the framework's problem.
      ## Absent entirely when no strong validator can be claimed - see
      ## ``_published_tag``.
      ##
      response.set_etag(tag)
    ##
    ## Private media must not be retained by any cache between here and the
    ## browser - a shared proxy holding one user's video would serve it to the
    ## next person who asked. An entity tag is a resume validator, not an
    ## invitation to store a copy.
    ##
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

  def _unsatisfiable(opened):
    """416, with the one thing a client needs to correct itself.

    ``Content-Range: bytes *​/<length>`` tells it how long the representation
    actually is, so the next attempt can be right.
    """
    complete = opened.size_bytes
    tag = _published_tag(opened)
    ##
    ## Nothing is going to be sent, so the descriptor is released now rather
    ## than being carried to the end of a response that will never read it.
    ##
    opened.close()

    response = jsonify(
      {"status": "error", "code": 416, "message": "请求的范围无法满足"}
    )
    response.status_code = 416
    response.headers["Content-Range"] = "bytes */{}".format(complete)
    response.headers["Accept-Ranges"] = "bytes"
    if tag is not None:
      response.set_etag(tag)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

  def _partial(opened, window):
    """206, carrying exactly the requested window and not one byte more."""
    start, end = window
    length = end - start
    complete = opened.size_bytes

    ##
    ## An iterable rather than a file object, deliberately. Werkzeug will hand
    ## a file with a ``fileno`` to the WSGI server, which may copy it to the
    ## socket with ``sendfile`` and ignore every limit expressed in Python -
    ## sending the rest of the file after the window. There is no descriptor
    ## here to find.
    ##
    reader = BoundedRangeReader(opened.stream, start, length)
    response = Response(
      reader,
      status=206,
      mimetype=opened.asset.media_type,
      direct_passthrough=True,
    )
    response.headers["Content-Range"] = "bytes {}-{}/{}".format(
      start, end - 1, complete
    )
    response.headers["Content-Length"] = str(length)
    ##
    ## A partial response is still an attachment of the same file, under the
    ## same name: a resumed download must not suddenly become something else.
    ##
    response.headers["Content-Disposition"] = _attachment_disposition(opened)
    _common_headers(response, opened)

    ##
    ## The reader closes the file when it finishes, is abandoned, or fails.
    ## This covers the remaining case: a response discarded before anything
    ## iterated it at all.
    ##
    response.call_on_close(reader.close)
    return response

  def _attachment_disposition(opened):
    """The Content-Disposition Werkzeug would build for this file.

    Borrowed from a throwaway ``send_file`` rather than formatted here, so that
    the RFC 5987 encoding a Chinese file name needs - and the escaping that
    stops a crafted name from injecting a header - stay the framework's job.
    """
    return send_file(
      io.BytesIO(b""),
      mimetype=opened.asset.media_type,
      as_attachment=True,
      download_name=opened.asset.name,
      conditional=False,
      etag=False,
      last_modified=None,
    ).headers["Content-Disposition"]

  def _deliver(opened):
    """Stream an already-open media file as an attachment.

    The file object is passed to ``send_file`` rather than a path. A path would
    be re-opened by name, which would discard the secure walk that produced
    this descriptor and reintroduce the race it exists to close.
    """
    ##
    ## Resolved against the descriptor, after the file has been proven - never
    ## against a size remembered from an earlier listing.
    ##
    ## HEAD describes the representation rather than a slice of it. Flask
    ## dispatches HEAD to this same view, so without this it would inherit the
    ## GET behaviour and answer 206 with a Content-Length for a body that is
    ## never sent - a worse answer than describing the whole thing. Range
    ## semantics are defined for GET.
    ##
    if request.method == "HEAD":
      outcome, window = "full", None
    else:
      outcome, window = _requested_range(opened.size_bytes)

    if outcome == "unsatisfiable":
      return _unsatisfiable(opened)

    if outcome == "partial" and _honours_if_range(opened):
      return _partial(opened, window)

    ##
    ## Everything else is the whole representation: no Range, an unsupported
    ## unit, several ranges, a malformed header, or an ``If-Range`` naming a
    ## version this is no longer. The last of those is the resume-safety case -
    ## the client gets the current file in full rather than a tail that would
    ## not match what it already has.
    ##
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
      ## Ranges are handled above rather than here. Werkzeug's own conditional
      ## handling would work from the file object it was given, and would have
      ## to be trusted to respect the window; the explicit path above sends the
      ## bytes through an iterator that cannot be optimised past.
      ##
      conditional=False,
      ##
      ## And the entity tag is set by ``_common_headers`` from the opened
      ## descriptor's identity and timestamps. Werkzeug's own would be derived
      ## from what it can see of this file object, which is not the same
      ## question - and neither is a digest of the content, which would mean
      ## reading a multi-gigabyte recording once per request.
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
    _common_headers(response, opened)

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
