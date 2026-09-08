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

import yaml

from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import (
  config_diagnostic,
  post_diagnostic,
  redirect_diagnostic,
)
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_archive_notes import _write_text
from backend.src.platform.douyin.douyin_header import DouyinPostInfoHeader
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.platform.douyin.douyin_post_config import DouyinPostConfig
from backend.src.platform.douyin import douyin_owner_posts
from backend.src.service.direct_post_download_task import (
  DirectPostDownloadTaskService,
)
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


##
## >>============== the service a deployment actually runs in ==============>>
##
##
## Everything below this comment is the P2-12 closure: the resolver and the
## aweme downloader above were closed earlier, but the *service* they run
## inside, and the four configuration objects they are built from, were not.
##
## Nothing here reaches the network, a database or a platform credential. The
## task layer, the downloader and the executor are all injected, and the
## configuration is the image's own file with sentinels written into it.
##


class ExplodingTaskService:
  """Every task-layer call fails the way a driver failure really does."""

  def __getattr__(self, name):
    def failing(*unused, **also_unused):
      raise platform_error()

    return failing


class AcceptingTaskService:
  def __getattr__(self, name):
    if name == "create_task":
      return lambda *a, **k: {"task_id": "task-1"}
    return lambda *a, **k: None


class ProbeConfig:
  concurrency = 1
  debug = True


class CrashingDownloader:
  config = ProbeConfig()

  def run(self, *unused, **also_unused):
    raise platform_error()

  def link_post(self, *unused, **also_unused):
    raise platform_error()


class InlineExecutor:
  def __init__(self, *unused, **also_unused):
    pass

  def submit(self, call, *arguments, **options):
    return call(*arguments, **options)


class RefusingExecutor:
  def __init__(self, *unused, **also_unused):
    pass

  def submit(self, *unused, **also_unused):
    raise platform_error()


def sentinel_config():
  """The image's own configuration, with the credential fields made findable."""
  source = yaml.safe_load(
    (PROJECT_ROOT / "config" / "config.yml").read_text(encoding="utf-8")
  )
  source["download"]["user_login"] = True
  source["server"]["debug_mode"] = True
  douyin = source["platform"]["douyin"]
  for name in ("post_info", "post_info_no_login"):
    header = douyin["headers"].setdefault(name, {})
    header["Cookie"] = SECRET_POST_COOKIE
    header["Authorization"] = SECRET_POST_COOKIE
  douyin["login"]["msToken"] = SECRET_SIGNED_QUERY
  douyin["login"]["strData"] = SECRET_POST_CONFIG
  douyin["post"]["verifyFp"] = SECRET_SIGNED_QUERY
  douyin["post"]["webid"] = SECRET_POST_CONFIG
  douyin["api"]["SECRET_PROBE_ENDPOINT"] = SECRET_POST_CONFIG
  return source


def exercise_production_service():
  """Every failure route of the service every post download runs inside."""
  token = {
    "url": SECRET_POST_SHARE_URL,
    "resolved_url": SIGNED_URL,
    "aweme_id": "7123456789012345678",
  }

  ##
  ## The reporting no-op: one failing task layer exercises create, start,
  ## metadata, progress and finish in a single run.
  ##
  try:
    DirectPostDownloadTaskService(
      task_service=ExplodingTaskService(),
      downloader_factory=CrashingDownloader,
      executor_factory=InlineExecutor,
    ).submit(dict(token))
  except Exception:
    pass

  ##
  ## The crash route. This used to be ``logger.exception`` with the pasted
  ## share url in the message, so the traceback quoted the signed url too.
  ##
  try:
    DirectPostDownloadTaskService(
      task_service=AcceptingTaskService(),
      downloader_factory=CrashingDownloader,
      executor_factory=InlineExecutor,
    ).submit(dict(token))
  except Exception:
    pass

  ##
  ## The pool refusing the work, on both entry points.
  ##
  DirectPostDownloadTaskService(
    task_service=AcceptingTaskService(),
    downloader_factory=CrashingDownloader,
    executor_factory=RefusingExecutor,
  ).submit(dict(token))
  try:
    DirectPostDownloadTaskService(
      task_service=AcceptingTaskService(),
      downloader_factory=CrashingDownloader,
      executor_factory=RefusingExecutor,
    ).submit_tracked(
      aweme_id="7123456789012345678",
      resolved_url=SIGNED_URL,
      source_url=SECRET_POST_SHARE_URL,
      resolve_id="resolve-1",
    )
  except Exception:
    pass


def exercise_configuration_objects():
  """The four objects a post downloader is assembled from, dumped."""
  source = sentinel_config()
  douyin = source["platform"]["douyin"]

  header = DouyinPostInfoHeader(douyin["headers"])
  header.init_header(True)
  header.dump_header()

  DouyinLogin(douyin["login"]).dump_config()

  api = DouyinApi(douyin["api"])
  api.dump_config()
  try:
    api.get_config_dict_attr("$.no.such." + SECRET_POST_CONFIG)
  except Exception:
    pass

  DouyinPostConfig(source).dump_config()


def exercise_support_paths():
  """The note beside a post, and the walk over an owner's pages."""
  ##
  ## A path that cannot be written to, whose own name is a sentinel.
  ##
  _write_text(
    Path("/proc/smsd-{}/{}.txt".format(SECRET_POST_CONFIG, SECRET_POST_CONFIG)),
    SECRET_POST_RESPONSE_BODY,
  )

  class Page:
    def __init__(self, cursor):
      self.payloads = [{"aweme_id": "7123456789012345678"}]
      self.has_more = True
      self.count = 1
      self.next_cursor = cursor

  original = douyin_owner_posts.fetch_post_page
  ##
  ## A free-text owner, which the closed identifier field has to refuse. A real
  ## ``sec_user_id`` is an allowed field and renders as itself; the property
  ## being proved is that the field is checked rather than trusted.
  ##
  douyin_owner_posts.fetch_post_page = (
    lambda *a, **k: Page(douyin_owner_posts.FIRST_CURSOR)
  )
  try:
    list(douyin_owner_posts.iter_all_posts(None, SECRET_POST_SHARE_URL))
  finally:
    douyin_owner_posts.fetch_post_page = original


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

  ##
  ## And the P2-12 surface: the service, the configuration objects and the
  ## support paths around them.
  ##
  exercise_production_service()
  exercise_configuration_objects()
  exercise_support_paths()


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

  ##
  ## The closed fields that carry the P2-12 diagnostics still say something.
  ##
  error_output = dict(everything)[logging.ERROR]
  require(
    "event=post_task_report_failed" in error_output
    or "event=post_job_failed" in error_output,
    "the post service produced no safe failure diagnostic",
  )
  require(
    "configuration diagnostic" in info_output,
    "a configuration object produced no safe diagnostic",
  )
  require(
    "section=post_header" in info_output,
    "the header dump did not report which section it was",
  )
  require(
    "owner_user_id=unknown" in warning_output,
    "a free-text owner was not refused by the closed identifier field",
  )

  ##
  ## Every builder on this path refuses an event it does not define, so none of
  ## them can become a place to render a sentence.
  ##
  for builder in (post_diagnostic, config_diagnostic, redirect_diagnostic):
    try:
      builder("anything_a_caller_wants_to_say")
    except ValueError:
      continue
    raise SystemExit(
      "FAIL: {} accepts an undefined event".format(builder.__name__)
    )

  print("ok   runtime post download diagnostic redaction")


if __name__ == "__main__":
  main()
