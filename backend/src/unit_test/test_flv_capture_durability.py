import builtins
from datetime import datetime
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from backend.src.base import file_fetcher as fetcher_module
from backend.src.base.file_fetcher import fetch_file
from backend.src.platform.douyin import douyin_live_downloader as live_module
from backend.src.platform.douyin.douyin_live_downloader import LiveDownloadResult
from backend.src.service.live_recording_task import LiveRecordingTaskService


class Response:
  def __init__(self, chunks=(b"flv-media",), content_length=None, events=None):
    self._chunks = chunks
    self._content_length = content_length
    self._events = events
    self.closed = False

  @property
  def headers(self):
    response = self

    class Headers:
      def get(self, name):
        if response._events is not None:
          response._events.append("validate-length")
        if name == "Content-Length" and response._content_length is not None:
          return str(response._content_length)
        return None

    return Headers()

  def raise_for_status(self):
    return None

  def iter_content(self, chunk_size=None):
    return iter(self._chunks)

  def close(self):
    self.closed = True


class FlvDurabilityOrderingTest(unittest.TestCase):
  def test_success_orders_buffer_file_close_and_parent_commit_before_return(self):
    events = []

    class Output:
      def __enter__(self):
        return self

      def write(self, chunk):
        events.append("write")
        return len(chunk)

      def flush(self):
        events.append("flush")

      def fileno(self):
        return 41

      def __exit__(self, exc_type, exc, traceback):
        events.append("close-file")

    response = Response(content_length=9, events=events)

    def fsync(descriptor):
      events.append("fsync-file" if descriptor == 41 else "fsync-parent")

    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", return_value=response
    ), patch.object(fetcher_module, "open", return_value=Output(), create=True), patch.object(
      fetcher_module.os, "open", side_effect=lambda path, flags: events.append(
        "open-parent"
      ) or 84
    ), patch.object(fetcher_module.os, "fsync", side_effect=fsync), patch.object(
      fetcher_module.os, "close", side_effect=lambda fd: events.append("close-parent")
    ):
      target = fetch_file(
        "https://cdn.example.test/live.flv",
        directory,
        "live.flv",
        durable_success=True,
      )
      events.append("return-success")

    self.assertEqual(Path(directory) / "live.flv", target)
    self.assertEqual(
      [
        "write",
        "validate-length",
        "flush",
        "fsync-file",
        "close-file",
        "open-parent",
        "fsync-parent",
        "close-parent",
        "return-success",
      ],
      events,
    )

  def test_default_fetch_does_not_add_a_durability_barrier(self):
    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", return_value=Response()
    ), patch.object(
      fetcher_module.os,
      "fsync",
      side_effect=AssertionError("post/default fetch must not fsync"),
    ):
      target = fetch_file(
        "https://cdn.example.test/post.mp4", directory, "post.mp4"
      )
      written = target.read_bytes()

    self.assertEqual(b"flv-media", written)

  def test_non_http_durable_fetch_is_rejected_before_transfer(self):
    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module,
      "urlretrieve",
      side_effect=AssertionError("unsupported transfer must not start"),
    ):
      with self.assertRaises(ValueError):
        fetch_file(
          "file:///tmp/live.flv",
          directory,
          "live.flv",
          durable_success=True,
        )

  def test_content_length_must_match_exactly_before_durable_success(self):
    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module,
      "request",
      return_value=Response(chunks=(b"too-many-bytes",), content_length=3),
    ):
      with self.assertRaises(Exception):
        fetch_file(
          "https://cdn.example.test/live.flv",
          directory,
          "live.flv",
          durable_success=True,
        )


