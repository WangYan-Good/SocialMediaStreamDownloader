##<<Base>>
import hashlib
import os
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

##<<Third-part>>
from backend.src.platform.douyin.douyin_aweme_naming import (
  image_position,
  post_media_kind,
)


##
## >>============================= the filesystem trust boundary =============================>>
##
##
## What the database knows is where a downloader once wrote something.  What is
## on disk now is a different fact, and only the disk can answer it.
##
## This module is where the two meet, and it is deliberately web-neutral: no
## Flask, no cookies, no session, no SQL, no HTTP.  It is handed a recorded path
## and a configured root and answers what is actually there.  Authorization
## happens strictly before anything here is called - see the route layer - so
## that a request for somebody else's resource never reaches the filesystem at
## all.
##
## Phase 10B will serve bytes through this same boundary.  It is drawn carefully
## now so that it does not have to be drawn again under pressure later.
##


class StorageState(str, Enum):
  """What can be said about a resource's files right now."""

  ##
  ## The path is safe, exists, and holds at least one recognisable asset.
  ##
  AVAILABLE = "available"
  ##
  ## The recorded target simply is not there any more. The database row is
  ## still perfectly valid - this is the honest answer to "did the file
  ## survive", not a claim that the resource does not exist.
  ##
  MISSING = "missing"
  ##
  ## The directory is there and holds nothing this program recognises as this
  ## post's media. Different from missing: somebody may have emptied it.
  ##
  EMPTY = "empty"
  ##
  ## The server cannot safely say. A path that escapes the configured root, a
  ## symlink leading out of it, a permission error, a directory too large to
  ## inspect within bounds.
  ##
  ## Deliberately one state for all of them: the reason is a fact about this
  ## server's filesystem, and a browser has no use for it.
  ##
  UNAVAILABLE = "unavailable"


##
## A hard bound on how much of one directory will be looked at.
##
## Far above any real post - an image set runs to a few dozen files - and
## finite, so a directory that somebody has filled with a million entries
## cannot hold a request open while it is counted.
##
MAX_POST_ASSET_SCAN_ENTRIES = 1000


def contained_path(root, candidate):
  """Resolve ``candidate`` and return it only if it is genuinely inside ``root``.

  Returns ``None`` rather than raising: refusing is an ordinary outcome here,
  and the caller turns it into ``unavailable`` without needing to know which
  way the path escaped.

  Both sides are fully resolved first, which is what makes symlinks safe - a
  link out of the root, or a link *in the middle* of the path whose final
  component looks innocent, both land outside once resolved.

  Containment is a path-segment relationship, never a string prefix::

      root      = /var/downloads
      candidate = /var/downloads-evil/a.mp4

  ``startswith`` says yes to that. It is a different directory.
  """
  if candidate is None:
    return None
  text = str(candidate).strip()
  if not text:
    return None

  try:
    ##
    ## realpath rather than resolve(strict=True): a recorded path that no
    ## longer exists still has to be classified, and "missing" is a different
    ## answer from "unsafe".
    ##
    safe_root = Path(os.path.realpath(str(root)))
    ##
    ## A relative recorded path is relative to the configured root - which is
    ## how it was written, back when save_path itself was relative.
    ##
    raw = Path(text)
    joined = raw if raw.is_absolute() else safe_root / raw
    resolved = Path(os.path.realpath(str(joined)))
  except (OSError, ValueError):
    return None

  if resolved != safe_root and safe_root not in resolved.parents:
    return None
  return resolved


##
## >>========================= the secure open boundary =========================>>
##
##
## Phase 10A only ever answered questions: it resolved a path, stat'd it, and
## described what it found.  A wrong answer there is a wrong answer, and the
## next request asks again.
##
## Serving bytes is different.  Discovery and delivery are two moments, and
## everything between them is somebody else's opportunity:
##
##     discover  ->  [ the file is deleted and replaced with a symlink ]  ->  open
##
## A path is just a sentence about the filesystem, re-evaluated every time it is
## used.  ``open(discovered_path)`` re-walks every component, so all the checking
## Phase 10A did is discarded at exactly the instant it matters.  This is why
## ``send_file(path)`` is forbidden for media: it re-opens by name.
##
## What follows walks down from the root one directory at a time, holding a
## descriptor at each level and opening the next relative to it.  A descriptor
## names the directory that was actually opened - not a name that can be
## repointed afterwards - so an attacker who swaps a component mid-walk finds
## the walk already past it, or is refused by O_NOFOLLOW at that level.
##

