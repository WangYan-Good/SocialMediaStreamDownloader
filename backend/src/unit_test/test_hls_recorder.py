from pathlib import Path
import signal
import subprocess
import tempfile
import traceback
import unittest
from unittest import mock

import backend.src.platform.douyin.hls_recorder as hls_recorder_module
from backend.src.platform.douyin.hls_recorder import (
  FfmpegUnavailable,
  HlsStalled,
  HlsDownloadError,
  HlsRecorder,
)


class HlsRecorderTest(unittest.TestCase):
  def test_record_builds_safe_ffmpeg_stream_copy_command(self):
    calls = []

    class ImmediateSuccess:
      returncode = 0

      def poll(self):
        return self.returncode

      def wait(self, timeout=None):
        return self.returncode

    def process_factory(command, **kwargs):
      calls.append((command, kwargs))
      Path(command[-1]).write_bytes(b"fake-hls-data")
      return ImmediateSuccess()

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      result = HlsRecorder("/test/ffmpeg", process_factory).record(
        "https://stream.example.test/index.m3u8?sign=sensitive",
        output,
        headers={
          "User-Agent": "test-agent",
          "Cookie": "session=sensitive",
          "Empty": None,
        },
        proxies={"http": None, "https": "http://proxy-sensitive"},
        max_retry=0,
        io_timeout=7,
      )

    self.assertEqual(output, result)
    self.assertEqual(1, len(calls))
    command, kwargs = calls[0]
    self.assertIsInstance(command, list)
    self.assertEqual("/test/ffmpeg", command[0])
    self.assertIn("-nostdin", command)
    self.assertIn("-nostats", command)
    self.assertIn("-y", command)
    self.assertEqual(
      "User-Agent: test-agent\r\nCookie: session=sensitive\r\n",
      command[command.index("-headers") + 1],
    )
    self.assertEqual(
      "http://proxy-sensitive",
      command[command.index("-http_proxy") + 1],
    )
    self.assertEqual(
      ["-i", "https://stream.example.test/index.m3u8?sign=sensitive"],
      command[command.index("-i"):command.index("-i") + 2],
    )
    self.assertIn("-rw_timeout", command)
    self.assertEqual(
      [
        "-rw_timeout", "7000000",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_on_network_error", "1",
        "-reconnect_on_http_error", "429,5xx",
        "-reconnect_delay_max", "7",
        "-seg_max_retry", "0",
      ],
      command[command.index("-rw_timeout"):command.index("-i")],
    )
    self.assertIn("copy", command)
    self.assertIn("mpegts", command)
    self.assertEqual(
      str(output.parent / ".live.ts.attempt-1.part"),
      command[-1],
    )
    self.assertEqual(
      {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "shell": False,
        "start_new_session": True,
      },
      kwargs,
    )

  def test_fractional_io_timeout_uses_microseconds_and_ceil_seconds(self):
    calls = []

    class ImmediateSuccess:
      def poll(self):
        return 0

      def wait(self, timeout=None):
        return 0

    def process_factory(command, **kwargs):
      calls.append(command)
      Path(command[-1]).write_bytes(b"fake-hls-data")
      return ImmediateSuccess()

    with tempfile.TemporaryDirectory() as temporary_directory:
      HlsRecorder("/test/ffmpeg", process_factory).record(
        "https://stream.example.test/index.m3u8",
        Path(temporary_directory) / "live.ts",
        io_timeout=0.5,
      )

    command = calls[0]
    self.assertEqual("500000", command[command.index("-rw_timeout") + 1])
    self.assertEqual(
      "1",
      command[command.index("-reconnect_delay_max") + 1],
    )

  def test_tiny_positive_io_timeout_uses_at_least_one_microsecond(self):
    calls = []

    class ImmediateSuccess:
      def poll(self):
        return 0

      def wait(self, timeout=None):
        return 0

    def process_factory(command, **kwargs):
      calls.append(command)
      Path(command[-1]).write_bytes(b"fake-hls-data")
      return ImmediateSuccess()

    with tempfile.TemporaryDirectory() as temporary_directory:
      HlsRecorder("/test/ffmpeg", process_factory).record(
        "https://stream.example.test/index.m3u8",
        Path(temporary_directory) / "live.ts",
        io_timeout=1e-7,
      )

    command = calls[0]
    self.assertEqual("1", command[command.index("-rw_timeout") + 1])

  def test_record_rejects_non_finite_timeouts_before_process_start(self):
    def process_factory(command, **kwargs):
      self.fail("non-finite timeouts must be rejected before process start")

    for name in ("io_timeout", "stall_timeout", "terminate_grace"):
      for value in (float("nan"), float("inf"), float("-inf")):
        with self.subTest(name=name, value=value):
          arguments = {name: value}
          caught = None
          try:
            with tempfile.TemporaryDirectory() as temporary_directory:
              HlsRecorder("/test/ffmpeg", process_factory).record(
                "https://stream.example.test/index.m3u8",
                Path(temporary_directory) / "live.ts",
                **arguments,
              )
          except Exception as exc:
            caught = exc

          self.assertIsInstance(caught, ValueError)
          self.assertIn("positive finite number", str(caught))

  def test_record_retries_until_configured_limit(self):
    return_codes = [1, 1, 0]
    calls = []

    class FinishedProcess:
      def __init__(self, returncode):
        self.returncode = returncode

      def poll(self):
        return self.returncode

      def wait(self, timeout=None):
        return self.returncode

    def process_factory(command, **kwargs):
      calls.append((command, kwargs))
      returncode = return_codes.pop(0)
      if returncode == 0:
        Path(command[-1]).write_bytes(b"complete-hls")
      return FinishedProcess(returncode)

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      result = HlsRecorder("/test/ffmpeg", process_factory).record(
        "https://stream.example.test/index.m3u8",
        output,
        headers=None,
        proxies=None,
        max_retry=2,
      )

    self.assertEqual(output, result)
    self.assertEqual(3, len(calls))

  def test_record_escalates_and_reaps_a_permanently_stalled_process(self):
    now = [0.0]
    signals = []

    class StalledProcess:
      pid = 321

      def __init__(self):
        self.wait_calls = []

      def poll(self):
        return None

      def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        if timeout is not None:
          raise subprocess.TimeoutExpired("redacted", timeout)
        return -signal.SIGKILL

    process = StalledProcess()

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaises(HlsDownloadError) as raised:
        HlsRecorder(
          "/test/ffmpeg",
          lambda command, **kwargs: process,
          clock=lambda: now[0],
          sleeper=lambda seconds: now.__setitem__(0, now[0] + seconds),
          group_signaler=lambda pid, sent_signal: signals.append(
            (pid, sent_signal)
          ),
        ).record(
          "https://stream.example.test/index.m3u8",
          output,
          stall_timeout=0.4,
          terminate_grace=0.5,
        )

    self.assertEqual("HlsStalled", type(raised.exception).__name__)
    self.assertEqual(
      [(321, signal.SIGTERM), (321, signal.SIGKILL)],
      signals,
    )
    self.assertEqual([0.5, None], process.wait_calls)

  def test_record_retries_after_a_stall_and_can_then_succeed(self):
    now = [0.0]
    attempt_paths = []

    class StalledProcess:
      pid = 111

      def poll(self):
        return None

      def wait(self, timeout=None):
        return -signal.SIGTERM

    class SuccessfulProcess:
      def poll(self):
        return 0

      def wait(self, timeout=None):
        return 0

    def process_factory(command, **kwargs):
      attempt_path = Path(command[-1])
      attempt_paths.append(attempt_path)
      if len(attempt_paths) == 1:
        attempt_path.write_bytes(b"stalled-partial")
        return StalledProcess()
      attempt_path.write_bytes(b"complete-hls")
      return SuccessfulProcess()

    with tempfile.TemporaryDirectory() as temporary_directory:
      temporary_path = Path(temporary_directory)
      output = temporary_path / "live.ts"
      result = None
      try:
        result = HlsRecorder(
          "/test/ffmpeg",
          process_factory,
          clock=lambda: now[0],
          sleeper=lambda seconds: now.__setitem__(0, now[0] + seconds),
          group_signaler=lambda pid, sent_signal: None,
        ).record(
          "https://stream.example.test/index.m3u8",
          output,
          max_retry=1,
          stall_timeout=0.2,
        )
      except HlsDownloadError:
        pass

      self.assertEqual(output, result)
      self.assertEqual(b"complete-hls", output.read_bytes())
      self.assertEqual(
        b"stalled-partial",
        (temporary_path / "live.attempt-1.partial.ts").read_bytes(),
      )
    self.assertEqual(2, len(attempt_paths))

  def test_record_reports_total_attempt_count_when_every_attempt_stalls(self):
    now = [0.0]
    processes = []

    class StalledProcess:
      pid = 222

      def poll(self):
        return None

      def wait(self, timeout=None):
        return -signal.SIGTERM

    def process_factory(command, **kwargs):
      process = StalledProcess()
      processes.append(process)
      return process

    with tempfile.TemporaryDirectory() as temporary_directory:
      with self.assertRaises(HlsStalled) as raised:
        HlsRecorder(
          "/test/ffmpeg",
          process_factory,
          clock=lambda: now[0],
          sleeper=lambda seconds: now.__setitem__(0, now[0] + seconds),
          group_signaler=lambda pid, sent_signal: None,
        ).record(
          "https://stream.example.test/index.m3u8",
          Path(temporary_directory) / "live.ts",
          max_retry=2,
          stall_timeout=0.2,
        )

    self.assertEqual(3, len(processes))
    self.assertIn("3 attempts", str(raised.exception))

  def test_monitor_error_terminates_kills_and_reaps_before_propagating(self):
    signals = []

    class MonitorError(BaseException):
      pass

    class BrokenProcess:
      pid = 333

      def __init__(self):
        self.wait_calls = []

      def poll(self):
        raise MonitorError("monitor failed")

      def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        if timeout is not None:
          raise subprocess.TimeoutExpired("redacted", timeout)
        return -signal.SIGKILL

    process = BrokenProcess()

    with tempfile.TemporaryDirectory() as temporary_directory:
      with self.assertRaises(MonitorError):
        HlsRecorder(
          "/test/ffmpeg",
          lambda command, **kwargs: process,
          group_signaler=lambda pid, sent_signal: signals.append(
            (pid, sent_signal)
          ),
        ).record(
          "https://stream.example.test/index.m3u8",
          Path(temporary_directory) / "live.ts",
          terminate_grace=0.5,
        )

    self.assertEqual(
      [(333, signal.SIGTERM), (333, signal.SIGKILL)],
      signals,
    )
    self.assertEqual([0.5, None], process.wait_calls)

  def test_truncate_then_grow_resets_the_stall_deadline(self):
    now = [0.0]
    sleep_count = [0]
    attempt_path = [None]

    class EventuallySuccessfulProcess:
      pid = 444

      def poll(self):
        return 0 if sleep_count[0] >= 4 else None

      def wait(self, timeout=None):
        return 0 if timeout is None else -signal.SIGTERM

    def process_factory(command, **kwargs):
      attempt_path[0] = Path(command[-1])
      attempt_path[0].write_bytes(b"0123456789")
      return EventuallySuccessfulProcess()

    def change_size_during_sleep(seconds):
      sleep_count[0] += 1
      now[0] += seconds
      if sleep_count[0] == 1:
        attempt_path[0].write_bytes(b"")
      elif sleep_count[0] == 2:
        attempt_path[0].write_bytes(b"12345")

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      result = None
      try:
        result = HlsRecorder(
          "/test/ffmpeg",
          process_factory,
          clock=lambda: now[0],
          sleeper=change_size_during_sleep,
          group_signaler=lambda pid, sent_signal: None,
        ).record(
          "https://stream.example.test/index.m3u8",
          output,
          stall_timeout=0.5,
        )
      except HlsStalled:
        pass

      self.assertEqual(output, result)
      self.assertEqual(b"12345", output.read_bytes())

  def test_cancel_all_terminates_and_reaps_an_active_process(self):
    now = [0.0]
    signals = []

    class ActiveProcess:
      pid = 654

      def __init__(self):
        self.wait_calls = []

      def poll(self):
        return None

      def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        return -signal.SIGTERM

    process = ActiveProcess()
    recorder = None

    def cancel_during_sleep(seconds):
      now[0] += seconds
      cancel = getattr(recorder, "cancel_all", None)
      if cancel is not None:
        cancel()

    with tempfile.TemporaryDirectory() as temporary_directory:
      recorder = HlsRecorder(
        "/test/ffmpeg",
        lambda command, **kwargs: process,
        clock=lambda: now[0],
        sleeper=cancel_during_sleep,
        group_signaler=lambda pid, sent_signal: signals.append(
          (pid, sent_signal)
        ),
      )
      with self.assertRaises(HlsDownloadError) as raised:
        recorder.record(
          "https://stream.example.test/index.m3u8",
          Path(temporary_directory) / "live.ts",
          stall_timeout=0.4,
          terminate_grace=0.5,
        )

    self.assertEqual("HlsCancelled", type(raised.exception).__name__)
    self.assertEqual([(654, signal.SIGTERM)], signals)
    self.assertEqual([0.5], process.wait_calls)

  def test_record_manages_distinct_retry_files_without_losing_partials(self):
    return_codes = [1, 0, 0]
    attempt_paths = []

    class FinishedProcess:
      def __init__(self, returncode):
        self.returncode = returncode
        self.waited = False

      def poll(self):
        return self.returncode

      def wait(self, timeout=None):
        self.waited = True
        return self.returncode

    processes = []

    def process_factory(command, **kwargs):
      attempt_path = Path(command[-1])
      attempt_paths.append(attempt_path)
      attempt_number = len(attempt_paths)
      if attempt_number == 1:
        attempt_path.write_bytes(b"new-partial")
      elif attempt_number == 2:
        attempt_path.touch()
      else:
        attempt_path.write_bytes(b"complete-hls")
      process = FinishedProcess(return_codes.pop(0))
      processes.append(process)
      return process

    with tempfile.TemporaryDirectory() as temporary_directory:
      temporary_path = Path(temporary_directory)
      output = temporary_path / "live.ts"
      existing_partial = temporary_path / "live.attempt-1.partial.ts"
      existing_partial.write_bytes(b"existing-partial")

      result = HlsRecorder("/test/ffmpeg", process_factory).record(
        "https://stream.example.test/index.m3u8",
        output,
        max_retry=2,
      )

      self.assertEqual(output, result)
      self.assertEqual(b"complete-hls", output.read_bytes())
      self.assertEqual(b"existing-partial", existing_partial.read_bytes())
      preserved_partial = temporary_path / "live.attempt-1.partial-2.ts"
      self.assertTrue(preserved_partial.exists())
      self.assertEqual(
        b"new-partial",
        preserved_partial.read_bytes(),
      )
      self.assertFalse(
        (temporary_path / ".live.ts.attempt-2.part").exists()
      )
      self.assertFalse(
        (temporary_path / "live.attempt-2.partial.ts").exists()
      )

    self.assertEqual(
      [
        ".live.ts.attempt-1.part",
        ".live.ts.attempt-2.part",
        ".live.ts.attempt-3.part",
      ],
      [path.name for path in attempt_paths],
    )
    self.assertTrue(all(process.waited for process in processes))

  def test_partial_preservation_does_not_clobber_a_racing_writer(self):
    class FailedProcess:
      def poll(self):
        return 1

      def wait(self, timeout=None):
        return 1

    with tempfile.TemporaryDirectory() as temporary_directory:
      temporary_path = Path(temporary_directory)
      output = temporary_path / "live.ts"
      first_partial = temporary_path / "live.attempt-1.partial.ts"
      second_partial = temporary_path / "live.attempt-1.partial-2.ts"
      race_created = [False]
      real_exists = Path.exists
      real_link = hls_recorder_module.os.link

      def process_factory(command, **kwargs):
        Path(command[-1]).write_bytes(b"recorded-partial")
        return FailedProcess()

      def racing_exists(path):
        exists = real_exists(path)
        if path == first_partial and not exists and not race_created[0]:
          first_partial.write_bytes(b"racing-partial")
          race_created[0] = True
        return exists

      def racing_link(source, destination):
        destination = Path(destination)
        if destination == first_partial and not race_created[0]:
          first_partial.write_bytes(b"racing-partial")
          race_created[0] = True
        return real_link(source, destination)

      with (
        mock.patch.object(Path, "exists", new=racing_exists),
        mock.patch.object(
          hls_recorder_module.os,
          "link",
          side_effect=racing_link,
        ),
      ):
        with self.assertRaises(HlsDownloadError):
          HlsRecorder("/test/ffmpeg", process_factory).record(
            "https://stream.example.test/index.m3u8",
            output,
          )

      self.assertEqual(b"racing-partial", first_partial.read_bytes())
      self.assertTrue(second_partial.exists())
      self.assertEqual(b"recorded-partial", second_partial.read_bytes())

  def test_supervised_term_returning_zero_is_never_success(self):
    for attempt_contents in (b"", b"incomplete-hls"):
      with self.subTest(attempt_contents=attempt_contents):
        now = [0.0]

        class TermAcceptedProcess:
          pid = 987

          def poll(self):
            return None

          def wait(self, timeout=None):
            return 0

        def process_factory(command, **kwargs):
          Path(command[-1]).write_bytes(attempt_contents)
          return TermAcceptedProcess()

        with tempfile.TemporaryDirectory() as temporary_directory:
          output = Path(temporary_directory) / "live.ts"
          with self.assertRaises(HlsDownloadError) as raised:
            HlsRecorder(
              "/test/ffmpeg",
              process_factory,
              clock=lambda: now[0],
              sleeper=lambda seconds: now.__setitem__(
                0,
                now[0] + seconds,
              ),
              group_signaler=lambda pid, sent_signal: None,
            ).record(
              "https://stream.example.test/index.m3u8",
              output,
              stall_timeout=0.2,
            )

          self.assertEqual("HlsStalled", type(raised.exception).__name__)
          self.assertFalse(output.exists())

  def test_record_reports_missing_ffmpeg_without_exposing_url(self):
    def process_factory(command, **kwargs):
      raise FileNotFoundError(command[0])

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaises(FfmpegUnavailable) as raised:
        HlsRecorder("missing-ffmpeg", process_factory).record(
          "https://stream.example.test/index.m3u8?sign=sensitive",
          output,
          max_retry=3,
        )

    self.assertIn("ffmpeg executable", str(raised.exception))
    self.assertNotIn("sensitive", str(raised.exception))

  def test_record_reports_unexecutable_ffmpeg_as_unavailable(self):
    def process_factory(command, **kwargs):
      raise PermissionError(command[0])

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaises(FfmpegUnavailable):
        HlsRecorder("unexecutable-ffmpeg", process_factory).record(
          "https://stream.example.test/index.m3u8",
          output,
        )

  def test_unavailable_error_redacts_the_process_construction_exception(self):
    sensitive_values = (
      "signed-url-marker",
      "cookie-marker",
      "proxy-marker",
    )

    def process_factory(command, **kwargs):
      raise OSError(" ".join(command))

    with tempfile.TemporaryDirectory() as temporary_directory:
      with self.assertRaises(FfmpegUnavailable) as raised:
        HlsRecorder("missing-ffmpeg", process_factory).record(
          "https://stream.example.test/index.m3u8?signed-url-marker",
          Path(temporary_directory) / "live.ts",
          headers={"Cookie": "cookie-marker"},
          proxies={"https": "http://proxy-marker"},
        )

    self.assertIn("1 attempt", str(raised.exception))
    formatted_exception = "".join(
      traceback.format_exception(raised.exception)
    )
    for value in sensitive_values:
      self.assertNotIn(value, formatted_exception)

  def test_construction_error_cleans_empty_and_preserves_nonempty_attempts(self):
    for attempt_contents in (b"", b"partial-before-error"):
      with self.subTest(attempt_contents=attempt_contents):
        with tempfile.TemporaryDirectory() as temporary_directory:
          temporary_path = Path(temporary_directory)
          output = temporary_path / "live.ts"
          hidden_attempt = temporary_path / ".live.ts.attempt-1.part"
          partial = temporary_path / "live.attempt-1.partial.ts"

          def process_factory(command, **kwargs):
            Path(command[-1]).write_bytes(attempt_contents)
            raise OSError("sensitive construction failure")

          with self.assertRaises(FfmpegUnavailable):
            HlsRecorder("missing-ffmpeg", process_factory).record(
              "https://stream.example.test/index.m3u8",
              output,
            )

          self.assertFalse(hidden_attempt.exists())
          if attempt_contents:
            self.assertTrue(partial.exists())
            self.assertEqual(attempt_contents, partial.read_bytes())
          else:
            self.assertFalse(partial.exists())

  def test_record_failure_is_redacted_and_preserves_partial_output(self):
    sensitive_values = (
      "signed-url-marker",
      "cookie-marker",
      "proxy-marker",
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"

      class FailedProcess:
        returncode = 1

        def poll(self):
          return self.returncode

        def wait(self, timeout=None):
          return self.returncode

      def process_factory(command, **kwargs):
        Path(command[-1]).write_bytes(b"partial-hls-data")
        return FailedProcess()

      with self.assertRaises(HlsDownloadError) as raised:
        HlsRecorder("/test/ffmpeg", process_factory).record(
          "https://stream.example.test/index.m3u8?signed-url-marker",
          output,
          headers={"Cookie": "cookie-marker"},
          proxies={"https": "http://proxy-marker"},
          max_retry=1,
        )

      self.assertFalse(output.exists())
      self.assertEqual(
        b"partial-hls-data",
        (output.parent / "live.attempt-1.partial.ts").read_bytes(),
      )
      self.assertEqual(
        b"partial-hls-data",
        (output.parent / "live.attempt-2.partial.ts").read_bytes(),
      )

    message = str(raised.exception)
    self.assertIn("2 attempts", message)
    for value in sensitive_values:
      self.assertNotIn(value, message)

  def test_record_rejects_header_line_injection_before_process_start(self):
    def process_factory(command, **kwargs):
      self.fail("invalid headers must be rejected before starting ffmpeg")

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaisesRegex(ValueError, "CR or LF"):
        HlsRecorder("/test/ffmpeg", process_factory).record(
          "https://stream.example.test/index.m3u8",
          output,
          headers={"Cookie": "valid\r\nInjected: value"},
          max_retry=0,
        )

  def test_record_rejects_negative_retry_count(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaisesRegex(ValueError, "non-negative integer"):
        HlsRecorder("/test/ffmpeg").record(
          "https://stream.example.test/index.m3u8",
          output,
          max_retry=-1,
        )

  def test_record_runs_a_real_executable_and_writes_target(self):
    with tempfile.TemporaryDirectory() as temporary_directory:
      temporary_path = Path(temporary_directory)
      fake_ffmpeg = temporary_path / "fake-ffmpeg"
      fake_ffmpeg.write_text(
        "#!/bin/sh\n"
        "for last_argument do :; done\n"
        "printf 'fake-hls-data' > \"$last_argument\"\n",
        encoding="utf-8",
      )
      fake_ffmpeg.chmod(0o700)
      output = temporary_path / "live.ts"

      result = HlsRecorder(str(fake_ffmpeg)).record(
        "https://stream.example.test/index.m3u8",
        output,
        max_retry=0,
      )

      self.assertEqual(output, result)
      self.assertEqual(b"fake-hls-data", output.read_bytes())


if __name__ == "__main__":
  unittest.main()
