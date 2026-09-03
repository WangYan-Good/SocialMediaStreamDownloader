#!/usr/bin/env python3
"""Create and verify the identity record for one CI-tested image archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = 1
SHA1_PATTERN = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
IMAGE_ID_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
IMMUTABLE_REF_PATTERN = re.compile(r"[^\s@]+:[^\s@]+@sha256:[0-9a-f]{64}")
REGISTRY_DIGEST_PATTERN = re.compile(
  r"ghcr\.io/[a-z0-9][a-z0-9._/-]*@sha256:[0-9a-f]{64}"
)
##
## The floor a promoted artifact's runtime evidence may not fall below.
##
## Raised with every phase that adds a proof, so a manifest produced by an
## older workflow - or by a hand-edited one that quietly dropped a probe - is
## refused rather than promoted. P17 shipped 18; P18 adds the recording orphan
## inventory/quarantine proof and the persistence diagnostic redaction proof.
##
MINIMUM_RUNTIME_MARKERS = 20

REQUIRED_FIELDS = {
  "schema_version",
  "source_commit_sha",
  "source_tree_sha",
  "image_id",
  "image_archive_sha256",
  "requirements_sha256",
  "python_base_ref",
  "node_base_ref",
  "mysql_image_ref",
  "runtime_marker_count",
  "created_by_workflow",
}


def sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
  descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8", closefd=False) as stream:
      stream.write(serialized)
      stream.flush()
      os.fsync(stream.fileno())
  finally:
    os.close(descriptor)
  path.chmod(0o600)


def _validate_manifest_shape(manifest: dict[str, Any]) -> None:
  if manifest.get("schema_version") != SCHEMA_VERSION:
    raise ValueError("unsupported artifact manifest schema version")
  missing = sorted(REQUIRED_FIELDS.difference(manifest))
  if missing:
    raise ValueError("missing manifest field: " + ", ".join(missing))
  if set(manifest) != REQUIRED_FIELDS:
    raise ValueError("unknown artifact manifest field")
  if not SHA1_PATTERN.fullmatch(str(manifest["source_commit_sha"])):
    raise ValueError("malformed source_commit_sha")
  if not SHA1_PATTERN.fullmatch(str(manifest["source_tree_sha"])):
    raise ValueError("malformed source_tree_sha")
  if not IMAGE_ID_PATTERN.fullmatch(str(manifest["image_id"])):
    raise ValueError("malformed image_id")
  for field in ("image_archive_sha256", "requirements_sha256"):
    if not SHA256_PATTERN.fullmatch(str(manifest[field])):
      raise ValueError(f"malformed {field}")
  for field in ("python_base_ref", "node_base_ref", "mysql_image_ref"):
    if not IMMUTABLE_REF_PATTERN.fullmatch(str(manifest[field])):
      raise ValueError(f"malformed {field}")
  marker_count = manifest["runtime_marker_count"]
  if not isinstance(marker_count, int) or isinstance(marker_count, bool) or marker_count < MINIMUM_RUNTIME_MARKERS:
    raise ValueError(
      f"runtime_marker_count must be at least {MINIMUM_RUNTIME_MARKERS}"
    )
  workflow = manifest["created_by_workflow"]
  if not isinstance(workflow, str) or not workflow or len(workflow) > 100:
    raise ValueError("created_by_workflow is invalid")


def create_manifest(
  manifest_path: Path,
  *,
  archive_path: Path,
  requirements_path: Path,
  source_commit_sha: str,
  source_tree_sha: str,
  image_id: str,
  python_base_ref: str,
  node_base_ref: str,
  mysql_image_ref: str,
  runtime_marker_count: int,
  created_by_workflow: str,
) -> dict[str, Any]:
  manifest = {
    "schema_version": SCHEMA_VERSION,
    "source_commit_sha": source_commit_sha,
    "source_tree_sha": source_tree_sha,
    "image_id": image_id,
    "image_archive_sha256": sha256_file(archive_path),
    "requirements_sha256": sha256_file(requirements_path),
    "python_base_ref": python_base_ref,
    "node_base_ref": node_base_ref,
    "mysql_image_ref": mysql_image_ref,
    "runtime_marker_count": runtime_marker_count,
    "created_by_workflow": created_by_workflow,
  }
  _validate_manifest_shape(manifest)
  _write_private_json(manifest_path, manifest)
  return manifest


def load_manifest(path: Path) -> dict[str, Any]:
  try:
    manifest = json.loads(path.read_text(encoding="utf-8"))
  except (OSError, ValueError) as error:
    raise ValueError("artifact manifest is not valid JSON") from error
  if not isinstance(manifest, dict):
    raise ValueError("artifact manifest must be an object")
  _validate_manifest_shape(manifest)
  return manifest


def verify_manifest(
  manifest_path: Path,
  *,
  archive_path: Path,
  requirements_path: Path,
  expected_source_commit: str | None = None,
  expected_source_tree: str | None = None,
  loaded_image_id: str | None = None,
  revision_label: str | None = None,
  requirements_label: str | None = None,
) -> dict[str, Any]:
  manifest = load_manifest(manifest_path)
  if sha256_file(archive_path) != manifest["image_archive_sha256"]:
    raise ValueError("image archive SHA-256 mismatch")
  if sha256_file(requirements_path) != manifest["requirements_sha256"]:
    raise ValueError("requirements SHA-256 mismatch")
  if expected_source_commit is not None and expected_source_commit != manifest["source_commit_sha"]:
    raise ValueError("source commit mismatch")
  if expected_source_tree is not None and expected_source_tree != manifest["source_tree_sha"]:
    raise ValueError("source tree mismatch")
  if loaded_image_id is not None and loaded_image_id != manifest["image_id"]:
    raise ValueError("loaded image ID mismatch")
  if revision_label is not None and revision_label != manifest["source_commit_sha"]:
    raise ValueError("revision label mismatch")
  if requirements_label is not None and requirements_label != manifest["requirements_sha256"]:
    raise ValueError("requirements label mismatch")
  return manifest


def create_promotion_manifest(
  output_path: Path,
  *,
  artifact_manifest_path: Path,
  registry_digest: str,
  ci_run_id: str,
  ci_run_attempt: str,
) -> dict[str, Any]:
  artifact = load_manifest(artifact_manifest_path)
  if not REGISTRY_DIGEST_PATTERN.fullmatch(registry_digest):
    raise ValueError("registry digest is not a canonical lowercase GHCR reference")
  if not ci_run_id.isdigit() or not ci_run_attempt.isdigit():
    raise ValueError("CI run identity must be numeric")
  promotion = {
    "schema_version": SCHEMA_VERSION,
    "source_commit_sha": artifact["source_commit_sha"],
    "source_tree_sha": artifact["source_tree_sha"],
    "tested_image_id": artifact["image_id"],
    "registry_digest": registry_digest,
    "requirements_sha256": artifact["requirements_sha256"],
    "ci_run_id": ci_run_id,
    "ci_run_attempt": ci_run_attempt,
  }
  _write_private_json(output_path, promotion)
  return promotion


def _parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest="command", required=True)
  create = subparsers.add_parser("create")
  create.add_argument("manifest", type=Path)
  create.add_argument("--archive", required=True, type=Path)
  create.add_argument("--requirements", required=True, type=Path)
  create.add_argument("--source-commit", required=True)
  create.add_argument("--source-tree", required=True)
  create.add_argument("--image-id", required=True)
  create.add_argument("--python-base-ref", required=True)
  create.add_argument("--node-base-ref", required=True)
  create.add_argument("--mysql-image-ref", required=True)
  create.add_argument("--runtime-marker-count", required=True, type=int)
  create.add_argument("--created-by-workflow", required=True)

  verify = subparsers.add_parser("verify")
  verify.add_argument("manifest", type=Path)
  verify.add_argument("--archive", required=True, type=Path)
  verify.add_argument("--requirements", required=True, type=Path)
  verify.add_argument("--expected-source-commit")
  verify.add_argument("--expected-source-tree")
  verify.add_argument("--loaded-image-id")
  verify.add_argument("--revision-label")
  verify.add_argument("--requirements-label")

  field = subparsers.add_parser("field")
  field.add_argument("manifest", type=Path)
  field.add_argument("name", choices=sorted(REQUIRED_FIELDS))

  promotion = subparsers.add_parser("create-promotion")
  promotion.add_argument("output", type=Path)
  promotion.add_argument("--artifact-manifest", required=True, type=Path)
  promotion.add_argument("--registry-digest", required=True)
  promotion.add_argument("--ci-run-id", required=True)
  promotion.add_argument("--ci-run-attempt", required=True)
  return parser


def main(argv: list[str] | None = None) -> int:
  arguments = _parser().parse_args(argv)
  try:
    if arguments.command == "create":
      create_manifest(
        arguments.manifest,
        archive_path=arguments.archive,
        requirements_path=arguments.requirements,
        source_commit_sha=arguments.source_commit,
        source_tree_sha=arguments.source_tree,
        image_id=arguments.image_id,
        python_base_ref=arguments.python_base_ref,
        node_base_ref=arguments.node_base_ref,
        mysql_image_ref=arguments.mysql_image_ref,
        runtime_marker_count=arguments.runtime_marker_count,
        created_by_workflow=arguments.created_by_workflow,
      )
    elif arguments.command == "verify":
      verify_manifest(
        arguments.manifest,
        archive_path=arguments.archive,
        requirements_path=arguments.requirements,
        expected_source_commit=arguments.expected_source_commit,
        expected_source_tree=arguments.expected_source_tree,
        loaded_image_id=arguments.loaded_image_id,
        revision_label=arguments.revision_label,
        requirements_label=arguments.requirements_label,
      )
    elif arguments.command == "field":
      print(load_manifest(arguments.manifest)[arguments.name])
    else:
      create_promotion_manifest(
        arguments.output,
        artifact_manifest_path=arguments.artifact_manifest,
        registry_digest=arguments.registry_digest,
        ci_run_id=arguments.ci_run_id,
        ci_run_attempt=arguments.ci_run_attempt,
      )
  except ValueError as error:
    print(f"release artifact manifest failed: {error}", file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
