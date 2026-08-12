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
from backend.src.platform.douyin.douyin_archive_notes import write_post_note
from backend.src.platform.douyin.douyin_aweme_external_info import naming_tick
from backend.src.platform.douyin.douyin_owner_directory import (
  choose_owner_directory,
)
from backend.src.database.table.person_identity import DouyinPersonIdentityTable
from backend.src.platform.douyin.douyin_url_hosts import host_of, is_short_link_host
from backend.src.platform.douyin.douyin_aweme_resolver import DouyinAwemeResolver
from backend.src.platform.douyin.douyin_header import DouyinPostInfoHeader
from backend.src.platform.douyin.douyin_login import DouyinLogin


PLATFORM = "douyin"

##
## Path segment for post downloads.  A literal rather than
## $.platform.douyin.download.type, whose value is "live" process-wide.
##
AWEME_PATH_SEGMENT = "aweme"


def _owner_share_link(url: str):
  """Return ``url`` if it is an owner's share link, else ``None``.

  Two conditions, and both are needed.  It has to be the short form, because a
  long profile url is rebuildable from ``sec_user_id`` and is not what douyin
  expects handed back.  And it has to have been declared an owner's by the
  caller, because an owner's share link and a post's are the same shape and
  nothing in the string separates them - only the path that followed it knows.
  """
  if not url or not isinstance(url, str):
    return None
  return url if is_short_link_host(host_of(url)) else None


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
    self._person_database = None
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

    return self.download_detail(resolution.detail, url)

  def download_detail(
    self,
    detail,
    share_url: str,
    owner_share_url: str = None,
  ) -> AwemeDownloadResult:
    """Download one already-resolved post.

    Split out from ``run`` so a caller that already holds the post object can skip
    resolving it.  The owner browse path lists posts through ``USER_POST``, whose
    items are the same shape ``POST_DETAIL`` returns - so downloading a page of
    posts costs no per-post requests at all.

    ``owner_share_url`` is the profile link the browse path was given, passed
    down only by a caller that knows the link is an owner's.  It cannot be told
    from a post link by looking - both are ``v.douyin.com/<code>/`` - so it is
    declared rather than detected.
    """
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
      ##
      ## Written every run, not only the first.  A folder downloaded before notes
      ## existed gets one added, and an edited caption is picked up - both without
      ## a platform request.  Deliberately outside the "nothing to fetch" check
      ## below, or an already-complete post would never gain its note.
      ##
      if not self.config.test_mode:
        write_post_note(save_dir, detail)
      self._persist(detail, share_url, save_dir, saved_count, owner_share_url)

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
    ##
    ## Asked first and independently of the record table.  Whether this account
    ## belongs to a marked person has nothing to do with whether aweme_record is
    ## readable, and a person folder still applies when that lookup is skipped.
    ##
    person = self._person_folder(detail.owner_user_id)
    person_directory = person["directory_name"] if person else None
    person_owner = person["main_owner_user_id"] if person else None

    database = self._database_for_read()
    if database is None or not detail.owner_user_id:
      return choose_owner_directory(
        fallback,
        person_directory=person_directory,
        person_owner_user_id=person_owner,
        owner_count=self._identity_count(person_directory),
      )
    try:
      recorded = database.find_owner_directory_name(detail.owner_user_id)
      ##
      ## A marked account is counted by identity, so that its person's own
      ## accounts - which all record the same folder - do not look like a
      ## collision with each other.
      ##
      owners = (
        self._identity_count(person_directory) if person_directory
        else database.count_owners_using_directory_name(recorded or fallback)
      )
    except Exception as e:
      get_logger().warning(
        "database directory lookup failed, use post nickname: {}".format(e)
      )
      self._mark_database_unavailable()
      return choose_owner_directory(
        fallback,
        person_directory=person_directory,
        person_owner_user_id=person_owner,
      )

    resolved = choose_owner_directory(
      fallback,
      recorded_directory=recorded,
      owner_user_id=detail.owner_user_id,
      owner_count=owners,
      person_directory=person_directory,
      person_owner_user_id=person_owner,
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

  def _identity_count(self, directory_name) -> int:
    """How many distinct identities file under ``directory_name``.

    Answers 1 when it cannot be known: an unknown count must not invent a
    collision that would append a discriminator nobody asked for.
    """
    if not directory_name:
      return 1
    database = self._person_database_for_read()
    if database is None:
      return 1
    try:
      return max(1, database.count_identities_using_directory_name(directory_name))
    except Exception as e:
      get_logger().warning("identity count failed, assume unique: {}".format(e))
      return 1

  def _person_folder(self, owner_user_id: str):
    """Return this account's person folder and discriminating id, or ``None``.

    Every failure answers ``None``: no person table, no marking, or a database
    that will not answer.  Whose account this is, is extra information about a
    download - never a precondition for one - so a lookup that fails here must
    leave the download filing exactly where it would have without people.
    """
    if not owner_user_id:
      return None
    database = self._person_database_for_read()
    if database is None:
      return None
    try:
      return database.find_person_folder(owner_user_id)
    except Exception as e:
      get_logger().warning(
        "person directory lookup failed, use the account's own: {}".format(e)
      )
      return None

  def _person_database_for_read(self):
    """Lazily hold a person table handle, sharing the process-wide pool.

    Separate from the aweme handle so each table's SQL stays with its own
    module.  The connection pool is class-wide, so a second handle costs a
    Python object rather than a connection.
    """
    if self._person_database is not None:
      return self._person_database
    if self.config.get_config_dict_attr("$.database.enable") is not True:
      return None
    try:
      self._person_database = DouyinPersonIdentityTable(
        host=self.config.get_config_dict_attr("$.database.host"),
        user=self.config.get_config_dict_attr("$.database.username"),
        passwd=self.config.get_config_dict_attr("$.database.password"),
        database=self.config.get_config_dict_attr("$.database.name"),
      )
    except Exception as e:
      get_logger().warning("person table unavailable: {}".format(e))
      return None
    return self._person_database

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
    tick = naming_tick(detail.create_time)
    return self.build_owner_dir(detail) / "_".join(
      part for part in (tick, detail.aweme_id) if part
    )

  def build_owner_dir(self, detail) -> Path:
    """Return the owner-level folder that this post's folder sits in.

    Separated from ``build_save_dir`` because the owner's own card is written
    here, one level above the individual posts.
    """
    base = Path(self.config.save_path) / PLATFORM / AWEME_PATH_SEGMENT
    directory_name = self.resolve_directory_name(detail)
    if self.config.folderize and directory_name:
      base = base / directory_name
    return base

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
  def _persist(
    self,
    detail,
    url: str,
    save_dir: Path,
    saved_count: int,
    owner_share_url: str = None,
  ):
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
        ##
        ## share_url.post_share_url holds the owner's *profile* link, paired with
        ## live_share_url - one row per owner, two ways in.  A post link does not
        ## belong there, and writing one overwrites a profile link that was
        ## already correct.
        ##
        ## Exactly one shape goes in: the owner's *share* link, short form, stored
        ## as pasted.  Anything else yields None, which the upsert's COALESCE
        ## turns into "leave whatever is there alone".
        ##
        ## Not a long profile url.  ``douyin.com/user/<sec_user_id>`` can be
        ## rebuilt from the sec_user_id in this same row, so keeping it stores
        ## nothing new.  The short code cannot be rebuilt - douyin issues it and
        ## it is opaque - and it is the form that behaves like a real share when
        ## handed back, which is the point of keeping it at all.
        ##
        ## Not a post's share link either, though it is the same shape.  Nothing
        ## in the string tells the two apart, so the only evidence is the caller:
        ## the browse path declares what it was given, and no other path may.
        ##
        database.upsert_post_owner({
          "owner_user_id": detail.owner_user_id,
          "sec_user_id": detail.sec_user_id,
          "nickname": detail.nickname,
          "post_share_url": _owner_share_link(owner_share_url),
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
_post_pool = None
_post_pool_lock = Lock()


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


def get_post_pool(max_workers: int = None):
  """Return the pool that runs individual posts inside a batch download.

  Separate from ``get_aweme_executor`` on purpose, and it has to stay separate.
  A job task occupies one of that pool's workers for as long as its whole
  download runs; if its posts were submitted back to the same pool and it then
  waited for them, enough concurrent jobs would hold every worker and nothing
  could be scheduled to release them.

  A singleton, so the worker count is fixed the first time it is built - which
  is why changing ``owner.download_concurrency`` needs a restart.  An unusable
  count falls back to one worker, matching the serial default.
  """
  global _post_pool
  if _post_pool is None:
    with _post_pool_lock:
      if _post_pool is None:
        workers = max_workers
        if not isinstance(workers, int) or isinstance(workers, bool) \
           or workers < 1:
          workers = 1
        _post_pool = ThreadPoolExecutor(
          max_workers=workers,
          thread_name_prefix="aweme-post",
        )
  return _post_pool


def shutdown_aweme_downloads(wait: bool = False) -> None:
  """Stop accepting new posts.  Files in flight finish or are discarded."""
  global _executor
  global _post_pool
  with _executor_lock:
    existing = _executor
    _executor = None
  with _post_pool_lock:
    existing_post_pool = _post_pool
    _post_pool = None
  if existing is not None:
    existing.shutdown(wait=wait, cancel_futures=True)
  if existing_post_pool is not None:
    existing_post_pool.shutdown(wait=wait, cancel_futures=True)


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
