"""No-network runtime proof for the recording orphan inventory and quarantine.

Runs inside the production image against the real service modules, a real
temporary storage root and real Linux descriptors. No database, no platform
credentials and no network are involved: the claim authorities are injected, so
what is proved here is the filesystem and refusal behaviour the image ships.
"""

from datetime import datetime
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if not (PROJECT_ROOT / "backend").is_dir():
  PROJECT_ROOT = Path("/app")
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.service import recording_orphan as orphan_module
from backend.src.service.recording_orphan import (
  QUARANTINE_DIRECTORY_NAME,
  OrphanQuarantineIncomplete,
  OrphanQuarantineRefused,
  OrphanScanOverflow,
  RecordingOrphanInventory,
)
from backend.src.service.recording_recovery_journal import (
  RecordingRecoveryJournal,
)
from backend.src.service.recording_resource import RecordingPersistenceIntent


##
## Values that exist nowhere else, so finding one in this probe's own output
## could only mean the service put it there.
##
SECRET_OWNER = "SECRET_ORPHAN_OWNER_P18"
SECRET_TITLE = "SECRET_ORPHAN_TITLE_P18"

KEY_PENDING = "aa" * 16
KEY_SECOND = "bb" * 16


def require(condition, message):
  if not condition:
    raise SystemExit("FAIL: " + message)


def require_refusal(kind, call, message):
  try:
    call()
  except kind:
    return
  except Exception as e:
    raise SystemExit(
      "FAIL: {} (raised {} instead)".format(message, type(e).__name__)
    )
  raise SystemExit("FAIL: " + message)


class References:
  def __init__(self, paths=(), error=None):
    self.paths = list(paths)
    self.error = error

  def referenced_output_paths(self):
    if self.error is not None:
      raise self.error
    return list(self.paths)


class BrokenJournal:
  def pending_keys_snapshot(self):
    raise RuntimeError("journal directory is unusable")


def settings_for(root):
  return {
    "download": {"save_path": str(root)},
    "platform": {"douyin": {"download": {"type": "live"}}},
  }


def build(root, references=None, journal=None):
  settings = settings_for(root)
  real_journal = RecordingRecoveryJournal(config_loader=lambda: settings)
  return real_journal, RecordingOrphanInventory(
    journal=real_journal if journal is None else journal,
    references=References() if references is None else references,
    config_loader=lambda: settings,
  )


def write_media(directory, name, payload=b"a whole broadcast"):
  directory.mkdir(parents=True, exist_ok=True)
  path = directory / name
  path.write_bytes(payload)
  return path


def publish(journal, output_path, key):
  journal.publish(
    RecordingPersistenceIntent(
      app_user_id=1,
      platform="douyin",
      room_id="7700",
      owner_user_id=SECRET_OWNER,
      title=SECRET_TITLE,
      protocol="flv",
      output_path=str(output_path),
      started_at=datetime(2026, 9, 3, 12, 0, 0),
      finished_at=datetime(2026, 9, 3, 13, 0, 0),
      source="live",
    ),
    key,
  )


