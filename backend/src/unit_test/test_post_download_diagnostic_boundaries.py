##
## P2-12: the post-download path that a deployment actually runs.
##
## ``test_post_download_diagnostics`` closed the three modules a post link is
## resolved and fetched through. It did not close the path *around* them, and
## that path is where a production post download does most of its logging:
##
##   - ``direct_post_download_task`` is the service every pasted link and every
##     ``POST /api/tasks`` post download runs inside. Six of its failure routes
##     formatted the caught exception into the message, and two of them
##     formatted the share url the user pasted; one used ``logger.exception``,
##     which appends the whole traceback - and a ``requests`` traceback quotes
##     the signed url it failed on.
##   - the configuration, header, api and login objects the downloader is built
##     from each had a ``dump`` that wrote every key and value it held. Between
##     them those hold the request ``Cookie``, ``msToken``, ``verifyFp`` and
##     ``a_bogus`` - which is to say the credential set. ``output_dict`` writes
##     them to *stdout*, where no log level hides them.
##   - ``douyin_archive_notes`` wrote the absolute path of somebody's media and
##     the raw ``OSError`` beside it.
##
## The mitigation is the one the rest of P18 uses, and deliberately not a
## scrubber: a closed field vocabulary. A regular expression that recognises
## ``a_bogus`` does not recognise whatever the platform renames it to next
## quarter, and truncating a message keeps the first hundred characters of
## exactly the thing that must not be kept. ``post_diagnostic`` has no mapping,
## no ``**kwargs`` and no free-text field, so a header dict, a params dict, a
## response body, a config section or an exception message has no argument to
## arrive through at all.
##
from contextlib import contextmanager
from copy import deepcopy
import io
import logging
from pathlib import Path
import sys
import unittest

import yaml

from backend.src.library.loglib import get_logger


PROJECT_ROOT = Path(__file__).resolve().parents[3]

##
## Values that appear nowhere else in this repository, so finding one in
## captured output can only mean the code under test put it there.
##
SECRET_POST_SHARE_URL = "https://v.douyin.test/SECRET_POST_SHARE_URL_P2X/"
SECRET_SIGNED_QUERY = "SECRET_SIGNED_QUERY_P2X"
SECRET_POST_COOKIE = "SECRET_POST_COOKIE_P2X"
SECRET_POST_RESPONSE_BODY = "SECRET_POST_RESPONSE_BODY_P2X"
SECRET_POST_CONFIG = "SECRET_POST_CONFIG_P2X"
SECRET_POST_EXCEPTION = "SECRET_POST_EXCEPTION_P2X"

ALL_SENTINELS = (
  "SECRET_POST_SHARE_URL_P2X",
  SECRET_SIGNED_QUERY,
  SECRET_POST_COOKIE,
  SECRET_POST_RESPONSE_BODY,
  SECRET_POST_CONFIG,
  SECRET_POST_EXCEPTION,
)

##
## The query parameter *names* too. A future edit that renders a url without
## going through the host check would leak these even if it renamed the values.
##
SIGNED_PARAMETERS = ("a_bogus", "X-Bogus", "msToken", "verifyFp")

LEVELS = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)

SIGNED_URL = (
  "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7123456789012345678"
  "&a_bogus=" + SECRET_SIGNED_QUERY
  + "&msToken=" + SECRET_SIGNED_QUERY
  + "&verifyFp=" + SECRET_SIGNED_QUERY
)


class PlatformError(RuntimeError):
  """Shaped like a real transport failure: the signed url is in the message."""


def platform_error():
  ##
  ## Everything a ``requests`` exception really carries, in one message: the
  ## url it failed on, the cookie the session sent, the platform's answer, and
  ## a reason. None of it was ever chosen for logging - it arrives through
  ## ``format(e)`` and nothing else.
  ##
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
  """Logger, stdout and stderr together, at one configured level.

  All three, because the leaks this file closes are not all log lines:
  ``output_dict`` writes a header - cookie included - straight to stdout, where
  no ``$.log.level`` can hide it.
  """
  log, out, err = io.StringIO(), io.StringIO(), io.StringIO()
  ##
  ## The logger production code actually writes through, asked for the same way
  ## it asks. A hard-coded name would attach the handler to a logger nothing
  ## uses, after which every absence assertion would pass by capturing nothing.
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