class FlvDurabilityFailureTest(unittest.TestCase):
  def _failure(self, fail_at):
    requests = []
    real_fsync = os.fsync
    calls = []

    def request(**kwargs):
      requests.append(kwargs["url"])
      return Response(chunks=(b"captured-before-fsync",))

    def fsync(descriptor):
      calls.append(descriptor)
      if len(calls) == fail_at:
        raise OSError("durability failed")
      return real_fsync(descriptor)

    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", side_effect=request
    ), patch.object(fetcher_module.os, "fsync", side_effect=fsync):
      target = Path(directory) / "live.flv"
      with self.assertRaises(OSError):
        fetch_file(
          "https://cdn.example.test/live.flv",
          directory,
          target.name,
          max_retry=5,
          durable_success=True,
        )
      retained = target.read_bytes()

    return requests, retained

  def test_file_fsync_failure_retains_bytes_and_never_retries_network(self):
    requests, retained = self._failure(fail_at=1)

    self.assertEqual(["https://cdn.example.test/live.flv"], requests)
    self.assertEqual(b"captured-before-fsync", retained)

  def test_parent_fsync_failure_retains_bytes_and_never_retries_network(self):
    requests, retained = self._failure(fail_at=2)

    self.assertEqual(["https://cdn.example.test/live.flv"], requests)
    self.assertEqual(b"captured-before-fsync", retained)

  def test_response_close_cannot_mask_or_retry_a_storage_failure(self):
    requests = []

    class CloseFailureResponse(Response):
      def close(self):
        raise fetcher_module.exceptions.RequestException(
          "response-close-secret"
        )

    def request(**kwargs):
      requests.append(kwargs["url"])
      return CloseFailureResponse(chunks=(b"retained",))

    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", side_effect=request
    ), patch.object(
      fetcher_module.os,
      "fsync",
      side_effect=OSError("primary-storage-failure"),
    ):
      target = Path(directory) / "live.flv"
      with self.assertRaisesRegex(OSError, "primary-storage-failure"):
        fetch_file(
          "https://cdn.example.test/live.flv",
          directory,
          target.name,
          max_retry=3,
          durable_success=True,
        )

      self.assertEqual(b"retained", target.read_bytes())
      self.assertEqual(1, len(requests))

  def test_file_close_failure_prevents_parent_commit_and_success(self):
    real_open = builtins.open
    parent_opens = []
    requests = []

    class CloseFailure:
      def __init__(self, path):
        self._file = real_open(path, "wb")

      def __enter__(self):
        return self._file

      def __exit__(self, exc_type, exc, traceback):
        self._file.close()
        raise OSError("close failed")

    def request(**kwargs):
      requests.append(kwargs["url"])
      return Response()

    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", side_effect=request
    ), patch.object(
      fetcher_module,
      "open",
      side_effect=lambda path, mode: CloseFailure(path),
      create=True,
    ), patch.object(
      fetcher_module.os,
      "open",
      side_effect=lambda path, flags: parent_opens.append(path),
    ):
      target = Path(directory) / "live.flv"
      with self.assertRaises(OSError):
        fetch_file(
          "https://cdn.example.test/live.flv",
          directory,
          target.name,
          max_retry=5,
          durable_success=True,
        )

      self.assertEqual(b"flv-media", target.read_bytes())
      self.assertEqual([], parent_opens)
      self.assertEqual(1, len(requests))

  def test_real_file_and_directory_descriptors_close_after_success(self):
    real_open = builtins.open
    real_os_open = os.open
    descriptors = []

    class TrackingFile:
      def __init__(self, path, mode):
        self._file = real_open(path, mode)

      def __enter__(self):
        descriptors.append(self._file.fileno())
        return self._file

      def __exit__(self, exc_type, exc, traceback):
        return self._file.__exit__(exc_type, exc, traceback)

    def open_directory(path, flags):
      descriptor = real_os_open(path, flags)
      descriptors.append(descriptor)
      return descriptor

    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", return_value=Response()
    ), patch.object(
      fetcher_module, "open", side_effect=TrackingFile, create=True
    ), patch.object(fetcher_module.os, "open", side_effect=open_directory):
      fetch_file(
        "https://cdn.example.test/live.flv",
        directory,
        "live.flv",
        durable_success=True,
      )

    self.assertEqual(2, len(descriptors))
    for descriptor in descriptors:
      with self.assertRaises(OSError):
        os.fstat(descriptor)

  def test_real_file_and_directory_descriptors_close_after_parent_failure(self):
    real_open = builtins.open
    real_os_open = os.open
    real_fsync = os.fsync
    descriptors = []
    fsync_calls = []

    class TrackingFile:
      def __init__(self, path, mode):
        self._file = real_open(path, mode)

      def __enter__(self):
        descriptors.append(self._file.fileno())
        return self._file

      def __exit__(self, exc_type, exc, traceback):
        return self._file.__exit__(exc_type, exc, traceback)

    def open_directory(path, flags):
      descriptor = real_os_open(path, flags)
      descriptors.append(descriptor)
      return descriptor

    def fsync(descriptor):
      fsync_calls.append(descriptor)
      if len(fsync_calls) == 2:
        raise OSError("parent sync failed")
      return real_fsync(descriptor)

    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", return_value=Response()
    ), patch.object(
      fetcher_module, "open", side_effect=TrackingFile, create=True
    ), patch.object(
      fetcher_module.os, "open", side_effect=open_directory
    ), patch.object(fetcher_module.os, "fsync", side_effect=fsync):
      with self.assertRaises(OSError):
        fetch_file(
          "https://cdn.example.test/live.flv",
          directory,
          "live.flv",
          durable_success=True,
        )

    self.assertEqual(2, len(descriptors))
    for descriptor in descriptors:
      with self.assertRaises(OSError):
        os.fstat(descriptor)


