"""No-network runtime proof that post-download diagnostics carry no raw values.

Runs inside the production image against the real post modules with an injected
transport standing in for the platform. No network, no database and no platform
credentials are involved.

The transport is what makes this a runtime proof rather than a formatter test:
the share urls, signed request urls, response bodies, cookies and exception
messages below travel through the shipped ``DouyinAwemeResolver`` and
``DouyinAwemeDownloader`` code paths, and what is captured is whatever those
paths actually emit at every level a deployment can be configured to.
"""

from contextlib import contextmanager
import io
import logging
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if not (PROJECT_ROOT / "backend").is_dir():
  PROJECT_ROOT = Path("/app")
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import post_diagnostic
from backend.src.platform.douyin.douyin_aweme_downloader import (
  DouyinAwemeDownloader,
)
from backend.src.platform.douyin.douyin_aweme_resolver import (
  AwemeResolution,
  DouyinAwemeResolver,
)


SECRET_POST_SHARE_URL = "https://v.douyin.test/SECRET_POST_SHARE_URL_RUNTIME/"
SECRET_SIGNED_QUERY = "SECRET_SIGNED_QUERY_RUNTIME"
SECRET_POST_COOKIE = "SECRET_POST_COOKIE_RUNTIME"
SECRET_POST_RESPONSE_BODY = "SECRET_POST_RESPONSE_BODY_RUNTIME"
SECRET_POST_CONFIG = "SECRET_POST_CONFIG_RUNTIME"
SECRET_POST_EXCEPTION = "SECRET_POST_EXCEPTION_RUNTIME"

SENTINELS = (
  "SECRET_POST_SHARE_URL_RUNTIME",
  SECRET_SIGNED_QUERY,
  SECRET_POST_COOKIE,
  SECRET_POST_RESPONSE_BODY,
  SECRET_POST_CONFIG,
  SECRET_POST_EXCEPTION,
)

SIGNED_URL = (
  "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7123456789012345678"
  "&a_bogus=" + SECRET_SIGNED_QUERY
  + "&msToken=" + SECRET_SIGNED_QUERY
  + "&verifyFp=" + SECRET_SIGNED_QUERY
)

LEVELS = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)


def require(condition, message):
  if not condition:
    raise SystemExit("FAIL: " + message)


class PlatformError(RuntimeError):
  """Shaped like a real transport failure: the signed url is in the message."""


def platform_error():
  return PlatformError(
    "HTTPSConnectionPool: Max retries exceeded with url: {} "
    "(Cookie: {}) ({}) body={}".format(
      SIGNED_URL,
      SECRET_POST_COOKIE,
      SECRET_POST_EXCEPTION,
      SECRET_POST_RESPONSE_BODY,
    )
  )


@contextmanager
def capture(level):
  """Logger, stdout and stderr together, at one configured level."""
  log, out, err = io.StringIO(), io.StringIO(), io.StringIO()
  ##
  ## The logger the production code actually writes through, asked for the same
  ## way it asks. A hard-coded name would attach the handler to a logger nothing
  ## uses, and every absence check would then pass by capturing nothing.
  ##
  logger = get_logger()
  handler = logging.StreamHandler(log)
  handler.setLevel(level)
  handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
  previous_level = logger.level
  previous_stdout, previous_stderr = sys.stdout, sys.stderr
  logger.addHandler(handler)
  logger.setLevel(level)
  sys.stdout, sys.stderr = out, err
  try:
    yield (log, out, err)
  finally:
    sys.stdout, sys.stderr = previous_stdout, previous_stderr
    logger.removeHandler(handler)
    logger.setLevel(previous_level)


class RefusingResolver:
  def __init__(self, resolution):
    self._resolution = resolution

  def resolve(self, *unused, **also_unused):
    return self._resolution

  def pause(self):
    return None


def exercise():
  """Drive every production post path that can fail, once."""
  ##
  ## The resolver's two failure routes: the detail API, and the html fallback
  ## after it. Both catch a transport exception whose message quotes the signed
  ## url it could not reach.
  ##
  def exploding(*unused, **also_unused):
    raise platform_error()

  resolver = DouyinAwemeResolver(request_function=exploding)
  resolution = resolver.resolve("https://www.douyin.com/video/7123456789012345678")
  require(resolution.ok is not True, "the injected transport was not used")

  ##
  ## A share link the resolver refuses. Both the link and the platform's reason
  ## are free text and used to be logged verbatim.
  ##
  downloader = DouyinAwemeDownloader()
  downloader.resolver = RefusingResolver(
    AwemeResolution(ok=False, reason=SECRET_POST_RESPONSE_BODY)
  )
  result = downloader.run({"url": SECRET_POST_SHARE_URL})
  require(result.ok is not True, "the refusing resolver was not used")

  ##
  ## And a resolution that names an id, so the safe identifier field is
  ## exercised rather than only the refusal path.
  ##
  downloader.resolver = RefusingResolver(
    AwemeResolution(
      ok=False,
      aweme_id="7123456789012345678",
      reason=SECRET_POST_RESPONSE_BODY,
    )
  )
  downloader.run({"url": SECRET_POST_SHARE_URL})


def main():
  everything = []
  for level in LEVELS:
    with capture(level) as (log, out, err):
      exercise()
    everything.append((level, log.getvalue() + out.getvalue() + err.getvalue()))

  for level, visible in everything:
    name = logging.getLevelName(level)
    for sentinel in SENTINELS:
      require(
        sentinel not in visible,
        "post diagnostics leaked {} at {}".format(sentinel, name),
      )
    ##
    ## The query parameter names themselves, in case a future edit renders a
    ## url without its host check.
    ##
    for parameter in ("a_bogus", "msToken", "verifyFp", "X-Bogus"):
      require(
        parameter not in visible,
        "post diagnostics leaked the {} parameter at {}".format(parameter, name),
      )

  ##
  ## Redaction that deleted the diagnostic would pass everything above and be
  ## useless, so the closed fields have to still be there.
  ##
  warning_output = dict(everything)[logging.WARNING]
  info_output = dict(everything)[logging.INFO]
  require(
    "post diagnostic" in warning_output,
    "the post path produced no safe diagnostic at WARNING",
  )
  require(
    "error=PlatformError" in warning_output,
    "the safe exception class diagnostic is missing",
  )
  require(
    "host=v.douyin.test" in info_output,
    "the safe host diagnostic is missing",
  )
  require(
    "aweme_id=7123456789012345678" in info_output,
    "a safe identifier diagnostic is missing",
  )

  ##
  ## The builder itself refuses what no call site should ever be able to pass.
  ##
  rendered = post_diagnostic("post_request_failed", url=SIGNED_URL, status=403)
  require("host=www.douyin.com" in rendered, "a url did not render as its host")
  require("status=403" in rendered, "an HTTP status was not rendered")
  for parameter in ("a_bogus", "msToken", "verifyFp", SECRET_SIGNED_QUERY):
    require(parameter not in rendered, "the builder rendered a signed query")

  try:
    post_diagnostic("anything_a_caller_wants_to_say")
  except ValueError:
    pass
  else:
    raise SystemExit("FAIL: the post diagnostic vocabulary is not closed")

  print("ok   runtime post download diagnostic redaction")


if __name__ == "__main__":
  main()