class PostBoundaryTestCase(unittest.TestCase):
  ##
  ## One helper, used by every case below: run something at all four levels a
  ## deployment can be configured to, and require that no sentinel appears in
  ## anything an operator could read - while still requiring the diagnostic to
  ## exist, because redaction that deleted the message would pass an absence
  ## check and be useless.
  ##
  def assert_closed(self, drive, where, expect_event=True):
    for level in LEVELS:
      with self.subTest(where=where, level=logging.getLevelName(level)):
        with capture(level) as (log, out, err):
          drive()
        visible = log.getvalue() + out.getvalue() + err.getvalue()
        for sentinel in ALL_SENTINELS:
          self.assertNotIn(
            sentinel,
            visible,
            "{} leaked {} at {}:\n{}".format(
              where, sentinel, logging.getLevelName(level), visible
            ),
          )
        for parameter in SIGNED_PARAMETERS:
          self.assertNotIn(
            parameter,
            visible,
            "{} leaked the {} parameter at {}:\n{}".format(
              where, parameter, logging.getLevelName(level), visible
            ),
          )
        self.assertNotIn("Traceback", visible, where)
        if expect_event and level <= logging.WARNING:
          self.assertIn(
            "post diagnostic",
            visible,
            "{} produced no safe diagnostic at {}:\n{}".format(
              where, logging.getLevelName(level), visible
            ),
          )


##
## >>=============== the service every post download runs in ===============>>
##
##
## ``DirectPostDownloadTaskService`` is production by every definition: the
## legacy paste endpoint dispatches into it, ``POST /api/tasks`` dispatches into
## it, and every failure it reports is a failure a deployment will really see.
## Its collaborators are all injectable, so each route below is driven for real
## rather than asserted about.
##


class ExplodingTaskService:
  """Every task-layer call fails the way a driver failure really does."""

  def __getattr__(self, name):
    def failing(*unused, **also_unused):
      raise platform_error()

    return failing


class CountingTaskService:
  """Accepts everything, so a route can be reached without the task layer failing."""

  def create_task(self, *unused, **also_unused):
    return {"task_id": "task-1"}

  def start_task(self, *unused, **also_unused):
    return None

  def update_metadata(self, *unused, **also_unused):
    return None

  def update_progress(self, *unused, **also_unused):
    return None

  def finish_success(self, *unused, **also_unused):
    return None

  def finish_partial(self, *unused, **also_unused):
    return None

  def finish_failed(self, *unused, **also_unused):
    return None


class FakeDownloaderConfig:
  concurrency = 1
  debug = True


class CrashingDownloader:
  config = FakeDownloaderConfig()

  def run(self, *unused, **also_unused):
    raise platform_error()

  def link_post(self, *unused, **also_unused):
    raise platform_error()


class SavedResult:
  ok = True
  skipped = False
  partial = False
  saved_count = 1
  media_count = 1
  save_dir = "/srv/media/somebody"
  reason = None
  aweme_id = "7123456789012345678"


class SavingDownloader:
  """Downloads fine, then fails to record who it belongs to."""

  config = FakeDownloaderConfig()

  def run(self, *unused, **also_unused):
    return SavedResult()

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


TOKEN = {
  "url": SECRET_POST_SHARE_URL,
  "resolved_url": SIGNED_URL,
  "aweme_id": "7123456789012345678",
}


