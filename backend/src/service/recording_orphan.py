##
## The crash window P2-03 leaves behind, and the only safe thing to say about it.
##
## A finished recording becomes durable on disk before the recovery note that
## would let a restart catalogue it becomes durable. Between those two moments
## there is a state nothing in this system could previously describe: real media
## on real storage, referenced by no database row and by no pending note. The
## reconciler cannot help - it replays notes, and is deliberately forbidden from
## scanning media - so those bytes stay invisible to the library forever.
##
## This module makes that state *visible*, and stops there.
##
## What it deliberately is not:
##
##   - an owner reconstructor. Nothing on disk carries an ``app_user_id``. The
##     directory name comes from a broadcaster's nickname, and several accounts
##     may record the same broadcaster; a filename is a stream name; a timestamp
##     is a time. Every one of those is a guess, and a wrong guess attaches one
##     person's recording to another person's account. There is no code path
##     here that reads, derives or writes an owner.
##   - a recovery path. It never inserts a recording row. A file whose owner
##     cannot be known cannot be catalogued, and cataloguing it without one
##     would publish somebody's private recording into a shared library.
##   - a cleaner. It never deletes media. The strongest action available is to
##     hard-link a file into a hidden directory and unlink the original, which
##     loses nothing and is reversible by hand.
##
## So the contract is: detect, inventory, and - only when an operator explicitly
## asks, for one named file at a time - quarantine.
##
from dataclasses import dataclass
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import List

from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.service.media_asset import contained_path
from backend.src.service.recording_recovery_journal import resolve_storage_root


##
## Where quarantined media goes: a hidden directory in the storage root, beside
## the recovery journal rather than inside the recording tree.
##
## Outside the scanned subtree on purpose. A quarantine folder *within* the
## recording root would be walked by the next scan, and a file that had already
## been set aside would be offered again as a fresh candidate - which is how a
## one-way action becomes a loop.
##
## Hidden for the same reason the journal is: it is not media and not for
## people, and a visible directory in a media root invites both a user and a
## media scanner to treat it as content.
##
QUARANTINE_DIRECTORY_NAME = ".smsd-recording-orphan-quarantine"

##
## The media a successful live recording of this project can actually produce.
##
## FLV is written directly by the streaming fetcher. HLS is captured as ``.ts``
## and republished as ``.mp4``; both spellings can be the durable result,
## because a remux that could not run leaves the ``.ts`` as the recording.
##
## Closed, and deliberately narrow. Anything else in this tree - a response
## snapshot, an operator's note, a file somebody copied in - is not something
## this program recorded, and is therefore not something it may move.
##
RECORDED_MEDIA_SUFFIXES = frozenset({".flv", ".mp4", ".ts"})

##
## How much filesystem work one scan may do.
##
## Every directory entry counts, including names that can never be a candidate.
## Bounded because a directory somebody has filled - deliberately or by a
## runaway loop - must not hold an operator command open indefinitely.
##
## Sized for a real library rather than for a journal directory. The recovery
## journal bounds itself at 4096 because it holds only notes awaiting replay,
## which is a small number by construction; this walks the media tree, where a
## deployment recording daily across many broadcasters accumulates far more
## files than that. A bound a genuine library exceeds would make this command
## refuse to run for exactly the deployments that need it.
##
## Overflow raises rather than reporting what it found, and the reason is
## ordering rather than correctness. Whether a candidate is claimed depends on
## the reference set, which is either complete or has already caused a refusal,
## so a short walk would still classify what it saw correctly. What it would
## break is the resumable cursor: the walk is depth-first, so stopping at an
## entry count stops at an arbitrary point in *path* order, and a candidate
## that sorts early but is visited late would be skipped past forever.
##
## Read from the module at each check rather than captured once, so a test or a
## runtime probe can prove the overflow mechanism at a small bound instead of
## by materialising the production one.
##
MAX_ORPHAN_SCAN_ENTRIES = 200000

##
## How deep below the recording root a scan will look.
##
## Real layout is ``<root>/douyin/<type>/<directory>/<file>`` - one directory
## level below the recording root. Three is slack for a deployment that nests a
## little differently; it is not an invitation to walk an arbitrary tree.
##
MAX_ORPHAN_SCAN_DEPTH = 3

##
## How many candidates one invocation will report.
##
## The remainder is not lost: the scan is ordered and resumable, so a caller
## continues from the last path it saw. See ``scan``.
##
MAX_ORPHAN_CANDIDATES = 200

##
## How many recording rows the reference set may hold.
##
## ``recording_record.output_path`` has no index, so membership is answered from
## one bounded read of the column rather than one query per candidate - which
## would be a full table scan per file. Overflowing this raises: a reference set
## that is missing rows would call a referenced recording an orphan, and that is
## the one mistake this module must never make.
##
MAX_REFERENCED_RECORDINGS = 50000

