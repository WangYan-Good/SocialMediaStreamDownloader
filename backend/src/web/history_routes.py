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
from backend.src.database.query.owner_history import (
  OwnerHistoryFilter,
  OwnerHistoryFilterError,
  OwnerHistoryQuery,
)
from backend.src.database.table.share_url import DouyinShareUrlTable
from backend.src.library.configlib import load_config
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.service.live_probe import LiveProbeService, ProbeBatchStore, ProbeBatchError


class HistoryUnavailable(RuntimeError):
  """Raised when the history feature cannot serve a request right now."""


def _isoformat(value):
  if isinstance(value, datetime):
    return value.isoformat(timespec="milliseconds")
  return value


def _serialize_owner(row: dict) -> dict:
  return {
    "owner_user_id": row.get("owner_user_id"),
    "sec_user_id": row.get("sec_user_id"),
    "nickname": row.get("nickname"),
    "live_share_url": row.get("live_share_url"),
    "directory_name": row.get("directory_name"),
    "user_status": row.get("user_status"),
    "actived_count": row.get("actived_count"),
    "score": row.get("score"),
    "favorite": row.get("score") is not None,
    "last_live_status": row.get("last_live_status"),
    "last_checked_at": _isoformat(row.get("last_checked_at")),
    "last_room_id": row.get("last_room_id"),
  }


def _serialize_session(row: dict) -> dict:
  return {
    "observed_at": _isoformat(row.get("observed_at")),
    "room_id": row.get("room_id"),
    "title": row.get("title"),
    "room_status": row.get("room_status"),
    "start_time": _isoformat(row.get("start_time")),
    "finish_time": _isoformat(row.get("finish_time")),
    "status_code": row.get("status_code"),
  }


