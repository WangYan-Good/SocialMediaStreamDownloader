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
from math import isfinite
from numbers import Real
import os
from pathlib import Path
import signal
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
  def _publish(self, temporary_path, final_path):
    os.link(temporary_path, final_path)

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

    self._publish(temporary_path, final_path)
    return True

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
    ## Published.  The temporary is now a second link to bytes the final name
    ## also holds, so dropping it cannot lose anything.
    ##
    self._discard(temporary_path)
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
    get_logger().info(
      "HLS recording normalized to MP4: {}".format(final_path.name)
    )
    return final_path


__all__ = ["HlsMp4Normalizer"]