##
## Every byte written here is metadata about one moved file.
##
_RECORD_SUFFIX = ".json"
_RECORD_SCHEMA_VERSION = 1


class OrphanInventoryUnavailable(RuntimeError):
  """The question cannot be answered, so nothing may be called an orphan."""


class OrphanScanOverflow(OrphanInventoryUnavailable):
  """The recording tree exceeded the fixed scan-work bound."""


class OrphanQuarantineRefused(RuntimeError):
  """The move was refused; nothing on disk was changed."""


##
## The move started and did not finish.
##
## A subclass, so every caller that already refuses to treat a quarantine as
## successful keeps doing so - but it is a different situation from a refusal
## and says so. The media is linked into quarantine and the original name still
## exists, which means nothing is lost and the file is reachable under two
## names.
##
## Safe to retry, and retrying is the fix. The destination name is derived from
## the source path, so the next attempt computes the same name, finds the same
## inode already there and completes the unlink it could not do here.
##
class OrphanQuarantineIncomplete(OrphanQuarantineRefused):
  """The media is in quarantine but the original name could not be removed."""


##
## One file, and everything a later action must be able to re-prove about it.
##
## The path is root-relative and never absolute: this is what an operator reads
## and what a record file stores, and neither has any business carrying the
## deployment's filesystem layout.
##
## The rest is the identity of the *file*, not of the name. A name can be made
## to mean something else between the scan and the move; a device and an inode
## cannot. Size and modification time are carried too, so a file rewritten in
## place - same inode, different contents - is also refused.
##
## There is deliberately no owner field of any kind. See the module note.
##
@dataclass(frozen=True)
class OrphanCandidate:
  relative_path: str
  size: int
  device: int
  inode: int
  mtime_ns: int


##
## What one scan found. ``truncated`` says a bounded run stopped early and the
## remainder is still there, not that anything was skipped or lost.
##
@dataclass(frozen=True)
class OrphanScan:
  candidates: List[OrphanCandidate]
  truncated: bool
  scanned: int


##
## What one quarantine attempt did. ``quarantined`` is false for a dry run,
## which is the only way this returns without having moved anything.
##
@dataclass(frozen=True)
class QuarantineOutcome:
  relative_path: str
  destination_name: str
  quarantined: bool


##
## Where live recordings actually land.
##
## Narrower than the storage root, and that narrowing is a correctness
## requirement rather than an optimisation. Post downloads live under
## ``<root>/douyin/aweme`` and are catalogued in a different table entirely, so
## a scan rooted at the storage root would find every downloaded post
## unreferenced by ``recording_record`` and offer somebody's entire download
## history as orphaned media.
##
## Built from the same two settings the downloader builds it from, read through
## the same accessor, so the two cannot drift into disagreeing about where a
## recording goes.
##
##
## The storage root, answered in this module's own vocabulary.
##
## Delegated rather than reimplemented: the journal already resolves
## ``$.download.save_path``, and two resolutions of one setting would eventually
## disagree about which root a file was judged against. Only the exception type
## is translated, so a caller of this module handles one family of failures
## rather than two.
##
def resolve_recording_storage_root(settings) -> Path:
  try:
    return resolve_storage_root(settings)
  except Exception as e:
    raise OrphanInventoryUnavailable(
      "recording orphan inventory requires a configured storage root"
    ) from e


def resolve_recording_media_root(settings) -> Path:
  root = resolve_recording_storage_root(settings)
  download_type = get_dict_attr(settings, "$.platform.douyin.download.type")
  if not isinstance(download_type, str) or not download_type.strip():
    raise OrphanInventoryUnavailable(
      "recording orphan inventory requires a configured download type"
    )
  ##
  ## A configured value that is not a single plain path segment would let a
  ## setting point the scan somewhere else entirely.
  ##
  segment = download_type.strip()
  if segment in (".", "..") or "/" in segment or "\\" in segment:
    raise OrphanInventoryUnavailable(
      "configured download type is not a single path segment"
    )
  return root / "douyin" / segment


##
## The same host capabilities the journal and the media boundary require.
##
## Probed rather than assumed: without directory-relative opens there is no way
## to walk a tree while refusing a component that has been swapped for a link,
## and a path-based fallback that looks identical and is not would be worse than
## refusing outright.
##
_SUPPORTS_DIRECTORY_RELATIVE_OPEN = (
  hasattr(os, "O_DIRECTORY")
  and hasattr(os, "O_NOFOLLOW")
  and os.open in os.supports_dir_fd
  and os.unlink in os.supports_dir_fd
  and os.link in os.supports_dir_fd
)

_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_O_NONBLOCK = getattr(os, "O_NONBLOCK", 0)


def _require_host_support():
  if not _SUPPORTS_DIRECTORY_RELATIVE_OPEN:
    raise OrphanInventoryUnavailable(
      "this host cannot open recording media relative to a directory"
    )


