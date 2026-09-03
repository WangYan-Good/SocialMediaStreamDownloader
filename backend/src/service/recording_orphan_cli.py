##
## The operator's way in, and the only one.
##
## Deliberately a command rather than an endpoint. Everything below either
## reports internal storage state or moves media, and neither belongs on an
## HTTP surface: a browser API would need its own authorization story, would put
## a filesystem walk on a request path, and would make a destructive action
## something a session could be tricked into performing. P18 adds no route.
##
## Two commands, mirroring the two halves of the contract:
##
##   scan        - answer what is there. Reads nothing else, changes nothing.
##   quarantine  - set one named file aside, and only with ``--confirm``.
##
## Everything printed is root-relative. An operator running this frequently
## captures its output into a ticket or a paste, and the deployment's absolute
## filesystem layout, its database location and its credentials have no reason
## to travel with it.
##
import argparse
from collections.abc import Sequence
import sys

from backend.src.database.schema_guard import require_database_write_ready
from backend.src.database.table.recording_record import RecordingRecordTable
from backend.src.library.baselib import get_dict_attr
from backend.src.library.configlib import load_config
from backend.src.service.recording_orphan import (
  MAX_ORPHAN_CANDIDATES,
  MAX_ORPHAN_SCAN_ENTRIES,
  MAX_REFERENCED_RECORDINGS,
  OrphanInventoryUnavailable,
  OrphanQuarantineRefused,
  RecordingOrphanInventory,
)
from backend.src.service.recording_recovery_journal import RecordingRecoveryJournal


EXIT_OK = 0
EXIT_USAGE = 1
EXIT_CONFIG = 2
EXIT_UNAVAILABLE = 3
EXIT_REFUSED = 4


##
## The database side of the claim authority.
##
## A thin adapter rather than a method on the table, so the inventory service
## keeps knowing nothing about MySQL - which is what lets its tests plant a
## refusing repository and its source stay free of any column that could name
## an owner.
##
## One more row than the bound is requested on purpose: the inventory refuses
## when it sees more than it can hold, and it can only see that if the read was
## allowed to exceed it by one.
##
class RecordingReferenceRepository:
  def __init__(self, table):
    self._table = table

  def referenced_output_paths(self):
    return self._table.referenced_output_paths(MAX_REFERENCED_RECORDINGS + 1)


##
## Build the inventory against the deployment's real configuration.
##
## The schema guard is consulted before anything is read. A database whose
## managed schema is not the one this build expects cannot be trusted to answer
## "which recordings exist", and an inventory built on a wrong answer would
## report catalogued recordings as orphans.
##
def build_inventory(config_loader=load_config, table_factory=RecordingRecordTable):
  settings = config_loader()
  if get_dict_attr(settings, "$.database.enable") is not True:
    raise OrphanInventoryUnavailable(
      "recording orphan inventory requires the database"
    )
  require_database_write_ready()
  table = table_factory(
    host=get_dict_attr(settings, "$.database.host"),
    user=get_dict_attr(settings, "$.database.username"),
    passwd=get_dict_attr(settings, "$.database.password"),
    database=get_dict_attr(settings, "$.database.name"),
  )
  return RecordingOrphanInventory(
    journal=RecordingRecoveryJournal(config_loader=lambda: settings),
    references=RecordingReferenceRepository(table),
    config_loader=lambda: settings,
  )


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="smsd recording orphan inventory and quarantine",
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  scan = subparsers.add_parser(
    "scan", help="list durable recordings that nothing claims"
  )
  scan.add_argument("--limit", type=int, default=MAX_ORPHAN_CANDIDATES)
  scan.add_argument(
    "--after",
    default=None,
    help="resume after this root-relative path",
  )

  quarantine = subparsers.add_parser(
    "quarantine", help="set one named orphan aside"
  )
  quarantine.add_argument("path", help="the root-relative path from scan")
  ##
  ## Two flags rather than one, and neither defaults to acting. A command that
  ## moved media when run with no options would eventually be run with no
  ## options by somebody exploring.
  ##
  quarantine.add_argument("--dry-run", action="store_true")
  quarantine.add_argument("--confirm", action="store_true")
  return parser


