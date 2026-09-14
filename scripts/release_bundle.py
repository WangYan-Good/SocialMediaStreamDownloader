#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


##
## Bumped to 2 when a bundle began saying which topology produced it.
##
## Version 1 predates the field and was only ever written by the Compose path,
## so it is read as Compose rather than refused: a backup taken before this
## change is still a backup somebody may one day need.
##
FORMAT_VERSION = 2
SUPPORTED_FORMAT_VERSIONS = (1, 2)

##
## The two deployments, and the different media asset each one can actually
## produce.
##
## Compose keeps media in a named volume small enough to stream into a tar.
## Production's media is terabytes on a filesystem that could not hold a copy of
## it, so it is captured as a reflink snapshot and what travels here is the
## snapshot's *identity* - per-file path, size, mtime, device and inode - rather
## than its bytes. Same manifest, same checksum file, same isolated-restore
## rule; a different asset.
##
TOPOLOGY_COMPOSE = "compose"
TOPOLOGY_EXTERNAL = "external-host"

COMPOSE_ASSETS = ("database.sql", "downloads.tar", "manifest.json")
EXTERNAL_ASSETS = ("database.sql", "media-snapshot.json", "manifest.json")

ASSETS_BY_TOPOLOGY = {
  TOPOLOGY_COMPOSE: COMPOSE_ASSETS,
  TOPOLOGY_EXTERNAL: EXTERNAL_ASSETS,
}

##
## The media asset each topology records its checksum under. Named differently
## on purpose: a bundle that carried a tar's hash under the snapshot's key would
## verify against the wrong thing and say nothing about it.
##
MEDIA_ASSET_BY_TOPOLOGY = {
  TOPOLOGY_COMPOSE: ("downloads.tar", "download_archive_sha256"),
  TOPOLOGY_EXTERNAL: ("media-snapshot.json", "media_snapshot_sha256"),
}

##
## Kept as the Compose asset tuple it has always been, because the Compose
## scripts and their contract tests refer to it by name.
##
REQUIRED_ASSETS = COMPOSE_ASSETS

##
## What makes one file in a snapshot the file that was snapshotted.
##
## The same notion of identity the quarantine record uses: a name and a size are
## forgeable, and a device and an inode are not.
##
SNAPSHOT_IDENTITY_FIELDS = (
  "relative_path",
  "size",
  "mtime_ns",
  "device",
  "inode",
)

RESTORE_PROJECT_PATTERN = re.compile(r"^smsd-restore-test-[a-z0-9][a-z0-9-]{2,62}$")


def require_topology(topology: str) -> str:
  if topology not in ASSETS_BY_TOPOLOGY:
    raise ValueError("backup topology is unsupported")
  return topology


def file_sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def parse_schema_status(text: str) -> dict[str, str]:
  fields = {}
  for item in text.split():
    if "=" in item:
      key, value = item.split("=", 1)
      fields[key] = value
  if not all(fields.get(key) for key in ("state", "current", "heads")):
    raise ValueError("schema status is incomplete")
  return fields


def prepare_output(directory: Path) -> None:
  directory = Path(directory)
  if directory.exists():
    if not directory.is_dir() or any(directory.iterdir()):
      raise ValueError("backup output directory must be absent or empty")
  else:
    directory.mkdir(parents=True, mode=0o700)
  directory.chmod(0o700)


##
## Whether a snapshot document describes a set of files well enough to prove,
## later, that the snapshot is still the one that was taken.
##
## Checked here rather than in the script that writes it, because this is the
## thing a restore will be judged against and the judging happens on this side.
##
def validate_media_snapshot(document) -> dict:
  if not isinstance(document, dict):
    raise ValueError("media snapshot document is invalid")
  entries = document.get("entries")
  if not isinstance(entries, list):
    raise ValueError("media snapshot document has no entries")

  total_bytes = 0
  for entry in entries:
    if not isinstance(entry, dict):
      raise ValueError("media snapshot entry is invalid")
    for field in SNAPSHOT_IDENTITY_FIELDS:
      if field not in entry:
        raise ValueError(f"media snapshot entry is missing {field}")
    if not isinstance(entry["relative_path"], str) or not entry["relative_path"]:
      raise ValueError("media snapshot entry has no path")
    for field in ("size", "mtime_ns", "device", "inode"):
      if type(entry[field]) is not int or entry[field] < 0:
        raise ValueError(f"media snapshot entry has an invalid {field}")
    total_bytes += entry["size"]

  ##
  ## The totals are not decoration. They are the cheap check that the entry list
  ## was not truncated between being written and being read, which a per-entry
  ## check cannot notice.
  ##
  if document.get("entry_count") != len(entries):
    raise ValueError("media snapshot entry count disagrees with its entries")
  if document.get("total_bytes") != total_bytes:
    raise ValueError("media snapshot byte total disagrees with its entries")
  return document


