##<<Base>>
import hashlib
import os
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

  def as_dict(self) -> dict:
    return {
      "asset_id": self.asset_id,
      "kind": self.kind,
      "name": self.name,
      "size_bytes": self.size_bytes,
      "media_type": self.media_type,
      "image_index": self.image_index,
    }


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


class _ScanTooLarge(Exception):
  """A directory with more entries than this program will look at."""


__all__ = [
  "MAX_POST_ASSET_SCAN_ENTRIES",
  "AssetDiscovery",
  "MediaAsset",
  "MediaAssetResolver",
  "StorageState",
  "asset_id_for",
  "contained_path",
  "image_position",
  "media_type_for",
  "recognise_post_file",
]
