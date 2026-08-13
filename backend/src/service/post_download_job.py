##<<Base>>
from threading import Lock
from time import monotonic

##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.base.file_fetcher import ON_EXISTS_OVERWRITE, fetch_file
from backend.src.platform.douyin.douyin_archive_notes import (
  OWNER_AVATAR_NAME,
  write_owner_note,
)
from backend.src.platform.douyin.douyin_aweme_external_info import (
  AwemeUnavailable,
  build_aweme_detail,
)
from backend.src.platform.douyin.douyin_owner_detail import fetch_owner_detail
from backend.src.platform.douyin.douyin_owner_posts import iter_all_posts
from backend.src.service.bounded_map import run_bounded
from backend.src.service.job_store import (
  JOB_DONE,
  JOB_ERROR,
  STATE_DONE,
  STATE_ERROR,
  STATE_RUNNING,
  STATE_SKIPPED,
  JobStore,
)
from backend.src.service.owner_task_mirror import PLATFORM_DOUYIN, OwnerTaskMirror
from backend.src.task.model import (
  ITEM_STATE_FAILED,
  ITEM_STATE_SKIPPED,
  ITEM_STATE_SUCCESS,
)


class PayloadCache:
  """Holds fetched post payloads so a download can reference them by id.

  A post object is a few kilobytes and a page carries nineteen of them, so asking
  the browser to send them back would move megabytes and let the client choose
  what gets downloaded.  The browser sends ids; the payloads stay here.
  """

  def __init__(self, retention_seconds: float = 1800.0, clock=monotonic) -> None:
    self._retention_seconds = retention_seconds
    self._clock = clock
    self._guard = Lock()
    self._entries = {}

  def _evict_expired(self) -> None:
    now = self._clock()
    expired = [
      key
      for key, entry in self._entries.items()
      if now - entry["touched_at"] >= self._retention_seconds
    ]
    for key in expired:
      del self._entries[key]

  def remember(self, payloads) -> int:
    """Store payloads by aweme id.  Returns how many were kept."""
    now = self._clock()
    kept = 0
    with self._guard:
      self._evict_expired()
      for payload in payloads:
        aweme_id = get_dict_attr(payload, "$.aweme_id")
        if not isinstance(aweme_id, str) or not aweme_id.strip():
          continue
        self._entries[aweme_id.strip()] = {
          "payload": payload,
          "touched_at": now,
        }
        kept += 1
    return kept

  def take(self, aweme_ids):
    """Return ``(payloads, missing_ids)`` for the requested ids, in order."""
    payloads = []
    missing = []
    with self._guard:
      self._evict_expired()
      for aweme_id in aweme_ids:
        key = str(aweme_id).strip()
        entry = self._entries.get(key)
        if entry is None:
          missing.append(key)
          continue
        entry["touched_at"] = self._clock()
        payloads.append(entry["payload"])
    return payloads, missing

  def tracked(self) -> int:
    with self._guard:
      self._evict_expired()
      return len(self._entries)


class MissingPayloads(KeyError):
  """Some requested posts are no longer cached.

  The browser must re-read the page rather than download something arbitrary.
  """

  def __init__(self, missing):
    self.missing = list(missing)
    super().__init__(
      "these posts are no longer cached, reload the page: {}".format(
        ", ".join(self.missing[:5])
      )
    )


def _owner_title(payload=None) -> str:
  """Name the task after the owner when the payload already says who that is.

  Never worth a platform request: the title is decoration on a task the user
  just started, and the walk has no payload at all until its first page lands.
  """
  nickname = get_dict_attr(payload or {}, "$.author.nickname")
  if isinstance(nickname, str) and nickname.strip():
    return "下载{}的作品".format(nickname.strip())
  return "下载主播作品"


