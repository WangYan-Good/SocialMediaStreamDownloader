import tempfile
import unittest
from pathlib import Path
from urllib.error import ContentTooShortError

from requests import exceptions

from backend.src.base import file_fetcher as fetcher_module
from backend.src.base.file_fetcher import (
  ON_EXISTS_OVERWRITE,
  ON_EXISTS_SKIP,
  ON_EXISTS_UNIQUE,
  fetch_file,
)


class FakeResponse:
  """Minimal stand-in for a streaming ``requests`` response."""

  def __init__(self, chunks, content_length=None, status_error=None):
    self._chunks = chunks
    self.headers = {}
    if content_length is not None:
      self.headers["Content-Length"] = str(content_length)
    self._status_error = status_error
    self.closed = False

  def raise_for_status(self):
    if self._status_error is not None:
      raise self._status_error

  def iter_content(self, chunk_size=None):
    return iter(self._chunks)

  def close(self):
    self.closed = True


class FileFetcherOnExistsTest(unittest.TestCase):
  """The three name-collision policies the two download paths need."""

  def _fetch_into(self, directory, on_exists, chunks=(b"payload",)):
    responses = []

    def fake_request(**kwargs):
      response = FakeResponse(list(chunks))
      responses.append(response)
      return response

    original_request = fetcher_module.request
    fetcher_module.request = fake_request
    try:
      return fetch_file(
        "https://example.test/file.bin",
        directory,
        "file.bin",
        on_exists=on_exists,
      )
    finally:
      fetcher_module.request = original_request

  def test_unique_keeps_existing_file_and_writes_prefixed_name(self):
    with tempfile.TemporaryDirectory() as directory:
      existing = Path(directory) / "file.bin"
      existing.write_bytes(b"first")

      written = self._fetch_into(directory, ON_EXISTS_UNIQUE, (b"second",))

      self.assertEqual(written, Path(directory) / "re_0_file.bin")
      self.assertEqual(existing.read_bytes(), b"first")
      self.assertEqual(written.read_bytes(), b"second")

  def test_unique_increments_until_a_free_name_is_found(self):
    with tempfile.TemporaryDirectory() as directory:
      (Path(directory) / "file.bin").write_bytes(b"a")
      (Path(directory) / "re_0_file.bin").write_bytes(b"b")

      written = self._fetch_into(directory, ON_EXISTS_UNIQUE, (b"c",))

      self.assertEqual(written, Path(directory) / "re_1_file.bin")

  def test_skip_reports_nothing_written_and_leaves_the_file_untouched(self):
    with tempfile.TemporaryDirectory() as directory:
      existing = Path(directory) / "file.bin"
      existing.write_bytes(b"already here")

      written = self._fetch_into(directory, ON_EXISTS_SKIP, (b"new",))

      self.assertIsNone(written)
      self.assertEqual(existing.read_bytes(), b"already here")

  def test_skip_downloads_when_the_target_is_absent(self):
    with tempfile.TemporaryDirectory() as directory:
      written = self._fetch_into(directory, ON_EXISTS_SKIP, (b"new",))

      self.assertEqual(written, Path(directory) / "file.bin")
      self.assertEqual(written.read_bytes(), b"new")

  def test_overwrite_replaces_the_existing_file(self):
    with tempfile.TemporaryDirectory() as directory:
      existing = Path(directory) / "file.bin"
      existing.write_bytes(b"stale")

      written = self._fetch_into(directory, ON_EXISTS_OVERWRITE, (b"fresh",))

      self.assertEqual(written, existing)
      self.assertEqual(existing.read_bytes(), b"fresh")

  def test_unknown_policy_is_rejected(self):
    with tempfile.TemporaryDirectory() as directory:
      with self.assertRaises(ValueError):
        fetch_file(
          "https://example.test/file.bin",
          directory,
          "file.bin",
          on_exists="clobber-maybe",
        )

  def test_negative_retry_budget_is_rejected(self):
    with tempfile.TemporaryDirectory() as directory:
      with self.assertRaises(ValueError):
        fetch_file(
          "https://example.test/file.bin",
          directory,
          "file.bin",
          max_retry=-1,
        )