##
## Whether this host can make the guarantee above.
##
## Probed rather than assumed.  If any piece is missing the honest answer is
## that binary delivery is unavailable here - never a plain ``open()`` that
## looks like it works.  Metadata discovery does not depend on this and keeps
## working either way.
##
##
## How recently a file must have been modified before its validator stops being
## trustworthy.
##
## One second, chosen to cover the coarsest timestamp resolution a supported
## filesystem is likely to have rather than the ~1ms this host happens to give.
## Probing the real granularity per request would be both expensive and racy;
## being generous costs an occasional re-sent file and never costs correctness.
##
WEAK_VALIDATOR_WINDOW_NS = 1_000_000_000


SECURE_OPEN_SUPPORTED = (
  hasattr(os, "O_NOFOLLOW")
  and hasattr(os, "O_DIRECTORY")
  and os.open in os.supports_dir_fd
)

_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
##
## Non-blocking, so that a fifo left where a video should be cannot hold a
## worker forever waiting for a writer.  For a regular file it has no effect.
##
_O_NONBLOCK = getattr(os, "O_NONBLOCK", 0)


def _open_within_root(root, target):
  """Open ``target`` by walking down from ``root``, one descriptor at a time.

  Returns an open binary file object, or ``None``.  ``None`` for every refusal
  - a component that is a symlink, a target that is not a regular file, a file
  that vanished - because the caller turns all of them into the same answer and
  telling them apart would leak the shape of the filesystem.

  ``target`` must already be inside ``root``; ``contained_path`` decides that.
  This function does not re-decide it, it *enforces* it: even a target that
  passed containment is only reachable here through components that were each
  opened without following a link.
  """
  if not SECURE_OPEN_SUPPORTED:
    return None

  try:
    relative = target.relative_to(root)
  except ValueError:
    return None

  parts = relative.parts
  if not parts:
    return None

  directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | _O_CLOEXEC
  file_flags = os.O_RDONLY | os.O_NOFOLLOW | _O_CLOEXEC | _O_NONBLOCK

  ##
  ## The root itself is opened by name - it is the configured trust anchor, and
  ## there is nothing above it to walk down from.  O_NOFOLLOW is deliberately
  ## not set here: an administrator is entitled to point save_path at a symlink.
  ##
  try:
    current = os.open(str(root), os.O_RDONLY | os.O_DIRECTORY | _O_CLOEXEC)
  except OSError:
    return None

  fd = None
  try:
    ##
    ## Every directory between the root and the file. O_NOFOLLOW at each level
    ## is the point: checking only the final component would leave every parent
    ## free to be swapped for a link to somewhere else entirely.
    ##
    for name in parts[:-1]:
      try:
        nxt = os.open(name, directory_flags, dir_fd=current)
      except OSError:
        return None
      ##
      ## Closed as soon as the next level is held, so a deep path costs two
      ## descriptors rather than one per level.
      ##
      os.close(current)
      current = nxt

    try:
      fd = os.open(parts[-1], file_flags, dir_fd=current)
    except OSError:
      ##
      ## ENOENT (deleted since discovery), ELOOP (now a symlink), EACCES,
      ## ENOTDIR - one answer for all of them.
      ##
      return None

    ##
    ## The descriptor is open; this asks what it actually is, which no earlier
    ## check can answer because no earlier check held this descriptor. A
    ## directory, fifo, socket or device must not be streamed.
    ##
    try:
      info = os.fstat(fd)
    except OSError:
      return None
    if not stat.S_ISREG(info.st_mode):
      return None

    ##
    ## Handed to a file object, which takes ownership of the descriptor.
    ##
    stream = os.fdopen(fd, "rb")
    fd = None
    ##
    ## The stat is returned rather than re-taken later: it describes the
    ## descriptor at the moment it was proven, which is the only moment whose
    ## answer is trustworthy.
    ##
    return stream, info
  finally:
    ##
    ## Whatever happened, no directory descriptor outlives this call, and a
    ## file descriptor that never reached a file object is not leaked either.
    ##
    try:
      os.close(current)
    except OSError:
      pass
    if fd is not None:
      try:
        os.close(fd)
      except OSError:
        pass


