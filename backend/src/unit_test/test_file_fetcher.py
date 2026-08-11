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
  ##
  ## These assert retry counts, not pacing, so the backoff is silenced: leaving
  ## it in would make the suite sleep through every retry it exercises.
  ##
  def setUp(self):
    self._original_sleep = fetcher_module.sleep
    self.slept = []
    fetcher_module.sleep = self.slept.append

  def tearDown(self):
    fetcher_module.sleep = self._original_sleep

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


class FileFetcherBackoffTest(unittest.TestCase):
  """Retries must wait, and the wait must grow.

  A retry that fires immediately re-sends into the very window the server just
  refused, which is how a single rejection turns into four requests in 300ms.
  """

  def _failing_fetch(self, directory, max_retry, **kwargs):
    """Run a fetch that always fails, returning the waits it asked for."""
    slept = []
    attempts = []

    def fake_request(**request_kwargs):
      attempts.append(request_kwargs["url"])
      raise exceptions.ConnectionError("refused")

    original_request = fetcher_module.request
    original_sleep = fetcher_module.sleep
    fetcher_module.request = fake_request
    fetcher_module.sleep = slept.append
    try:
      with self.assertRaises(exceptions.ConnectionError):
        fetch_file(
          "https://example.test/file.bin",
          directory,
          "file.bin",
          max_retry=max_retry,
          **kwargs
        )
    finally:
      fetcher_module.request = original_request
      fetcher_module.sleep = original_sleep
    return slept, attempts

  def test_each_retry_waits_longer_than_the_one_before(self):
    with tempfile.TemporaryDirectory() as directory:
      slept, attempts = self._failing_fetch(directory, 3, retry_backoff=1.0)

      self.assertEqual(len(attempts), 4)
      ##
      ## one wait per retry, none before the first attempt
      ##
      self.assertEqual(len(slept), 3)
      ##
      ## equal jitter: each wait lands in [d/2, d] for d = 1, 2, 4
      ##
      self.assertGreaterEqual(slept[0], 0.5)
      self.assertLessEqual(slept[0], 1.0)
      self.assertGreaterEqual(slept[1], 1.0)
      self.assertLessEqual(slept[1], 2.0)
      self.assertGreaterEqual(slept[2], 2.0)
      self.assertLessEqual(slept[2], 4.0)

  def test_no_wait_after_the_final_attempt(self):
    """The budget is spent, so sleeping only delays the report."""
    with tempfile.TemporaryDirectory() as directory:
      slept, attempts = self._failing_fetch(directory, 0, retry_backoff=1.0)

      self.assertEqual(len(attempts), 1)
      self.assertEqual(slept, [])

  def test_backoff_is_capped(self):
    with tempfile.TemporaryDirectory() as directory:
      slept, _ = self._failing_fetch(
        directory,
        6,
        retry_backoff=1.0,
        retry_backoff_max=3.0,
      )

      self.assertEqual(len(slept), 6)
      for wait in slept:
        self.assertLessEqual(wait, 3.0)
      ##
      ## the cap is reached, not merely approached
      ##
      self.assertGreaterEqual(max(slept), 1.5)

  def test_jitter_keeps_parallel_workers_from_retrying_in_lockstep(self):
    """Three concurrent downloads must not re-send at the same instant."""
    with tempfile.TemporaryDirectory() as directory:
      first_waits = [
        self._failing_fetch(directory, 1, retry_backoff=8.0)[0][0]
        for _ in range(12)
      ]

      self.assertGreater(len(set(first_waits)), 1)


class RateLimitedResponse(FakeResponse):
  """A CDN response that refuses the request with 429 Too Many Requests."""

  def __init__(self, retry_after=None):
    super().__init__([])
    self.status_code = 429
    if retry_after is not None:
      self.headers["Retry-After"] = str(retry_after)

  def raise_for_status(self):
    raise exceptions.HTTPError(
      "429 Client Error: Too Many Requests",
      response=self,
    )


class FileFetcherRateLimitTest(unittest.TestCase):
  """429 is an instruction, not a transport hiccup.

  It says the caller is going too fast, so it has to be paced differently from
  a dropped connection -- and when the server names its own interval, that
  number wins over any interval we invented.
  """

  def _rate_limited_fetch(self, directory, retry_after=None, **kwargs):
    slept = []

    def fake_request(**request_kwargs):
      return RateLimitedResponse(retry_after=retry_after)

    original_request = fetcher_module.request
    original_sleep = fetcher_module.sleep
    fetcher_module.request = fake_request
    fetcher_module.sleep = slept.append
    try:
      with self.assertRaises(exceptions.HTTPError):
        fetch_file(
          "https://example.test/file.bin",
          directory,
          "file.bin",
          max_retry=1,
          **kwargs
        )
    finally:
      fetcher_module.request = original_request
      fetcher_module.sleep = original_sleep
    return slept

  def _transport_failure_wait(self, directory, **kwargs):
    slept = []

    def fake_request(**request_kwargs):
      raise exceptions.ConnectionError("refused")

    original_request = fetcher_module.request
    original_sleep = fetcher_module.sleep
    fetcher_module.request = fake_request
    fetcher_module.sleep = slept.append
    try:
      with self.assertRaises(exceptions.ConnectionError):
        fetch_file(
          "https://example.test/other.bin",
          directory,
          "other.bin",
          max_retry=1,
          **kwargs
        )
    finally:
      fetcher_module.request = original_request
      fetcher_module.sleep = original_sleep
    return slept[0]

  def test_retry_after_header_is_honoured(self):
    with tempfile.TemporaryDirectory() as directory:
      slept = self._rate_limited_fetch(directory, retry_after=7)

      self.assertEqual(len(slept), 1)
      ##
      ## never come back before the server said to
      ##
      self.assertGreaterEqual(slept[0], 7.0)
      self.assertLessEqual(slept[0], 8.0)

  def test_rate_limit_waits_longer_than_a_transport_failure(self):
    """Retrying a 429 on the transport schedule is what amplified the limit."""
    with tempfile.TemporaryDirectory() as directory:
      rate_limited = self._rate_limited_fetch(directory, retry_backoff=1.0)[0]
      transport = self._transport_failure_wait(directory, retry_backoff=1.0)

      self.assertGreater(rate_limited, transport)
      ##
      ## half of the 5s rate-limit window is the floor
      ##
      self.assertGreaterEqual(rate_limited, 2.5)

  def test_an_absurd_retry_after_is_clamped_to_the_ceiling(self):
    """A rate limit must not park a download for an hour.

    The header is still respected as far as the ceiling allows -- clamped, not
    discarded, so an hour becomes the longest wait we permit rather than the
    shortest one we would have chosen anyway.
    """
    with tempfile.TemporaryDirectory() as directory:
      slept = self._rate_limited_fetch(directory, retry_after=3600)

      self.assertGreaterEqual(slept[0], 60.0)
      self.assertLessEqual(slept[0], 61.0)

  def test_unparseable_retry_after_falls_back_to_the_rate_limit_wait(self):
    """``Retry-After`` may be an HTTP date; we still have to pace ourselves."""
    with tempfile.TemporaryDirectory() as directory:
      slept = self._rate_limited_fetch(
        directory,
        retry_after="Wed, 21 Oct 2026 07:28:00 GMT",
      )

      self.assertEqual(len(slept), 1)
      self.assertGreaterEqual(slept[0], 2.5)
      self.assertLessEqual(slept[0], 5.0)


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