##
## >>=========================== the inventory half ===========================>>
##
def prove_inventory(root):
  media_root = root / "douyin" / "live"
  broadcaster = media_root / "broadcaster"

  referenced = write_media(broadcaster, "referenced.flv")
  pending = write_media(broadcaster, "pending.flv")
  orphan = write_media(broadcaster, "orphan.flv")

  ##
  ## Every shape the scanner must refuse, planted beside a real orphan so a
  ## scanner that ignored one of them would report more than one candidate.
  ##
  outside = root / "elsewhere.flv"
  outside.write_bytes(b"not this library's file")
  os.symlink(outside, broadcaster / "linked.flv")
  os.mkfifo(broadcaster / "stream.flv")
  (broadcaster / "reserved.ts").touch()
  (broadcaster / ".capture.remux-abc.part.mp4").write_bytes(b"partial")
  (broadcaster / "capture.part.mp4").write_bytes(b"partial")
  write_media(root / "douyin" / "aweme", "a-downloaded-post.mp4")

  ##
  ## A symlinked directory: the walk must not descend into it.
  ##
  hidden = root / "hidden"
  write_media(hidden, "reachable.flv")
  os.symlink(hidden, media_root / "linked-broadcaster")

  journal, inventory = build(root, references=References(paths=[str(referenced)]))
  publish(journal, pending, KEY_PENDING)

  scan = inventory.scan()
  found = [candidate.relative_path for candidate in scan.candidates]
  require(
    found == [str(orphan.relative_to(root))],
    "inventory did not isolate exactly the one true orphan: %r" % found,
  )

  candidate = scan.candidates[0]
  info = os.stat(orphan)
  require(
    (candidate.device, candidate.inode, candidate.size, candidate.mtime_ns)
    == (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns),
    "candidate identity does not describe the file on disk",
  )
  require(
    not Path(candidate.relative_path).is_absolute()
    and str(root) not in candidate.relative_path,
    "candidate exposed an absolute path",
  )
  for forbidden in ("app_user_id", "owner_user_id", "owner", "nickname"):
    require(
      not hasattr(candidate, forbidden),
      "candidate carried an owner field: %s" % forbidden,
    )

  ##
  ## A scan must never move, remove or create anything.
  ##
  require(referenced.is_file(), "scan disturbed a referenced recording")
  require(pending.is_file(), "scan disturbed pending media")
  require(orphan.is_file(), "scan removed the orphan it reported")
  require(
    not (root / QUARANTINE_DIRECTORY_NAME).exists(),
    "a scan created the quarantine directory",
  )

  ##
  ## Fail closed: neither authority may be guessed at.
  ##
  unavailable = build(root, references=References(error=RuntimeError("down")))[1]
  require_refusal(
    Exception,
    unavailable.scan,
    "an unreachable repository did not fail closed",
  )
  broken = build(root, journal=BrokenJournal())[1]
  require_refusal(
    Exception,
    broken.scan,
    "an unreadable journal did not fail closed",
  )

  print("ok   runtime orphan inventory authority and refusals")
  return inventory, orphan, referenced


##
## >>============================ the bounded scan ============================>>
##
def prove_bounded_scan(root):
  bounded = root / "bounded"
  media = bounded / "douyin" / "live" / "broadcaster"
  media.mkdir(parents=True)
  for index in range(12):
    (media / "file-{:05d}.flv".format(index)).write_bytes(b"m")

  unused, inventory = build(bounded)

  ##
  ## The bound is lowered rather than materialised. The property being proved
  ## is that the walk refuses once it exceeds whatever bound is configured;
  ## creating the production bound's worth of files would prove the same thing
  ## and turn a smoke test into a filesystem benchmark.
  ##
  original = orphan_module.MAX_ORPHAN_SCAN_ENTRIES
  orphan_module.MAX_ORPHAN_SCAN_ENTRIES = 4
  try:
    require_refusal(
      OrphanScanOverflow,
      inventory.scan,
      "an oversized recording tree was not bounded",
    )
  finally:
    orphan_module.MAX_ORPHAN_SCAN_ENTRIES = original

  ##
  ## The same tree under the shipped bound, so the refusal above is the bound
  ## working rather than the walk being broken - and the shipped bound is one a
  ## genuine media library fits inside.
  ##
  require(
    len(inventory.scan().candidates) == 12,
    "the shipped bound refused a tree it should have walked",
  )
  require(
    orphan_module.MAX_ORPHAN_SCAN_ENTRIES >= 100000,
    "the shipped scan bound is too small for a real media library",
  )

  ##
  ## Ordered, resumable continuation: every candidate is eventually offered and
  ## none is offered twice.
  ##
  paged = root / "paged"
  paged_media = paged / "douyin" / "live" / "broadcaster"
  paged_media.mkdir(parents=True)
  for index in range(6):
    (paged_media / "orphan-{}.flv".format(index)).write_bytes(b"media")

  unused, paged_inventory = build(paged)
  seen = []
  cursor = None
  for unused_page in range(6):
    page = paged_inventory.scan(limit=2, after=cursor)
    if not page.candidates:
      break
    seen.extend(item.relative_path for item in page.candidates)
    cursor = page.candidates[-1].relative_path
  require(seen == sorted(seen), "continuation was not ordered")
  require(len(seen) == len(set(seen)) == 6, "continuation starved a candidate")

  print("ok   runtime orphan bounded resumable scan")