class DirectPostDownloadTaskDiagnosticTest(PostBoundaryTestCase):
  def service(self, task_service, downloader, executor):
    from backend.src.service.direct_post_download_task import (
      DirectPostDownloadTaskService,
    )

    return DirectPostDownloadTaskService(
      task_service=task_service,
      downloader_factory=lambda: downloader,
      executor_factory=executor,
    )

  ##
  ## The reporting no-op. Every task-layer call in this service goes through
  ## ``_safe``, so one failing task service exercises create, start, metadata,
  ## progress and finish in a single run.
  ##
  def test_a_failing_task_layer_never_logs_what_it_was_told(self):
    def drive():
      service = self.service(
        ExplodingTaskService(), SavingDownloader(), InlineExecutor
      )
      try:
        service.submit(dict(TOKEN))
      except Exception:
        pass

    self.assert_closed(drive, "task layer failure")

  ##
  ## The crash route, and the worst of the old lines: the pasted share url and
  ## the caught exception, through ``logger.exception`` - which appends the
  ## traceback, and a ``requests`` traceback quotes the signed url.
  ##
  def test_a_download_crash_logs_neither_the_share_url_nor_the_exception(self):
    def drive():
      service = self.service(
        CountingTaskService(), CrashingDownloader(), InlineExecutor
      )
      try:
        service.submit(dict(TOKEN))
      except Exception:
        pass

    self.assert_closed(drive, "download crash")

  ##
  ## The post saved, and only the ownership link failed. A different route with
  ## its own log line, and one that runs after a successful download.
  ##
  def test_an_ownership_failure_never_logs_the_platform_error(self):
    def drive():
      service = self.service(
        CountingTaskService(), SavingDownloader(), InlineExecutor
      )
      try:
        service.submit_tracked(
          aweme_id="7123456789012345678",
          resolved_url=SIGNED_URL,
          source_url=SECRET_POST_SHARE_URL,
          resolve_id="resolve-1",
          app_user_id=7,
        )
      except Exception:
        pass

    self.assert_closed(drive, "ownership failure")

  ##
  ## The pool refusing the work, on both entry points. ``submit`` formatted the
  ## share url into its message; ``submit_tracked`` formatted the exception.
  ##
  def test_a_refused_schedule_logs_neither_the_url_nor_the_reason(self):
    def drive():
      service = self.service(
        CountingTaskService(), SavingDownloader(), RefusingExecutor
      )
      service.submit(dict(TOKEN))

    self.assert_closed(drive, "refused schedule")

  def test_a_refused_tracked_schedule_stays_closed_too(self):
    def drive():
      service = self.service(
        CountingTaskService(), SavingDownloader(), RefusingExecutor
      )
      try:
        service.submit_tracked(
          aweme_id="7123456789012345678",
          resolved_url=SIGNED_URL,
          source_url=SECRET_POST_SHARE_URL,
          resolve_id="resolve-1",
        )
      except Exception:
        pass

    self.assert_closed(drive, "refused tracked schedule")

  ##
  ## The strict creation refusing. Promised a task id and unable to make one,
  ## this route used to format the driver's exception into the log.
  ##
  def test_a_strict_creation_failure_never_logs_the_reason(self):
    def drive():
      service = self.service(
        ExplodingTaskService(), SavingDownloader(), InlineExecutor
      )
      try:
        service.submit_tracked(
          aweme_id="7123456789012345678",
          resolved_url=SIGNED_URL,
          source_url=SECRET_POST_SHARE_URL,
          resolve_id="resolve-1",
        )
      except Exception:
        pass

    self.assert_closed(drive, "strict creation failure")


##
## >>================ the objects the downloader is built from ================>>
##
##
## A post downloader is a configuration, a header, a login and an api object.
## Each of them had a ``dump`` that wrote every key and value it held, and
## between them they hold the whole of what makes a signed request work as this
## account. Two of those dumps went to *stdout* rather than to the logger, which
## is worse: no ``$.log.level`` can turn stdout down.
##


def sentinel_config(login: bool):
  """The deployment's real configuration shape, with sentinels in it.

  Built from ``config/config.yml`` rather than from a hand-written literal so
  the objects under test are constructed exactly as production constructs them
  - a trimmed fake would not carry the sections whose dumps are the defect.
  """
  source = yaml.safe_load(
    (PROJECT_ROOT / "config" / "config.yml").read_text(encoding="utf-8")
  )
  source["download"]["user_login"] = login
  source["server"]["debug_mode"] = True
  douyin = source["platform"]["douyin"]

  ##
  ## The credential set, as a deployment really holds it.
  ##
  for header_name in ("post_info", "post_info_no_login"):
    header = douyin["headers"].setdefault(header_name, {})
    header["Cookie"] = SECRET_POST_COOKIE
    header["Authorization"] = SECRET_POST_COOKIE
    header["User-Agent"] = "smsd-test"
  douyin["login"]["msToken"] = SECRET_SIGNED_QUERY
  douyin["login"]["strData"] = SECRET_POST_CONFIG
  douyin["post"]["verifyFp"] = SECRET_SIGNED_QUERY
  douyin["post"]["webid"] = SECRET_POST_CONFIG
  douyin["post"]["sec_user_id"] = SECRET_POST_CONFIG
  douyin["api"]["SECRET_TEST_ENDPOINT"] = SECRET_POST_CONFIG
  douyin["aweme"]["video_quality"] = SECRET_POST_CONFIG
  return source


