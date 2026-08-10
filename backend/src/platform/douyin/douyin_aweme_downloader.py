##<<Base>>
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from time import monotonic

##<<Third-part>>
from backend.src.base.downloader import Downloader
from backend.src.base.file_fetcher import (
  ON_EXISTS_OVERWRITE,
  ON_EXISTS_SKIP,
  fetch_file,
)
from backend.src.database.schema_guard import (
  DatabaseWriteBlocked,
  get_schema_guard,
)
from backend.src.database.table.aweme_record import DouyinAwemeRecordTable
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.platform.douyin.douyin_aweme_config import DouyinAwemeConfig
from backend.src.platform.douyin.douyin_aweme_external_info import naming_tick
from backend.src.platform.douyin.douyin_owner_directory import (
  choose_owner_directory,
)
from backend.src.platform.douyin.douyin_aweme_resolver import DouyinAwemeResolver
from backend.src.platform.douyin.douyin_header import DouyinPostInfoHeader
from backend.src.platform.douyin.douyin_login import DouyinLogin


PLATFORM = "douyin"

##
## Path segment for post downloads.  A literal rather than
## $.platform.douyin.download.type, whose value is "live" process-wide.
##
AWEME_PATH_SEGMENT = "aweme"


class PostLocks:
  """Serialises work on one post without keeping a lock per id forever.

  Two workers handed the same link - a duplicated line in one paste, or the same
  link submitted twice - would otherwise both list the directory, both find the
  file missing, and both open the same path for writing, interleaving two streams
  into one file.  The pool has several workers, so this is reachable.

  Entries are reference counted and dropped when the last holder leaves, so a
  long-running server does not accumulate one lock per post it has ever seen.
  """

  def __init__(self) -> None:
    self._guard = Lock()
    self._entries = {}

  @contextmanager
  def hold(self, key: str):
    with self._guard:
      entry = self._entries.get(key)
      if entry is None:
        entry = [Lock(), 0]
        self._entries[key] = entry
      entry[1] += 1
    lock = entry[0]
    lock.acquire()
    try:
      yield
    finally:
      lock.release()
      with self._guard:
        entry[1] -= 1
        if entry[1] <= 0:
          self._entries.pop(key, None)

  def tracked(self) -> int:
    """How many posts currently hold or await a lock.  For tests."""
    with self._guard:
      return len(self._entries)


@dataclass(frozen=True)
class AwemeDownloadResult:
  """What one post attempt produced."""

  ok: bool
  aweme_id: str = None
  save_dir: str = None
  media_count: int = 0
  saved_count: int = 0
  skipped: bool = False
  reason: str = None

  @property
  def partial(self) -> bool:
    return self.ok and 0 < self.saved_count < self.media_count


class DouyinAwemeDownloader(Downloader):
  """Downloads one post per ``run`` call.

  Post files are fetched one after another inside a single call; the concurrency
  in this path sits between posts, on the executor below.  That keeps a pasted
  batch of links from turning into one burst of platform requests.
  """

  def __init__(self, config: dict = None) -> None:
    self.database = None
    self._database_warning_state = None
    self._database_clock = monotonic
    self._database_retry_at = 0.0
    self._database_retry_seconds = 30.0
    self._lock = Lock()
    self.post_locks = PostLocks()
    self.construct_aggregation_class(config)
    super().__init__(self.config.get_config_dict_attr("$.download"))