def _scan(inventory, arguments, out) -> int:
  scan = inventory.scan(limit=arguments.limit, after=arguments.after)
  for candidate in scan.candidates:
    ##
    ## Root-relative path and size only. Enough to recognise a recording and to
    ## hand back to ``quarantine``; not enough to describe the host.
    ##
    print(
      "orphan {} bytes={}".format(candidate.relative_path, candidate.size),
      file=out,
    )
  print(
    "scanned={} candidates={} truncated={}".format(
      scan.scanned, len(scan.candidates), "true" if scan.truncated else "false"
    ),
    file=out,
  )
  return EXIT_OK


##
## The named path, as this run actually observed it, or ``None``.
##
## One scan, asking for everything, rather than the page size ``scan`` reports
## by default. A file an operator can list but never quarantine would be a
## command that silently does not work for the case it exists for, and paging
## to reach it would re-walk the whole tree once per page.
##
## Asking for everything costs nothing extra: ``scan`` collects the complete
## candidate set before it applies a limit, and that set is already capped by
## the walk's own entry bound. The limit exists to keep a *report* readable,
## not to keep the scan small.
##
def _find_candidate(inventory, path):
  scan = inventory.scan(limit=MAX_ORPHAN_SCAN_ENTRIES)
  for candidate in scan.candidates:
    if candidate.relative_path == path:
      return candidate
  return None


def _quarantine(inventory, arguments, out) -> int:
  if not arguments.dry_run and not arguments.confirm:
    print(
      "quarantine moves media and requires --confirm (or --dry-run)", file=out
    )
    return EXIT_USAGE

  ##
  ## Found through a scan rather than constructed from the argument, so the
  ## file being moved is one this run just proved unclaimed - and so the
  ## fingerprint it is rechecked against is one this run actually observed.
  ## A candidate assembled from a command line would be an operator's
  ## description of a file rather than an observation of one.
  ##
  wanted = _find_candidate(inventory, arguments.path)
  if wanted is None:
    print("no current orphan candidate names that path", file=out)
    return EXIT_REFUSED

  outcome = inventory.quarantine(wanted, dry_run=arguments.dry_run)
  print(
    "{} {} -> {}".format(
      "would quarantine" if arguments.dry_run else "quarantined",
      outcome.relative_path,
      outcome.destination_name,
    ),
    file=out,
  )
  return EXIT_OK


def main(argv: Sequence[str] | None = None, *, inventory_factory=build_inventory,
         out=sys.stdout) -> int:
  arguments = build_parser().parse_args(argv)
  try:
    inventory = inventory_factory()
    if arguments.command == "scan":
      return _scan(inventory, arguments, out)
    return _quarantine(inventory, arguments, out)
  except OrphanQuarantineRefused as e:
    ##
    ## The class and this module's own sentence, never the underlying message.
    ## A driver error or an OS error carries a path, a host or a statement.
    ##
    print("quarantine refused: {}".format(type(e).__name__), file=out)
    return EXIT_REFUSED
  except OrphanInventoryUnavailable as e:
    print("orphan inventory unavailable: {}".format(type(e).__name__), file=out)
    return EXIT_UNAVAILABLE
  except (KeyError, TypeError, ValueError):
    print("invalid recording orphan configuration", file=out)
    return EXIT_CONFIG


__all__ = [
  "EXIT_CONFIG",
  "EXIT_OK",
  "EXIT_REFUSED",
  "EXIT_UNAVAILABLE",
  "EXIT_USAGE",
  "RecordingReferenceRepository",
  "build_inventory",
  "build_parser",
  "main",
]