class StubLogin:
  """A login whose token is a sentinel, so a params dump would show it."""

  msToken = SECRET_SIGNED_QUERY

  def update_douyin_msToken(self):
    return None

  def dump_config(self):
    return None


def post_downloader(login: bool):
  from backend.src.platform.douyin import douyin_post_downloader as module

  downloader = module.DouyinPostDownloader(sentinel_config(login))
  return module, downloader


class PostDownloaderFlowDiagnosticTest(PostBoundaryTestCase):
  ##
  ## Both flows, because they are different code with different headers, a
  ## different api endpoint and a different signing story - and only one of them
  ## carries a cookie.
  ##
  def drive_flow(self, login):
    module, downloader = post_downloader(login)
    downloader.login = StubLogin()
    downloader.config.sec_user_id = "MS4wLjABAAAAtestsecuserid"
    ##
    ## Both request builders read their header fields off the header object's
    ## attributes rather than off its mapping, so a deployment that reaches
    ## these flows has them there. Put there explicitly, with the cookie the
    ## logged-in flow really sends, so the request path runs rather than
    ## stopping on a missing key before it can log anything.
    ##
    downloader.header.__dict__.update({
      "Accept": "application/json",
      "Accept-Encoding": "gzip, deflate",
      "Accept-Language": "en-US",
      "Agw-Js-Conv": "str",
      "Cookie": SECRET_POST_COOKIE,
      "Priority": "u=1, i",
      "Referer": "https://www.douyin.com/",
      "Sec-Ch-Ua": "Chromium",
      "Sec-Ch-Ua-Mobile": "?0",
      "Sec-Ch-Ua-Platform": "Windows",
      "Sec-Fetch-Dest": "empty",
      "Sec-Fetch-Mode": "cors",
      "Sec-Fetch-Site": "same-origin",
      "User-Agent": "smsd-test",
    })
    ##
    ## The post header class has never carried ``set_referer``; both flows call
    ## it, which is why nothing in the server reaches this module today. Supplied
    ## here so the request path can be driven to the end and its diagnostics
    ## judged - the point of this file is what gets logged, not whether this
    ## legacy copy is wired up.
    ##
    downloader.header.set_referer = (
      lambda value: downloader.header.__dict__.__setitem__("Referer", value)
    )
    ##
    ## What ``query_share_url`` would have cached. The logged-out flow builds
    ## its referer out of this, so it has to be there for that path to run.
    ##
    build = getattr(downloader, "_DouyinPostDownloader__build")
    build["share_info"] = {"query": {"sec_uid": ["MS4wLjABAAAAtestsecuserid"]}}

    def exploding(*unused, **also_unused):
      raise platform_error()

    original_get = module.get
    module.get = exploding
    try:
      if login:
        downloader.query_user_post()
      else:
        downloader.query_user_post_without_login()
    except Exception:
      pass
    finally:
      module.get = original_get

  def test_the_logged_in_post_flow_leaks_nothing(self):
    self.assert_closed(lambda: self.drive_flow(True), "logged-in post flow")

  def test_the_logged_out_post_flow_leaks_nothing(self):
    self.assert_closed(lambda: self.drive_flow(False), "logged-out post flow")

  ##
  ## Every dump the post downloader can reach, driven rather than asserted
  ## about. A source check would say the downloader no longer calls them; it
  ## would not say what they do when something else does.
  ##
  def test_no_dump_on_the_post_path_writes_a_value(self):
    for login in (True, False):
      module, downloader = post_downloader(login)

      def drive():
        downloader.dump_config()
        downloader.header.dump_header()
        downloader.login.dump_config()
        downloader.API.dump_config()
        downloader.config.dump_config()

      self.assert_closed(
        drive,
        "post configuration dump (login={})".format(login),
        expect_event=False,
      )

  ##
  ## The api helper every owner and post request resolves its endpoint through.
  ## A missing attribute is an ordinary production failure, and it used to log
  ## the raw exception.
  ##
  def test_a_failing_api_lookup_never_logs_the_reason(self):
    unused_module, downloader = post_downloader(True)

    def drive():
      try:
        downloader.API.get_config_dict_attr("$.no.such." + SECRET_POST_CONFIG)
      except Exception:
        pass

    self.assert_closed(drive, "api attribute lookup", expect_event=False)