##
## >>============================= abstract method =============================>>
##
  def construct_aggregation_class(self, config: dict = None):
    self.config = (
      config if isinstance(config, DouyinAwemeConfig)
      else DouyinAwemeConfig(config)
    )
    self.login = DouyinLogin(
      self.config.get_config_dict_attr("$.platform.douyin.login")
    )
    self.resolver = DouyinAwemeResolver(self.config)

  def media_proxies(self):
    """Proxies for media transfers, from ``$.platform.douyin.login.proxies``.

    Passed explicitly, exactly as the live path does.  Omitting it would let
    ``requests`` fall back to HTTP_PROXY/HTTPS_PROXY, so a configured proxy would
    apply to recordings but be bypassed for posts.
    """
    return self.login.proxies.get_proxies_dict()

  def media_headers(self) -> dict:
    """Headers for media transfers: the browser identity plus a referer.

    The CDN is a different host from the API, so only the identifying fields
    carry over; sending the API's full header set here would be noise.
    """
    header = DouyinPostInfoHeader(
      self.config.get_config_dict_attr("$.platform.douyin.headers")
    )
    header.init_header(self.config.login)
    source = header.to_dict()
    headers = {}
    for key, value in source.items():
      if not isinstance(value, str):
        continue
      if key.lower() in ("user-agent", "referer", "accept-language"):
        headers[key] = value
    return headers

  def dump_config(self):
    self.config.dump_config()

  def run(self, token) -> AwemeDownloadResult:
    """Resolve one post link and fetch its files."""
    url = get_dict_attr(token, "$.url") if isinstance(token, dict) else None
    if not isinstance(url, str) or not url.strip():
      raise ValueError("Aweme token must contain a URL")

    ##
    ## The handler already followed the share link, so it passes down what it
    ## learned.  A bare token still works - the resolver follows the link itself -
    ## but then it costs one more request.
    ##
    resolved_url = get_dict_attr(token, "$.resolved_url") or url
    resolution = self.resolver.resolve(
      resolved_url,
      aweme_id=get_dict_attr(token, "$.aweme_id"),
    )
    if resolution.ok is not True:
      ##
      ## A link that cannot be resolved is an ordinary answer, not a crash: the
      ## post may be deleted, private or follower-only.  Report and move on so a
      ## batch of links is not abandoned over one of them.
      ##
      get_logger().info(
        "skip post {}: {}".format(
          resolution.aweme_id or url,
          resolution.reason,
        )
      )
      return AwemeDownloadResult(
        ok=False,
        aweme_id=resolution.aweme_id,
        reason=resolution.reason,
      )

    detail = resolution.detail
    save_dir = self.build_save_dir(detail)

    ##
    ## What is on disk decides what still needs fetching - see _fetch_media.  The
    ## recorded counts deliberately do not: media_count is only what one payload
    ## happened to expose, and the platform is not consistent about it.  A run
    ## that saw no cover would record a complete 2 of 2, and gating on that would
    ## make the next run skip the post entirely and never fetch the cover.
    ##
    ## Held for one post at a time so that reading the directory and writing into
    ## it cannot interleave with another worker handed the same link.
    ##
    with self.post_locks.hold(detail.aweme_id):
      saved_count, fetched_count = self._fetch_media(detail, save_dir)
      self._persist(detail, url, save_dir, saved_count)

    if fetched_count == 0 and saved_count == detail.media_count:
      get_logger().info(
        "post {} was already on disk, nothing to fetch".format(detail.aweme_id)
      )
      return AwemeDownloadResult(
        ok=True,
        aweme_id=detail.aweme_id,
        save_dir=str(save_dir),
        media_count=detail.media_count,
        saved_count=saved_count,
        skipped=True,
        reason="already downloaded",
      )

    if saved_count < detail.media_count:
      get_logger().warning(
        "post {} saved {} of {} files".format(
          detail.aweme_id,
          saved_count,
          detail.media_count,
        )
      )
    else:
      get_logger().info(
        "post {} complete: {} files in {}".format(
          detail.aweme_id,
          saved_count,
          save_dir,
        )
      )

    return AwemeDownloadResult(
      ok=True,
      aweme_id=detail.aweme_id,
      save_dir=str(save_dir),
      media_count=detail.media_count,
      saved_count=saved_count,
    )

