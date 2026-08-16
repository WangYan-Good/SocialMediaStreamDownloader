##<<Base>>
from copy import deepcopy
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from uuid import uuid4

##<<Third-part>>
from backend.src.platform.douyin.douyin_resource_resolver import (
  DouyinResourceResolver,
)
from backend.src.platform.resource_resolution import (
  BatchTooLarge,
  InputMissing,
  MultipleUrls,
  NoUrlFound,
  ResourceResolution,
  ResourceResolveError,
  UnsupportedPlatform,
  extract_urls,
)


##
## How long a resolution stays readable.  Long enough for a user to read what
## they pasted and decide what to do with it, short enough that a server left
## running does not keep a record of every link anyone ever pasted.
##
DEFAULT_RETENTION_SECONDS = 600.0
MAX_BATCH_RESOURCES = 20


class ResolveStore:
  """The server's own memory of what it just resolved, held in memory.

  Deliberately not persisted and deliberately not consume-once.

  Not persisted, matching TaskStore and JobStore: a resolution describes a
  decision this process made moments ago, and a row surviving a restart would
  only ever describe an answer nobody is waiting for.

  Not consume-once because reading is not acting.  A browser may retry a request
  it never saw the answer to, and one resolved link may legitimately be acted on
  twice - downloading a post again, starting a second recording.  Whether
  repeating an action is allowed belongs to whatever creates the task; the store
  has no business deciding it by forgetting.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    retention_seconds: float = DEFAULT_RETENTION_SECONDS,
    clock=monotonic,
  ) -> None:
    ##
    ## The monotonic clock, not the wall clock: nothing here is shown to a user
    ## as a time, and expiry must not be moved by the system clock stepping.
    ##
    self._retention_seconds = retention_seconds
    self._clock = clock
    self._guard = Lock()
    self._entries = dict()

  def _evict_expired(self) -> None:
    ##
    ## Caller must hold the guard.
    ##
    deadline = self._clock() - self._retention_seconds
    expired = [
      resolve_id
      for resolve_id, entry in self._entries.items()
      if entry["stored_at"] <= deadline
    ]
    for resolve_id in expired:
      del self._entries[resolve_id]

##
## >>============================= sub class method =============================>>
##
  @property
  def retention_seconds(self) -> float:
    return self._retention_seconds

  def put(self, resolution: ResourceResolution) -> str:
    """Store one resolution and return the opaque id that reads it back.

    The id is random rather than derived from the resource.  A derivable id -
    the aweme id, a hash of the url - would let a caller present one for a
    resource this server never resolved, which is exactly the guarantee the id
    exists to provide.
    """
    resolve_id = uuid4().hex
    with self._guard:
      self._evict_expired()
      self._entries[resolve_id] = {
        ##
        ## Copied on the way in, so a caller that keeps and later edits the
        ## resolution it handed over cannot reach into the record.
        ##
        "resolution": deepcopy(resolution),
        "stored_at": self._clock(),
      }
    return resolve_id

  def get(self, resolve_id: str):
    """Return a detached copy of one resolution, or ``None``.

    Tolerates an unknown id because a browser may hold one the store has since
    dropped; that is an expired receipt, not a defect.
    """
    with self._guard:
      self._evict_expired()
      entry = self._entries.get(resolve_id)
      if entry is None:
        return None
      ##
      ## Copied on the way out too.  ``identity`` is a dict, so two readers
      ## handed the same object could edit each other's answer.
      ##
      return deepcopy(entry["resolution"])

  def tracked(self) -> int:
    """How many resolutions are currently held.  For tests and diagnostics."""
    with self._guard:
      self._evict_expired()
      return len(self._entries)


@dataclass(frozen=True)
class ResolveRecord:
  """What one call to ``resolve`` produced: the receipt and what it names."""

  resolve_id: str
  resolution: ResourceResolution


@dataclass(frozen=True)
class BatchResolvedItem:
  index: int
  status: str
  record: ResolveRecord


@dataclass(frozen=True)
class BatchFailedItem:
  index: int
  status: str
  error_kind: str
  error_message: str


@dataclass(frozen=True)
class BatchResolveRecord:
  total: int
  resolved_count: int
  failed_count: int
  items: tuple


class ResourceResolveService:
  """Answers "what is this thing the user pasted?" and remembers the answer.

  Two steps, deliberately separated.  Reading the input down to exactly one url
  is platform-neutral and happens here; deciding what that url points at belongs
  to whichever platform claims its host.  Adding a second platform is therefore
  a new resolver in the list, not a change to this class.

  Nothing here executes anything.  No task is created, no media is fetched, no
  profile is read and no live status is checked - each of those needs a decision
  the user has not made yet, and two of them need a credential that a question
  about a url should never depend on.
  """

##
## >>============================= private method =============================>>
##
  def __init__(
    self,
    resolvers=None,
    store: ResolveStore = None,
    retention_seconds: float = DEFAULT_RETENTION_SECONDS,
  ) -> None:
    self._resolvers = tuple(
      resolvers if resolvers is not None else (DouyinResourceResolver(),)
    )
    self._store = (
      store if store is not None else ResolveStore(retention_seconds)
    )

  def _single_url(self, text) -> str:
    if not isinstance(text, str) or not text.strip():
      raise InputMissing("请粘贴一个链接")

    urls = extract_urls(text)
    if not urls:
      raise NoUrlFound("没有找到可解析的链接，请粘贴分享链接")
    if len(urls) > 1:
      ##
      ## Not "take the first".  Doing that would make the server's verdict
      ## disagree with what the user believes they submitted, and the mistake
      ## would only surface once something started against the wrong resource.
      ##
      raise MultipleUrls("一次只能解析一个链接")
    return urls[0]

  def _resolver_for(self, url: str):
    for resolver in self._resolvers:
      if resolver.claims(url):
        return resolver
    ##
    ## Refused before any request.  A host nobody claims must not become a
    ## request this server makes on a browser's behalf.
    ##
    raise UnsupportedPlatform("暂不支持该平台的链接")

##
## >>============================= sub class method =============================>>
##
  @property
  def retention_seconds(self) -> float:
    return self._store.retention_seconds

  def resolve(self, input_text) -> ResolveRecord:
    """Resolve one pasted input into one stored resolution.

    Raises a ``ResourceResolveError`` for every expected refusal, each carrying
    the status the api answers with.
    """
    url = self._single_url(input_text)
    resolution = self._resolver_for(url).resolve(url)
    return ResolveRecord(
      resolve_id=self._store.put(resolution), resolution=resolution
    )

  def resolve_many(self, input_text) -> BatchResolveRecord:
    """Resolve each distinct URL independently, in first-seen order."""
    if not isinstance(input_text, str) or not input_text.strip():
      raise InputMissing("请粘贴至少一个链接")

    urls = extract_urls(input_text)
    if not urls:
      raise NoUrlFound("没有找到可解析的链接，请粘贴分享链接")
    if len(urls) > MAX_BATCH_RESOURCES:
      raise BatchTooLarge(
        "一次最多解析 {} 个不同链接".format(MAX_BATCH_RESOURCES)
      )

    items = []
    resolved_count = 0
    for index, url in enumerate(urls):
      try:
        resolution = self._resolver_for(url).resolve(url)
      except ResourceResolveError as e:
        items.append(
          BatchFailedItem(
            index=index,
            status="failed",
            error_kind=e.kind,
            error_message=str(e),
          )
        )
        continue

      record = ResolveRecord(
        resolve_id=self._store.put(resolution), resolution=resolution
      )
      resolved_count += 1
      items.append(BatchResolvedItem(index=index, status="resolved", record=record))

    return BatchResolveRecord(
      total=len(urls),
      resolved_count=resolved_count,
      failed_count=len(urls) - resolved_count,
      items=tuple(items),
    )

  def get(self, resolve_id: str):
    """Read back a resolution this server produced, or ``None``.

    This is the method that makes the receipt worth anything: whatever acts on a
    resolution reads it from here rather than believing a browser's account of
    what was resolved.
    """
    return self._store.get(resolve_id)
