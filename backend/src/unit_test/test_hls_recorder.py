from pathlib import Path
import subprocess
import tempfile
import unittest

from backend.src.platform.douyin.hls_recorder import (
  FfmpegUnavailable,
  HlsDownloadError,
  HlsRecorder,
)


class HlsRecorderTest(unittest.TestCase):
  def test_record_builds_safe_ffmpeg_stream_copy_command(self):
    calls = []

    def runner(command, **kwargs):
      calls.append((command, kwargs))
      return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      result = HlsRecorder("/test/ffmpeg", runner).record(
        "https://stream.example.test/index.m3u8?sign=sensitive",
        output,
        headers={
          "User-Agent": "test-agent",
          "Cookie": "session=sensitive",
          "Empty": None,
        },
        proxies={"http": None, "https": "http://proxy-sensitive"},
        max_retry=0,
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
    self.assertIn("copy", command)
    self.assertIn("mpegts", command)
    self.assertEqual(str(output), command[-1])
    self.assertEqual(
      {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "shell": False,
      },
      kwargs,
    )

  def test_record_retries_until_configured_limit(self):
    return_codes = [1, 1, 0]
    calls = []

    def runner(command, **kwargs):
      calls.append((command, kwargs))
      return subprocess.CompletedProcess(
        command,
        return_codes.pop(0),
        stdout="",
        stderr="temporary failure",
      )

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      result = HlsRecorder("/test/ffmpeg", runner).record(
        "https://stream.example.test/index.m3u8",
        output,
        headers=None,
        proxies=None,
        max_retry=2,
      )

    self.assertEqual(output, result)
    self.assertEqual(3, len(calls))

  def test_record_reports_missing_ffmpeg_without_exposing_url(self):
    def runner(command, **kwargs):
      raise FileNotFoundError(command[0])

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaises(FfmpegUnavailable) as raised:
        HlsRecorder("missing-ffmpeg", runner).record(
          "https://stream.example.test/index.m3u8?sign=sensitive",
          output,
          max_retry=3,
        )

    self.assertIn("ffmpeg executable", str(raised.exception))
    self.assertNotIn("sensitive", str(raised.exception))

  def test_record_reports_unexecutable_ffmpeg_as_unavailable(self):
    def runner(command, **kwargs):
      raise PermissionError(command[0])

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaises(FfmpegUnavailable):
        HlsRecorder("unexecutable-ffmpeg", runner).record(
          "https://stream.example.test/index.m3u8",
          output,
        )

  def test_record_failure_is_redacted_and_preserves_partial_output(self):
    sensitive_values = (
      "signed-url-marker",
      "cookie-marker",
      "proxy-marker",
    )

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"

      def runner(command, **kwargs):
        output.write_bytes(b"partial-hls-data")
        return subprocess.CompletedProcess(
          command,
          1,
          stdout="",
          stderr=" ".join(sensitive_values),
        )

      with self.assertRaises(HlsDownloadError) as raised:
        HlsRecorder("/test/ffmpeg", runner).record(
          "https://stream.example.test/index.m3u8?signed-url-marker",
          output,
          headers={"Cookie": "cookie-marker"},
          proxies={"https": "http://proxy-marker"},
          max_retry=1,
        )

      self.assertEqual(b"partial-hls-data", output.read_bytes())

    message = str(raised.exception)
    self.assertIn("2 attempts", message)
    for value in sensitive_values:
      self.assertNotIn(value, message)

  def test_record_rejects_header_line_injection_before_process_start(self):
    def runner(command, **kwargs):
      self.fail("invalid headers must be rejected before starting ffmpeg")

    with tempfile.TemporaryDirectory() as temporary_directory:
      output = Path(temporary_directory) / "live.ts"
      with self.assertRaisesRegex(ValueError, "CR or LF"):
        HlsRecorder("/test/ffmpeg", runner).record(
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