def write_manifest(
  directory: Path,
  *,
  source_git_commit: str,
  source_image: str,
  source_project: str,
  database_name: str,
  schema_status: str,
  topology: str = TOPOLOGY_COMPOSE,
) -> dict:
  directory = Path(directory)
  require_topology(topology)
  media_name, media_key = MEDIA_ASSET_BY_TOPOLOGY[topology]
  database = directory / "database.sql"
  media = directory / media_name
  for asset in (database, media):
    if not asset.is_file():
      raise ValueError(f"backup asset is missing: {asset.name}")
    asset.chmod(0o600)
  if topology == TOPOLOGY_EXTERNAL:
    ##
    ## Refused at capture time rather than at restore time. A snapshot document
    ## that cannot prove identity is worth finding out about while the media it
    ## describes is still there.
    ##
    try:
      validate_media_snapshot(
        json.loads(media.read_text(encoding="utf-8"))
      )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
      raise ValueError("media snapshot document is invalid") from error
  status = parse_schema_status(schema_status)
  heads = status["heads"].split(",")
  manifest = {
    "format_version": FORMAT_VERSION,
    "topology": topology,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "source_git_commit": source_git_commit,
    "source_image": source_image,
    "source_project": source_project,
    "database_name": database_name,
    "schema_status": status["state"],
    "schema_current": status["current"],
    "schema_heads": heads,
    media_key: file_sha256(media),
    "database_dump_sha256": file_sha256(database),
  }
  target = directory / "manifest.json"
  target.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  target.chmod(0o600)
  return manifest


def write_checksums(directory: Path, topology: str = TOPOLOGY_COMPOSE) -> None:
  directory = Path(directory)
  require_topology(topology)
  lines = []
  for name in ASSETS_BY_TOPOLOGY[topology]:
    path = directory / name
    if not path.is_file():
      raise ValueError(f"backup asset is missing: {name}")
    lines.append(f"{file_sha256(path)}  {name}")
  target = directory / "SHA256SUMS"
  target.write_text("\n".join(lines) + "\n", encoding="utf-8")
  target.chmod(0o600)


def _read_checksums(directory: Path, assets: tuple) -> dict[str, str]:
  target = directory / "SHA256SUMS"
  if not target.is_file():
    raise ValueError("backup asset is missing: SHA256SUMS")
  checksums = {}
  for line in target.read_text(encoding="utf-8").splitlines():
    pieces = line.split("  ", 1)
    if len(pieces) != 2 or not re.fullmatch(r"[0-9a-f]{64}", pieces[0]):
      raise ValueError("backup checksum file is invalid")
    name = pieces[1]
    if name not in assets or name in checksums:
      raise ValueError("backup checksum file is invalid")
    checksums[name] = pieces[0]
  if set(checksums) != set(assets):
    raise ValueError("backup checksum file is incomplete")
  return checksums


##
## Which topology a bundle claims, read before anything is checked against it.
##
## The manifest has to be parsed before the checksums can be verified - the
## asset list depends on the answer - so this deliberately reads it without
## trusting it, and every later step re-derives from the validated result.
##
def _declared_topology(directory: Path) -> tuple[dict, str]:
  try:
    manifest = json.loads(
      (directory / "manifest.json").read_text(encoding="utf-8")
    )
  except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
    raise ValueError("backup manifest is invalid") from error
  if not isinstance(manifest, dict):
    raise ValueError("backup manifest is invalid")
  version = manifest.get("format_version")
  if version not in SUPPORTED_FORMAT_VERSIONS:
    raise ValueError("backup manifest format is unsupported")
  ##
  ## Version 1 predates the field and could only ever have been Compose, so it
  ## is *interpreted* rather than refused - a backup taken before this change is
  ## still a backup somebody may need.
  ##
  ## Every later version must say so itself. A current-format bundle with no
  ## topology is one this build did not write, and the answer is never to infer
  ## one from whatever the reading environment happens to be: that is how a
  ## Compose restore ends up pointed at an external bundle because it was run on
  ## a host that happens to use Compose.
  ##
  if version == 1:
    topology = manifest.get("topology", TOPOLOGY_COMPOSE)
  else:
    topology = manifest.get("topology")
  if topology not in ASSETS_BY_TOPOLOGY:
    raise ValueError("backup topology is unsupported")
  return manifest, topology