def recognise_post_file(file_name: str, aweme_id: str):
  """Which media kind this file is for this post, or None.

  The downloader's own rule, reached through the shared naming module so the
  two cannot disagree about what belongs to a post.
  """
  return post_media_kind(file_name, aweme_id)


def asset_id_for(resource_kind: str, identity, file_name: str) -> str:
  """A stable name for one file that says nothing about where it lives.

  Derived rather than stored: a file that appears on disk is immediately
  addressable, a file that is deleted immediately stops being, and there is no
  second copy of the truth in a table to drift from the first.

  **Not an authorization token.** Knowing an asset id must never be enough to
  read a file. Phase 10B has to authenticate the request, authorize the parent
  resource, discover its assets again, and only then match this id against what
  discovery found. An id that could be redeemed on its own would be a bearer
  token that never expires and was handed out in a list.

  A cryptographic digest rather than ``hash()``: the built-in is randomised per
  process, so an id issued by one worker would be meaningless to another.
  """
  ##
  ## NUL separated, so that ("a", "bc") and ("ab", "c") cannot produce the same
  ## digest - neither part can contain a NUL.
  ##
  parts = [resource_kind, *(str(one) for one in identity), file_name]
  material = "\0".join(parts).encode("utf-8")
  return hashlib.sha256(material).hexdigest()


##
## What a file's extension means, as far as this program is willing to say.
##
## Read from the name on disk rather than inferred from a protocol column: the
## recording may have been written by a path this code no longer takes, and the
## file that is actually there is the current fact.
##
_MEDIA_TYPES = {
  ".mp4": "video/mp4",
  ".flv": "video/x-flv",
  ".ts": "video/mp2t",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".mp3": "audio/mpeg",
}

_FALLBACK_MEDIA_TYPE = "application/octet-stream"


##
## >>========================== what may be shown inline ==========================>>
##
##
## The complete set of media types this server will send for a browser to
## render in place, and the element that would render each.
##
## A closed list rather than a rule.  Every plausible rule admits something it
## should not: "images are safe" admits ``image/svg+xml``, which is a document
## that can carry script; "video is safe" admits containers no browser can
## decode without a JavaScript demuxer this project does not ship.  The set
## worth the risk is small enough to write down, so it is written down, and
## anything absent is refused without further reasoning.
##
## Inline delivery is the thing being decided here.  A file sent as an
## attachment is inert - the browser saves it. A file sent inline is one the
## browser interprets, and interpretation is where a stored file becomes
## behaviour.
##
PREVIEWABLE_MEDIA_TYPES = {
  "image/jpeg": "image",
  "video/mp4": "video",
  "audio/mpeg": "audio",
}


def preview_kind_for(media_type):
  """Which element would render this type inline, or ``None``.

  Exact match only.  A type carrying parameters, an unknown type, and anything
  that is not a string all answer ``None`` - the question is whether this
  server has decided to render the value, and it has only decided about the
  three spellings above.

  This is the single authority.  The route that serves bytes inline and the
  metadata that tells a browser a preview exists both ask here, so the two
  cannot drift into disagreeing about what is previewable.
  """
  if not isinstance(media_type, str):
    return None
  return PREVIEWABLE_MEDIA_TYPES.get(media_type)


def media_type_for(file_name: str) -> str:
  suffix = Path(file_name).suffix.lower()
  return _MEDIA_TYPES.get(suffix, _FALLBACK_MEDIA_TYPE)


@dataclass(frozen=True)
class MediaAsset:
  """One file that is on disk right now.

  Carries a name and a size and no location. The directory it sits in is this
  server's business, and a browser that learned it would learn the shape of the
  filesystem behind the application.
  """

  asset_id: str
  kind: str
  name: str
  size_bytes: int
  media_type: str
  image_index: int = None

  @property
  def preview_kind(self):
    """Which element could render this asset inline, or ``None``.

    Derived rather than stored, and derived from the *media type* rather than
    from ``kind``: a recording is a ``recording`` whether it was written as mp4
    or flv, and only one of those is something a browser can show.
    """
    return preview_kind_for(self.media_type)

  def as_dict(self) -> dict:
    return {
      "asset_id": self.asset_id,
      "kind": self.kind,
      "name": self.name,
      "size_bytes": self.size_bytes,
      "media_type": self.media_type,
      "image_index": self.image_index,
      ##
      ## Capability metadata, not a location. It says whether a preview is on
      ## offer; it does not say where the file is or hand out a url.
      ##
      "preview_kind": self.preview_kind,
    }