##
## >>=========================== the quarantine half ===========================>>
##
def prove_quarantine(root, inventory, orphan, referenced):
  candidate = inventory.scan().candidates[0]
  before = os.stat(orphan)

  ##
  ## A dry run is the preview, and previews do not act.
  ##
  preview = inventory.quarantine(candidate, dry_run=True)
  require(preview.quarantined is False, "a dry run reported acting")
  require(orphan.is_file(), "a dry run moved media")
  require(
    not (root / QUARANTINE_DIRECTORY_NAME).exists(),
    "a dry run created the quarantine directory",
  )

  outcome = inventory.quarantine(candidate)
  require(outcome.quarantined is True, "quarantine did not report acting")

  ##
  ## The source is gone and the destination holds the *same inode*, which is
  ## what separates an atomic same-filesystem move from a copy.
  ##
  require(not orphan.exists(), "the quarantined source survived")
  quarantine_root = root / QUARANTINE_DIRECTORY_NAME
  media = sorted(
    path for path in quarantine_root.iterdir() if path.suffix != ".json"
  )
  require(len(media) == 1, "quarantine holds %d media files" % len(media))
  after = os.stat(media[0])
  require(
    (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino),
    "the quarantined file is a copy, not the file that was there",
  )
  require(
    media[0].read_bytes() == b"a whole broadcast",
    "the quarantined file's contents changed",
  )
  require(referenced.is_file(), "quarantine disturbed a referenced recording")

  ##
  ## Permissions and the record beside it.
  ##
  require(
    quarantine_root.name.startswith("."), "the quarantine root is not hidden"
  )
  require(
    (os.lstat(quarantine_root).st_mode & 0o077) == 0,
    "the quarantine root is group or world accessible",
  )
  records = sorted(quarantine_root.glob("*.json"))
  require(len(records) == 1, "expected exactly one quarantine record")
  require(
    (os.lstat(records[0]).st_mode & 0o177) == 0,
    "the quarantine record is not owner-only",
  )
  written = json.loads(records[0].read_text(encoding="utf-8"))
  require(
    written["source_relative_path"] == candidate.relative_path,
    "the quarantine record does not name the file it describes",
  )
  for forbidden in (
    "app_user_id", "owner_user_id", "user_id", "owner", "nickname", "room_id",
  ):
    require(
      forbidden not in written,
      "the quarantine record carried an owner field: %s" % forbidden,
    )
  raw_record = records[0].read_text(encoding="utf-8")
  require(str(root) not in raw_record, "the quarantine record leaked an absolute path")
  require(SECRET_OWNER not in raw_record, "the quarantine record leaked an owner")
  require(SECRET_TITLE not in raw_record, "the quarantine record leaked a title")

  ##
  ## Already set aside, so never offered again.
  ##
  require(
    inventory.scan().candidates == [],
    "a quarantined file was offered as a candidate again",
  )
  print("ok   runtime orphan quarantine atomic transition")


