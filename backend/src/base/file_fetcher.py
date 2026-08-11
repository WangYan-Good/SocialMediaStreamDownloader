##<<Base>>
import os
from pathlib import Path
from random import uniform
from time import sleep
from urllib.error import ContentTooShortError
from urllib.parse import urlparse
from urllib.request import urlretrieve

##<<Extension>>
from requests import request, exceptions

##<<Third-part>>
from backend.src.library.loglib import get_logger


##
## Retryable transport failures.  Anything else (a bad path, a full disk, a
## programming error) propagates on the first attempt: retrying those only
## delays the report.
##
RETRYABLE = (ContentTooShortError, exceptions.RequestException, TimeoutError)

##
## What to do when the target file name is already taken.
##
##   unique    - append an ``re_N_`` prefix and keep the existing file.  The live
##               path needs this: every recording session is a distinct file that
##               happens to derive its name from the same stream.
##   skip      - leave the existing file alone and report nothing was written.
##               The post path needs this: a file name carries the aweme id, so
##               the same name means the same content, and re-submitting a link
##               must not produce a second copy.
##   overwrite - replace the existing file.
##
ON_EXISTS_UNIQUE = "unique"
ON_EXISTS_SKIP = "skip"
ON_EXISTS_OVERWRITE = "overwrite"
_ON_EXISTS_CHOICES = (ON_EXISTS_UNIQUE, ON_EXISTS_SKIP, ON_EXISTS_OVERWRITE)

DEFAULT_CHUNK_SIZE = 1024 * 1024

##
## Retry pacing.  An immediate retry re-sends into the same window that just
## refused the request, so a single rejection becomes four requests inside a few
## hundred milliseconds -- the CDN reads that as more load, not less.
##
## The wait doubles per attempt and carries equal jitter (half fixed, half
## random) so that concurrent downloads, which fail together, do not come back
## together.
##
DEFAULT_RETRY_BACKOFF = 1.0
DEFAULT_RETRY_BACKOFF_MAX = 30.0

##
## 429 is not a transport hiccup, it is the server naming the problem: the
## caller is going too fast.  Pacing it on the transport schedule is what turned
## one refusal into four requests, so it gets a wider window of its own, and
## when the response carries ``Retry-After`` that number wins outright -- capped
## only so a rate limit cannot park a download indefinitely.
##
RATE_LIMIT_STATUS = 429
DEFAULT_RATE_LIMIT_BACKOFF = 5.0
RETRY_AFTER_MAX = 60.0


def _jittered(window: float) -> float:
  """Half the window fixed, half random, so parallel workers spread out."""
  return window / 2 + uniform(0, window / 2)


def _is_rate_limited(error) -> bool:
  response = getattr(error, "response", None)
  return getattr(response, "status_code", None) == RATE_LIMIT_STATUS


def _retry_after_seconds(error):
  """Seconds demanded by ``Retry-After``, or ``None`` if it says nothing usable.

  The header may also hold an HTTP date.  We do not read that form: falling back
  to the rate-limit window is already the safe answer, and a date we misparse
  would be worse than one we ignore.
  """
  response = getattr(error, "response", None)
  headers = getattr(response, "headers", None) or {}
  raw = headers.get("Retry-After")
  if raw is None:
    return None
  try:
    return max(0.0, float(str(raw).strip()))
  except (TypeError, ValueError):
    return None


def _retry_delay(
  error,
  attempt: int,
  backoff: float,
  backoff_max: float,
  rate_limit_backoff: float,
) -> float:
  """Seconds to wait before ``attempt``, doubling per attempt with jitter."""
  if _is_rate_limited(error):
    demanded = _retry_after_seconds(error)
    if demanded is not None:
      ##
      ## jittered upward, never below what was asked for
      ##
      return min(demanded, RETRY_AFTER_MAX) + uniform(0, 1.0)
    return _jittered(min(rate_limit_backoff * (2 ** (attempt - 1)), backoff_max))
  return _jittered(min(backoff * (2 ** (attempt - 1)), backoff_max))


def _unique_path(directory: Path, file_name: str) -> Path:
  """Return ``directory/file_name``, prefixed with ``re_N_`` if taken."""
  candidate = directory / file_name
  duplicate_index = 0
  while candidate.exists():
    candidate = directory / "re_{}_{}".format(duplicate_index, file_name)
    duplicate_index += 1
  return candidate


