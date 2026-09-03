#!/usr/bin/env python3
"""Verify that a running production image exactly matches its hashed lock."""

from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable


BOOTSTRAP_EXCLUSIONS = frozenset({"pip"})
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def canonical_name(name: str) -> str:
  return re.sub(r"[-_.]+", "-", name).lower()


def parse_lock(path: Path) -> dict[str, str]:
  packages: dict[str, str] = {}
  current = ""
  entries: list[str] = []
  for raw in path.read_text(encoding="utf-8").splitlines():
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
      continue
    if raw[:1].isspace() or stripped.startswith("--hash="):
      current += " " + stripped.rstrip("\\").strip()
      continue
    if current:
      entries.append(current)
    current = stripped.rstrip("\\").strip()
  if current:
    entries.append(current)

  for entry in entries:
    token = entry.split()[0]
    match = re.fullmatch(
      r"([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==([^\s;]+)", token
    )
    if not match or not re.search(r"--hash=sha256:[0-9a-f]{64}(?:\s|$)", entry):
      raise ValueError("requirements lock contains a non-exact or unhashed entry")
    name = canonical_name(match.group(1))
    if name in packages:
      raise ValueError(f"duplicate locked package: {name}")
    packages[name] = match.group(2)
  if not packages:
    raise ValueError("requirements lock is empty")
  return packages


def _pip_check() -> None:
  completed = subprocess.run(
    [sys.executable, "-m", "pip", "check"],
    text=True,
    capture_output=True,
  )
  if completed.returncode != 0:
    raise ValueError("pip check failed")


def verify_dependency_identity(
  lock_path: Path,
  *,
  expected_lock_sha: str,
  version_reader: Callable[[str], str] = version,
  pip_check: Callable[[], None] = _pip_check,
) -> dict[str, str]:
  if not SHA256_PATTERN.fullmatch(expected_lock_sha):
    raise ValueError("expected lock SHA-256 is malformed")
  if sha256_file(lock_path) != expected_lock_sha:
    raise ValueError("lock SHA-256 mismatch")
  locked = parse_lock(lock_path)
  installed: dict[str, str] = {}
  for name, expected_version in locked.items():
    if name in BOOTSTRAP_EXCLUSIONS:
      continue
    try:
      actual_version = version_reader(name)
    except PackageNotFoundError as error:
      raise ValueError(f"missing locked package: {name}") from error
    if actual_version != expected_version:
      raise ValueError(
        f"installed version mismatch for {name}: expected {expected_version}, got {actual_version}"
      )
    installed[name] = actual_version
  pip_check()
  return installed


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--requirements", type=Path, default=Path("/app/requirements.txt"))
  parser.add_argument("--expected-lock-sha", required=True)
  arguments = parser.parse_args(argv)
  try:
    verify_dependency_identity(
      arguments.requirements,
      expected_lock_sha=arguments.expected_lock_sha,
    )
  except (OSError, ValueError) as error:
    print(f"runtime dependency identity failed: {error}", file=sys.stderr)
    return 1
  print("ok   runtime locked dependency identity")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
