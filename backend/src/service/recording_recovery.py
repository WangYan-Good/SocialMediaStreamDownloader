##
## Turning the notes a crash left behind into the rows they were about to be.
##
## Phase 11B made the handoff durable and stopped there.  A recording whose
## media reached the disk publishes a note *before* the insert, so a process
## that dies in between leaves a complete description of a recording nobody
## catalogued.  Nothing ever read those notes back, which meant the gap this
## whole line of work exists to close - media survives, the library cannot see
## it - was merely recorded rather than repaired.
##
## This is the repair, and it is deliberately small: discover the notes that
## are there, prove the media each one names still exists, hand the *same*
## persistence intent to the *same* repository the ordinary path uses, and only
## then retire the note.
##
## Why it is not part of ``LiveRecordingTaskService``: that service persists a
## recording this process just made, and it does so with everything still in
## hand.  This one persists a recording a *dead* process made, with nothing but
## a note.  Two different lifetimes, two different failure modes, and folding
## them together would mean a startup path threading through a live-recording
## service and a recording path carrying reconciliation state it never uses.
##
## What it is not allowed to become:
##
##   - a media scanner.  The only trusted recovery input is a note this server
##     published.  Walking the download directory and guessing an owner, a room
##     or a user from a filename would attach real media to the wrong account,
##     and there is no filename convention that could ever prove otherwise.
##   - a second persistence path.  It never calls ``prepare``, never fabricates
##     a download result, and never re-normalises a field.  The note carries the
##     canonical intent; re-deriving it here would be a second copy of the rules
##     that would eventually disagree with the first.
##   - a second idempotency rule.  It never looks a key up before inserting.
##     The database's unique constraint is the authority, and Phase 11B-0's
##     create-or-get is reached through the ordinary ``record_prepared`` call.
##
## Every failure below has one shape: no database mutation, the note stays, the
## run carries on to the next note.  A note is evidence, and nothing here
## destroys evidence it could not act on - there is no quarantine, no rename and
## no delete-on-corrupt.
##
from dataclasses import dataclass

from backend.src.database.table.recording_record import RecordingRecoveryConflict
from backend.src.library.loglib import get_logger
from backend.src.service.media_asset import open_regular_file_within_root
from backend.src.service.recording_recovery_journal import (
  MAX_RECOVERY_JOURNALS_PER_RUN,
  RecordingJournalCorrupt,
  RecordingJournalScanOverflow,
  RecordingJournalUnavailable,
  RecordingJournalUnsupportedVersion,
  resolve_storage_root,
)
from backend.src.service.recording_resource import (
  RecordingPersistenceUnavailable,
)


##
## What one run did.
##
## For tests and the log, and nothing else.  No route reports this, no browser
## sees it, and no operator API returns it: a count of unrecovered recordings
## describes this server's internal state and is nobody's business over HTTP.
##
## ``truncated`` means a backlog larger than one run's bound is present and the
## remainder is still on disk, untouched, waiting for the next restart.
##
@dataclass(frozen=True)
class ReconciliationSummary:
  discovered: int = 0
  attempted: int = 0
  recovered: int = 0
  retained: int = 0
  missing: int = 0
  conflicted: int = 0
  corrupt: int = 0
  deferred: int = 0
  truncated: bool = False