class PostDownloadJobService:
  """Runs post downloads in the background and reports progress.

  Reuses ``DouyinAwemeDownloader`` wholesale: directory layout, identity-based
  deduplication, shared-nickname disambiguation, per-post locking and persistence
  all come from there.  This service only decides *which* posts to hand it.
  """

  def __init__(
    self,
    downloader,
    api=None,
    store: JobStore = None,
    cache: PayloadCache = None,
    executor=None,
    media_switches=None,
    task_service=None,
    post_pool=None,
    post_concurrency: int = 1,
  ) -> None:
    self.downloader = downloader
    self.api = api
    self.store = store if store is not None else JobStore()
    self.cache = cache if cache is not None else PayloadCache()
    ##
    ## Owner batch download is temporarily dual-written: ``store`` is the legacy
    ## compatibility surface the current page polls, and the mirror reports the
    ## same work onto the unified TaskService the next frontend will read.
    ##
    ## The task service is injected rather than constructed here.  One process
    ## must have exactly one task store, and a service that built its own would
    ## report into a store no request could ever read.  Passing ``None`` is a
    ## supported wiring that simply reports nothing.
    ##
    self.task_service = task_service
    self._tasks = OwnerTaskMirror(task_service)
    self._executor = executor
    self._media_switches = media_switches
    ##
    ## The pool that runs posts, distinct from ``executor`` which runs whole
    ## jobs.  Shared across jobs on purpose: the limit is how many posts are in
    ## flight process-wide, not per job, because the CDN quota that this pacing
    ## protects is counted process-wide too.
    ##
    self._post_pool = post_pool
    self._post_concurrency = post_concurrency

  def task_id_for(self, job_id: str):
    """The unified task mirroring ``job_id``, or ``None`` when there is not one.

    The association is held by the mirror; neither id is ever derived from the
    other.
    """
    return self._tasks.task_id(job_id)

  def _switches(self):
    if self._media_switches is not None:
      return self._media_switches
    return self.downloader.config.media_switches

  def _quality(self):
    return getattr(self.downloader.config, "video_quality", "highest")

  def _write_owner_card(self, payload) -> None:
    """Put the owner's card and avatar in their folder, one level above the posts.

    Refreshed on every job: the counts are a snapshot, and a folder downloaded
    before cards existed gains one.  One platform request per job, not per post.

    Failure is never fatal - the card is a convenience beside the media, so a
    profile that cannot be read or an avatar that will not fetch leaves the
    download itself untouched.
    """
    if self.api is None:
      return
    try:
      detail = build_aweme_detail(
        payload,
        switches=self._switches(),
        quality=self._quality(),
      )
    except AwemeUnavailable:
      return
    sec_user_id = detail.sec_user_id
    if not sec_user_id:
      return

    try:
      owner = fetch_owner_detail(self.api, sec_user_id)
    except Exception as e:
      get_logger().warning("owner card skipped, profile unavailable: {}".format(e))
      return

    owner_dir = self.downloader.build_owner_dir(detail)
    write_owner_note(owner_dir, owner)

    if not owner.avatar_url:
      return
    try:
      fetch_file(
        owner.avatar_url,
        owner_dir,
        OWNER_AVATAR_NAME,
        headers=self.downloader.media_headers(),
        proxies=self.downloader.media_proxies(),
        timeout=self.downloader.config.max_timeout,
        max_retry=0,
        ##
        ## Overwritten rather than skipped: an avatar changes, and the card next
        ## to it is a fresh snapshot every time.
        ##
        on_exists=ON_EXISTS_OVERWRITE,
        keep_partial=False,
      )
    except Exception as e:
      get_logger().warning("owner avatar not saved: {}".format(e))

  def _download_each(self, job_id: str, payloads, share_url: str) -> None:
    """Download every payload, at most ``post_concurrency`` at once.

    Returns only when all of them have finished, so the caller may mark the job
    complete straight after.  At the default of one this is an ordinary serial
    loop, byte for byte the behaviour before the setting existed.
    """
    run_bounded(
      payloads,
      lambda payload: self._download_one(job_id, payload, share_url),
      pool=self._post_pool,
      limit=self._post_concurrency,
    )

  def _submit(self, function, *args):
    if self._executor is None:
      ##
      ## No executor means run inline; the tests and the "download one page"
      ## path use this.
      ##
      function(*args)
      return None
    return self._executor.submit(function, *args)