##
## >>============================= sub class method =============================>>
##
  def resolve_directory_name(self, detail) -> str:
    """Return the folder to use for this owner.

    The naming policy is shared with the live path - see
    ``douyin_owner_directory`` for what it corrects and why.  This method only
    fetches the two inputs the policy needs from this path's database handle.

    Both inputs need the database.  Without it the bare nickname is used, matching
    the live path rather than refusing to download.
    """
    fallback = detail.directory_name
    database = self._database_for_read()
    if database is None or not detail.owner_user_id:
      return choose_owner_directory(fallback)
    try:
      recorded = database.find_owner_directory_name(detail.owner_user_id)
      owners = database.count_owners_using_directory_name(recorded or fallback)
    except Exception as e:
      get_logger().warning(
        "database directory lookup failed, use post nickname: {}".format(e)
      )
      self._mark_database_unavailable()
      return choose_owner_directory(fallback)

    resolved = choose_owner_directory(
      fallback,
      recorded_directory=recorded,
      owner_user_id=detail.owner_user_id,
      owner_count=owners,
    )
    if resolved != fallback:
      get_logger().info(
        "owner {} files under {} rather than {} (recorded={}, owners={})".format(
          detail.owner_user_id,
          resolved,
          fallback,
          recorded,
          owners,
        )
      )
    return resolved

  def build_save_dir(self, detail) -> Path:
    """Return the directory this post's files belong in.

    Every post gets its own folder, not just image posts.  A single video post
    already yields three files - the video, its audio track and its cover - so
    filing them flat under the owner mixes several posts' pieces together with
    nothing but the file names to tell them apart.  One folder per post keeps a
    post archived as a unit.

    The folder is named ``{publish tick}_{aweme_id}``, both stable, so a re-run
    lands in the same place.
    """
    base = Path(self.config.save_path) / PLATFORM / AWEME_PATH_SEGMENT
    directory_name = self.resolve_directory_name(detail)
    if self.config.folderize and directory_name:
      base = base / directory_name
    tick = naming_tick(detail.create_time)
    return base / "_".join(part for part in (tick, detail.aweme_id) if part)

  @staticmethod
  def existing_file_names(save_dir) -> list:
    directory = Path(save_dir)
    if not directory.is_dir():
      return []
    return [entry.name for entry in directory.iterdir() if entry.is_file()]

  @staticmethod
  def carries_aweme_id(file_name: str, aweme_id: str) -> bool:
    """Whether ``file_name`` names this post, on an underscore boundary.

    A plain substring test would let one id match inside a longer one - the id
    ``7657271784144009946`` appears inside ``9957657271784144009946`` - and skip a
    download because of an unrelated post's file.  Real ids are all 19 digits, so
    equal-length ids cannot nest and the bug would never fire on live data; that
    is a property of the data, not of the code, and not worth relying on.
    """
    if not file_name or not aweme_id:
      return False
    stem = file_name.rsplit(".", 1)[0]
    return aweme_id in stem.split("_")

  @classmethod
  def match_existing(cls, existing_names, aweme_id: str, item):
    """Return the name of the file this media item already produced, if any.

    Matched on the aweme id plus the item's stable tail rather than on the whole
    file name, so a file written by an earlier version of the naming scheme is
    still recognised.  Names used to carry the post caption; an exact-name check
    would miss those and fetch a second copy under the new name.
    """
    if not item.identity:
      return None
    for name in existing_names:
      if cls.carries_aweme_id(name, aweme_id) and name.endswith(item.identity):
        return name
    return None

  def _fetch_media(self, detail, save_dir: Path):
    """Fetch what is missing.  Returns ``(saved_count, fetched_count)``.

    ``saved_count`` is how many of the planned files are now on disk, whether
    this call put them there or found them.  ``fetched_count`` is how many were
    actually transferred, which is what tells a caller whether the post was
    already complete.

    Disk is the authority here rather than the recorded counts: it survives a
    payload that omits a file, a database that is switched off, and a record that
    was removed by hand.
    """
    if self.config.test_mode:
      get_logger().info(
        "test mode enabled, skip post file download for {}".format(
          detail.aweme_id
        )
      )
      return 0, 0

    saved_count = 0
    fetched_count = 0
    proxies = self.media_proxies()
    headers = self.media_headers()
    ##
    ## Listed once: a 35-image post would otherwise re-scan a growing directory
    ## for every file.
    ##
    existing_names = (
      self.existing_file_names(save_dir) if self.config.skip_downloaded else []
    )
    for item in detail.media:
      already = self.match_existing(existing_names, detail.aweme_id, item)
      if already is not None:
        ##
        ## the file this post already produced, possibly under an older caption
        ##
        get_logger().info(
          "post {} {} already on disk as {}".format(
            detail.aweme_id,
            item.kind,
            already,
          )
        )
        saved_count += 1
        continue
      try:
        written = fetch_file(
          item.url,
          save_dir,
          item.file_name,
          headers=headers,
          proxies=proxies,
          timeout=self.config.max_timeout,
          max_retry=self.config.max_retry,
          ##
          ## A file name carries the aweme id, so the same name is the same
          ## content: skip it rather than write a second copy.  A truncated file
          ## must not survive either, or the next run would read it as complete.
          ##
          on_exists=(
            ON_EXISTS_SKIP if self.config.skip_downloaded
            else ON_EXISTS_OVERWRITE
          ),
          keep_partial=False,
        )
        ##
        ## a skipped file is already on disk, so it counts as saved
        ##
        saved_count += 1
        if written is not None:
          fetched_count += 1
          existing_names.append(written.name)
      except Exception as e:
        get_logger().warning(
          "post {} {} failed: {}".format(detail.aweme_id, item.kind, e)
        )
      self.resolver.pause()
    return saved_count, fetched_count