def _resolve_target(directory: Path, file_name: str, on_exists: str):
  """Return the path to write, or ``None`` when the fetch should be skipped."""
  target = directory / file_name
  if not target.exists():
    return target
  if on_exists == ON_EXISTS_SKIP:
    return None
  if on_exists == ON_EXISTS_OVERWRITE:
    return target
  return _unique_path(directory, file_name)


def _stream_to_file(
  url: str,
  target: Path,
  headers: dict,
  proxies: dict,
  timeout: int,
  chunk_size: int,
):
  """Download ``url`` into ``target``, verifying the advertised length."""
  response = None
  try:
    response = request(
      method="GET",
      url=url,
      headers=headers,
      proxies=proxies,
      timeout=timeout,
      stream=True,
    )
    response.raise_for_status()
    written_size = 0
    with open(target, "wb") as output:
      for chunk in response.iter_content(chunk_size=chunk_size):
        if not chunk:
          continue
        output.write(chunk)
        written_size += len(chunk)

    content_length = response.headers.get("Content-Length")
    if content_length is not None and written_size < int(content_length):
      raise ContentTooShortError("incomplete download", written_size)
  finally:
    if response is not None and hasattr(response, "close"):
      response.close()


def _discard_partial(target: Path) -> None:
  """Remove a partially written file.

  Only for callers that pass ``keep_partial=False``; see ``fetch_file``.
  """
  try:
    if target.exists():
      target.unlink()
  except OSError as e:
    get_logger().warning(
      "could not remove partial file {}: {}".format(target, e)
    )


def fetch_file(
  url: str,
  save_path,
  file_name: str,
  headers: dict = None,
  proxies: dict = None,
  timeout: int = 10,
  max_retry: int = 0,
  on_exists: str = ON_EXISTS_UNIQUE,
  keep_partial: bool = True,
  chunk_size: int = DEFAULT_CHUNK_SIZE,
  retry_backoff: float = DEFAULT_RETRY_BACKOFF,
  retry_backoff_max: float = DEFAULT_RETRY_BACKOFF_MAX,
  rate_limit_backoff: float = DEFAULT_RATE_LIMIT_BACKOFF,
):
  """Fetch ``url`` into ``save_path/file_name`` and return the path written.

  Returns ``None`` only when ``on_exists`` is ``skip`` and the target already
  exists; every other outcome either returns a path or raises.

  ``max_retry`` counts attempts *after* the first, matching
  ``$.download.max_retry``: ``max_retry=2`` means at most three attempts.

  ``keep_partial`` decides what a failed attempt leaves on disk, and the two
  download paths need opposite answers:

  - Live recording keeps it (the default).  A stream cut off after two hours is
    still two hours of recording, and deleting it would undo the fix that made
    an interrupted download save what it had already received.
  - Post download discards it.  There the file name encodes the aweme id, so a
    truncated file would later read as a completed download and suppress the
    retry that would have finished it.

  Retries are paced: ``retry_backoff`` doubles per attempt up to
  ``retry_backoff_max``, and a rate-limited response waits on the wider
  ``rate_limit_backoff`` schedule instead, or on ``Retry-After`` when the server
  sends one.  Tests replace this module's ``sleep`` to keep the wait off the
  clock.
  """
  if on_exists not in _ON_EXISTS_CHOICES:
    raise ValueError(
      "on_exists must be one of {}, got {!r}".format(
        _ON_EXISTS_CHOICES,
        on_exists,
      )
    )
  if max_retry < 0:
    raise ValueError("max_retry must not be negative")

  directory = Path(save_path)
  os.makedirs(directory, exist_ok=True)

  target = _resolve_target(directory, file_name, on_exists)
  if target is None:
    get_logger().info(
      "file already present, skip download: {}".format(directory / file_name)
    )
    return None

  is_http = urlparse(url).scheme in ("http", "https")
  attempt = 0
  while True:
    try:
      if is_http:
        _stream_to_file(url, target, headers, proxies, timeout, chunk_size)
      else:
        urlretrieve(url, str(target))
      return target
    except RETRYABLE as e:
      if not keep_partial:
        _discard_partial(target)
      if attempt >= max_retry:
        raise
      attempt += 1
      delay = _retry_delay(
        e,
        attempt,
        retry_backoff,
        retry_backoff_max,
        rate_limit_backoff,
      )
      get_logger().warning(
        "download attempt {} of {} failed{}, retrying in {:.1f}s: {}".format(
          attempt,
          max_retry + 1,
          " (rate limited)" if _is_rate_limited(e) else "",
          delay,
          url,
        )
      )
      sleep(delay)