##
## >>=========== the rest of what a production post download runs ===========>>
##


class PostSupportPathDiagnosticTest(PostBoundaryTestCase):
  ##
  ## A note is written beside every downloaded post. When the write fails the
  ## warning used to carry the absolute path of somebody's media directory and
  ## the raw ``OSError`` beside it - a filesystem layout and a broadcaster's
  ## directory name, in a log stream read far more widely than the media.
  ##
  def test_a_failed_note_write_names_neither_the_path_nor_the_error(self):
    from backend.src.platform.douyin import douyin_archive_notes as notes

    target = Path("/proc/smsd-{}/{}.txt".format(SECRET_POST_CONFIG, SECRET_POST_CONFIG))

    def drive():
      self.assertFalse(notes._write_text(target, SECRET_POST_RESPONSE_BODY))

    self.assert_closed(drive, "note write failure", expect_event=False)

  ##
  ## Walking an owner's pages. Both stopping conditions formatted whatever was
  ## handed to them as the owner into the message.
  ##
  ## An opaque ``sec_user_id`` is an allowed closed field and renders as itself;
  ## the property that matters is that the field is *checked*, so anything that
  ## is not an identifier - a share url, a nickname, a directory name - renders
  ## as ``unknown`` instead of being written down. That is what is driven here.
  ##
  def test_the_owner_page_walk_never_names_the_owner_in_free_text(self):
    from backend.src.platform.douyin import douyin_owner_posts as owner_posts

    class Page:
      def __init__(self, cursor):
        self.payloads = [{"aweme_id": "712345678901234567" + str(cursor)}]
        self.has_more = True
        self.count = 1
        self.next_cursor = cursor

    def drive_cap():
      pages = iter([Page(1), Page(2), Page(3)])
      original = owner_posts.fetch_post_page
      owner_posts.fetch_post_page = lambda *a, **k: next(pages)
      try:
        list(owner_posts.iter_all_posts(None, SECRET_POST_SHARE_URL, max_pages=2))
      finally:
        owner_posts.fetch_post_page = original

    def drive_repeat():
      ##
      ## A cursor that never advances - the loop guard this warning exists for.
      ##
      original = owner_posts.fetch_post_page
      owner_posts.fetch_post_page = lambda *a, **k: Page(owner_posts.FIRST_CURSOR)
      try:
        list(owner_posts.iter_all_posts(None, SECRET_POST_SHARE_URL))
      finally:
        owner_posts.fetch_post_page = original

    self.assert_closed(drive_cap, "owner page cap", expect_event=False)
    self.assert_closed(drive_repeat, "owner repeating cursor", expect_event=False)

  ##
  ## The batch submit path a deployment runs with ``$.server.debug_mode`` on.
  ## It dumped the whole aweme configuration section - to stdout, where no log
  ## level reaches it.
  ##
  def test_the_batch_submit_debug_dump_writes_no_configuration(self):
    from backend.src.platform.douyin import douyin_aweme_downloader as module

    class Config:
      debug = True
      concurrency = 1

      def dump_config(self):
        from backend.src.platform.douyin.douyin_aweme_config import (
          DouyinAwemeConfig,
        )

        DouyinAwemeConfig(sentinel_config(True)).dump_config()

    class Downloader:
      config = Config()

      def dump_config(self):
        self.config.dump_config()

      def run(self, token):
        return None

    def drive():
      original_downloader = module.get_aweme_downloader
      original_executor = module.get_aweme_executor
      module.get_aweme_downloader = lambda: Downloader()
      module.get_aweme_executor = lambda *a, **k: InlineExecutor()
      try:
        module.download_multiple_aweme([dict(TOKEN)])
      finally:
        module.get_aweme_downloader = original_downloader
        module.get_aweme_executor = original_executor

    self.assert_closed(drive, "batch submit debug dump", expect_event=False)