@dataclass(frozen=True)
class OpenedFileVersion:
  """Which bytes this opening of a file is looking at.

  A resumed download has to answer a question the asset id cannot: not "which
  file" but "is this still the same content I started".  An asset id is derived
  from the parent identity and the file name, so replacing a file with entirely
  different content leaves it identical - and resuming against that would append
  the tail of a new file to the head of an old one and produce a corrupt result
  that nothing reported.

  Every field comes from ``fstat`` on the descriptor that was actually opened,
  never from a path stat that might by then describe a different file.

  ``st_ctime_ns`` is included alongside ``st_mtime_ns`` because mtime can be set
  backwards deliberately; ctime moves whenever the inode does, so the two
  together are much harder to make collide by accident.

  Nothing here may ever be serialized.  An inode and a device number describe
  this host's filesystem, and the only thing that leaves this object is the
  opaque digest below.
  """

  st_dev: int
  st_ino: int
  st_size: int
  st_mtime_ns: int
  st_ctime_ns: int

  def is_strong_at(self, now_ns: int) -> bool:
    """Whether this validator can be trusted to have noticed a change.

    A filesystem records modification times at some finite resolution - a
    millisecond or two on the xfs this runs on, a full second on others.  Two
    writes inside one tick are indistinguishable afterwards, so a file rewritten
    immediately after being read can carry the identical tuple and therefore the
    identical tag.

    That matters in exactly one place: ``If-Range``.  Honouring a resume on a
    tag that could not have noticed the change would append the tail of new
    content to the head of old content and call it a download - the corruption
    this validator exists to prevent, arriving through the mechanism meant to
    prevent it.

    So a representation modified within the margin below is reported as not
    strong, and the caller falls back to sending the whole thing.  This is the
    same reasoning RFC 9110 §8.8.2.2 gives for last-modified times, and the
    conservative direction: the cost is re-sending a file, and the alternative
    is silent corruption.

    Files written more than a moment ago - which is nearly all of them - are
    unaffected.  A recording still being written is not, and should not be.
    """
    return (now_ns - self.st_mtime_ns) >= WEAK_VALIDATOR_WINDOW_NS

  @property
  def entity_tag(self) -> str:
    """An opaque, deterministic name for this exact representation.

    A digest of the metadata rather than of the content: hashing a recording
    would mean reading tens of gigabytes to answer a question ``fstat`` has
    already answered, once per request.

    Deterministic rather than ``hash()``, which is randomised per process - a
    validator issued by one worker has to mean the same thing to the next, or a
    resume would fail whenever it landed on a different one.

    The digest hides its inputs.  An inode or a device number sent verbatim in
    a header would describe the host's filesystem to whoever received it.
    """
    material = "\0".join(
      str(one)
      for one in (
        self.st_dev,
        self.st_ino,
        self.st_size,
        self.st_mtime_ns,
        self.st_ctime_ns,
      )
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()

  @classmethod
  def of(cls, info) -> "OpenedFileVersion":
    return cls(
      st_dev=info.st_dev,
      st_ino=info.st_ino,
      st_size=info.st_size,
      st_mtime_ns=info.st_mtime_ns,
      st_ctime_ns=info.st_ctime_ns,
    )


@dataclass(frozen=True)
class OpenedMediaAsset:
  """One media file, already open, ready to be streamed.

  Deliberately has no ``as_dict``.  This is the one object in the module that
  knows a location, and it exists only between the resolver and the response -
  it must never acquire a way to describe itself to a browser.

  What it carries is the descriptor, not the name: everything downstream reads
  from an open file that was proven to be the right one, so no later step can
  re-resolve a path and get a different answer.
  """

  ##
  ## The public, path-free description - the same shape discovery reports.
  ##
  asset: MediaAsset
  ##
  ## The already-open binary file object.
  ##
  stream: object
  ##
  ## From ``fstat`` on the open descriptor, not from discovery. The file may
  ## have grown between the two, and the descriptor is the current truth.
  ##
  size_bytes: int
  ##
  ## Which bytes these are, so a resumed request can be told whether it is
  ## still talking about the same ones.
  ##
  version: OpenedFileVersion

  def close(self) -> None:
    """Release the descriptor. Safe to call more than once."""
    try:
      self.stream.close()
    except Exception:
      ##
      ## A close that fails has still released what it could, and the request
      ## it belonged to is already over.
      ##
      pass


@dataclass(frozen=True)
class AssetDiscovery:
  """What could be said about one resource's files."""

  storage_state: StorageState
  assets: tuple

  @classmethod
  def nothing(cls, state: StorageState) -> "AssetDiscovery":
    return cls(storage_state=state, assets=tuple())


##
## The order assets are reported in.
##
## Fixed, so that two requests for the same directory answer identically -
## filesystem iteration order is not a promise anybody makes.
##
_KIND_ORDER = {"video": 0, "image": 1, "music": 2, "cover": 3}


class MediaAssetResolver:
  """Reads what is on disk for one already-authorized resource.

  Web-neutral on purpose: no Flask, no session, no SQL. It is handed a recorded
  path and answers what is there. Whether the caller is allowed to ask has been
  decided before this is reached - see the route layer, and the test that
  asserts this class is never even constructed for a request that fails
  authorization.
  """

  def __init__(self, root_provider):
    ##
    ## A callable rather than a value: configuration is the authority on where
    ## downloads live, and it is read when the question is asked rather than
    ## frozen at import.
    ##
    self._root_provider = root_provider

  def _root(self):
    try:
      configured = self._root_provider()
    except Exception:
      return None
    if not configured or not str(configured).strip():
      return None
    return str(configured)

  ##
  ## >>--------------------------- posts ---------------------------<<
  ##
  def post_assets(self, save_dir, platform: str, aweme_id: str) -> AssetDiscovery:
    root = self._root()
    if root is None:
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    directory = contained_path(root, save_dir)
    if directory is None:
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    if not directory.exists():
      ##
      ## The row is still valid; the files are not there any more. That is a
      ## different fact from "no such resource", and the route keeps it so.
      ##
      return AssetDiscovery.nothing(StorageState.MISSING)
    if not directory.is_dir():
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    try:
      found = self._scan_post_directory(directory, platform, aweme_id)
    except _ScanTooLarge:
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)
    except OSError:
      ##
      ## A permission error, a device that went away mid-listing. The server
      ## cannot say what is there, which is not the same as saying nothing is.
      ##
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    if not found:
      return AssetDiscovery.nothing(StorageState.EMPTY)
    return AssetDiscovery(storage_state=StorageState.AVAILABLE, assets=tuple(found))

  def _scan_post_directory(self, directory: Path, platform: str, aweme_id: str) -> list:
    assets = []
    seen = 0

    ##
    ## Immediate children only - no rglob, no walk. One post's media is written
    ## into one directory, so descending would widen the read surface for
    ## nothing and make a deep tree expensive to answer about.
    ##
    with os.scandir(directory) as entries:
      for entry in entries:
        seen += 1
        if seen > MAX_POST_ASSET_SCAN_ENTRIES:
          raise _ScanTooLarge()

        try:
          ##
          ## follow_symlinks=False on both: a link is a second name for a file
          ## somewhere else, and following one would let a post claim media it
          ## does not own - or, if it leads out of the root, report a file the
          ## boundary exists to keep out.
          ##
          if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
            continue
          kind = recognise_post_file(entry.name, aweme_id)
          if kind is None:
            continue
          size = entry.stat(follow_symlinks=False).st_size
        except OSError:
          ##
          ## The entry went away between being listed and being asked about.
          ## One file disappearing is not a reason to fail the whole request.
          ##
          continue

        assets.append(
          MediaAsset(
            asset_id=asset_id_for("post", (platform, aweme_id), entry.name),
            kind=kind,
            name=entry.name,
            size_bytes=size,
            media_type=media_type_for(entry.name),
            image_index=image_position(entry.name),
          )
        )

    assets.sort(
      key=lambda one: (
        _KIND_ORDER.get(one.kind, 99),
        one.image_index if one.image_index is not None else 0,
        one.name,
      )
    )
    return assets

  ##
  ## >>--------------------------- recordings ---------------------------<<
  ##
  def recording_asset(self, output_path, recording_id) -> AssetDiscovery:
    """The single file this recording wrote, if it is still there.

    Never a directory listing. ``recording_record`` holds the exact path it
    wrote, and the files beside it belong to other recordings - possibly other
    users' recordings.
    """
    root = self._root()
    if root is None:
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    ##
    ## Checked before resolution: a symlink here would resolve to its target
    ## and could pass containment while still being a second name for a file
    ## this recording never wrote.
    ##
    try:
      if output_path is not None and str(output_path).strip():
        if Path(str(output_path).strip()).is_symlink():
          return AssetDiscovery.nothing(StorageState.UNAVAILABLE)
    except OSError:
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    target = contained_path(root, output_path)
    if target is None:
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    try:
      if not target.exists():
        return AssetDiscovery.nothing(StorageState.MISSING)
      if not target.is_file():
        return AssetDiscovery.nothing(StorageState.UNAVAILABLE)
      size = target.stat().st_size
    except OSError:
      return AssetDiscovery.nothing(StorageState.UNAVAILABLE)

    asset = MediaAsset(
      asset_id=asset_id_for("recording", (recording_id,), target.name),
      kind="recording",
      name=target.name,
      size_bytes=size,
      media_type=media_type_for(target.name),
    )
    return AssetDiscovery(storage_state=StorageState.AVAILABLE, assets=(asset,))


  ##
  ## >>--------------------------- opening ---------------------------<<
  ##
  ##
  ## Both methods below rediscover before they open, and neither takes a path
  ## from a caller.  An asset id is matched against what is on disk *now* -
  ## never against a remembered listing, and never turned back into a file name
  ## by inverting the digest, which is not possible and must not be simulated by
  ## keeping a table.
  ##
  ## Returning ``None`` for every refusal is deliberate.  "No such id", "deleted
  ## since you listed it", "now a symlink" and "outside the root" are one answer
  ## to a browser; the difference between them describes this host's filesystem.
  ##

  def _open_matching(self, discovery, asset_id, root, directory):
    """Find ``asset_id`` in a fresh discovery and open that exact file."""
    if discovery.storage_state is not StorageState.AVAILABLE:
      return None

    ##
    ## The name comes from the asset discovery just found - never from the
    ## request. The caller supplies an id and nothing else, so there is no
    ## component of the final path that a browser chose.
    ##
    current = next(
      (one for one in discovery.assets if one.asset_id == asset_id), None
    )
    if current is None:
      return None

    target = contained_path(root, directory / current.name)
    if target is None:
      return None

    opened = _open_within_root(Path(os.path.realpath(str(root))), target)
    if opened is None:
      return None

    stream, info = opened
    ##
    ## The size is re-read from the open descriptor rather than reused from
    ## discovery: the file may have grown between the two, and Content-Length
    ## has to describe what is about to be sent.
    ##
    return OpenedMediaAsset(
      asset=current,
      stream=stream,
      size_bytes=info.st_size,
      version=OpenedFileVersion.of(info),
    )

  def open_post_asset(self, save_dir, platform: str, aweme_id: str, asset_id: str):
    """Open one of this post's files, chosen by id, as it exists right now."""
    root = self._root()
    if root is None:
      return None

    directory = contained_path(root, save_dir)
    if directory is None:
      return None

    ##
    ## Rediscovered, not remembered. The list this id came from may be minutes
    ## old, and the only listing that can authorize an open is the current one.
    ##
    discovery = self.post_assets(save_dir, platform, aweme_id)
    return self._open_matching(discovery, asset_id, root, directory)

  def open_recording_asset(self, output_path, recording_id, asset_id: str):
    """Open the exact file this recording wrote, if it is still that file."""
    root = self._root()
    if root is None:
      return None

    target = contained_path(root, output_path)
    if target is None:
      return None

    discovery = self.recording_asset(output_path, recording_id)
    ##
    ## The parent directory of the recorded path - never a listing of it. A
    ## recording owns one file, and its neighbours belong to other recordings,
    ## possibly other users'.
    ##
    return self._open_matching(discovery, asset_id, root, target.parent)


class _ScanTooLarge(Exception):
  """A directory with more entries than this program will look at."""


__all__ = [
  "MAX_POST_ASSET_SCAN_ENTRIES",
  "SECURE_OPEN_SUPPORTED",
  "WEAK_VALIDATOR_WINDOW_NS",
  "AssetDiscovery",
  "MediaAsset",
  "MediaAssetResolver",
  "OpenedFileVersion",
  "OpenedMediaAsset",
  "StorageState",
  "PREVIEWABLE_MEDIA_TYPES",
  "asset_id_for",
  "contained_path",
  "image_position",
  "media_type_for",
  "preview_kind_for",
  "recognise_post_file",
]
