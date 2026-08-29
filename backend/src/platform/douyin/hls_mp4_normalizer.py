##
## Turning a finished HLS recording into a file the library can actually show.
##
## The live downloader tries FLV first and falls back to HLS.  The HLS path
## captures MPEG-TS, because TS is the container that survives an interrupted
## recording: it is a stream of self-describing packets, so a file cut off
## mid-broadcast is still the recording up to that point.  Ordinary MP4 is not -
## its index lives in a ``moov`` atom written when the muxer is allowed to
## finish, and a recording killed by a shutdown leaves bytes no player will
## open.  So capture stays TS, and the container is corrected afterwards.
##
## "Afterwards" is the whole design.  Once the broadcast has ended the recording
## is complete and sitting on local disk, which is the first moment an MP4 can
## be produced safely.  What happens here is a *remux*: the same encoded video
## and audio packets are copied into an MP4 container.  Nothing is decoded and
## nothing is re-compressed, so it costs a file copy rather than an encode, and
## the recording that comes out is bit-for-bit the same footage.
##
## The invariant this module exists to hold: the TS is the authoritative
## recording until a complete MP4 has been published, and every way this can go
## wrong ends with the TS still there.  A recording that was captured
## successfully must never be damaged by an attempt to improve its container.
##
import errno
from math import isfinite
from numbers import Real
import os
from pathlib import Path
import signal
import stat
import subprocess
from threading import Event
from time import sleep
from uuid import uuid4

from backend.src.library.loglib import get_logger


