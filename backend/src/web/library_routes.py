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
  LibraryQuery,
  MAX_PAGE_SIZE,
)
from backend.src.database.table.share_url import DouyinShareUrlTable
from backend.src.library.baselib import get_dict_attr
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger


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
  def list_posts():
    try:
      post_filter = LibraryPostFilter.from_mapping(
        request.args, runtime.page_size_limit()
      )
      page = runtime.query().posts(post_filter)
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
        "items": [_serialize_post(row) for row in page.items],
      }
    )

  @blueprint.route("/library/lives", methods=["GET"])
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

  return blueprint