##
## >>============================= selected posts =============================>>
##
  def start_selected(self, aweme_ids, share_url: str = ""):
    """Download the posts the user ticked.  Returns a job id."""
    ids = [str(value).strip() for value in aweme_ids if str(value).strip()]
    if not ids:
      raise ValueError("no posts were selected")
    payloads, missing = self.cache.take(ids)
    if missing:
      raise MissingPayloads(missing)

    job_id = self.store.create(ids)
    ##
    ## The task counts posts, not clicks.  A selection carrying the same id twice
    ## is one post to download, so the task lists it once and its total says two
    ## rather than a three nothing could ever reach.  The legacy job keeps the
    ## list exactly as it was given; changing how it counts is not this
    ## migration's business.
    ##
    unique_ids = list(dict.fromkeys(ids))
    self._tasks.open(
      job_id,
      title=_owner_title(payloads[0] if payloads else None),
      metadata={
        "platform": PLATFORM_DOUYIN,
        "legacy_job_id": job_id,
        "mode": "selected",
        "requested_count": len(unique_ids),
      },
      ##
      ## No explicit total: the store derives it from the items, which keeps the
      ## two numbers from ever disagreeing.
      ##
      items=unique_ids,
    )
    self._submit(self._run_selected, job_id, payloads, share_url)
    return job_id

  def _run_selected(self, job_id: str, payloads, share_url: str) -> None:
    self._tasks.start(job_id, message="正在下载所选作品")
    try:
      if payloads:
        self._write_owner_card(payloads[0])
      self._download_each(job_id, payloads, share_url)
    except BaseException as e:
      get_logger().error("post download job {} failed: {}".format(job_id, e))
      self.store.finish(job_id, state=JOB_ERROR, message=str(e))
      self._tasks.finish(job_id, message=str(e), stopped_early=True)
      return
    self.store.finish(job_id, state=JOB_DONE)
    self._tasks.finish(job_id)

##
## >>============================= every post =============================>>
##
  def start_all(self, sec_user_id: str, share_url: str = ""):
    """Download every post of one owner, walking the pages.  Returns a job id."""
    if not isinstance(sec_user_id, str) or not sec_user_id.strip():
      raise ValueError("sec_user_id is required")
    if self.api is None:
      raise ValueError("an owner api is required to walk the pages")
    ##
    ## The item list starts empty and grows as pages arrive - the total is not
    ## knowable until the walk ends.
    ##
    job_id = self.store.create([])
    self._tasks.open(
      job_id,
      title=_owner_title(),
      metadata={
        "platform": PLATFORM_DOUYIN,
        "legacy_job_id": job_id,
        "mode": "all",
        "sec_user_id": sec_user_id.strip(),
      },
      ##
      ## Explicitly unknown rather than the profile's ``aweme_count``: that is a
      ## platform statistic which disagrees with what the pages actually hand
      ## over often enough that trusting it would buy a tidy percentage with a
      ## wrong one.  The real total is settled when the walk ends.
      ##
      total=None,
    )
    self._submit(self._run_all, job_id, sec_user_id.strip(), share_url)
    return job_id

  def _run_all(self, job_id: str, sec_user_id: str, share_url: str) -> None:
    ##
    ## Held in a list so the walk, which runs inside the generator below, and the
    ## error report, which runs out here, see the same count.
    ##
    progress = {"walked": 0, "wrote_card": False}
    self._tasks.start(job_id, message="正在读取主播作品")

    def walk():
      """Yield each post, doing the once-per-owner work as it goes.

      The card, the cache and the count stay on this thread even when the
      downloads themselves are handed to the pool: they are ordered work about
      the walk, not about any one post.
      """
      for payload in iter_all_posts(
        self.api,
        sec_user_id,
        max_pages=self.downloader.config.owner_max_pages,
      ):
        if not progress["wrote_card"]:
          ##
          ## Written from the first post rather than up front, because that is
          ## where the owner identity the folder is named after comes from.
          ##
          self._write_owner_card(payload)
          progress["wrote_card"] = True
        self.cache.remember([payload])
        progress["walked"] += 1
        ##
        ## Registered before it is yielded, so the post is on the task list
        ## before any worker can report running against it.  Registering is
        ## idempotent, which is what makes an overlapping page harmless.
        ##
        aweme_id = get_dict_attr(payload, "$.aweme_id")
        if aweme_id:
          self._tasks.add_item(job_id, aweme_id)
        self._tasks.narrate(
          job_id, "已读取 {} 个作品".format(progress["walked"])
        )
        yield payload

    try:
      self._download_each(job_id, walk(), share_url)
    except BaseException as e:
      walked = progress["walked"]
      stop_message = "停在第 {} 个作品：{}".format(walked + 1, e)
      ##
      ## Pages already walked stay downloaded.  A mid-walk refusal - an expired
      ## session, most likely - is reported with how far it got rather than
      ## discarding the work.
      ##
      get_logger().error(
        "owner {} download stopped after {} posts: {}".format(
          sec_user_id,
          walked,
          e,
        )
      )
      self.store.finish(job_id, state=JOB_ERROR, message=stop_message)
      self._tasks.finish(job_id, message=stop_message, stopped_early=True)
      return
    ##
    ## Only now is the size of this owner's feed known, so this is where the
    ## total stops being null.
    ##
    self._tasks.settle_total(job_id)
    self.store.finish(job_id, state=JOB_DONE)
    self._tasks.finish(job_id)