##
## Open a directory without following a link at that name.
##
## Returns ``None`` when the name is absent, which is an ordinary answer: a
## deployment that has never recorded has no recording root, and a broadcaster
## directory can be removed between one scan and the next.
##
## Every other refusal - a link where a directory should be, a file where a
## directory should be, permissions - raises, because those describe a tree this
## code is no longer entitled to reason about.
##
def _open_directory(name, parent=None):
  flags = os.O_RDONLY | os.O_DIRECTORY | _O_CLOEXEC
  if parent is not None:
    ##
    ## O_NOFOLLOW only below the root. The root itself is the configured trust
    ## anchor and an operator is entitled to point it at a symlinked mount -
    ## exactly the allowance the media boundary already makes.
    ##
    flags |= os.O_NOFOLLOW
  try:
    if parent is None:
      return os.open(str(name), flags)
    return os.open(name, flags, dir_fd=parent)
  except FileNotFoundError:
    return None
  except NotADirectoryError:
    return None
  except OSError as e:
    if e.errno in (errno.ELOOP, errno.ENOTDIR):
      ##
      ## A symlink at this name. Not descended into, and not an error worth
      ## stopping the whole scan for - the rest of the tree is still real.
      ##
      return None
    raise OrphanInventoryUnavailable(
      "recording media directory is unusable ({})".format(type(e).__name__)
    ) from e


##
## Open one file for validation only, refusing anything that is not a plain
## regular file reached without following a link.
##
## The descriptor is what makes the answer trustworthy. A path is a sentence
## about the filesystem re-evaluated every time it is used; ``fstat`` on an open
## descriptor describes the object that was actually opened, which is the only
## thing a later move may be based on.
##
## Nothing is read. A recording is gigabytes and this needs none of them.
##
def _open_regular_file(name, parent):
  flags = os.O_RDONLY | os.O_NOFOLLOW | _O_CLOEXEC | _O_NONBLOCK
  try:
    descriptor = os.open(name, flags, dir_fd=parent)
  except OSError:
    ##
    ## ENOENT, ELOOP (it is a symlink), ENXIO (a FIFO with no writer), EACCES.
    ## One answer for all of them: this is not a file this code may act on.
    ##
    return None
  try:
    info = os.fstat(descriptor)
  except OSError:
    os.close(descriptor)
    return None
  if not stat.S_ISREG(info.st_mode):
    ##
    ## A FIFO that happened to have a writer, a device, a socket. O_NOFOLLOW
    ## and O_NONBLOCK got this far without blocking; the descriptor itself is
    ## what settles what it is.
    ##
    os.close(descriptor)
    return None
  return descriptor, info


##
## Whether a directory entry's *name* could ever be a finished recording.
##
## Applied before anything is opened, so an in-flight capture is never even
## looked at. Three rules, each closing a specific way a live file could be
## mistaken for a finished one:
##
##   - Hidden names are never candidates. Every temporary this project writes is
##     hidden: the remux temporary is ``.<stem>.remux-<token>.part.mp4``, the
##     journal's is ``.<key>.journal-<token>.part``. The journal and quarantine
##     directories are hidden too, so this one rule also keeps the scan out of
##     both without naming either.
##   - A ``.part`` component is never a candidate, hidden or not. Belt and
##     braces for a temporary spelled without a leading dot.
##   - The suffix must be one this project actually records.
##
def _is_candidate_name(name: str) -> bool:
  if not name or name.startswith("."):
    return False
  if ".part." in name or name.endswith(".part"):
    return False
  return Path(name).suffix.lower() in RECORDED_MEDIA_SUFFIXES


##
## Whether a directory entry's name may be descended into.
##
## The journal and quarantine directories are hidden, so the hidden rule covers
## both. It also keeps a scan out of anything else somebody hid there, which is
## the right default for a directory this code does not own.
##
def _is_scannable_directory_name(name: str) -> bool:
  return bool(name) and not name.startswith(".")


##
## The identity a later action must be able to re-prove.
##
## Device and inode say *which file*; size and modification time say *which
## contents*. Together they refuse both substitutions that matter: the name
## repointed at a different file, and the same file rewritten underneath.
##
def _fingerprint(info):
  return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _candidate_from(relative_path: str, info) -> OrphanCandidate:
  return OrphanCandidate(
    relative_path=relative_path,
    size=info.st_size,
    device=info.st_dev,
    inode=info.st_ino,
    mtime_ns=info.st_mtime_ns,
  )


##
## Where one candidate's quarantined copy would live.
##
## Derived from the candidate's own root-relative path rather than from a fresh
## random token, and that determinism is deliberate. A crash between linking the
## media into quarantine and unlinking the original leaves both names; the next
## attempt then computes the *same* destination, finds it already holds the same
## inode, and finishes the move rather than writing a second copy under a new
## name.
##
## The path is hashed rather than reproduced. A broadcaster directory name is
## somebody's nickname, and a quarantine directory listing should not be a list
## of who has been recorded. The original spelling is in the record file beside
## it, which is owner-only.
##
def _destination_name(relative_path: str) -> str:
  digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:32]
  suffix = Path(relative_path).suffix.lower()
  return digest + suffix