class LiveFlvDurabilityIntegrationTest(unittest.TestCase):
  def test_live_auto_down_enables_the_narrow_durable_contract(self):
    class Config:
      def get_config_dict_attr(self, path):
        return 3

    downloader = object.__new__(live_module.DouyinLiveDownloader)
    downloader.config = Config()

    with patch.object(live_module, "fetch_file", return_value=Path("live.flv")) as fetch:
      downloader.auto_down(
        "https://cdn.example.test/live.flv",
        "/media",
        "live.flv",
        0,
      )

    self.assertTrue(fetch.call_args.kwargs["durable_success"])

  def test_parent_commit_precedes_result_journal_and_database(self):
    events = []
    real_fsync = os.fsync
    fsync_count = []

    def fsync(descriptor):
      fsync_count.append(descriptor)
      real_fsync(descriptor)
      events.append("fsync-file" if len(fsync_count) == 1 else "fsync-parent")

    class Downloader:
      def __init__(self, directory):
        self.directory = directory

      def run_with_result(self, token):
        path = fetch_file(
          "https://cdn.example.test/live.flv",
          self.directory,
          "live.flv",
          durable_success=True,
        )
        events.append("result")
        return LiveDownloadResult(
          ok=True,
          recorded=True,
          room_status=2,
          room_id="998877",
          owner_user_id="owner-1",
          nickname="Host",
          title="Live",
          protocol="flv",
          output_path=str(path),
          started_at=datetime(2026, 8, 31, 1, 0, 0),
          finished_at=datetime(2026, 8, 31, 2, 0, 0),
        )

    class Recording:
      def prepare(self, result, **kwargs):
        return object()

      def record_prepared(self, intent, *, recovery_key=None):
        events.append("database")
        return 73

    class Journal:
      def publish(self, intent, recovery_key):
        events.append("journal-publish")

      def acknowledge(self, recovery_key):
        events.append("journal-ack")

    with tempfile.TemporaryDirectory() as directory, patch.object(
      fetcher_module, "request", return_value=Response()
    ), patch.object(fetcher_module.os, "fsync", side_effect=fsync):
      service = LiveRecordingTaskService(
        downloader_factory=lambda: Downloader(directory),
        recording_service=Recording(),
        recovery_journal=Journal(),
        recovery_key_factory=lambda: "0123456789abcdef0123456789abcdef",
      )
      result = service._run(None, {"url": "https://v.douyin.com/example/"}, 7)

    self.assertTrue(result.recorded)
    self.assertLess(events.index("fsync-parent"), events.index("result"))
    self.assertLess(events.index("result"), events.index("journal-publish"))
    self.assertLess(events.index("journal-publish"), events.index("database"))

  def test_durability_failure_never_reaches_result_journal_or_database(self):
    for fail_at in (1, 2):
      with self.subTest(fail_at=fail_at), tempfile.TemporaryDirectory() as directory:
        events = []
        requests = []
        real_fsync = os.fsync
        fsync_calls = []

        def request(**kwargs):
          requests.append(kwargs["url"])
          return Response(chunks=(b"retained",))

        def fsync(descriptor):
          fsync_calls.append(descriptor)
          if len(fsync_calls) == fail_at:
            raise OSError("durability failed")
          return real_fsync(descriptor)

        class Downloader:
          def run_with_result(self, token):
            fetch_file(
              "https://cdn.example.test/live.flv",
              directory,
              "live.flv",
              max_retry=4,
              durable_success=True,
            )
            events.append("result")

        class Recording:
          def prepare(self, result, **kwargs):
            events.append("database-prepare")

          def record_prepared(self, intent, *, recovery_key=None):
            events.append("database")

        class Journal:
          def publish(self, intent, recovery_key):
            events.append("journal")

          def acknowledge(self, recovery_key):
            events.append("ack")

        service = LiveRecordingTaskService(
          downloader_factory=Downloader,
          recording_service=Recording(),
          recovery_journal=Journal(),
        )
        with patch.object(fetcher_module, "request", side_effect=request), patch.object(
          fetcher_module.os, "fsync", side_effect=fsync
        ):
          with self.assertRaises(OSError):
            service._run(None, {"url": "https://v.douyin.com/example/"}, 7)

        self.assertEqual([], events)
        self.assertEqual(1, len(requests))
        self.assertEqual(b"retained", (Path(directory) / "live.flv").read_bytes())


if __name__ == "__main__":
  unittest.main()
