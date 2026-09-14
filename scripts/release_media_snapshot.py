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


def require_distinct_trees(media_root: Path, snapshot_root: Path) -> None:
  ##
  ## A snapshot root inside the media root would clone itself, and every release
  ## would nest the one before it until the tree was mostly its own history.
  ##
  try:
    snapshot_root.relative_to(media_root)
  except ValueError:
    return
  fail("the snapshot root must not be inside the media root")


def create(arguments) -> int:
  media_root = Path(os.path.realpath(arguments.media_root))
  snapshot_root = Path(os.path.realpath(arguments.snapshot_root))
  output = Path(arguments.output)

  if str(media_root) == "/":
    fail("the media root must not be the filesystem root")
  if not media_root.is_dir():
    fail("the media root is not an existing directory")
  require_distinct_trees(media_root, snapshot_root)

  snapshot_root.mkdir(parents=True, exist_ok=True, mode=0o700)
  if not reflink_available(snapshot_root):
    ##
    ## Refused, never degraded. See the module note.
    ##
    fail(
      "the snapshot destination does not support reflink; a byte copy of the "
      "media tree is not a supported fallback"
    )

  stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
  snapshot_path = snapshot_root / stamp
  if snapshot_path.exists():
    fail("a snapshot already exists under that name")

  ##
  ## ``-a`` to keep ownership, mode and timestamps; ``--reflink=always`` so the
  ## command fails rather than silently copying; ``-T`` so the destination is
  ## the snapshot itself rather than a directory inside it.
  ##
  completed = subprocess.run(
    ["cp", "-a", "--reflink=always", "-T", str(media_root), str(snapshot_path)],
    capture_output=True,
    text=True,
  )
  if completed.returncode != 0:
    ##
    ## Remove the half-made clone. A partial snapshot that looked like a whole
    ## one is the failure this whole file exists to avoid.
    ##
    shutil.rmtree(snapshot_path, ignore_errors=True)
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