class RecordingRecoveryReconciler:
  """Replay the pending recovery notes once, and durably retire the ones that land."""

  def __init__(self, *, journal, recording_service, config_loader):
    ##
    ## All three injected, none defaulted.  The application already owns a
    ## journal and a recording service, and constructing a second of either
    ## here is the exact mistake #157 shipped in the other direction: two
    ## instances that disagree about which notes exist, or which write through
    ## a repository the rest of the application is not using.
    ##
    ## ``config_loader`` is the application's own snapshot - the same callable
    ## the journal and the resource service were given - so the root a note was
    ## judged against when it was written is the root its media is judged
    ## against now.
    ##
    self._journal = journal
    self._recording_service = recording_service
    self._config_loader = config_loader

  ##
  ## The media gate.
  ##
  ## ``load`` has already proved everything that can be proved about the note:
  ## its schema, that it claims its own key, the shape of every field, and that
  ## its output path is inside the configured storage root.  It cannot prove the
  ## one fact this replay depends on - that the recording is still there.  A
  ## note is durable and a file is not.
  ##
  ## Delegated whole to the media boundary: containment, the descriptor walk
  ## that refuses a link at any level, and the regular-file check all live there
  ## already, and a second implementation of any of them would be a second
  ## answer to the same question.
  ##
  ## Validation only.  Nothing is read, hashed, probed or modified - a startup
  ## that hashed every pending recording would read gigabytes before serving a
  ## request - and ``intent.output_path`` is left exactly as journalled, so the
  ## row still records the path the recorder actually wrote.
  ##
  @staticmethod
  def _media_survives(root, output_path) -> bool:
    opened = open_regular_file_within_root(root, output_path)
    if opened is None:
      return False
    stream, info = opened
    try:
      ##
      ## A note says a recording completed. A zero-byte file is not one - it is
      ## a reservation, a truncated write, or a placeholder somebody left - and
      ## cataloguing it would advertise a playable resource that is not there.
      ##
      return info.st_size > 0
    finally:
      stream.close()

  def reconcile_once(self) -> ReconciliationSummary:
    """Replay every pending note once; never raise into the caller's startup."""
    try:
      root = resolve_storage_root(self._config_loader())
      pending = self._journal.scan_pending_keys(
        limit=MAX_RECOVERY_JOURNALS_PER_RUN
      )
    except RecordingJournalScanOverflow as e:
      ##
      ## A directory larger than the fixed scan-work budget is an explicit
      ## safe degraded state. No partial prefix is replayed: doing so would
      ## make attacker-controlled enumeration order choose database work.
      ##
      get_logger().error(
        "recording recovery deferred: journal scan overflow ({})".format(
          type(e).__name__
        )
      )
      return ReconciliationSummary()
    except RecordingJournalUnavailable as e:
      ##
      ## No usable journal directory - unconfigured storage, a link where the
      ## directory should be, a root that cannot be opened as one. Recovery is
      ## unavailable; the server is not.
      ##
      get_logger().error(
        "recording recovery could not read its journal directory ({}: {})".format(
          type(e).__name__, e
        )
      )
      return ReconciliationSummary()

    counts = {
      "attempted": 0,
      "recovered": 0,
      "retained": 0,
      "missing": 0,
      "conflicted": 0,
      "corrupt": 0,
      "deferred": 0,
    }
    keys = pending.keys

    for position, key in enumerate(keys):
      counts["attempted"] += 1
      try:
        intent = self._journal.load(key)
      except (RecordingJournalCorrupt, RecordingJournalUnsupportedVersion) as e:
        ##
        ## The storage is fine and the note is not readable by this build. It
        ## stays where it is: an operator can look at it, and a later build may
        ## understand it. One bad note must not stop the good ones after it.
        ##
        counts["corrupt"] += 1
        counts["retained"] += 1
        self._log_refusal(key, e)
        continue
      except Exception as e:
        counts["retained"] += 1
        self._log_refusal(key, e)
        continue

      if intent is None:
        ##
        ## Gone between the scan and the load. Two processes starting together
        ## both scan, and one acknowledges before the other reads - that is the
        ## protocol working, not a fault, and there is nothing left to retain.
        ##
        continue

      if not self._media_survives(root, intent.output_path):
        counts["missing"] += 1
        counts["retained"] += 1
        get_logger().error(
          "recording recovery journal {} names media that is missing or "
          "unusable; the note is retained".format(key[:8])
        )
        continue

      try:
        recording_id = self._recording_service.record_prepared(
          intent, recovery_key=key
        )
      except RecordingPersistenceUnavailable as e:
        ##
        ## Not this note's problem - the repository itself is unreachable, so
        ## every remaining note would fail the same way. Stopping here keeps a
        ## startup from hammering a database that is already down once per
        ## pending note, and everything untouched is replayed next restart.
        ##
        remaining = len(keys) - position
        counts["deferred"] += remaining
        counts["retained"] += remaining
        get_logger().error(
          "recording recovery deferred at journal {}: the recording "
          "repository is unavailable ({}); {} note(s) retained".format(
            key[:8], type(e).__name__, remaining
          )
        )
        return self._summary(pending, counts)
      except RecordingRecoveryConflict as e:
        ##
        ## The key already names different media. Neither answer is safe:
        ## returning the stored id would attach this note's identity to
        ## somebody else's bytes, and inserting would defeat the key. The
        ## stored row is left exactly as it is, nothing is reassigned, and the
        ## note is kept as the evidence an operator will need.
        ##
        counts["conflicted"] += 1
        counts["retained"] += 1
        self._log_refusal(key, e)
        continue
      except Exception as e:
        ##
        ## One record's failure - a rejected foreign key for an owner that no
        ## longer exists, a malformed row, a driver error. Never repaired by
        ## guessing: an insert retried without its owner would silently
        ## transfer a recording to nobody, and ownership uncertainty is not
        ## fixable by downgrading the owner.
        ##
        counts["retained"] += 1
        self._log_refusal(key, e)
        continue

      counts["recovered"] += 1
      try:
        self._journal.acknowledge(key)
      except Exception as e:
        ##
        ## The row exists; that stands. Nothing is rolled back and the row is
        ## not deleted - a surviving note replayed under the same key resolves
        ## to this same recording rather than creating a second one, which is
        ## exactly the guarantee Phase 11B-0 built.
        ##
        get_logger().warning(
          "recording {} recovered but its journal {} could not be retired "
          "({}: {})".format(recording_id, key[:8], type(e).__name__, e)
        )

    return self._summary(pending, counts)

  ##
  ## Enough to find the note on disk and know why it was refused, and nothing
  ## more. Never the payload, the title, the room, the owner or the path: this
  ## goes to a log file that is not covered by the access rules the recording
  ## itself is.
  ##
  @staticmethod
  def _log_refusal(key, error):
    get_logger().error(
      "recording recovery journal {} was not replayed ({}); "
      "the note is retained".format(key[:8], type(error).__name__)
    )

  @staticmethod
  def _summary(pending, counts) -> ReconciliationSummary:
    summary = ReconciliationSummary(
      discovered=len(pending.keys),
      truncated=pending.truncated,
      **counts,
    )
    get_logger().info(
      "recording recovery reconciled: discovered={} attempted={} "
      "recovered={} retained={} missing={} conflicted={} corrupt={} "
      "deferred={} truncated={}".format(
        summary.discovered,
        summary.attempted,
        summary.recovered,
        summary.retained,
        summary.missing,
        summary.conflicted,
        summary.corrupt,
        summary.deferred,
        summary.truncated,
      )
    )
    return summary


__all__ = [
  "ReconciliationSummary",
  "RecordingRecoveryReconciler",
]
