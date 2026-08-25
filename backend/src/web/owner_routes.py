##<<Base>>
import threading

##<<Extension>>
from flask import Blueprint, jsonify, request
from requests import request as http_request

##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.library.configlib import load_config
from backend.src.library.loglib import get_logger
from backend.src.platform.douyin.douyin_aweme_downloader import (
  get_aweme_downloader,
  get_aweme_executor,
  get_post_pool,
)
from backend.src.platform.douyin.douyin_header import DouyinShareHeader
from backend.src.platform.douyin.douyin_owner_api import DouyinOwnerApi
from backend.src.platform.douyin.douyin_owner_detail import (
  OwnerUnavailable,
  fetch_owner_detail,
)
from backend.src.platform.douyin.douyin_owner_posts import (
  FIRST_CURSOR,
  fetch_post_page,
)
from backend.src.platform.douyin.douyin_owner_url import (
  classify_owner_url,
  extract_url,
  needs_resolution,
)
from backend.src.platform.douyin.douyin_session import (
  SessionExpired,
  UpstreamRejected,
)
from backend.src.service.job_store import JobStore
from backend.src.service.post_download_job import (
  MissingPayloads,
  PayloadCache,
  PostDownloadJobService,
)
from backend.src.web.auth_routes import require_admin, require_admin_csrf


##
## The message a dead cookie must produce.  Stated once so every path says the
## same thing: during design verification an expired session was mistaken for
## "this owner has no posts" for over an hour, and the fix is that the program
## never phrases it that way.
##
SESSION_MESSAGE = (
  "抖音登录已失效，请更新 config/config.yml 中 "
  "platform.douyin.headers.post_info.cookie"
)