##
## >>================= the invariant, not just the instances =================>>
##
##
## The cases above prove that today's call sites are closed. This proves the
## *shape*, so a failure route added next month cannot reopen the boundary
## merely because no sentinel test knows it exists.
##
import ast


##
## Everything a production post download logs through, on either flow. The
## legacy ``douyin_post_downloader`` is here for the reason P18 gave: it holds
## the worst of the original leaks, and "unreachable" is one import away from
## "reachable".
##
PRODUCTION_POST_MODULES = (
  "backend/src/service/direct_post_download_task.py",
  "backend/src/platform/douyin/douyin_aweme_downloader.py",
  "backend/src/platform/douyin/douyin_aweme_resolver.py",
  "backend/src/platform/douyin/douyin_aweme_config.py",
  "backend/src/platform/douyin/douyin_archive_notes.py",
  "backend/src/platform/douyin/douyin_api.py",
  "backend/src/platform/douyin/douyin_header.py",
  "backend/src/platform/douyin/douyin_owner_posts.py",
  "backend/src/platform/douyin/douyin_post_config.py",
  "backend/src/platform/douyin/douyin_post_downloader.py",
  "backend/src/platform/douyin/douyin_redirect_trust.py",
  "backend/src/base/header.py",
  "backend/src/base/login.py",
)

LOG_METHODS = frozenset({"debug", "info", "warning", "error", "exception", "critical"})
SAFE_BUILDERS = frozenset({
  "config_diagnostic",
  "live_diagnostic",
  "post_diagnostic",
  "redirect_diagnostic",
})


def _logger_calls(tree):
  for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
      continue
    method = node.func
    if not isinstance(method, ast.Attribute) or method.attr not in LOG_METHODS:
      continue
    receiver = method.value
    if (
      isinstance(receiver, ast.Call)
      and isinstance(receiver.func, ast.Name)
      and receiver.func.id == "get_logger"
    ):
      yield node


def _is_closed_message(node):
  if isinstance(node, ast.Constant) and isinstance(node.value, str):
    return True
  return (
    isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id in SAFE_BUILDERS
  )


class ProductionPostSourceInvariantTest(unittest.TestCase):
  def sources(self):
    for relative in PRODUCTION_POST_MODULES:
      yield relative, ast.parse(
        (PROJECT_ROOT / relative).read_text(encoding="utf-8")
      )

  def test_no_post_log_message_is_built_from_a_value(self):
    offenders = []
    for relative, tree in self.sources():
      for node in _logger_calls(tree):
        if not node.args:
          continue
        if not _is_closed_message(node.args[0]):
          offenders.append("{}:{}".format(relative, node.lineno))
        if len(node.args) > 1:
          offenders.append(
            "{}:{} (lazy interpolation arguments)".format(relative, node.lineno)
          )
    self.assertEqual(
      [],
      offenders,
      "a post diagnostic must be a literal or a closed-field builder call: "
      "{}".format(offenders),
    )

  ##
  ## ``logger.exception`` appends the traceback, and a ``requests`` traceback
  ## quotes the signed url it failed on. There is no safe message that survives
  ## having a traceback stapled to it.
  ##
  def test_no_post_module_logs_a_traceback(self):
    offenders = []
    for relative, tree in self.sources():
      for node in _logger_calls(tree):
        if node.func.attr == "exception":
          offenders.append("{}:{}".format(relative, node.lineno))
    self.assertEqual([], offenders, "logger.exception writes a traceback")

  ##
  ## ``output_dict`` and ``print`` write to stdout, which no ``$.log.level``
  ## turns down. A configuration, header or login section rendered through
  ## either is the same disclosure as logging it, with less to stop it.
  ##
  def test_no_post_module_writes_a_mapping_to_stdout(self):
    offenders = []
    for relative, tree in self.sources():
      for node in ast.walk(tree):
        if (
          isinstance(node, ast.Call)
          and isinstance(node.func, ast.Name)
          and node.func.id in ("output_dict", "print")
        ):
          offenders.append("{}:{}".format(relative, node.lineno))
    self.assertEqual(
      [], offenders, "a post module writes to stdout: {}".format(offenders)
    )


if __name__ == "__main__":
  unittest.main()
