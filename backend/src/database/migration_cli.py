import argparse
from collections.abc import Sequence
import sys

from backend.src.database.migration_service import (
  DatabaseUnavailable,
  MigrationFailed,
  MigrationService,
  RevisionStateError,
  SchemaMismatchError,
)


EXIT_OK = 0
EXIT_CONFIG = 2
EXIT_DATABASE_UNAVAILABLE = 3
EXIT_SCHEMA_MISMATCH = 4
EXIT_REVISION_STATE = 5
EXIT_MIGRATION_FAILED = 6


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description="smsd database schema migration")
  subparsers = parser.add_subparsers(dest="command", required=True)
  subparsers.add_parser("status")
  subparsers.add_parser("check")
  subparsers.add_parser("stamp")
  subparsers.add_parser("upgrade")
  downgrade = subparsers.add_parser("downgrade")
  downgrade.add_argument("revision")
  downgrade.add_argument("--confirm-database")
  revision = subparsers.add_parser("revision")
  revision.add_argument("message")
  return parser


def main(argv: Sequence[str] | None = None) -> int:
  try:
    arguments = build_parser().parse_args(argv)
    service = MigrationService()
    if arguments.command == "status":
      status = service.status()
      heads = ",".join(status.heads) or "none"
      print(
        f"state={status.classification} current={status.current or 'none'} heads={heads}"
      )
      return EXIT_OK if status.classification == "ready" else EXIT_REVISION_STATE
    if arguments.command == "check":
      report = service.check()
      if report.format_text():
        print(report.format_text())
      else:
        print("managed schema is compatible")
      return EXIT_OK if report.is_compatible else EXIT_SCHEMA_MISMATCH
    if arguments.command == "stamp":
      service.stamp()
    elif arguments.command == "upgrade":
      service.upgrade("head")
    elif arguments.command == "downgrade":
      service.downgrade(
        arguments.revision,
        confirm_database=arguments.confirm_database,
      )
    elif arguments.command == "revision":
      service.revision(arguments.message)
    print(f"{arguments.command} completed")
    return EXIT_OK
  except SchemaMismatchError as exc:
    print(exc.report.format_text(), file=sys.stderr)
    return EXIT_SCHEMA_MISMATCH
  except DatabaseUnavailable as exc:
    location = exc.safe_location()
    suffix = f" {location}" if location else ""
    print(f"database unavailable{suffix}", file=sys.stderr)
    return EXIT_DATABASE_UNAVAILABLE
  except RevisionStateError as exc:
    print(str(exc), file=sys.stderr)
    return EXIT_REVISION_STATE
  except MigrationFailed:
    print("migration failed", file=sys.stderr)
    return EXIT_MIGRATION_FAILED
  except (KeyError, TypeError, ValueError):
    print("invalid migration configuration", file=sys.stderr)
    return EXIT_CONFIG


if __name__ == "__main__":
  raise SystemExit(main())