##
## Where the one OwnerRuntime lives for the life of the application.  Held on
## the app rather than only inside this blueprint's closure because a second
## entry point - the unified task api - has to reach the *same* runtime: two
## would mean two job stores, two payload caches and two sets of per-post locks,
## and the same post walked by one while downloaded by the other.
##
OWNER_RUNTIME_KEY = "smsd_owner_runtime"


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _success(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


def _serialize_owner(detail) -> dict:
  return {
    "sec_user_id": detail.sec_user_id,
    "uid": detail.uid,
    "nickname": detail.nickname,
    "unique_id": detail.unique_id,
    "signature": detail.signature,
    "avatar_url": detail.avatar_url,
    "follower_count": detail.follower_count,
    "following_count": detail.following_count,
    "aweme_count": detail.aweme_count,
    "total_favorited": detail.total_favorited,
  }


def _cover_url(payload) -> str:
  for path in ("$.video.cover.url_list", "$.video.dynamic_cover.url_list"):
    urls = get_dict_attr(payload, path)
    if isinstance(urls, (list, tuple)):
      for candidate in urls:
        if isinstance(candidate, str) and candidate.startswith("http"):
          return candidate
  images = get_dict_attr(payload, "$.images")
  if isinstance(images, (list, tuple)) and images:
    urls = (images[0] or {}).get("url_list") if isinstance(images[0], dict) else None
    if isinstance(urls, (list, tuple)):
      for candidate in urls:
        if isinstance(candidate, str) and candidate.startswith("http"):
          return candidate
  return ""


def _serialize_post(payload, record=None) -> dict:
  """Only what the list renders - not the whole post object.

  The payload itself stays server-side; see PayloadCache for why.
  """
  images = get_dict_attr(payload, "$.images")
  return {
    "aweme_id": get_dict_attr(payload, "$.aweme_id"),
    "desc": get_dict_attr(payload, "$.desc") or "",
    "create_time": get_dict_attr(payload, "$.create_time"),
    "cover_url": _cover_url(payload),
    "duration": get_dict_attr(payload, "$.video.duration"),
    "aweme_type": (
      "image" if isinstance(images, (list, tuple)) and images else "video"
    ),
    "digg_count": get_dict_attr(payload, "$.statistics.digg_count"),
    "comment_count": get_dict_attr(payload, "$.statistics.comment_count"),
    "downloaded": record is not None,
    "saved_count": (record or {}).get("saved_count"),
    "media_count": (record or {}).get("media_count"),
  }


class OwnerRuntime:
  """Lazily wires the owner api, the download service and the shared caches.

  Built on first use so importing the blueprint costs nothing: a server that never
  opens the owner page never constructs a platform client.
  """

  def __init__(self, config_loader=load_config, api_factory=None,
               downloader_factory=None, task_service=None) -> None:
    self._config_loader = config_loader
    self._api_factory = api_factory
    self._downloader_factory = downloader_factory
    ##
    ## Handed in by whoever built this runtime, never fetched from Flask.  The
    ## download service must stay testable without an application context, so
    ## the dependency travels down - Flask, to the factory, to the service -
    ## rather than being reached up for.
    ##
    self.task_service = task_service
    self._lock = threading.Lock()
    self._config = None
    self._api = None
    self._service = None

  def settings(self) -> dict:
    if self._config is None:
      self._config = self._config_loader()
    return self._config

  def api(self):
    with self._lock:
      if self._api is None:
        factory = self._api_factory or DouyinOwnerApi
        self._api = factory(self.settings())
      return self._api

  def service(self):
    with self._lock:
      if self._service is None:
        api = self._api
        if api is None:
          factory = self._api_factory or DouyinOwnerApi
          api = self._api = factory(self.settings())
        ##
        ## The process-wide downloader on purpose, not one built from
        ## ``self.settings()``.  It carries the PostLocks and the post executor,
        ## and a second instance would hold its own copies - so the same post
        ## arriving from a pasted link and from this page could interleave writes
        ## to one file.  Sharing the singleton is what keeps that from happening.
        ##
        ## The consequence is that this downloader follows the *process* config,
        ## which is why a test that wants a different save_path has to pass
        ## ``downloader_factory`` rather than a modified config.
        ##
        downloader = (
          self._downloader_factory()
          if self._downloader_factory is not None
          else get_aweme_downloader()
        )
        config = downloader.config
        self._service = PostDownloadJobService(
          downloader=downloader,
          api=api,
          store=JobStore(retention_seconds=config.job_retention_seconds),
          cache=PayloadCache(
            retention_seconds=config.payload_retention_seconds
          ),
          ##
          ## The process-wide task service, so a batch download started here is
          ## visible from /api/tasks in the same process.
          ##
          task_service=self.task_service,
          executor=get_aweme_executor(config.concurrency),
          ##
          ## Two different limits: ``concurrency`` bounds how many download jobs
          ## run at once, ``download_concurrency`` how many posts do, across all
          ## of them.  The pools have to be separate or a job waiting on its own
          ## posts could hold the workers those posts need.
          ##
          post_pool=get_post_pool(config.owner_download_concurrency),
          post_concurrency=config.owner_download_concurrency,
        )
      return self._service

  def resolve_owner(self, url: str):
    """Turn pasted share text into a ``sec_user_id``, following a short link once.

    The input may be a whole sentence - that is what the app puts on the clipboard
    - so the link is pulled out first.  The browser does this too; doing it here
    as well means the api does not depend on the browser having done it.
    """
    return classify_owner_url(self.follow_share_link(url) or "")

  def follow_share_link(self, url: str):
    """Return the url a share link leads to, following it at most once.

    Split out from ``resolve_owner`` because a share link identifies an owner
    whichever kind it is - profile, post or live room - and each kind is read
    from the resolved url differently.  Following it is the step they share, and
    it costs a request, so it happens once here rather than once per attempt.
    """
    url = extract_url(url) or url
    if not url:
      return None
    if not needs_resolution(url):
      return url
    header = DouyinShareHeader(
      get_dict_attr(self.settings(), "$.platform.douyin.headers")
    )
    header.init_share_post_header(False)
    headers = {
      key: value
      for key, value in header.to_dict().items()
      if isinstance(value, str)
    }
    response = http_request(
      "GET",
      url,
      headers=headers,
      timeout=get_dict_attr(self.settings(), "$.platform.douyin.owner.max_timeout"),
      proxies=self.api().proxies(),
    )
    ##
    ## The status is not a gate: only response.url is read, redirects have
    ## already been followed, and douyin answers a share link opened outside the
    ## app with 444 after resolving it perfectly well.
    ##
    return response.url

  def records_for(self, aweme_ids) -> dict:
    """Look up which of these posts are already downloaded.

    Returns an empty mapping when the database is unavailable: the list still
    renders, it just cannot mark anything.  Deduplication does not depend on this
    - it reads the files on disk - so an unmarked list is cosmetic.
    """
    database = None
    try:
      database = self.service().downloader._database_for_read()
    except Exception as e:
      get_logger().warning("owner record lookup unavailable: {}".format(e))
      return {}
    if database is None:
      return {}
    try:
      return database.find_aweme_records(aweme_ids)
    except Exception as e:
      get_logger().warning("owner record lookup failed: {}".format(e))
      return {}


def _started(service, job_id: str) -> dict:
  """Expose only the unified progress identity of a started owner download.

  The service still returns and uses its internal job id to coordinate
  JobStore with OwnerTaskMirror.  That implementation identity is deliberately
  consumed here rather than published as a second browser polling contract.
  ``task_id`` remains nullable for the existing degraded no-mirror mode.
  """
  return {"task_id": service.task_id_for(job_id)}


def build_owner_blueprint(runtime: OwnerRuntime = None, task_service=None) -> Blueprint:
  runtime = (
    runtime if runtime is not None else OwnerRuntime(task_service=task_service)
  )
  blueprint = Blueprint("owner", __name__, url_prefix="/api")

  def _page_response(sec_user_id, cursor):
    page = fetch_post_page(runtime.api(), sec_user_id, cursor=cursor)
    runtime.service().cache.remember(page.payloads)
    records = runtime.records_for(
      [get_dict_attr(item, "$.aweme_id") for item in page.payloads]
    )
    return {
      "posts": [
        _serialize_post(item, records.get(get_dict_attr(item, "$.aweme_id")))
        for item in page.payloads
      ],
      "next_cursor": page.next_cursor,
      "has_more": page.has_more,
    }

  @blueprint.route("/owner", methods=["GET"])
  @require_admin
  def read_owner():
    url = (request.args.get("url") or "").strip()
    if not url:
      return _error("缺少必需参数: url", 400)

    try:
      sec_user_id = runtime.resolve_owner(url)
    except Exception as e:
      get_logger().error("owner link resolution failed: {}".format(e))
      return _error("无法解析该链接，请稍后重试", 502)
    if sec_user_id is None:
      return _error("请粘贴主播主页分享链接", 400)

    ##
    ## The two requests are independent on purpose: a profile that cannot be read
    ## must not hide the post list, and vice versa.
    ##
    owner = None
    owner_message = None
    try:
      owner = _serialize_owner(fetch_owner_detail(runtime.api(), sec_user_id))
    except SessionExpired:
      return _error(SESSION_MESSAGE, 502)
    except OwnerUnavailable as e:
      owner_message = "主播详情不可用：{}".format(e)
    except Exception as e:
      get_logger().warning("owner detail failed: {}".format(e))
      owner_message = "主播详情不可用"

    try:
      page = _page_response(sec_user_id, FIRST_CURSOR)
    except SessionExpired:
      return _error(SESSION_MESSAGE, 502)
    except UpstreamRejected as e:
      return _error("抖音拒绝了请求：{}".format(e), 502)
    except Exception as e:
      get_logger().error("owner post page failed: {}".format(e))
      return _error("读取作品列表失败，请稍后重试", 502)

    return _success({
      "sec_user_id": sec_user_id,
      "owner": owner,
      "owner_message": owner_message,
      "credential": {"expires_in_days": runtime.api().credential_days_left()},
      **page,
    })

  @blueprint.route("/owner/posts", methods=["GET"])
  @require_admin
  def read_owner_posts():
    sec_user_id = (request.args.get("sec_user_id") or "").strip()
    if not sec_user_id:
      return _error("缺少必需参数: sec_user_id", 400)
    raw_cursor = request.args.get("cursor") or "0"
    try:
      cursor = int(raw_cursor)
    except (TypeError, ValueError):
      return _error("cursor 必须是整数", 400)

    try:
      return _success(_page_response(sec_user_id, cursor))
    except SessionExpired:
      return _error(SESSION_MESSAGE, 502)
    except UpstreamRejected as e:
      return _error("抖音拒绝了请求：{}".format(e), 502)
    except Exception as e:
      get_logger().error("owner post page failed: {}".format(e))
      return _error("读取作品列表失败，请稍后重试", 502)

  @blueprint.route("/owner/download", methods=["POST"])
  @require_admin_csrf
  def start_owner_download():
    if not request.is_json:
      return _error("请求必须是 JSON 格式", 400)
    payload = request.get_json(silent=True)
    if payload is None:
      return _error("请求体为空或格式错误", 400)

    share_url = (payload.get("share_url") or "").strip()
    service = runtime.service()

    if payload.get("all") is True:
      sec_user_id = (payload.get("sec_user_id") or "").strip()
      if not sec_user_id:
        return _error("缺少必需字段: sec_user_id", 400)
      try:
        job_id = service.start_all(sec_user_id, share_url=share_url)
      except ValueError as e:
        return _error(str(e), 400)
      return _success(_started(service, job_id))

    aweme_ids = payload.get("aweme_ids")
    if not isinstance(aweme_ids, list) or not aweme_ids:
      return _error("缺少必需字段: aweme_ids（必须是非空数组）", 400)
    try:
      job_id = service.start_selected(aweme_ids, share_url=share_url)
    except MissingPayloads as e:
      ##
      ## The cached payloads aged out.  The browser must re-read the page rather
      ## than have the server guess what those ids meant.
      ##
      return _error("作品数据已过期，请重新读取该页后再下载", 404)
    except ValueError as e:
      return _error(str(e), 400)
    return _success(_started(service, job_id))

  return blueprint
