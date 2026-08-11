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
from backend.src.service.job_store import (
  JOB_DONE,
  JOB_ERROR,
  STATE_DONE,
  STATE_ERROR,
  STATE_RUNNING,
  STATE_SKIPPED,
  JobStore,
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
  ) -> None:
    self.downloader = downloader
    self.api = api
    self.store = store if store is not None else JobStore()
    self.cache = cache if cache is not None else PayloadCache()
    self._executor = executor
    self._media_switches = media_switches

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
    self._submit(self._run_selected, job_id, payloads, share_url)
    return job_id

  def _run_selected(self, job_id: str, payloads, share_url: str) -> None:
    try:
      if payloads:
        self._write_owner_card(payloads[0])
      for payload in payloads:
        self._download_one(job_id, payload, share_url)
    except BaseException as e:
      get_logger().error("post download job {} failed: {}".format(job_id, e))
      self.store.finish(job_id, state=JOB_ERROR, message=str(e))
      return
    self.store.finish(job_id, state=JOB_DONE)

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
    self._submit(self._run_all, job_id, sec_user_id.strip(), share_url)
    return job_id

  def _run_all(self, job_id: str, sec_user_id: str, share_url: str) -> None:
    walked = 0
    wrote_card = False
    try:
      for payload in iter_all_posts(
        self.api,
        sec_user_id,
        max_pages=self.downloader.config.owner_max_pages,
      ):
        if not wrote_card:
          ##
          ## Written from the first post rather than up front, because that is
          ## where the owner identity the folder is named after comes from.
          ##
          self._write_owner_card(payload)
          wrote_card = True
        self.cache.remember([payload])
        self._download_one(job_id, payload, share_url)
        walked += 1
    except BaseException as e:
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
      self.store.finish(
        job_id,
        state=JOB_ERROR,
        message="停在第 {} 个作品：{}".format(walked + 1, e),
      )
      return
    self.store.finish(job_id, state=JOB_DONE)

##
## >>============================= one post =============================>>
##
  def _download_one(self, job_id: str, payload, share_url: str) -> None:
    aweme_id = get_dict_attr(payload, "$.aweme_id") or "?"
    self.store.update_item(job_id, aweme_id, state=STATE_RUNNING)
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
