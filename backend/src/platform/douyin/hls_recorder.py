from collections.abc import Mapping
import errno
from math import ceil, isfinite
from numbers import Real
import os
from pathlib import Path
import signal
import stat
import subprocess
from threading import Event
from time import monotonic, sleep


class HlsDownloadError(RuntimeError):
  pass


class FfmpegUnavailable(HlsDownloadError):
  pass


class HlsStalled(HlsDownloadError):
  pass


class HlsCancelled(HlsDownloadError):
  pass


##
## The capture finished, but it could not be committed to stable storage.
##
## Distinct from every other error here because it is not a network problem and
## must not be treated as one: the broadcast has already been recorded, and
## reconnecting to re-record it would be both pointless and impossible - the
## stream may well have ended.  It is a local storage failure discovered after
## the media was captured, and the only honest answer is to refuse to report
## success while leaving every captured byte where it is.
##
class HlsDurabilityError(HlsDownloadError):
  pass


class HlsRecorder:
  def __init__(
    self,
    ffmpeg_path="ffmpeg",
    process_factory=subprocess.Popen,
    clock=monotonic,
    sleeper=sleep,
    group_signaler=os.killpg,
  ):
    self.ffmpeg_path = ffmpeg_path
    self.process_factory = process_factory
    self.clock = clock
    self.sleeper = sleeper
    self.group_signaler = group_signaler
    self._shutdown_event = Event()

  def cancel_all(self):
    self._shutdown_event.set()

  def _is_cancelled(self, cancel_event):
    return self._shutdown_event.is_set() or (
      cancel_event is not None and cancel_event.is_set()
    )

  @staticmethod
  def _header_block(headers):
    if headers is None:
      return None
    if not isinstance(headers, Mapping):
      raise TypeError("HLS headers must be a mapping")
    lines = []
    for name, value in headers.items():
      if value is None or value == "":
        continue
      name = str(name)
      value = str(value)
      if "\r" in name or "\n" in name or "\r" in value or "\n" in value:
        raise ValueError("HLS headers must not contain CR or LF")
      lines.append("{}: {}\r\n".format(name, value))
    return "".join(lines) or None

  @staticmethod
  def _proxy(proxies):
    if proxies is None:
      return None
    if not isinstance(proxies, Mapping):
      raise TypeError("HLS proxies must be a mapping")
    return proxies.get("https") or proxies.get("http")

  def _command(
    self,
    url,
    output_path,
    headers,
    proxies,
    max_retry,
    io_timeout,
  ):
    command = [
      self.ffmpeg_path,
      "-nostdin",
      "-hide_banner",
      "-nostats",
      "-loglevel",
      "error",
      "-y",
    ]
    header_block = self._header_block(headers)
    if header_block is not None:
      command.extend(["-headers", header_block])
    proxy = self._proxy(proxies)
    if proxy:
      command.extend(["-http_proxy", str(proxy)])
    command.extend([
      "-rw_timeout",
      str(max(1, ceil(io_timeout * 1000000))),
      "-reconnect",
      "1",
      "-reconnect_streamed",
      "1",
      "-reconnect_on_network_error",
      "1",
      "-reconnect_on_http_error",
      "429,5xx",
      "-reconnect_delay_max",
      str(ceil(io_timeout)),
      "-seg_max_retry",
      str(max_retry),
      "-i",
      str(url),
      "-c",
      "copy",
      "-f",
      "mpegts",
      str(output_path),
    ])
    return command

  @staticmethod
  def _size(path):
    try:
      return path.stat().st_size
    except FileNotFoundError:
      return 0

  def _preserve_failed_attempt(self, attempt_path, destination, attempt):
    if self._size(attempt_path) == 0:
      attempt_path.unlink(missing_ok=True)
      return
    partial_number = 1
    while True:
      suffix = "" if partial_number == 1 else "-{}".format(partial_number)
      partial_path = destination.with_name(
        "{}.attempt-{}.partial{}.ts".format(
          destination.stem,
          attempt,
          suffix,
        )
      )
      try:
        os.link(attempt_path, partial_path)
      except FileExistsError:
        partial_number += 1
      else:
        attempt_path.unlink()
        return

  ##
  ## Commit this attempt's bytes to stable storage.
  ##
  ## ffmpeg has exited by the time this runs, so its writes have returned - but
  ## returning is not reaching the device.  ``fsync`` is what obliges the kernel
  ## to put the data, and the inode metadata needed to find it, on disk.
  ##
  ## Opened read-only and without following symlinks: this is a second open of
  ## a name an external program has been writing, so the thing being committed
  ## should be the regular file that was recorded, not whatever a link now
  ## points at.  Type and size are re-asked on the descriptor rather than
  ## trusted from an earlier path stat, because this descriptor is the one
  ## about to become the recording.
  ##
  ## Deliberately its own helper rather than one shared with the normalizer.
  ## Capture durability is this class's responsibility, and reaching into
  ## another module's private method to get it would tie the two stages'
  ## safety together for no gain.
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
          errno.EINVAL, "HLS attempt is not a regular file", str(path)
        )
      if info.st_size == 0:
        raise OSError(errno.EINVAL, "HLS attempt is empty", str(path))
      os.fsync(descriptor)
    finally:
      os.close(descriptor)

  ##
  ## Commit a directory's entries to stable storage.
  ##
  ## The half that syncing the file does not cover: a name lives in its parent
  ## directory, so a rename can be complete in the kernel's view while the
  ## entry that reaches the bytes is still only in an uncommitted journal.
  ##
  ## Opened per call and never cached - a directory descriptor held across a
  ## recording that runs for hours would pin a directory that may be renamed or
  ## removed underneath it.
  ##
  @staticmethod
  def _sync_directory(path):
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
      os.fsync(descriptor)
    finally:
      os.close(descriptor)

  ##
  ## Turn a completed attempt into a durable recording.
  ##
  ## Knows only about two paths.  No url, no headers, no proxy, no task, no
  ## database - the question here is purely "are these captured bytes safely
  ## the destination now", and answering it needs nothing else.
  ##
  ## The sequence, and why each step is where it is:
  ##
  ##   fsync(attempt)     the bytes must be on the device before any name is
  ##                      pointed at them
  ##   fsync(parent)      commits the *pre-rename* namespace, so the state
  ##                      holding the hidden attempt is itself durable; a crash
  ##                      during the rename then falls back to a committed
  ##                      namespace in which the complete media still has a name
  ##   os.replace         publication.  A rename rather than the normalizer's
  ##                      no-clobber link because this destination was reserved
  ##                      for this recording by the caller before capture began;
  ##                      the MP4 final name has no such placeholder, which is
  ##                      why that stage needs different machinery
  ##   fsync(parent)      commits the new name
  ##
  ## Only after all four may the recording be reported as finished.
  ##
  def _finalize_successful_attempt(self, attempt_path, destination):
    try:
      self._sync_file(attempt_path)
      self._sync_directory(destination.parent)
      os.replace(attempt_path, destination)
      self._sync_directory(destination.parent)
    except OSError as e:
      ##
      ## Nothing captured is removed here, at any step.  Being unable to prove
      ## the recording is durable is not a reason to destroy it - the bytes are
      ## either still in the attempt or already in the destination, and both
      ## are worth more than a tidy directory.
      ##
      raise HlsDurabilityError(
        "ffmpeg HLS recording completed but could not be committed to stable "
        "storage ({}: {})".format(type(e).__name__, e)
      ) from e
    return destination

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

  def _monitor(
    self,
    process,
    attempt_path,
    stall_timeout,
    terminate_grace,
    cancel_event,
  ):
    last_size = self._size(attempt_path)
    no_progress_deadline = self.clock() + stall_timeout
    while True:
      if self._is_cancelled(cancel_event):
        self._terminate_process(process, terminate_grace)
        raise HlsCancelled("ffmpeg HLS recording cancelled after 1 attempt")
      returncode = process.poll()
      if returncode is not None:
        process.wait()
        return returncode

      current_size = self._size(attempt_path)
      if current_size > last_size:
        no_progress_deadline = self.clock() + stall_timeout
      last_size = current_size
      if self.clock() >= no_progress_deadline:
        self._terminate_process(process, terminate_grace)
        raise HlsStalled("ffmpeg HLS recording stalled after 1 attempt")
      self.sleeper(0.2)

  def record(
    self,
    url,
    output_path,
    *,
    headers=None,
    proxies=None,
    max_retry=0,
    io_timeout=10,
    stall_timeout=30,
    terminate_grace=5,
    cancel_event=None,
  ):
    if type(max_retry) is not int or max_retry < 0:
      raise ValueError("HLS max_retry must be a non-negative integer")
    for name, value in (
      ("io_timeout", io_timeout),
      ("stall_timeout", stall_timeout),
      ("terminate_grace", terminate_grace),
    ):
      if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not isfinite(value)
        or value <= 0
      ):
        raise ValueError(
          "HLS {} must be a positive finite number".format(name)
        )
    destination = Path(output_path)
    for attempt in range(1, max_retry + 2):
      if self._is_cancelled(cancel_event):
        raise HlsCancelled(
          "ffmpeg HLS recording cancelled after {} attempts".format(
            attempt - 1
          )
        )
      attempt_path = destination.parent / ".{}.attempt-{}.part".format(
        destination.name,
        attempt,
      )
      attempt_path.unlink(missing_ok=True)
      command = self._command(
        url,
        attempt_path,
        headers,
        proxies,
        max_retry,
        io_timeout,
      )
      try:
        process = self.process_factory(
          command,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
          shell=False,
          start_new_session=True,
        )
      except OSError:
        self._preserve_failed_attempt(attempt_path, destination, attempt)
        raise FfmpegUnavailable(
          "ffmpeg executable is required for HLS download after {} attempt{}".format(
            attempt,
            "" if attempt == 1 else "s",
          )
        ) from None
      try:
        returncode = self._monitor(
          process,
          attempt_path,
          stall_timeout,
          terminate_grace,
          cancel_event,
        )
      except HlsCancelled as exc:
        self._preserve_failed_attempt(attempt_path, destination, attempt)
        raise HlsCancelled(
          "ffmpeg HLS recording cancelled after {} attempts".format(
            attempt,
          )
        ) from exc
      except HlsStalled as exc:
        self._preserve_failed_attempt(attempt_path, destination, attempt)
        if attempt <= max_retry:
          continue
        raise HlsStalled(
          "ffmpeg HLS recording stalled after {} attempts".format(attempt)
        ) from exc
      except BaseException:
        try:
          self._terminate_process(process, terminate_grace)
        except BaseException:
          pass
        raise
      if returncode == 0 and attempt_path.is_file() and attempt_path.stat().st_size:
        ##
        ## The capture is complete.  Finalization is deliberately outside the
        ## retry loop's reach: a failure to commit it raises HlsDurabilityError
        ## straight out of ``record``, so a local storage problem can never
        ## send this back to re-dial a broadcast that has already been recorded
        ## and may already be over.
        ##
        return self._finalize_successful_attempt(attempt_path, destination)
      self._preserve_failed_attempt(attempt_path, destination, attempt)
    raise HlsDownloadError(
      "ffmpeg HLS recording failed after {} attempts".format(max_retry + 1)
    )


__all__ = [
  "FfmpegUnavailable",
  "HlsCancelled",
  "HlsDownloadError",
  "HlsDurabilityError",
  "HlsRecorder",
  "HlsStalled",
]