##
## >>============================= persistence =============================>>
##
  def _persist(self, detail, url: str, save_dir: Path, saved_count: int):
    database = self._database_if_ready()
    if database is None:
      return
    try:
      ##
      ## No owner id, no owner row.  The platform sometimes answers without
      ## author.uid, and share_url is keyed on it - writing a blank key would leave
      ## a row nothing can match and inflate the count of owners sharing a folder.
      ## The aweme_record below is still written; it is keyed on the post.
      ##
      if detail.owner_user_id:
        database.upsert_post_owner({
          "owner_user_id": detail.owner_user_id,
          "sec_user_id": detail.sec_user_id,
          "nickname": detail.nickname,
          "post_share_url": url,
          "directory_name": detail.directory_name,
        })
      else:
        get_logger().warning(
          "post {} carries no owner id, skipping the owner row".format(
            detail.aweme_id
          )
        )
      record = database.get_aweme_record_table_tuple().copy()
      record.update({
        "platform": PLATFORM,
        "aweme_id": detail.aweme_id,
        "owner_user_id": detail.owner_user_id or None,
        "sec_user_id": detail.sec_user_id or None,
        "aweme_type": detail.aweme_type,
        "desc": detail.desc,
        "create_time": detail.create_time,
        "downloaded_at": datetime.now(),
        "media_count": detail.media_count,
        "saved_count": saved_count,
        "save_dir": str(save_dir),
        "source": detail.source,
      })
      database.upsert_aweme_record(record)
    except Exception as e:
      get_logger().warning(
        "database persistence failed, files are kept: {}".format(e)
      )
      self._mark_database_unavailable()

  def _new_database(self):
    return DouyinAwemeRecordTable(
      host=self.config.get_config_dict_attr("$.database.host"),
      user=self.config.get_config_dict_attr("$.database.username"),
      passwd=self.config.get_config_dict_attr("$.database.password"),
      database=self.config.get_config_dict_attr("$.database.name"),
    )

  def _mark_database_unavailable(self):
    self.database = None
    self._database_retry_at = (
      self._database_clock() + self._database_retry_seconds
    )

  def _database_for_read(self):
    if self.database is not None:
      return self.database
    if self.config.get_config_dict_attr("$.database.enable") is not True:
      return None
    now = self._database_clock()
    if now < self._database_retry_at:
      return None
    try:
      self.database = self._new_database()
      self._database_retry_at = 0.0
      if self._database_warning_state == "unavailable":
        self._database_warning_state = None
    except Exception:
      self._mark_database_unavailable()
      if self._database_warning_state != "unavailable":
        get_logger().warning(
          "database unavailable, continue post download without database"
        )
        self._database_warning_state = "unavailable"
    return self.database

  def _database_if_ready(self):
    if self.config.get_config_dict_attr("$.database.enable") is not True:
      return None
    guard = get_schema_guard()
    if guard is not None:
      try:
        guard.require_write_ready()
      except DatabaseWriteBlocked:
        snapshot = guard.snapshot
        state = "blocked" if snapshot is None else snapshot.state.value
        if self._database_warning_state != state:
          get_logger().warning(
            "database persistence is {}, continue post download".format(state)
          )
          self._database_warning_state = state
        return None
    return self._database_for_read()


##
## >>================================ public method ===============================>>
##
downloader = None
_downloader_lock = Lock()
_executor = None
_executor_lock = Lock()


def get_aweme_downloader():
  global downloader
  if downloader is None:
    with _downloader_lock:
      if downloader is None:
        downloader = DouyinAwemeDownloader()
  return downloader


def get_aweme_executor(max_workers: int = None):
  """Return the post download pool.

  Its own pool on purpose.  The live executor has a single worker held for the
  length of a recording, and the probe pool is sized for probing; borrowing
  either would let one path stall the other.
  """
  global _executor
  if _executor is None:
    with _executor_lock:
      if _executor is None:
        workers = max_workers
        if not isinstance(workers, int) or workers < 1:
          workers = 3
        _executor = ThreadPoolExecutor(
          max_workers=workers,
          thread_name_prefix="aweme-download",
        )
  return _executor


def shutdown_aweme_downloads(wait: bool = False) -> None:
  """Stop accepting new posts.  Files in flight finish or are discarded."""
  global _executor
  with _executor_lock:
    existing = _executor
    _executor = None
  if existing is not None:
    existing.shutdown(wait=wait, cancel_futures=True)


def download_single_aweme(token: dict):
  return get_aweme_downloader().run(token)


def download_multiple_aweme(token_list: list):
  """Submit each post to the post pool and return without waiting."""
  if not token_list:
    return []
  active_downloader = get_aweme_downloader()
  if active_downloader.config.debug:
    active_downloader.dump_config()
  executor = get_aweme_executor(active_downloader.config.concurrency)
  futures = []
  for token in token_list:
    futures.append(executor.submit(active_downloader.run, token))
  return futures