##
## >>============================= one post =============================>>
##
  def _download_one(self, job_id: str, payload, share_url: str) -> None:
    aweme_id = get_dict_attr(payload, "$.aweme_id") or "?"
    self.store.update_item(job_id, aweme_id, state=STATE_RUNNING)
    self._tasks.item_running(job_id, aweme_id)
    try:
      detail = build_aweme_detail(
        payload,
        switches=self._switches(),
        quality=self._quality(),
      )
    except AwemeUnavailable as e:
      ##
      ## Nothing downloadable in this post - deleted, restricted, or every media
      ## kind switched off.  An ordinary answer, not a failure of the job.
      ##
      self.store.update_item(
        job_id,
        aweme_id,
        state=STATE_SKIPPED,
        message=str(e),
      )
      self._tasks.item_finished(
        job_id, aweme_id, ITEM_STATE_SKIPPED, message=str(e)
      )
      return

    try:
      ##
      ## Declared as the owner's, which only this path can do: it was given a
      ## profile link to browse, and a short link says nothing about itself.
      ##
      result = self.downloader.download_detail(
        detail,
        share_url or "",
        owner_share_url=share_url or None,
      )
    except Exception as e:
      get_logger().warning("post {} failed: {}".format(aweme_id, e))
      self.store.update_item(
        job_id,
        aweme_id,
        state=STATE_ERROR,
        message=str(e),
      )
      ##
      ## The reason only, never the traceback: this reaches a browser.  The full
      ## trace is already in the log line above.
      ##
      self._tasks.item_finished(
        job_id, aweme_id, ITEM_STATE_FAILED, message=str(e)
      )
      return

    self.store.update_item(
      job_id,
      aweme_id,
      state=STATE_SKIPPED if result.skipped else STATE_DONE,
      saved=result.saved_count,
      planned=result.media_count,
      save_dir=result.save_dir,
      message=result.reason,
    )
    self._tasks.item_finished(
      job_id,
      aweme_id,
      ITEM_STATE_SKIPPED if result.skipped else ITEM_STATE_SUCCESS,
      message=result.reason,
      ##
      ## A summary of what landed on disk, not the post payload: the payload
      ## stays in PayloadCache, and a task carries state rather than transporting
      ## platform data to the browser.
      ##
      metadata={
        "saved_count": result.saved_count,
        "media_count": result.media_count,
        "save_dir": result.save_dir,
      },
    )