##
## >>========================== the races it refuses ==========================>>
##
def prove_races(root):
  base = root / "races"

  ##
  ## Replaced inode: same name, same size, same bytes, different file.
  ##
  replaced_root = base / "replaced"
  media = replaced_root / "douyin" / "live" / "broadcaster"
  source = write_media(media, "orphan.flv")
  unused, inventory = build(replaced_root)
  candidate = inventory.scan().candidates[0]
  stand_in = source.with_name("stand-in.flv")
  stand_in.write_bytes(b"a whole broadcast")
  os.replace(stand_in, source)
  require_refusal(
    OrphanQuarantineRefused,
    lambda: inventory.quarantine(candidate),
    "a replaced inode was quarantined",
  )
  require(source.is_file(), "a refused quarantine removed the file")

  ##
  ## Rewritten in place: same inode, different contents.
  ##
  rewritten_root = base / "rewritten"
  media = rewritten_root / "douyin" / "live" / "broadcaster"
  source = write_media(media, "orphan.flv")
  unused, inventory = build(rewritten_root)
  candidate = inventory.scan().candidates[0]
  source.write_bytes(b"a longer, different broadcast entirely")
  require_refusal(
    OrphanQuarantineRefused,
    lambda: inventory.quarantine(candidate),
    "a rewritten file was quarantined",
  )
  require(source.is_file(), "a refused quarantine removed the file")

  ##
  ## Claimed after the inventory, by each authority in turn.
  ##
  claimed_root = base / "claimed"
  media = claimed_root / "douyin" / "live" / "broadcaster"
  source = write_media(media, "orphan.flv")
  references = References()
  unused, inventory = build(claimed_root, references=references)
  candidate = inventory.scan().candidates[0]
  references.paths = [str(source)]
  require_refusal(
    OrphanQuarantineRefused,
    lambda: inventory.quarantine(candidate),
    "a newly referenced recording was quarantined",
  )
  require(source.is_file(), "a refused quarantine removed the file")

  journalled_root = base / "journalled"
  media = journalled_root / "douyin" / "live" / "broadcaster"
  source = write_media(media, "orphan.flv")
  journal, inventory = build(journalled_root)
  candidate = inventory.scan().candidates[0]
  publish(journal, source, KEY_SECOND)
  require_refusal(
    OrphanQuarantineRefused,
    lambda: inventory.quarantine(candidate),
    "media a new note describes was quarantined",
  )
  require(source.is_file(), "a refused quarantine removed the file")

  ##
  ## Authorities unreachable at the moment of acting.
  ##
  references = References()
  unused, unreachable = build(claimed_root, references=references)
  candidate = unreachable.scan().candidates[0]
  references.error = RuntimeError("database is down")
  require_refusal(
    OrphanQuarantineRefused,
    lambda: unreachable.quarantine(candidate),
    "quarantine acted while the repository was unreachable",
  )

  ##
  ## Turned into a symlink between the inventory and the move.
  ##
  swapped_root = base / "swapped"
  media = swapped_root / "douyin" / "live" / "broadcaster"
  source = write_media(media, "orphan.flv")
  unused, inventory = build(swapped_root)
  candidate = inventory.scan().candidates[0]
  target = swapped_root / "somebody-elses.flv"
  target.write_bytes(b"not this library's file")
  source.unlink()
  os.symlink(target, source)
  require_refusal(
    OrphanQuarantineRefused,
    lambda: inventory.quarantine(candidate),
    "a symlinked candidate was quarantined",
  )
  require(target.is_file(), "a refused quarantine touched a link target")

  ##
  ## A destination somebody else already holds is never overwritten.
  ##
  collision_root = base / "collision"
  media = collision_root / "douyin" / "live" / "broadcaster"
  source = write_media(media, "orphan.flv")
  unused, inventory = build(collision_root)
  candidate = inventory.scan().candidates[0]
  destination = inventory.quarantine_destination_for(candidate)
  destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
  destination.write_bytes(b"an earlier quarantine of something else")
  require_refusal(
    OrphanQuarantineRefused,
    lambda: inventory.quarantine(candidate),
    "a quarantine collision overwrote an existing file",
  )
  require(
    destination.read_bytes() == b"an earlier quarantine of something else",
    "a refused quarantine altered the existing destination",
  )
  require(source.is_file(), "a refused quarantine removed the source")

  print("ok   runtime orphan quarantine race refusals")


