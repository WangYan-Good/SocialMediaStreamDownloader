#!/usr/bin/env python3
import argparse
from pathlib import Path
import subprocess
import sys


GITIGNORE_CAPTURE_RULE = "/api/douyin/*.json"
DOCKERIGNORE_CAPTURE_RULE = "/api/douyin/"
CAPTURE_PREFIX = "api/douyin/"


def _policy_lines(path: Path) -> list[str]:
  try:
    source = path.read_text(encoding="utf-8")
  except OSError:
    return []
  return [
    line.strip()
    for line in source.splitlines()
    if line.strip() and not line.lstrip().startswith("#")
  ]


def _has_closed_rule(path: Path, required_rule: str) -> bool:
  lines = _policy_lines(path)
  if required_rule not in lines:
    return False
  required_index = max(
    index for index, line in enumerate(lines) if line == required_rule
  )
  return not any(
    line.startswith("!") and "api/douyin" in line
    for line in lines[required_index + 1 :]
  )


def _tracked_paths(repository_root: Path) -> list[str]:
  completed = subprocess.run(
    [
      "git",
      "-C",
      str(repository_root),
      "ls-files",
      "-z",
      "--",
      "api/douyin/*.json",
    ],
    check=True,
    stdout=subprocess.PIPE,
  )
  tracked = [
    item.decode("utf-8")
    for item in completed.stdout.split(b"\0")
    if item
  ]
  # A reviewable, uncommitted deletion is already absent from the candidate
  # source tree. CI always runs from a clean checkout, where every tracked path
  # exists, so a force-added capture remains a hard failure there.
  return [
    path
    for path in tracked
    if (repository_root / path).exists()
    or (repository_root / path).is_symlink()
  ]


def check_repository_hygiene(
  repository_root: Path, *, tracked_paths: list[str] | None = None
) -> list[str]:
  repository_root = Path(repository_root)
  if tracked_paths is None:
    tracked_paths = _tracked_paths(repository_root)
  issues = []
  for path in tracked_paths:
    normalized = path.replace("\\", "/")
    if normalized.startswith(CAPTURE_PREFIX) and normalized.endswith(".json"):
      issues.append(f"tracked upstream response capture: {normalized}")
  if not _has_closed_rule(
    repository_root / ".gitignore", GITIGNORE_CAPTURE_RULE
  ):
    issues.append(".gitignore does not protect upstream response captures")
  if not _has_closed_rule(
    repository_root / ".dockerignore", DOCKERIGNORE_CAPTURE_RULE
  ):
    issues.append(".dockerignore does not protect the capture directory")
  return issues


def check_image_hygiene(image_root: Path) -> list[str]:
  capture_directory = Path(image_root) / "api" / "douyin"
  if capture_directory.is_dir() and any(capture_directory.glob("*.json")):
    return ["production image contains upstream response capture"]
  return []


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="check release artifacts for upstream response captures"
  )
  parser.add_argument(
    "--repository-root",
    type=Path,
    default=Path(__file__).resolve().parents[1],
  )
  parser.add_argument("--image-root", type=Path)
  return parser


def main(argv=None) -> int:
  args = build_parser().parse_args(argv)
  try:
    if args.image_root is None:
      issues = check_repository_hygiene(args.repository_root)
    else:
      issues = check_image_hygiene(args.image_root)
  except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as error:
    print(f"release artifact hygiene check could not run: {type(error).__name__}", file=sys.stderr)
    return 1
  if issues:
    for issue in issues:
      print(f"FAIL: {issue}", file=sys.stderr)
    return 1
  print("release artifact hygiene check passed")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