class RecordingOrphanInventory:
  """Find durable recording media that nothing claims, and set it aside."""

  def __init__(self, *, journal, references, config_loader):
    ##
    ## All three injected, none defaulted, for the same reason the reconciler
    ## takes its collaborators explicitly: a second journal instance would read
    ## a different directory than the one the application publishes into, and a
    ## second configuration snapshot would judge media against a different root
    ## than the one it was written under.
    ##
    self._journal = journal
    self._references = references
    self._config_loader = config_loader

  ##
  ## >>============================= authority =============================>>
  ##

  def _settings(self):
    return self._config_loader()

  def _roots(self):
    settings = self._settings()
    return (
      resolve_recording_storage_root(settings),
      resolve_recording_media_root(settings),
    )

  ##
  ## Every path the database currently claims, resolved.
  ##
  ## Resolved rather than compared as text, because one recording can be spelled
  ## several ways and every one of them protects the file: the recorder writes
  ## an absolute path built from the configured save path, older rows may hold a
  ## path relative to that root, and a deployment whose root is a symlinked
  ## mount produces both the link's spelling and the target's. Comparing strings
  ## would call a referenced recording an orphan the first time a deployment was
  ## re-pointed at the same storage by a different name.
  ##
  ## Any failure at all becomes ``OrphanInventoryUnavailable``. A reference set
  ## that could not be read is not an empty reference set - it is no answer, and
  ## the only safe thing to do with no answer is refuse to give one.
  ##
  def _referenced_paths(self, root):
    try:
      stored = self._references.referenced_output_paths()
    except Exception as e:
      raise OrphanInventoryUnavailable(
        "the recording repository could not be consulted ({})".format(
          type(e).__name__
        )
      ) from e

    referenced = set()
    for index, output_path in enumerate(stored):
      if index >= MAX_REFERENCED_RECORDINGS:
        ##
        ## More rows than this run will hold. Reporting the candidates found so
        ## far would mean answering "nothing references this" from a reference
        ## set known to be incomplete.
        ##
        raise OrphanInventoryUnavailable(
          "the recording repository holds more rows than one inventory bounds"
        )
      resolved = contained_path(root, output_path)
      if resolved is not None:
        referenced.add(resolved)
    return referenced

  ##
  ## Every path a pending recovery note describes, resolved.
  ##
  ## The other half of the reference set, and the half that exists precisely
  ## because of the crash this module is about: a note is published before the
  ## database row, so between those two moments the note is the *only* thing
  ## that knows the recording exists. Media a note names is on its way into the
  ## library and must never be touched.
  ##
  ## Coverage has to be complete or the answer is refused. A note that this
  ## build cannot read still describes *something*, and a file it might name
  ## cannot be ruled out. A corrupt note therefore blocks the inventory rather
  ## than being skipped - the reconciler already keeps corrupt notes on disk
  ## exactly so an operator can look at them.
  ##
  def _journalled_paths(self, root):
    try:
      keys = self._journal.pending_keys_snapshot()
    except Exception as e:
      raise OrphanInventoryUnavailable(
        "the recovery journal could not be enumerated ({})".format(
          type(e).__name__
        )
      ) from e

    journalled = set()
    for key in keys:
      try:
        intent = self._journal.load(key)
      except Exception as e:
        raise OrphanInventoryUnavailable(
          "a pending recovery note could not be read ({}); no file can be "
          "ruled out while one note is unreadable".format(type(e).__name__)
        ) from e
      if intent is None:
        ##
        ## Retired between the listing and the load. Its recording is already
        ## catalogued, so the database side of the reference set covers it.
        ##
        continue
      resolved = contained_path(root, intent.output_path)
      if resolved is not None:
        journalled.add(resolved)
    return journalled

  ##
  ## Both authorities, gathered before the walk.
  ##
  ## Order matters a little: asking the database and the journal first means a
  ## run that cannot answer refuses before it has walked a single directory,
  ## rather than after.
  ##
  def _claimed_paths(self, root):
    claimed = self._referenced_paths(root)
    claimed.update(self._journalled_paths(root))
    return claimed

  ##
  ## >>=============================== the scan ===============================>>
  ##

  ##
  ## Walk the recording tree once, in a fixed order, and report what nothing
  ## claims.
  ##
  ## Ordered by root-relative path rather than by filesystem enumeration order,
  ## which is neither stable across hosts nor across a rewrite of the same
  ## directory. Two scans of an unchanged tree therefore agree, which is what
  ## makes ``after`` a usable cursor: a caller that saw up to some path asks for
  ## what comes after it and cannot be handed the same file twice or be starved
  ## of a later one.
  ##
  ## Bounded twice over. ``MAX_ORPHAN_SCAN_ENTRIES`` bounds filesystem work and
  ## raises on overflow - a partial walk cannot support "nothing references
  ## this". ``limit`` bounds how many candidates are *reported*, and merely sets
  ## ``truncated``: the rest are still on disk, untouched, waiting to be asked
  ## for.
  ##
  ## Nothing here writes, moves, removes or opens for writing. A scan is a
  ## question.
  ##
  def scan(self, limit=MAX_ORPHAN_CANDIDATES, after=None) -> OrphanScan:
    _require_host_support()
    root, media_root = self._roots()
    claimed = self._claimed_paths(root)

    ##
    ## The recording root is entitled not to exist: a deployment that has never
    ## recorded has no such directory, and that is an empty inventory rather
    ## than a fault.
    ##
    descriptor = _open_directory(media_root)
    if descriptor is None:
      return OrphanScan(candidates=[], truncated=False, scanned=0)

    state = {"scanned": 0}
    candidates = []
    try:
      self._walk(
        descriptor,
        media_root,
        root,
        claimed,
        candidates,
        state,
        limit=limit,
        after=after,
        depth=0,
      )
    finally:
      os.close(descriptor)

    ##
    ## Sorted here rather than truncated during the walk, and the difference
    ## matters. A depth-first walk emits ``d/a.flv`` before ``d.flv`` because
    ## ``/`` sorts after ``.``, so walk order is not path order. Cutting the
    ## batch off mid-walk would drop a lexicographically earlier candidate that
    ## the cursor then skips past - which is exactly the starvation this
    ## ordering exists to prevent. The entry bound already caps how much can be
    ## collected, so sorting the whole set first costs nothing unbounded.
    ##
    candidates.sort(key=lambda candidate: candidate.relative_path)
    truncated = len(candidates) > limit
    return OrphanScan(
      candidates=candidates[:limit],
      truncated=truncated,
      scanned=state["scanned"],
    )

  ##
  ## One directory level.
  ##
  ## Recursive, with an explicit depth bound rather than a trust that the tree
  ## is shallow: a symlink loop cannot happen here because links are never
  ## descended into, but a genuinely deep tree still would.
  ##
  ## The descriptor for each level is opened relative to its parent's
  ## descriptor and closed before returning, so a deep path costs a bounded
  ## number of open descriptors rather than one per file.
  ##
  def _walk(
    self,
    descriptor,
    directory,
    root,
    claimed,
    candidates,
    state,
    *,
    limit,
    after,
    depth,
  ):
    if depth > MAX_ORPHAN_SCAN_DEPTH:
      return

    try:
      with os.scandir(descriptor) as entries:
        names = []
        for entry in entries:
          state["scanned"] += 1
          if state["scanned"] > MAX_ORPHAN_SCAN_ENTRIES:
            raise OrphanScanOverflow(
              "the recording tree exceeds the fixed orphan scan bound"
            )
          names.append(entry.name)
    except OrphanScanOverflow:
      raise
    except OSError as e:
      raise OrphanInventoryUnavailable(
        "a recording directory could not be read ({})".format(type(e).__name__)
      ) from e

    ##
    ## Sorted here, not by the filesystem. Everything below depends on two runs
    ## over the same tree producing the same sequence.
    ##
    for name in sorted(names):
      if _is_candidate_name(name):
        self._consider(
          name,
          descriptor,
          directory,
          root,
          claimed,
          candidates,
          state,
          limit=limit,
          after=after,
        )
        continue
      if depth >= MAX_ORPHAN_SCAN_DEPTH:
        continue
      if not _is_scannable_directory_name(name):
        continue
      child = _open_directory(name, parent=descriptor)
      if child is None:
        ##
        ## Not a directory, a link where a directory was, or gone since the
        ## listing. All three mean there is nothing here to walk.
        ##
        continue
      try:
        self._walk(
          child,
          directory / name,
          root,
          claimed,
          candidates,
          state,
          limit=limit,
          after=after,
          depth=depth + 1,
        )
      finally:
        os.close(child)

  ##
  ## One name that looks like a finished recording.
  ##
  ## The name got it this far; the descriptor decides. Opened without following
  ## a link and checked with ``fstat``, so a FIFO, a device, a directory or a
  ## symlink planted under a plausible name is refused by what it *is* rather
  ## than by what it is called.
  ##
  def _consider(
    self,
    name,
    descriptor,
    directory,
    root,
    claimed,
    candidates,
    state,
    *,
    limit,
    after,
  ):
    absolute = directory / name
    try:
      relative = str(absolute.relative_to(root))
    except ValueError:
      return
    if after is not None and relative <= after:
      return

    ##
    ## Membership first, and a descriptor only for what survives it.
    ##
    ## In a healthy library every file is claimed, so this is the answer for
    ## almost every name the walk reaches - and answering it without an open
    ## keeps a scan of a large tree to one resolution per file rather than an
    ## open, an fstat and a close on top of it.
    ##
    ## Containment is decided by the shared rule rather than by a second one
    ## here. The walk already refused to follow a link at any level, so this is
    ## the membership half of the same question the media boundary answers.
    ##
    resolved = contained_path(root, absolute)
    if resolved is None or resolved in claimed:
      return

    opened = _open_regular_file(name, descriptor)
    if opened is None:
      return
    file_descriptor, info = opened
    try:
      ##
      ## A finished recording has bytes in it. A zero-length file is a reserved
      ## HLS output that never captured anything, or a placeholder - never a
      ## broadcast somebody would want back.
      ##
      if info.st_size <= 0:
        return
      candidates.append(_candidate_from(relative, info))
    finally:
      os.close(file_descriptor)

  ##
  ## >>============================= the quarantine =============================>>
  ##

  ##
  ## Where this candidate's quarantined copy would go. Public because an
  ## operator preview and a test both need to name it without performing it.
  ##
  def quarantine_destination_for(self, candidate) -> Path:
    root, unused = self._roots()
    return root / QUARANTINE_DIRECTORY_NAME / _destination_name(
      candidate.relative_path
    )

  ##
  ## Create the quarantine directory the first time something is actually moved.
  ##
  ## Lazily, so a deployment that has never had an orphan does not grow a
  ## directory merely because this module was imported. 0700 because the record
  ## files beside the media say which paths were set aside, and nothing outside
  ## this service has a reason to read them.
  ##
  ## Checked with ``lstat`` afterwards, so a link planted at this name is seen
  ## as a link rather than followed to wherever it points - the same check the
  ## journal makes about its own directory, and for the same reason: this
  ## service is the only thing that should ever create it.
  ##
  def _ensure_quarantine_root(self, root) -> Path:
    target = root / QUARANTINE_DIRECTORY_NAME
    created = False
    try:
      try:
        os.mkdir(target, 0o700)
        created = True
      except FileExistsError:
        pass
      info = os.lstat(target)
      if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise OrphanQuarantineRefused(
          "the quarantine directory is not a directory this service created"
        )
      if created:
        _sync_directory(root)
    except OrphanQuarantineRefused:
      raise
    except OSError as e:
      raise OrphanQuarantineRefused(
        "the quarantine directory is unusable ({})".format(type(e).__name__)
      ) from e
    return target

  ##
  ## Re-open the candidate and prove it is still the file that was inventoried.
  ##
  ## Everything the scan established is established again, against a descriptor
  ## rather than a path, because the interval between reading an inventory and
  ## acting on it is unbounded - an operator reads, thinks, and types - and a
  ## name can come to mean something else in that time.
  ##
  ## Returns the open descriptor and the descriptor for its parent directory.
  ## The caller owns both and must close them: the move has to happen through
  ## the *same* parent descriptor the check was made against, or the check
  ## describes a directory the move does not use.
  ##
  def _reopen_candidate(self, candidate, root, media_root):
    relative = Path(candidate.relative_path)
    if relative.is_absolute() or any(
      part in ("..", ".") for part in relative.parts
    ):
      raise OrphanQuarantineRefused(
        "a quarantine candidate must be a plain path inside the recording root"
      )
    absolute = root / relative
    ##
    ## Membership decided by the shared containment rule, and then again by the
    ## walk below - one says the path belongs to the tree, the other says it is
    ## reachable without passing through a link.
    ##
    resolved = contained_path(root, absolute)
    if resolved is None:
      raise OrphanQuarantineRefused(
        "a quarantine candidate must resolve inside the storage root"
      )
    if contained_path(media_root, absolute) is None:
      raise OrphanQuarantineRefused(
        "a quarantine candidate must resolve inside the recording root"
      )

    parts = relative.parts
    if len(parts) < 2:
      raise OrphanQuarantineRefused(
        "a quarantine candidate must name a file inside a recording directory"
      )

    parent = _open_directory(root)
    if parent is None:
      raise OrphanQuarantineRefused("the storage root could not be opened")
    try:
      for name in parts[:-1]:
        child = _open_directory(name, parent=parent)
        if child is None:
          raise OrphanQuarantineRefused(
            "the candidate's directory is missing or is not a directory"
          )
        os.close(parent)
        parent = child
      opened = _open_regular_file(parts[-1], parent)
      if opened is None:
        raise OrphanQuarantineRefused(
          "the candidate is no longer a regular file reachable without a link"
        )
      file_descriptor, info = opened
      if _fingerprint(info) != (
        candidate.device,
        candidate.inode,
        candidate.size,
        candidate.mtime_ns,
      ):
        os.close(file_descriptor)
        raise OrphanQuarantineRefused(
          "the candidate changed after it was inventoried"
        )
      return file_descriptor, parent, resolved
    except BaseException:
      os.close(parent)
      raise

  ##
  ## Set one named file aside.
  ##
  ## Explicit, one file at a time, and never reached by a startup path, a
  ## request handler or a periodic job - the only caller is an operator command.
  ##
  ## The order below is the whole safety argument:
  ##
  ##   1. Ask both authorities again. A recording catalogued, or a note
  ##      published, between the inventory and now means this file is claimed
  ##      after all, and the answer is no.
  ##   2. Re-open the file and re-prove its identity against the descriptor.
  ##   3. Hard-link it into quarantine. ``os.link`` refuses to overwrite, which
  ##      is why it is used instead of ``os.rename``; a cross-device link fails
  ##      with EXDEV rather than degrading into copy-and-delete.
  ##   4. Commit the quarantine directory, then unlink the original, then
  ##      commit its directory.
  ##
  ## A crash anywhere in 3-4 leaves the file reachable under at least one name -
  ## never none. Because the destination name is derived from the source path, a
  ## retry recomputes it, finds the same inode already there, and finishes.
  ##
  def quarantine(self, candidate, dry_run=False) -> QuarantineOutcome:
    _require_host_support()
    root, media_root = self._roots()

    try:
      claimed = self._claimed_paths(root)
    except OrphanInventoryUnavailable as e:
      ##
      ## Cannot prove the file is unclaimed, so it is not moved. "Unknown" and
      ## "unreferenced" are different answers and only one of them permits this.
      ##
      raise OrphanQuarantineRefused(
        "the claim authorities could not be consulted ({})".format(
          type(e).__name__
        )
      ) from e

    file_descriptor, parent, resolved = self._reopen_candidate(
      candidate, root, media_root
    )
    try:
      if resolved in claimed:
        raise OrphanQuarantineRefused(
          "the candidate is now referenced by a recording or a pending note"
        )

      destination_name = _destination_name(candidate.relative_path)
      if dry_run:
        return QuarantineOutcome(
          relative_path=candidate.relative_path,
          destination_name=destination_name,
          quarantined=False,
        )

      quarantine_root = self._ensure_quarantine_root(root)
      quarantine_descriptor = _open_directory(quarantine_root)
      if quarantine_descriptor is None:
        raise OrphanQuarantineRefused("the quarantine directory could not be opened")
      try:
        self._link_into_quarantine(
          parts_name=Path(candidate.relative_path).name,
          source_parent=parent,
          destination_name=destination_name,
          destination_parent=quarantine_descriptor,
          candidate=candidate,
        )
        self._write_record(
          quarantine_descriptor, destination_name, candidate
        )
        ##
        ## Past the point of no loss: the bytes are reachable through the
        ## quarantine name whatever happens here. A failure is reported as its
        ## own state rather than as a refusal, because "nothing changed" would
        ## be untrue and an operator retrying is exactly the right response.
        ##
        try:
          os.unlink(Path(candidate.relative_path).name, dir_fd=parent)
        except OSError as e:
          raise OrphanQuarantineIncomplete(
            "the media is quarantined but its original name could not be "
            "removed ({}); retrying completes the move".format(
              type(e).__name__
            )
          ) from e
        _sync_directory(parent)
      finally:
        os.close(quarantine_descriptor)
    finally:
      os.close(file_descriptor)
      os.close(parent)

    ##
    ## An audit line for a destructive action, and a deliberately empty one.
    ##
    ## Which file moved is in the owner-only record beside it; putting the path
    ## here would copy a broadcaster's directory name into a log stream that is
    ## rotated and read far more widely than the media it describes. A literal
    ## with nothing interpolated into it cannot leak whatever it is handed.
    ##
    get_logger().warning(
      "recording orphan quarantined; the quarantine record names which file"
    )
    return QuarantineOutcome(
      relative_path=candidate.relative_path,
      destination_name=destination_name,
      quarantined=True,
    )

  ##
  ## The move itself.
  ##
  ## ``os.link`` rather than ``os.rename`` for one reason: rename silently
  ## destroys whatever already holds the destination name, and the one thing
  ## quarantine must never do is overwrite media somebody set aside earlier.
  ## Link refuses, which turns a collision into a reported refusal instead of a
  ## lost recording. Python exposes no ``RENAME_NOREPLACE``, so link-then-unlink
  ## is the only atomic no-clobber move available - and it is the same choice
  ## the recovery journal and the remux publisher already make.
  ##
  ## EXDEV is refused outright. Falling back to copy-and-delete would write a
  ## second copy of somebody's recording onto a filesystem nobody nominated, and
  ## would stop being atomic exactly when it mattered.
  ##
  ## EEXIST is where the crash-retry lives. The destination name is derived from
  ## the source path, so a retry after a crash between the link and the unlink
  ## computes the same name. If what is already there is the *same inode*, this
  ## attempt's own earlier link succeeded and the move simply continues. Any
  ## other file under that name is a genuine collision and is refused.
  ##
  def _link_into_quarantine(
    self,
    *,
    parts_name,
    source_parent,
    destination_name,
    destination_parent,
    candidate,
  ):
    try:
      os.link(
        parts_name,
        destination_name,
        src_dir_fd=source_parent,
        dst_dir_fd=destination_parent,
        follow_symlinks=False,
      )
    except FileExistsError as e:
      try:
        existing = os.stat(
          destination_name, dir_fd=destination_parent, follow_symlinks=False
        )
      except OSError as lookup_error:
        raise OrphanQuarantineRefused(
          "the quarantine destination is already taken and unreadable ({})".format(
            type(lookup_error).__name__
          )
        ) from lookup_error
      if (existing.st_dev, existing.st_ino) != (candidate.device, candidate.inode):
        raise OrphanQuarantineRefused(
          "the quarantine destination already holds a different file"
        ) from e
      ##
      ## The same inode: a previous attempt linked it and did not finish. Fall
      ## through and complete the move.
      ##
    except OSError as e:
      if e.errno == errno.EXDEV:
        raise OrphanQuarantineRefused(
          "the quarantine directory is on a different filesystem; "
          "media is never copied across devices"
        ) from e
      raise OrphanQuarantineRefused(
        "the candidate could not be linked into quarantine ({})".format(
          type(e).__name__
        )
      ) from e
    _sync_directory(destination_parent)

  ##
  ## What was set aside, and nothing about who it belonged to.
  ##
  ## The original root-relative path is here because it is the only way back:
  ## the quarantined name is a hash, deliberately, so a directory listing is not
  ## a list of who has been recorded. 0600 for the same reason.
  ##
  ## Never an absolute path, never an owner, never a nickname, never a room. If
  ## a field is not needed to put the file back by hand, it is not written.
  ##
  def _write_record(self, destination_parent, destination_name, candidate):
    payload = json.dumps(
      {
        "schema_version": _RECORD_SCHEMA_VERSION,
        "source_relative_path": candidate.relative_path,
        "quarantined_name": destination_name,
        "size": candidate.size,
        "mtime_ns": candidate.mtime_ns,
        "quarantined_at": datetime.now(timezone.utc).isoformat(
          timespec="milliseconds"
        ),
      },
      ensure_ascii=False,
      sort_keys=True,
      separators=(",", ":"),
      allow_nan=False,
    ) + "\n"

    name = destination_name + _RECORD_SUFFIX
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | _O_CLOEXEC
    try:
      descriptor = os.open(name, flags, 0o600, dir_fd=destination_parent)
    except FileExistsError:
      ##
      ## A previous attempt already wrote it. The media is what matters and it
      ## is already linked; rewriting the record would only risk truncating a
      ## good one.
      ##
      return
    except OSError as e:
      raise OrphanQuarantineRefused(
        "the quarantine record could not be written ({})".format(
          type(e).__name__
        )
      ) from e
    try:
      encoded = payload.encode("utf-8")
      written = 0
      while written < len(encoded):
        written += os.write(descriptor, encoded[written:])
      os.fsync(descriptor)
    finally:
      os.close(descriptor)
    _sync_directory(destination_parent)