##
## >>============ the half-finished move, and what it may claim ============>>
##
## Quarantine publishes twice - the media link, then the record beside it - and
## everything here is about the window between them. A refusal has to keep
## meaning "nothing was created", a partial completion has to be reachable and
## survivable, and a record that is present but not trustworthy must never be
## the thing that authorises removing somebody's recording.
##
def prove_partial_completion(root):
  base = root / "partial"

  def prepare(name):
    place = base / name
    media = place / "douyin" / "live" / "broadcaster"
    source = write_media(media, "orphan.flv")
    unused, inventory = build(place)
    return inventory, source, inventory.scan().candidates[0]

  def quarantine_root_of(place):
    return place / QUARANTINE_DIRECTORY_NAME

  ##
  ## The record never comes into existence before its bytes do.
  ##
  inventory, source, candidate = prepare("atomic")
  destination = inventory.quarantine_destination_for(candidate)
  opened = []
  real_open = os.open

  def watching_open(path, flags, *arguments, **options):
    opened.append((str(path), flags))
    return real_open(path, flags, *arguments, **options)

  os.open = watching_open
  try:
    inventory.quarantine(candidate)
  finally:
    os.open = real_open

  final = destination.name + ".json"
  writable = os.O_WRONLY | os.O_RDWR | os.O_CREAT
  require(
    any(path == final for path, unused_flags in opened),
    "an existing quarantine record was never looked for",
  )
  require(
    all(
      not (flags & writable)
      for path, flags in opened
      if path == final
    ),
    "the final quarantine record name was opened for writing",
  )
  require(
    any(path.endswith(".part") and flags & os.O_CREAT for path, flags in opened),
    "the quarantine record was not staged through an exclusive temporary",
  )
  leftovers = [
    item.name for item in quarantine_root_of(base / "atomic").iterdir()
    if ".part" in item.name
  ]
  require(not leftovers, "a record temporary survived publication: %s" % leftovers)

  ##
  ## A record that is present but empty - what a crash between creating a final
  ## name and writing it leaves - must stop the move with the source intact.
  ##
  for description, content in (
    ("empty", b""),
    ("truncated", b'{"schema_version":1,"sou'),
    (
      "conflicting",
      json.dumps(
        {
          "schema_version": 1,
          "source_relative_path": "douyin/live/somebody-else/other.flv",
          "quarantined_name": "whatever",
          "size": 1,
          "mtime_ns": 1,
          "quarantined_at": "2026-09-04T00:00:00.000+00:00",
        }
      ).encode("utf-8"),
    ),
  ):
    inventory, source, candidate = prepare("record-" + description)
    destination = inventory.quarantine_destination_for(candidate)
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    (destination.parent / (destination.name + ".json")).write_bytes(content)
    require_refusal(
      OrphanQuarantineIncomplete,
      lambda: inventory.quarantine(candidate),
      "a %s record did not stop the move" % description,
    )
    require(
      source.is_file(),
      "a %s record allowed the source to be unlinked" % description,
    )

  ##
  ## Interrupted after the media link, then retried. The retry must finish the
  ## same move rather than write a second copy under a new name.
  ##
  inventory, source, candidate = prepare("retry")
  real_unlink = os.unlink
  refusals = {"remaining": 1}

  def flaky_unlink(path, *arguments, **options):
    if str(path) == source.name and refusals["remaining"]:
      refusals["remaining"] -= 1
      raise PermissionError("read-only")
    return real_unlink(path, *arguments, **options)

  os.unlink = flaky_unlink
  try:
    require_refusal(
      OrphanQuarantineIncomplete,
      lambda: inventory.quarantine(candidate),
      "an interrupted move was not reported as incomplete",
    )
    require(source.is_file(), "an incomplete move lost the source")
    outcome = inventory.quarantine(candidate)
  finally:
    os.unlink = real_unlink

  require(outcome.quarantined is True, "the retry did not complete the move")
  require(not source.exists(), "the retry left the original in place")
  quarantine_root = quarantine_root_of(base / "retry")
  media = [item for item in quarantine_root.iterdir() if item.suffix != ".json"]
  records = list(quarantine_root.glob("*.json"))
  require(len(media) == 1, "the retry produced %d media copies" % len(media))
  require(len(records) == 1, "the retry produced %d records" % len(records))

  ##
  ## And a refusal still means nothing was created.
  ##
  inventory, source, candidate = prepare("refusal")
  references = References(paths=[str(source)])
  unused, refusing = build(base / "refusal", references=references)
  require_refusal(
    OrphanQuarantineRefused,
    lambda: refusing.quarantine(candidate),
    "a newly referenced recording was not refused",
  )
  require(
    not quarantine_root_of(base / "refusal").exists(),
    "a refusal created quarantine state",
  )

  print("ok   runtime orphan quarantine partial completion")


def main():
  captured = io.StringIO()
  stdout, stderr = sys.stdout, sys.stderr
  workspace = tempfile.mkdtemp(prefix="smsd-orphan-probe-")
  try:
    root = Path(workspace)
    sys.stdout = captured
    sys.stderr = captured
    try:
      inventory, orphan, referenced = prove_inventory(root)
      prove_bounded_scan(root)
      prove_quarantine(root, inventory, orphan, referenced)
      prove_races(root)
      prove_partial_completion(root)
    finally:
      sys.stdout, sys.stderr = stdout, stderr

    visible = captured.getvalue()
    print(visible, end="")
    for sentinel in (SECRET_OWNER, SECRET_TITLE, str(root), workspace):
      require(
        sentinel not in visible,
        "the orphan surface printed a secret or an absolute path",
      )
    for expected in (
      "ok   runtime orphan inventory authority and refusals",
      "ok   runtime orphan bounded resumable scan",
      "ok   runtime orphan quarantine atomic transition",
      "ok   runtime orphan quarantine race refusals",
      "ok   runtime orphan quarantine partial completion",
    ):
      require(expected in visible, "a required stage did not run: " + expected)
  finally:
    shutil.rmtree(workspace, ignore_errors=True)

  ##
  ## Printed last, and only after every property above held.
  ##
  print("ok   runtime recording orphan inventory quarantine")


if __name__ == "__main__":
  main()