def _serialize_probe_item(item: dict) -> dict:
  serialized = dict(item)
  serialized["checked_at"] = _isoformat(item.get("checked_at"))
  return serialized


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _success(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


class HistoryRuntime:
  """Lazily wires the history query and the probe service.

  Browsing history must not pay for the platform client, so the query side builds
  its own database handle and the probe side only constructs the downloader when
  an actual probe is requested.
  """

  def __init__(self, config_loader=load_config, downloader_factory=None) -> None:
    self._config_loader = config_loader
    self._downloader_factory = downloader_factory
    self._lock = threading.Lock()
    self._config = None
    self._query = None
    self._probe_service = None

  def _settings(self) -> dict:
    if self._config is None:
      self._config = self._config_loader()
    return self._config

  def page_size_limit(self) -> int:
    limit = get_dict_attr(self._settings(), "$.history.page_size_limit")
    return 10 if limit is None else int(limit)

  def query(self) -> OwnerHistoryQuery:
    settings = self._settings()
    if get_dict_attr(settings, "$.database.enable") is not True:
      raise HistoryUnavailable("历史功能需要启用数据库")
    with self._lock:
      if self._query is None:
        try:
          database = DouyinShareUrlTable(
            host=get_dict_attr(settings, "$.database.host"),
            user=get_dict_attr(settings, "$.database.username"),
            passwd=get_dict_attr(settings, "$.database.password"),
            database=get_dict_attr(settings, "$.database.name"),
          )
        except Exception as e:
          get_logger().warning("history database unavailable: {}".format(e))
          raise HistoryUnavailable("数据库暂时不可用")
        self._query = OwnerHistoryQuery(database)
      return self._query

  def probe_service(self) -> LiveProbeService:
    settings = self._settings()
    with self._lock:
      if self._probe_service is not None:
        return self._probe_service

    ##
    ## Imported here so that merely listing history never pulls in the platform
    ## client and its login side effects.
    ##
    if self._downloader_factory is None:
      from backend.src.platform.douyin.douyin_live_downloader import get_live_downloader
      downloader_factory = get_live_downloader
    else:
      downloader_factory = self._downloader_factory

    history_query = self.query()
    downloader = downloader_factory()

    def owner_lookup(owner_user_ids):
      return history_query.live_share_urls(owner_user_ids)

    def status_writer(owner_user_id, room_status, checked_at, room_id):
      database = downloader._database_if_ready()
      if database is None:
        return
      database.update_live_status_cache(
        owner_user_id=owner_user_id,
        last_live_status=room_status,
        last_checked_at=checked_at,
        last_room_id=room_id,
      )

    probe_root = "$.platform.douyin.live.probe"
    service = LiveProbeService(
      prober=downloader.prober,
      owner_lookup=owner_lookup,
      status_writer=status_writer,
      max_batch_size=int(get_dict_attr(settings, probe_root + ".max_batch_size")),
      concurrency=int(get_dict_attr(settings, probe_root + ".concurrency")),
      cache_ttl_seconds=float(
        get_dict_attr(settings, probe_root + ".cache_ttl_seconds")
      ),
      store=ProbeBatchStore(
        retention_seconds=float(
          get_dict_attr(settings, probe_root + ".batch_retention_seconds")
        )
      ),
    )
    with self._lock:
      if self._probe_service is None:
        self._probe_service = service
      return self._probe_service


def build_history_blueprint(runtime: HistoryRuntime = None) -> Blueprint:
  runtime = runtime if runtime is not None else HistoryRuntime()
  blueprint = Blueprint("history", __name__, url_prefix="/api")

  @blueprint.route("/history/owners", methods=["GET"])
  def list_owners():
    try:
      owner_filter = OwnerHistoryFilter.from_mapping(
        request.args, runtime.page_size_limit()
      )
      page = runtime.query().search(owner_filter)
    except OwnerHistoryFilterError as e:
      return _error(str(e), 400)
    except HistoryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      get_logger().error("history owner listing failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    return _success(
      {
        "total": page.total,
        "page": page.page,
        "page_size": page.page_size,
        "items": [_serialize_owner(row) for row in page.items],
      }
    )

  @blueprint.route("/history/owners/<owner_user_id>/sessions", methods=["GET"])
  def list_sessions(owner_user_id):
    try:
      limit = min(int(request.args.get("limit", 20)), 100)
    except (TypeError, ValueError):
      return _error("limit must be an integer", 400)
    if limit < 1:
      return _error("limit must be at least 1", 400)

    platform = (request.args.get("platform") or "douyin").strip() or "douyin"
    try:
      sessions = runtime.query().sessions(owner_user_id, platform, limit)
    except HistoryUnavailable as e:
      return _error(str(e), 503)
    except ValueError as e:
      return _error(str(e), 400)
    except Exception as e:
      get_logger().error("history session listing failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    return _success({"items": [_serialize_session(row) for row in sessions]})

  @blueprint.route("/live/probe", methods=["POST"])
  def submit_probe():
    if not request.is_json:
      return _error("请求必须是 JSON 格式", 400)
    payload = request.get_json(silent=True)
    if payload is None:
      return _error("请求体为空或格式错误", 400)

    owner_user_ids = payload.get("owner_user_ids")
    if not isinstance(owner_user_ids, list):
      return _error("缺少必需字段: owner_user_ids（必须是数组）", 400)

    try:
      service = runtime.probe_service()
      batch_id = service.submit(owner_user_ids)
    except ProbeBatchError as e:
      return _error(str(e), 400)
    except HistoryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      get_logger().error("live probe submission failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    snapshot = service.snapshot(batch_id) or {"batch_id": batch_id, "done": False, "items": []}
    return (
      jsonify(
        {
          "status": "success",
          "code": 202,
          "data": {
            "batch_id": snapshot["batch_id"],
            "done": snapshot["done"],
            "items": [_serialize_probe_item(item) for item in snapshot["items"]],
          },
        }
      ),
      202,
    )

  @blueprint.route("/live/probe/<batch_id>", methods=["GET"])
  def read_probe(batch_id):
    try:
      snapshot = runtime.probe_service().snapshot(batch_id)
    except HistoryUnavailable as e:
      return _error(str(e), 503)
    except Exception as e:
      get_logger().error("live probe lookup failed: {}".format(e))
      return _error("服务器内部错误，请稍后重试", 500)

    if snapshot is None:
      return _error("探测批次不存在或已过期", 404)

    return _success(
      {
        "batch_id": snapshot["batch_id"],
        "done": snapshot["done"],
        "items": [_serialize_probe_item(item) for item in snapshot["items"]],
      }
    )

  return blueprint
