#!/usr/bin/env python3
"""Fail closed when release dependency or artifact inputs can float."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import NamedTuple


SHA256 = r"[0-9a-f]{64}"
COMMIT_SHA = r"[0-9a-f]{40}"
REQUIRED_JOB_NAMES = {
  "Python tests",
  "MySQL schema and migrations",
  "Frontend build and tests",
  "Docker build and runtime smoke",
}


class Issue(NamedTuple):
  code: str
  message: str

  def __str__(self) -> str:
    return f"{self.code}: {self.message}"


def _add(issues: list[Issue], code: str, message: str) -> None:
  issues.append(Issue(code, message))


def _read(root: Path, relative: str) -> str:
  path = root / relative
  if not path.is_file():
    return ""
  return path.read_text(encoding="utf-8")


def _requirement_entries(text: str) -> list[tuple[str, str]]:
  entries: list[tuple[str, str]] = []
  current = ""
  for raw in text.splitlines():
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
      continue
    if raw[:1].isspace() or stripped.startswith("--hash="):
      current += " " + stripped.rstrip("\\").strip()
      continue
    if current:
      entries.append((current.split()[0], current))
    current = stripped.rstrip("\\").strip()
  if current:
    entries.append((current.split()[0], current))
  return entries


def _job_blocks(workflow: str) -> dict[str, str]:
  lines = workflow.splitlines(keepends=True)
  try:
    jobs_start = next(index for index, line in enumerate(lines) if line == "jobs:\n")
  except StopIteration:
    return {}
  starts: list[tuple[str, int]] = []
  for index in range(jobs_start + 1, len(lines)):
    match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", lines[index])
    if match:
      starts.append((match.group(1), index))
  blocks: dict[str, str] = {}
  for position, (name, start) in enumerate(starts):
    end = starts[position + 1][1] if position + 1 < len(starts) else len(lines)
    blocks[name] = "".join(lines[start:end])
  return blocks


def _job_name(block: str) -> str | None:
  match = re.search(r"^    name:\s*(.+?)\s*$", block, re.MULTILINE)
  return match.group(1).strip("'\"") if match else None


def check_repository(root: Path) -> list[Issue]:
  root = root.resolve()
  issues: list[Issue] = []
  requirements_in = _read(root, "requirements.in")
  requirements = _read(root, "requirements.txt")
  lock_generator = _read(root, "scripts/compile_requirements.sh")
  dockerfile = _read(root, "Dockerfile")
  workflow = _read(root, ".github/workflows/ci.yml")
  compose = _read(root, "docker-compose.yml")
  run_server = _read(root, "run-server.sh")
  deploy = _read(root, "scripts/release_deploy.sh")

  entries = _requirement_entries(requirements)
  if not requirements_in or not entries:
    _add(issues, "python-lock", "requirements.in and a generated lock are required")
  else:
    for token, entry in entries:
      if token.startswith(("-e", "git+", "http://", "https://")):
        _add(issues, "python-lock", f"untrusted dependency source: {token}")
        break
      if not re.fullmatch(r"[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?==[^\s;]+", token):
        _add(issues, "python-lock", f"dependency is not exact: {token}")
        break
      if not re.search(rf"--hash=sha256:{SHA256}(?:\s|$)", entry):
        _add(issues, "python-lock", f"dependency has no SHA-256 hash: {token}")
        break
    if re.search(r"(^|\s)(?:-e|--editable|git\+|https?://)", requirements, re.MULTILINE):
      _add(issues, "python-lock", "editable or arbitrary remote dependency is forbidden")
  if (
    'PIP_TOOLS_VERSION="7.6.1"' not in lock_generator
    or "--generate-hashes" not in lock_generator
    or "--resolver=backtracking" not in lock_generator
    or not re.search(rf'PYTHON_BASE="python:[^"@]+@sha256:{SHA256}"', lock_generator)
  ):
    _add(issues, "python-lock", "lock generator version and immutable environment are not fixed")

  install_sources = {
    "Dockerfile": dockerfile,
    ".github/workflows/ci.yml": workflow,
    "run-server.sh": run_server,
  }
  install_problem = False
  for name, source in install_sources.items():
    flattened = re.sub(r"\\\n\s*", " ", source)
    commands = re.findall(r"(?:python\s+-m\s+)?pip\s+install[^\n;&]*", flattened)
    if name == "run-server.sh":
      commands = [command for command in commands if command.startswith("python -m pip")]
    if not commands or any(
      (
        "requirements.txt" not in command
        and "$REQUIREMENTS_FILE" not in command
      )
      or "--require-hashes" not in command
      for command in commands
    ):
      install_problem = True
    if any("requirements.in" in command for command in commands):
      install_problem = True
  if install_problem:
    _add(issues, "python-install", "all production and CI installs must require the hashed lock")

  critical_install_text = "\n".join(install_sources.values())
  if re.search(r"pip\s+install[^\n]*(?:--upgrade|-U)\s+pip", critical_install_text):
    _add(issues, "pip-bootstrap", "floating pip bootstrap is forbidden")

  from_lines = re.findall(r"^FROM\s+(\S+)\s+AS\s+(\S+)", dockerfile, re.MULTILINE | re.IGNORECASE)
  stages = {stage.lower(): image for image, stage in from_lines}
  python_pattern = re.compile(rf"^python:\d+\.\d+\.\d+-slim-[a-z0-9]+@sha256:{SHA256}$")
  builder = stages.get("builder", "")
  runtime = stages.get("runtime", "")
  if not python_pattern.fullmatch(builder) or builder != runtime:
    _add(issues, "python-base", "Python builder/runtime must share one exact immutable base")
  node = stages.get("frontend-builder", "")
  node_match = re.fullmatch(rf"node:(\d+\.\d+\.\d+)-[a-z0-9-]+@sha256:{SHA256}", node)
  if not node_match:
    _add(issues, "node-base", "Node builder must use an exact immutable base")

  compose_mysql = re.search(r"^\s{4}image:\s*[\"']?(mysql:[^\s\"']+)", compose, re.MULTILINE)
  mysql_ref = compose_mysql.group(1) if compose_mysql else ""
  if (
    not re.fullmatch(rf"mysql:\d+\.\d+\.\d+@sha256:{SHA256}", mysql_ref)
    or workflow.count(mysql_ref) < 1
    or mysql_ref not in deploy
  ):
    _add(issues, "mysql-image", "Compose and CI must share one exact immutable MySQL image")

  snapshot = _read(root, "docker/debian-snapshot.sources")
  apt_config = _read(root, "docker/apt-snapshot.conf")
  snapshot_times = re.findall(r"snapshot\.debian\.org/archive/(?:debian|debian-security)/(\d{8}T\d{6}Z)", snapshot)
  apt_blocks = re.findall(
    r"apt-get\s+install\s+-y\s+--no-install-recommends\s+(.*?)(?:&&|$)",
    dockerfile,
    re.DOTALL,
  )
  apt_exact = bool(apt_blocks)
  for block in apt_blocks:
    cleaned = re.sub(r"\\\s*\n", " ", block)
    tokens = [token for token in cleaned.split() if not token.startswith("#")]
    requested = [token for token in tokens if not token.startswith("-")]
    if not requested or any("=" not in token for token in requested):
      apt_exact = False
  if (
    len(snapshot_times) != 2
    or len(set(snapshot_times)) != 1
    or "deb.debian.org" in snapshot
    or "Check-Valid-Until \"false\"" not in apt_config
    or dockerfile.count("docker/debian-snapshot.sources") < 1
    or not apt_exact
  ):
    _add(issues, "apt-inputs", "apt must use one fixed snapshot and exact requested versions")

  actions = re.findall(r"uses:\s*([^@\s]+)@([^\s#]+)([^\n]*)", workflow)
  if not actions or any(
    not re.fullmatch(COMMIT_SHA, revision) or not re.search(r"#\s*v\d", suffix)
    for _, revision, suffix in actions
  ):
    _add(issues, "action-pins", "every release-critical action must use a documented full commit SHA")

  package_lock = root / "frontend/app/package-lock.json"
  frontend_ok = "npm ci" in dockerfile and "npm ci" in workflow
  if package_lock.is_file():
    try:
      lock = json.loads(package_lock.read_text(encoding="utf-8"))
      packages = lock.get("packages", {})
      frontend_ok = frontend_ok and lock.get("lockfileVersion") == 3
      frontend_ok = frontend_ok and all(
        data.get("link") or all(key in data for key in ("version", "resolved", "integrity"))
        for name, data in packages.items()
        if name
      )
    except (ValueError, OSError):
      frontend_ok = False
  else:
    frontend_ok = False
  if node_match:
    frontend_ok = frontend_ok and f"node-version: '{node_match.group(1)}'" in workflow
  if not frontend_ok:
    _add(issues, "frontend-lock", "frontend builders and CI must consume the complete npm lock")

  digest_ref = rf"ghcr\.io/[a-z0-9][a-z0-9._/-]*@sha256:{SHA256}"
  if (
    not deploy
    or "--no-build" not in deploy
    or re.search(r"docker\s+(?:build|compose\s+build)", deploy)
    or digest_ref not in deploy
  ):
    _add(issues, "release-deploy", "production deploy must accept only GHCR digests and disable builds")

  blocks = _job_blocks(workflow)
  promotion = blocks.get("publish_tested_image", "")
  if not promotion or re.search(r"docker\s+(?:build|buildx\s+build)", promotion):
    _add(issues, "promotion-rebuild", "promotion must load, never rebuild, the tested image")
  if "github.event_name == 'push'" not in promotion or "github.ref == 'refs/heads/develop'" not in promotion:
    _add(issues, "promotion-scope", "promotion must be limited to develop pushes")
  needs_match = re.search(r"^    needs:\s*\[([^]]+)\]", promotion, re.MULTILINE)
  needs = {item.strip() for item in needs_match.group(1).split(",")} if needs_match else set()
  if needs != {"backend", "mysql", "frontend", "image"}:
    _add(issues, "promotion-needs", "promotion must depend explicitly on all four verification jobs")
  package_write_blocks = [name for name, block in blocks.items() if re.search(r"^      packages:\s*write\s*$", block, re.MULTILINE)]
  if package_write_blocks != ["publish_tested_image"]:
    _add(issues, "promotion-permissions", "packages: write must exist only on the promotion job")

  first_verify = promotion.find("release_artifact_manifest.py verify")
  load_at = promotion.find("docker load --input")
  second_verify = promotion.find("release_artifact_manifest.py verify", first_verify + 1)
  push_at = promotion.find("docker push")
  identity_tokens = {
    '--archive "$ARCHIVE"': 2,
    '--requirements requirements.txt': 2,
    '--expected-source-commit "$GITHUB_SHA"': 2,
    '--expected-source-tree "$SOURCE_TREE"': 2,
    '--loaded-image-id "$LOADED_IMAGE_ID"': 1,
    '--revision-label "$REVISION_LABEL"': 1,
    '--requirements-label "$REQUIREMENTS_LABEL"': 1,
    'test "$PULLED_IMAGE_ID" = "$TESTED_IMAGE_ID"': 1,
  }
  if (
    min(first_verify, load_at, second_verify, push_at) < 0
    or not (first_verify < load_at < second_verify < push_at)
    or any(promotion.count(token) < count for token, count in identity_tokens.items())
  ):
    _add(issues, "promotion-identity", "promotion must verify archive/source before load and image identity before push")

  names = {_job_name(block) for block in blocks.values()}
  if not REQUIRED_JOB_NAMES.issubset(names):
    _add(issues, "required-ci-names", "the four protected job names changed")

  if promotion:
    image_block = blocks.get("image", "")
    save_at = image_block.find("docker save smsd:ci")
    required_before_export = (
      "ok   runtime locked dependency identity",
      "ok   runtime platform redirect trust boundary",
      "ok   runtime secure compose deployment baseline",
      "ok   runtime release backup restore drill",
    )
    upload_at = image_block.find("actions/upload-artifact@")
    develop_scope = "if: github.event_name == 'push' && github.ref == 'refs/heads/develop'"
    if (
      save_at < 0
      or upload_at < save_at
      or image_block.count(develop_scope) < 2
      or any(image_block.rfind(marker, 0, save_at) < 0 for marker in required_before_export)
    ):
      _add(issues, "artifact-order", "tested image export must follow every runtime and restore proof")
  else:
    _add(issues, "artifact-order", "tested image export and promotion jobs are absent")

  return issues


def main(argv: list[str] | None = None) -> int:
  arguments = list(sys.argv[1:] if argv is None else argv)
  root = Path(arguments[0]) if arguments else Path(__file__).resolve().parents[1]
  issues = check_repository(root)
  if issues:
    for issue in issues:
      print(f"FAIL {issue}", file=sys.stderr)
    return 1
  print("ok   release reproducibility inputs are immutable")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