##
## Commit a directory's entries to stable storage.
##
## A file's name lives in its parent directory, so the link can be complete
## while the entry that reaches it is still only in an uncommitted metadata
## journal. Both directories are committed - the one gaining a name and the one
## losing it - because a crash that resurrected the old name while the new one
## was still uncommitted would leave the file in neither place.
##
## Takes the descriptor already held rather than reopening by path: the
## directory to commit is the one the move actually used, and a second open by
## name is a second chance for the name to mean something else.
##
def _sync_directory(target):
  try:
    if isinstance(target, int):
      os.fsync(target)
      return
    flags = os.O_RDONLY | os.O_DIRECTORY | _O_CLOEXEC
    descriptor = os.open(str(target), flags)
    try:
      os.fsync(descriptor)
    finally:
      os.close(descriptor)
  except OSError as e:
    raise OrphanQuarantineRefused(
      "a quarantine directory could not be committed ({})".format(
        type(e).__name__
      )
    ) from e


__all__ = [
  "MAX_ORPHAN_CANDIDATES",
  "MAX_ORPHAN_SCAN_DEPTH",
  "MAX_ORPHAN_SCAN_ENTRIES",
  "MAX_REFERENCED_RECORDINGS",
  "QUARANTINE_DIRECTORY_NAME",
  "RECORDED_MEDIA_SUFFIXES",
  "OrphanCandidate",
  "OrphanInventoryUnavailable",
  "OrphanQuarantineIncomplete",
  "OrphanQuarantineRefused",
  "OrphanScan",
  "OrphanScanOverflow",
  "QuarantineOutcome",
  "RecordingOrphanInventory",
  "resolve_recording_media_root",
  "resolve_recording_storage_root",
]