class FileFetcherRetryTest(unittest.TestCase):
  def test_short_content_is_retried_then_raised(self):
    attempts = []

    def fake_request(**kwargs):
      attempts.append(kwargs["url"])
      return FakeResponse([b"12"], content_length=100)

    with tempfile.TemporaryDirectory() as directory:
      original_request = fetcher_module.request
      fetcher_module.request = fake_request
      try:
        with self.assertRaises(ContentTooShortError):
          fetch_file(
            "https://example.test/file.bin",
            directory,
            "file.bin",
            max_retry=2,
          )
      finally:
        fetcher_module.request = original_request

      ##
      ## max_retry counts attempts after the first
      ##
      self.assertEqual(len(attempts), 3)

  def test_partial_file_is_kept_by_default(self):
    """An interrupted download keeps what it already received.

    This is the live recording contract: a stream cut off part way through is
    still a usable recording, so the bytes on disk must survive the failure.
    """

    def fake_request(**kwargs):
      return FakeResponse([b"received-before-the-cut"], content_length=100)

    with tempfile.TemporaryDirectory() as directory:
      original_request = fetcher_module.request
      fetcher_module.request = fake_request
      try:
        with self.assertRaises(ContentTooShortError):
          fetch_file(
            "https://example.test/file.bin",
            directory,
            "file.bin",
            max_retry=0,
          )
      finally:
        fetcher_module.request = original_request

      target = Path(directory) / "file.bin"
      self.assertTrue(target.is_file())
      self.assertEqual(target.read_bytes(), b"received-before-the-cut")

  def test_partial_file_is_discarded_when_keep_partial_is_false(self):
    """A truncated post file must not survive to look like a finished one.

    The post path names files after the aweme id, so a leftover fragment would
    later read as a completed download and suppress the retry that would have
    finished it.
    """

    def fake_request(**kwargs):
      return FakeResponse([b"12"], content_length=100)

    with tempfile.TemporaryDirectory() as directory:
      original_request = fetcher_module.request
      fetcher_module.request = fake_request
      try:
        with self.assertRaises(ContentTooShortError):
          fetch_file(
            "https://example.test/file.bin",
            directory,
            "file.bin",
            max_retry=1,
            on_exists=ON_EXISTS_SKIP,
            keep_partial=False,
          )
      finally:
        fetcher_module.request = original_request

      self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), [])

  def test_non_retryable_error_propagates_immediately(self):
    attempts = []

    def fake_request(**kwargs):
      attempts.append(kwargs["url"])
      return FakeResponse([], status_error=ValueError("bad payload"))

    with tempfile.TemporaryDirectory() as directory:
      original_request = fetcher_module.request
      fetcher_module.request = fake_request
      try:
        with self.assertRaises(ValueError):
          fetch_file(
            "https://example.test/file.bin",
            directory,
            "file.bin",
            max_retry=5,
          )
      finally:
        fetcher_module.request = original_request

      self.assertEqual(len(attempts), 1)

  def test_request_exception_is_retryable(self):
    attempts = []

    def fake_request(**kwargs):
      attempts.append(kwargs["url"])
      raise exceptions.ConnectionError("refused")

    with tempfile.TemporaryDirectory() as directory:
      original_request = fetcher_module.request
      fetcher_module.request = fake_request
      try:
        with self.assertRaises(exceptions.ConnectionError):
          fetch_file(
            "https://example.test/file.bin",
            directory,
            "file.bin",
            max_retry=1,
          )
      finally:
        fetcher_module.request = original_request

      self.assertEqual(len(attempts), 2)

  def test_response_is_closed_even_when_the_write_fails(self):
    created = []

    def fake_request(**kwargs):
      response = FakeResponse([b"12"], content_length=100)
      created.append(response)
      return response

    with tempfile.TemporaryDirectory() as directory:
      original_request = fetcher_module.request
      fetcher_module.request = fake_request
      try:
        with self.assertRaises(ContentTooShortError):
          fetch_file(
            "https://example.test/file.bin",
            directory,
            "file.bin",
            max_retry=0,
          )
      finally:
        fetcher_module.request = original_request

      self.assertTrue(all(response.closed for response in created))


class FileFetcherDirectoryTest(unittest.TestCase):
  def test_missing_directory_is_created(self):
    def fake_request(**kwargs):
      return FakeResponse([b"payload"])

    with tempfile.TemporaryDirectory() as directory:
      nested = Path(directory) / "douyin" / "aweme" / "Owner"
      original_request = fetcher_module.request
      fetcher_module.request = fake_request
      try:
        written = fetch_file(
          "https://example.test/file.bin",
          nested,
          "file.bin",
        )
      finally:
        fetcher_module.request = original_request

      self.assertTrue(nested.is_dir())
      self.assertEqual(written, nested / "file.bin")


if __name__ == "__main__":
  unittest.main()