def verify_bundle(directory: Path) -> dict:
  directory = Path(directory)
  manifest, topology = _declared_topology(directory)
  assets = ASSETS_BY_TOPOLOGY[topology]
  media_name, media_key = MEDIA_ASSET_BY_TOPOLOGY[topology]

  checksums = _read_checksums(directory, assets)
  for name, expected in checksums.items():
    path = directory / name
    if not path.is_file():
      raise ValueError(f"backup asset is missing: {name}")
    if file_sha256(path) != expected:
      raise ValueError(f"backup checksum mismatch: {name}")

  required = {
    "created_at",
    "source_git_commit",
    "source_image",
    "source_project",
    "database_name",
    "schema_status",
    "schema_current",
    "schema_heads",
    media_key,
    "database_dump_sha256",
  }
  if not required.issubset(manifest):
    raise ValueError("backup manifest is incomplete")
  if manifest["database_dump_sha256"] != file_sha256(directory / "database.sql"):
    raise ValueError("backup checksum mismatch: database.sql")
  if manifest[media_key] != file_sha256(directory / media_name):
    raise ValueError(f"backup checksum mismatch: {media_name}")
  if topology == TOPOLOGY_EXTERNAL:
    ##
    ## The snapshot document is the media asset, so its internal consistency is
    ## part of verifying the bundle rather than a separate courtesy.
    ##
    try:
      validate_media_snapshot(
        json.loads((directory / media_name).read_text(encoding="utf-8"))
      )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
      raise ValueError("media snapshot document is invalid") from error
  ##
  ## Reported so a caller never has to re-derive it, and so a version 1 bundle
  ## answers the same question a version 2 one does.
  ##
  manifest["topology"] = topology
  return manifest


def validate_restore_project(project: str, *, source_project: str) -> None:
  if not RESTORE_PROJECT_PATTERN.fullmatch(project or ""):
    raise ValueError("restore project must be an explicit isolated test project")
  if project == source_project:
    raise ValueError("restore project must differ from the source project")


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description="validate SMSD release backup bundles")
  subparsers = parser.add_subparsers(dest="command", required=True)
  prepare = subparsers.add_parser("prepare-output")
  prepare.add_argument("directory", type=Path)
  manifest = subparsers.add_parser("write-manifest")
  manifest.add_argument("directory", type=Path)
  manifest.add_argument("--source-git-commit", required=True)
  manifest.add_argument("--source-image", required=True)
  manifest.add_argument("--source-project", required=True)
  manifest.add_argument("--database-name", required=True)
  manifest.add_argument("--schema-status-file", required=True, type=Path)
  manifest.add_argument(
    "--topology",
    choices=sorted(ASSETS_BY_TOPOLOGY),
    default=TOPOLOGY_COMPOSE,
  )
  checksums = subparsers.add_parser("write-checksums")
  checksums.add_argument("directory", type=Path)
  checksums.add_argument(
    "--topology",
    choices=sorted(ASSETS_BY_TOPOLOGY),
    default=TOPOLOGY_COMPOSE,
  )
  verify = subparsers.add_parser("verify")
  verify.add_argument("directory", type=Path)
  field = subparsers.add_parser("field")
  field.add_argument("directory", type=Path)
  field.add_argument("name")
  validate = subparsers.add_parser("validate-restore-project")
  validate.add_argument("project")
  validate.add_argument("--source-project", required=True)
  return parser


def main(argv=None) -> int:
  args = build_parser().parse_args(argv)
  try:
    if args.command == "prepare-output":
      prepare_output(args.directory)
    elif args.command == "write-manifest":
      write_manifest(
        args.directory,
        source_git_commit=args.source_git_commit,
        source_image=args.source_image,
        source_project=args.source_project,
        database_name=args.database_name,
        schema_status=args.schema_status_file.read_text(encoding="utf-8"),
        topology=args.topology,
      )
    elif args.command == "write-checksums":
      write_checksums(args.directory, args.topology)
    elif args.command == "verify":
      verify_bundle(args.directory)
    elif args.command == "field":
      manifest = verify_bundle(args.directory)
      value = manifest.get(args.name)
      if not isinstance(value, (str, int)):
        raise ValueError("manifest field is not scalar")
      print(value)
    elif args.command == "validate-restore-project":
      validate_restore_project(args.project, source_project=args.source_project)
  except (OSError, ValueError) as error:
    print(str(error), file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