class HlsMp4Normalizer:
  """Best-effort lossless remux of a finished ``.ts`` recording into ``.mp4``.

  ``normalize`` answers with the path that should be recorded as the
  recording: the new MP4 when everything worked, and the untouched source
  otherwise.  It does not raise - a container that could not be improved is not
  a recording that failed.
  """

  def __init__(
    self,
    ffmpeg_path="ffmpeg",
    process_factory=subprocess.Popen,
    sleeper=sleep,
    group_signaler=os.killpg,
    token_factory=None,
  ):
    self.ffmpeg_path = ffmpeg_path
    self.process_factory = process_factory
    self.sleeper = sleeper
    self.group_signaler = group_signaler
    self.token_factory = token_factory or (lambda: uuid4().hex)
    self._shutdown_event = Event()

  ##
  ## Shutdown.  Note what this does *not* mean: cancelling a normalization
  ## cancels a container conversion, not a recording.  A cancelled recorder
  ## produces HlsCancelled and a cancelled task; a cancelled normalizer
  ## produces a ``.ts`` and a successful one.
  ##
  def cancel_all(self):
    self._shutdown_event.set()

  def _is_cancelled(self, cancel_event):
    return self._shutdown_event.is_set() or (
      cancel_event is not None and cancel_event.is_set()
    )

  def _command(self, source_path, temporary_path):
    ##
    ## Only video and audio are carried over.  A TS from a live edge can also
    ## contain timed metadata and private streams that the MP4 muxer has no
    ## mapping for, and ``-map 0`` would turn one of those into a hard failure
    ## for a recording whose picture and sound copy across perfectly.
    ##
    ## ``aac_adtstoasc`` is deliberately absent.  The MOV/MP4 muxer inserts it
    ## itself for the ADTS AAC that HLS carries; writing it out by hand would
    ## be a hand-maintained copy of muxer logic that also breaks on the inputs
    ## that do not need it.
    ##
    return [
      self.ffmpeg_path,
      "-nostdin",
      "-hide_banner",
      "-nostats",
      "-loglevel",
      "error",
      "-i",
      str(source_path),
      "-map",
      "0:v?",
      "-map",
      "0:a?",
      "-c",
      "copy",
      "-movflags",
      "+faststart",
      "-f",
      "mp4",
      str(temporary_path),
    ]

  ##
  ## A hidden, per-attempt name in the recording's own directory.  Hidden
  ## because a half-written MP4 must never look like a finished recording to
  ## anything scanning the library, and same-directory because publication is a
  ## hard link, which cannot cross a filesystem.
  ##
  def _reserve_temporary(self, source_path):
    return source_path.with_name(
      ".{}.remux-{}.part.mp4".format(source_path.stem, self.token_factory())
    )

  @staticmethod
  def _discard(path):
    if path is None:
      return
    try:
      path.unlink(missing_ok=True)
    except OSError:
      pass

  ##
  ## Commit this file's contents to stable storage.
  ##
  ## ffmpeg has exited by the time this runs, so there is no Python file object
  ## to flush - and flushing one would not be the same thing anyway.  A write
  ## that has returned successfully still lives in page cache; ``fsync`` is
  ## what obliges the kernel to put the data, and the inode metadata needed to
  ## find it, on the device.
  ##
  ## Opened read-only and without following symlinks.  This is a second open of
  ## a name this process chose, after an external program has been writing
  ## there, so it is worth insisting the thing being committed is the regular
  ## file that was validated - not something a link now points at.
  ##
  ## The size and type are re-checked on the descriptor itself rather than
  ## trusted from an earlier ``stat`` of the path: this descriptor is what gets
  ## published, so this descriptor is what the question is about.
  ##
  @staticmethod
  def _sync_file(path):
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
      info = os.fstat(descriptor)
      if not stat.S_ISREG(info.st_mode):
        raise OSError(
          errno.EINVAL, "normalization target is not a regular file", str(path)
        )
      if info.st_size == 0:
        raise OSError(
          errno.EINVAL, "normalization target is empty", str(path)
        )
      os.fsync(descriptor)
    finally:
      os.close(descriptor)

  ##
  ## Commit a directory's entries to stable storage.
  ##
  ## This is the half that ``fsync`` on the file does not cover.  A name is not
  ## part of the file it refers to - it is an entry in the parent directory -
  ## so after a hard link creates ``live.mp4``, the file can be fully durable
  ## while the name that reaches it is still only in an uncommitted journal.
  ## A crash there would leave the bytes on disk with nothing pointing at them,
  ## which is indistinguishable from having lost the recording.
  ##
  ## The descriptor is opened per call and never cached: a long-lived directory
  ## descriptor in a server that records for hours would pin a directory that
  ## may be renamed or removed underneath it.
  ##
  @staticmethod
  def _sync_directory(path):
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
      os.fsync(descriptor)
    finally:
      os.close(descriptor)

  def _terminate_process(self, process, terminate_grace):
    try:
      self.group_signaler(process.pid, signal.SIGTERM)
    except OSError:
      pass
    try:
      process.wait(timeout=terminate_grace)
    except subprocess.TimeoutExpired:
      try:
        self.group_signaler(process.pid, signal.SIGKILL)
      except OSError:
        pass
      process.wait()

  ##
  ## ``None`` means the remux was cancelled; anything else is ffmpeg's exit
  ## status.
  ##
  def _await(self, process, terminate_grace, cancel_event):
    while True:
      if self._is_cancelled(cancel_event):
        self._terminate_process(process, terminate_grace)
        return None
      returncode = process.poll()
      if returncode is not None:
        process.wait()
        return returncode
      self.sleeper(0.2)

  ##
  ## Publication is a hard link rather than a rename.  ``os.replace`` would
  ## silently destroy whatever already owns the final name, and by the time
  ## this runs that could be a different recording that reserved the name after
  ## this one started.  ``os.link`` refuses instead of overwriting, which makes
  ## the last-moment race a normalization failure rather than data loss.
  ##
  ## A filesystem with no hard links fails here too, and that is the intended
  ## reading: without a no-clobber publish there is no safe way to take the
  ## name, so the recording stays as it was captured.
  ##
  ##
  ## Commit the captured recording before anything is allowed to replace it.
  ##
  ## Everything downstream rests on one sentence: "a crash here still leaves
  ## the ``.ts``".  That sentence is not true when this stage begins.  The
  ## recorder finishes an attempt with ``os.replace(attempt, destination)`` and
  ## never fsyncs the inode or the parent directory, so on arrival the ``.ts``
  ## exists in the kernel's view and may exist nowhere else: its bytes can
  ## still be in page cache, and the rename that gave it its name can still be
  ## in an uncommitted journal - which could even restore the empty placeholder
  ## the name was originally reserved with.
  ##
  ## Publishing an MP4 on top of that and deleting the ``.ts`` would trade a
  ## recording whose durability is unknown for one whose durability is proven,
  ## and destroy the original in the process.  So the source is committed
  ## first, and normalization declines to start when it cannot be.
  ##
  ## Deliberately here rather than in ``HlsRecorder``: this is the stage that
  ## wants to delete the ``.ts``, so this is the stage that has to establish it
  ## is safe to. Capture semantics stay exactly as they are.
  ##
  def _establish_source_durability(self, source_path):
    try:
      self._sync_file(source_path)
      self._sync_directory(source_path.parent)
    except OSError as e:
      get_logger().warning(
        "HLS MP4 normalization declined: {} could not be committed to stable "
        "storage first ({}: {}), recording kept as captured".format(
          source_path.name,
          type(e).__name__,
          e,
        )
      )
      return False
    return True

  ## Publication is complete only when both halves are on stable storage: the
  ## bytes (``_sync_file``) and the name that reaches them (``_sync_directory``
  ## on the parent).  ``os.link`` returning success is neither - it is a change
  ## to the kernel's view that may still be sitting in a metadata journal.
  ##
  ## Answers whether the final name is durable.  ``False`` means this attempt
  ## did not achieve a publication it is willing to stand behind, and the
  ## caller must keep the captured ``.ts``.
  ##
  def _publish_durably(self, temporary_path, final_path):
    self._sync_file(temporary_path)
    ##
    ## Anything raised here - most importantly ``FileExistsError`` - leaves
    ## this attempt owning nothing, and is handled by the caller as an ordinary
    ## normalization failure.
    ##
    os.link(temporary_path, final_path)
    ##
    ## From here the name exists and *this attempt* is the one that created it.
    ## That distinction is what makes the rollback below safe: reaching this
    ## line is the only way to know the final name is not somebody else's.
    ##
    try:
      self._sync_directory(final_path.parent)
    except OSError as e:
      get_logger().warning(
        "HLS MP4 normalization could not make {} durable ({}: {}), "
        "recording kept as {}".format(
          final_path.name,
          type(e).__name__,
          e,
          temporary_path.name,
        )
      )
      ##
      ## Withdraw the name this attempt created.  It advertises a durable
      ## recording that is not durable, and leaving it would also take the name
      ## away from a later attempt that could publish properly.
      ##
      try:
        final_path.unlink(missing_ok=True)
      except OSError as rollback_error:
        ##
        ## Could not commit the name and could not withdraw it either.  That
        ## can leave a .ts and an .mp4 side by side - untidy, and strictly
        ## better than deleting the only copy of a broadcast.
        ##
        get_logger().warning(
          "HLS MP4 normalization could not withdraw {} ({}: {}); the "
          "recording is kept as {} and both may remain".format(
            final_path.name,
            type(rollback_error).__name__,
            rollback_error,
            temporary_path.name,
          )
        )
      else:
        ##
        ## The withdrawal is another directory-entry change, so it gets the
        ## same commit the publication would have had.  Best effort: the
        ## caller keeps the .ts regardless.
        ##
        try:
          self._sync_directory(final_path.parent)
        except OSError:
          pass
      return False
    return True

  ##
  ## The part that can go wrong.  Answers whether a complete MP4 now exists at
  ## ``final_path``; every ``False`` leaves the source untouched and says why.
  ##
  def _remux(
    self,
    source_path,
    temporary_path,
    final_path,
    terminate_grace,
    cancel_event,
  ):
    process = self.process_factory(
      self._command(source_path, temporary_path),
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      shell=False,
      start_new_session=True,
    )
    try:
      returncode = self._await(process, terminate_grace, cancel_event)
    except BaseException:
      ##
      ## Whatever is unwinding this thread - an interrupt, a thread being torn
      ## down - does not reach a child in its own session.  Left running it
      ## would keep writing an MP4 nobody is waiting for.
      ##
      try:
        self._terminate_process(process, terminate_grace)
      except BaseException:
        pass
      raise
    if returncode is None:
      get_logger().warning(
        "HLS MP4 normalization cancelled, recording kept as {}".format(
          source_path.name
        )
      )
      return False
    if returncode != 0:
      get_logger().warning(
        "HLS MP4 normalization failed (ffmpeg exit {}), recording kept as {}".format(
          returncode,
          source_path.name,
        )
      )
      return False
    ##
    ## ffmpeg reporting success is not enough to believe a file exists: the
    ## thing being published is the evidence, so it is inspected directly.
    ##
    if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
      get_logger().warning(
        "HLS MP4 normalization produced no output, recording kept as {}".format(
          source_path.name
        )
      )
      return False

    return self._publish_durably(temporary_path, final_path)

  def normalize(self, source_path, *, terminate_grace=5, cancel_event=None):
    """Remux ``source_path`` to MP4, or answer ``source_path`` unchanged."""
    if (
      isinstance(terminate_grace, bool)
      or not isinstance(terminate_grace, Real)
      or not isfinite(terminate_grace)
      or terminate_grace <= 0
    ):
      raise ValueError("normalization terminate_grace must be positive finite")

    source_path = Path(source_path)
    final_path = source_path.with_suffix(".mp4")
    temporary_path = None
    try:
      if self._is_cancelled(cancel_event):
        return source_path
      if not source_path.is_file():
        return source_path

      ##
      ## The fallback has to be real before it can be relied on.  Until this
      ## barrier passes there is no proven copy of the recording, so there is
      ## nothing safe to normalize towards.
      ##
      if not self._establish_source_durability(source_path):
        return source_path

      temporary_path = self._reserve_temporary(source_path)
      if not self._remux(
        source_path,
        temporary_path,
        final_path,
        terminate_grace,
        cancel_event,
      ):
        ##
        ## Nothing was published, so the temporary is the only reference to
        ## those bytes and a half-written MP4 is worth nothing to anyone.
        ##
        self._discard(temporary_path)
        return source_path
    except BaseException as e:
      ##
      ## An interrupt is not this stage's to swallow, but it must not leave a
      ## half-written MP4 in a directory the library scans either.
      ##
      if not isinstance(e, Exception):
        self._discard(temporary_path)
        raise
      ##
      ## Every remaining way this can fail - ffmpeg missing, the process dying,
      ## an unrepresentable codec, a full or read-only disk, another recording
      ## taking the name first - lands here, and all of them mean the same
      ## thing: the recording stays exactly as it was captured.
      ##
      self._discard(temporary_path)
      get_logger().warning(
        "HLS MP4 normalization failed ({}: {}), recording kept as {}".format(
          type(e).__name__,
          e,
          source_path.name,
        )
      )
      return source_path

    ##
    ## Past this point the MP4 is durable: its bytes and its name have both
    ## been committed.  Everything below is cleanup, and no failure in it can
    ## take the recording back to the ``.ts`` - that file may already be gone,
    ## and the MP4 is on stable storage either way.
    ##
    ## The temporary is now a second name for bytes the final name also holds,
    ## so dropping it cannot lose anything.  Failing to drop it leaves a hidden
    ## file behind, which is storage hygiene rather than a damaged recording.
    ##
    try:
      temporary_path.unlink(missing_ok=True)
    except OSError as e:
      get_logger().warning(
        "HLS MP4 normalization published {} but could not remove {} ({}: {})".format(
          final_path.name,
          temporary_path.name,
          type(e).__name__,
          e,
        )
      )
    ##
    ## Only now may the source go.  Failing to remove it leaves an orphan to be
    ## cleaned up later, which is not a reason to throw away a complete MP4
    ## that has already been published.
    ##
    try:
      source_path.unlink()
    except OSError as e:
      get_logger().warning(
        "HLS MP4 normalization published {} but could not remove {} ({}: {})".format(
          final_path.name,
          source_path.name,
          type(e).__name__,
          e,
        )
      )
    ##
    ## Commit the cleanup itself.  Without this the removals are only in the
    ## kernel's view, and a crash could resurrect the ``.ts`` beside a
    ## recording that has already been persisted as the MP4.
    ##
    ## A failure here cannot undo anything: the MP4 was durable before any of
    ## this ran, so the recording stands and the leftovers are cleaned up on
    ## some later pass.
    ##
    try:
      self._sync_directory(final_path.parent)
    except OSError as e:
      get_logger().warning(
        "HLS MP4 normalization published {} but could not commit cleanup "
        "({}: {})".format(final_path.name, type(e).__name__, e)
      )
    get_logger().info(
      "HLS recording normalized to MP4: {}".format(final_path.name)
    )
    return final_path


__all__ = ["HlsMp4Normalizer"]
