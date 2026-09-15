#!/usr/bin/env python3
"""Snapshot the media tree by reflink, and prove a snapshot is still itself.

The Compose backup tars its download volume. Production's media root holds
terabytes on a filesystem that has less free than it has used, so there is no
destination for a copy - not on that disk and not on any other one here. A
release that demanded one would never run.

Reflink is what does work. The media filesystem is XFS with ``reflink=1``, so a
copy-on-write clone is a metadata operation: it shares extents with the original
and costs almost nothing until one side diverges. That is a real snapshot of the
tree as it was at that instant, taken in seconds.

Two consequences, both deliberate.

Reflink is checked, never assumed. If the destination cannot clone, this stops.
Falling back to a byte copy would turn "this host has no rollback authority"
into "the release hangs for hours and then fails with a full disk", which is the
same outcome reached far more expensively and much later.

And the snapshot necessarily shares a filesystem with the media it clones. It is
authority against *logical* loss - a bad migration, an application bug, a wrong
delete - and it is not authority against the device failing. That boundary is
stated here and in the runbook rather than left for somebody to discover.

Two things this deliberately does **not** claim.

It is not atomic across the tree. ``cp --reflink`` clones entry by entry, so a
tree still being written to would be captured at slightly different instants per
file. Consistency is the *backup contract's* job, not this helper's: the writer
is stopped and proven stopped before this runs, and the ordering lives in
``release_external_backup.sh``. A snapshot taken under a live writer is a
snapshot of nothing in particular.

And the identity it records is the identity of *the snapshot object*, not a
content integrity hash. Device and inode prove that the files in a snapshot are
still the files that were cloned into it - that nothing was substituted
underneath - which is exactly what a later restore needs to know about its
source. They say nothing about a restored copy: restoring or re-cloning produces
new inodes by definition, so a restore is verified against what it produced, not
against these numbers.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


SNAPSHOT_DOCUMENT_VERSION = 1

##
## The identity of a file, in the terms that cannot be forged by rewriting one.
## A path and a size are chosen by whoever writes the bytes and a modification
## time is one ``utime`` away; a device and an inode are not.
##
IDENTITY_FIELDS = ("relative_path", "size", "mtime_ns", "device", "inode")


def fail(message: str) -> None:
  print("media snapshot refused: " + message, file=sys.stderr)
  raise SystemExit(1)


##
## Can this filesystem clone at all?
##
## Asked by doing it, in the directory the snapshot will actually be written to,
## rather than by reading a filesystem flag. The flag says the feature is
## compiled in; the attempt says this directory on this mount will accept it.
##
def reflink_available(directory: Path) -> bool:
  probe_source = directory / ".smsd-reflink-probe-source"
  probe_target = directory / ".smsd-reflink-probe-target"
  try:
    probe_source.write_bytes(b"smsd-reflink-probe")
    completed = subprocess.run(
      ["cp", "--reflink=always", str(probe_source), str(probe_target)],
      capture_output=True,
    )
    return completed.returncode == 0
  except OSError:
    return False
  finally:
    for path in (probe_source, probe_target):
      try:
        path.unlink()
      except OSError:
        pass


##
## Every regular file under ``root``, with its identity.
##
## Symbolic links are recorded as absent rather than followed: a link in a media
## tree points somewhere this snapshot does not own, and following one would
## silently pull an unrelated file into the release's idea of the library.
##
## Nothing is read. The tree is terabytes and this needs none of it.
##
def collect_identity(root: Path) -> tuple[list, int]:
  entries = []
  total_bytes = 0
  for current, directories, files in os.walk(root, followlinks=False):
    directories.sort()
    for name in sorted(files):
      path = Path(current) / name
      try:
        info = os.lstat(path)
      except OSError as error:
        fail("a snapshot entry could not be inspected ({})".format(
          type(error).__name__
        ))
      if not os.path.stat.S_ISREG(info.st_mode):
        continue
      entries.append({
        "relative_path": str(path.relative_to(root)),
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "device": info.st_dev,
        "inode": info.st_ino,
      })
      total_bytes += info.st_size
  return entries, total_bytes


##
## Where a snapshot store is allowed to be.
##
## Reflink cannot cross a filesystem, and the media root *is* the mount point of
## its filesystem, so the store has to live inside the tree being cloned. There
## is nowhere else on that disk. Everything here is about making that safe
## rather than pretending it can be avoided.
##
## Two rules, and both are load-bearing:
##
##   - same filesystem, checked by device rather than by path. A store on
##     another mount would either fail obscurely or, far worse, silently become
##     the byte copy this whole approach exists to avoid.
##   - a hidden directory *directly beneath* the media root, when it is inside
##     it at all. Two separate rules collapse into that one shape.
##
##     Hidden, because the application's orphan scan descends into every
##     directory whose name is not hidden, so a visible store would be walked as
##     if it were media and each cloned recording would be offered as an orphan
##     candidate. ``_is_scannable_directory_name`` in ``recording_orphan`` is
##     the rule this leans on, and a test pins the two together so they cannot
##     drift.
##
##     Directly beneath, because that is the only shape the clone below can
##     actually exclude. The clone iterates the media root's own entries and
##     skips the store; a store nested deeper - ``MEDIA/visible/.store`` - is not
##     one of those entries, so ``visible`` would be cloned whole and would carry
##     the store in with it. Every release would then nest the release before it.
##     The validator used to accept that shape and the clone could not honour it,
##     which is the kind of disagreement that shows up as a full disk.
##
##
## Remove a tree this process owns, including parts of it that were cloned with
## modes that forbid traversal.
##
## Ownership is what makes this safe: the mode can be restored because the
## caller created these entries a moment ago. Nothing outside the snapshot being
## abandoned is ever touched.
##
def _remove_tree(target: Path) -> None:
  def reopen(function, path, unused):
    try:
      os.chmod(path, 0o700)
    except OSError:
      return
    function(path)

  try:
    shutil.rmtree(target, onexc=reopen)
  except TypeError:
    ## Python 3.11 and earlier spell the same hook differently.
    shutil.rmtree(target, onerror=lambda f, p, e: reopen(f, p, e))
  except OSError:
    ##
    ## Reported rather than swallowed: an operator needs to know a directory
    ## was left behind, because the next release will see it.
    ##
    print(
      "media snapshot warning: an abandoned snapshot could not be removed",
      file=sys.stderr,
    )


def require_valid_snapshot_root(media_root: Path, snapshot_root: Path) -> bool:
  try:
    media_device = os.stat(media_root).st_dev
    snapshot_device = os.stat(
      snapshot_root if snapshot_root.exists() else snapshot_root.parent
    ).st_dev
  except OSError as error:
    fail("the snapshot root could not be inspected ({})".format(
      type(error).__name__
    ))
  if media_device != snapshot_device:
    fail(
      "the snapshot root must be on the same filesystem as the media root; "
      "reflink cannot cross one"
    )

  try:
    relative = snapshot_root.relative_to(media_root)
  except ValueError:
    return False
  ##
  ## Exactly one component, and hidden. Anything else - the media root itself,
  ## or a store buried under a visible directory - is refused rather than
  ## accepted into a clone that cannot leave it out.
  ##
  if len(relative.parts) == 1 and relative.parts[0].startswith("."):
    return True
  fail(
    "a snapshot root inside the media root must be a hidden directory directly "
    "beneath it: hidden so the application does not scan the snapshot as media, "
    "and directly beneath so the clone can leave it out of itself"
  )


def create(arguments) -> int:
  media_root = Path(os.path.realpath(arguments.media_root))
  snapshot_root = Path(os.path.realpath(arguments.snapshot_root))
  output = Path(arguments.output)

  if str(media_root) == "/":
    fail("the media root must not be the filesystem root")
  if not media_root.is_dir():
    fail("the media root is not an existing directory")

  snapshot_root.mkdir(parents=True, exist_ok=True, mode=0o700)
  nested = require_valid_snapshot_root(media_root, snapshot_root)
  if not reflink_available(snapshot_root):
    ##
    ## Refused, never degraded. See the module note.
    ##
    fail(
      "the snapshot destination does not support reflink; a byte copy of the "
      "media tree is not a supported fallback"
    )

  ##
  ## A readable timestamp so an operator can tell snapshots apart, and a random
  ## suffix so two taken in the same second cannot collide - which is not a
  ## hypothetical: a rehearsal takes several in a row.
  ##
  stamp = "{}-{}".format(
    datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    os.urandom(4).hex(),
  )
  snapshot_path = snapshot_root / stamp
  if snapshot_path.exists():
    fail("a snapshot already exists under that name")

  ##
  ## Cloned entry by entry rather than with one ``cp -T`` of the whole root,
  ## because the snapshot store lives inside the tree being cloned and must be
  ## left out of it. Without the exclusion each release would nest the release
  ## before it until the media root was mostly its own history.
  ##
  ## ``-a`` keeps ownership, mode and timestamps; ``--reflink=always`` makes the
  ## command fail rather than silently fall back to copying.
  ##
  snapshot_path.mkdir(mode=0o700)
  try:
    for entry in sorted(media_root.iterdir()):
      if nested and entry == snapshot_root:
        continue
      completed = subprocess.run(
        [
          "cp", "-a", "--reflink=always",
          str(entry), str(snapshot_path / entry.name),
        ],
        capture_output=True,
        text=True,
      )
      if completed.returncode != 0:
        raise OSError(completed.stderr.strip() or "clone failed")
  except OSError:
    ##
    ## Remove the half-made clone. A partial snapshot that looked like a whole
    ## one is the failure this whole file exists to prevent, and leaving one
    ## behind would let a later release mistake it for a complete capture.
    ##
    ## ``ignore_errors`` is deliberately not used. A clone can fail precisely
    ## because it hit a directory nothing can traverse, and ``cp`` will have
    ## reproduced that mode on the way in - so the removal has to be able to
    ## open what it is removing, and a silent failure here would leave exactly
    ## the debris this is here to clear.
    ##
    _remove_tree(snapshot_path)
    fail("the media tree could not be cloned by reflink")

  entries, total_bytes = collect_identity(snapshot_path)
  document = {
    "format_version": SNAPSHOT_DOCUMENT_VERSION,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "media_root": str(media_root),
    "snapshot_path": str(snapshot_path),
    "entry_count": len(entries),
    "total_bytes": total_bytes,
    "entries": entries,
  }
  output.write_text(
    json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
  )
  output.chmod(0o600)
  print(
    "media snapshot created: entries={} bytes={} path={}".format(
      len(entries), total_bytes, snapshot_path
    )
  )
  return 0


def verify(arguments) -> int:
  snapshot_path = Path(arguments.snapshot_path)
  try:
    document = json.loads(Path(arguments.document).read_text(encoding="utf-8"))
  except (OSError, UnicodeDecodeError, json.JSONDecodeError):
    fail("the snapshot document could not be read")

  expected = document.get("entries")
  if not isinstance(expected, list):
    fail("the snapshot document has no entries")

  observed, total_bytes = collect_identity(snapshot_path)
  by_path = {entry["relative_path"]: entry for entry in observed}

  for entry in expected:
    found = by_path.pop(entry.get("relative_path"), None)
    if found is None:
      fail("a snapshot entry is missing")
    for field in IDENTITY_FIELDS:
      if found[field] != entry.get(field):
        ##
        ## Deliberately silent about which file and which field. This runs on a
        ## release path whose output is pasted into tickets, and a media path is
        ## a broadcaster's directory name.
        ##
        fail("a snapshot entry is not the file that was snapshotted")
  if by_path:
    fail("the snapshot holds files the document does not describe")

  print(
    "media snapshot verified: entries={} bytes={}".format(
      len(expected), total_bytes
    )
  )
  return 0


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
  subparsers = parser.add_subparsers(dest="command", required=True)

  creator = subparsers.add_parser("create")
  creator.add_argument("--media-root", required=True)
  creator.add_argument("--snapshot-root", required=True)
  creator.add_argument("--output", required=True)

  verifier = subparsers.add_parser("verify")
  verifier.add_argument("--snapshot-path", required=True)
  verifier.add_argument("--document", required=True)
  return parser


def main(argv=None) -> int:
  arguments = build_parser().parse_args(argv)
  if arguments.command == "create":
    return create(arguments)
  return verify(arguments)


if __name__ == "__main__":
  raise SystemExit(main())
