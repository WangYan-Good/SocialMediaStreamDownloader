#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


FORMAT_VERSION = 1
REQUIRED_ASSETS = ("database.sql", "downloads.tar", "manifest.json")
RESTORE_PROJECT_PATTERN = re.compile(r"^smsd-restore-test-[a-z0-9][a-z0-9-]{2,62}$")


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


def write_manifest(
  directory: Path,
  *,
  source_git_commit: str,
  source_image: str,
  source_project: str,
  database_name: str,
  schema_status: str,
) -> dict:
  directory = Path(directory)
  database = directory / "database.sql"
  downloads = directory / "downloads.tar"
  for asset in (database, downloads):
    if not asset.is_file():
      raise ValueError(f"backup asset is missing: {asset.name}")
    asset.chmod(0o600)
  status = parse_schema_status(schema_status)
  heads = status["heads"].split(",")
  manifest = {
    "format_version": FORMAT_VERSION,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "source_git_commit": source_git_commit,
    "source_image": source_image,
    "source_project": source_project,
    "database_name": database_name,
    "schema_status": status["state"],
    "schema_current": status["current"],
    "schema_heads": heads,
    "download_archive_sha256": file_sha256(downloads),
    "database_dump_sha256": file_sha256(database),
  }
  target = directory / "manifest.json"
  target.write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  target.chmod(0o600)
  return manifest


def write_checksums(directory: Path) -> None:
  directory = Path(directory)
  lines = []
  for name in REQUIRED_ASSETS:
    path = directory / name
    if not path.is_file():
      raise ValueError(f"backup asset is missing: {name}")
    lines.append(f"{file_sha256(path)}  {name}")
  target = directory / "SHA256SUMS"
  target.write_text("\n".join(lines) + "\n", encoding="utf-8")
  target.chmod(0o600)


def _read_checksums(directory: Path) -> dict[str, str]:
  target = directory / "SHA256SUMS"
  if not target.is_file():
    raise ValueError("backup asset is missing: SHA256SUMS")
  checksums = {}
  for line in target.read_text(encoding="utf-8").splitlines():
    pieces = line.split("  ", 1)
    if len(pieces) != 2 or not re.fullmatch(r"[0-9a-f]{64}", pieces[0]):
      raise ValueError("backup checksum file is invalid")
    name = pieces[1]
    if name not in REQUIRED_ASSETS or name in checksums:
      raise ValueError("backup checksum file is invalid")
    checksums[name] = pieces[0]
  if set(checksums) != set(REQUIRED_ASSETS):
    raise ValueError("backup checksum file is incomplete")
  return checksums


def verify_bundle(directory: Path) -> dict:
  directory = Path(directory)
  checksums = _read_checksums(directory)
  for name, expected in checksums.items():
    path = directory / name
    if not path.is_file():
      raise ValueError(f"backup asset is missing: {name}")
    if file_sha256(path) != expected:
      raise ValueError(f"backup checksum mismatch: {name}")
  try:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
  except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
    raise ValueError("backup manifest is invalid") from error
  if not isinstance(manifest, dict) or manifest.get("format_version") != FORMAT_VERSION:
    raise ValueError("backup manifest format is unsupported")
  required = {
    "created_at",
    "source_git_commit",
    "source_image",
    "source_project",
    "database_name",
    "schema_status",
    "schema_current",
    "schema_heads",
    "download_archive_sha256",
    "database_dump_sha256",
  }
  if not required.issubset(manifest):
    raise ValueError("backup manifest is incomplete")
  if manifest["database_dump_sha256"] != file_sha256(directory / "database.sql"):
    raise ValueError("backup checksum mismatch: database.sql")
  if manifest["download_archive_sha256"] != file_sha256(directory / "downloads.tar"):
    raise ValueError("backup checksum mismatch: downloads.tar")
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
  checksums = subparsers.add_parser("write-checksums")
  checksums.add_argument("directory", type=Path)
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
      )
    elif args.command == "write-checksums":
      write_checksums(args.directory)
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
