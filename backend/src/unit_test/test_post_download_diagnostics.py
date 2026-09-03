##
## What the post-download path must never write down.
##
## The live recording path was closed in P17 and the persistence layer in P18.
## This is the third surface of the same defect: everything a post download
## touches is either somebody's link, a signed request, or the platform's whole
## answer to it, and all three used to reach the log verbatim.
##
## A signed douyin request url carries ``a_bogus``, ``X-Bogus``, ``msToken`` and
## ``verifyFp`` in its query. Those are the values that make a request accepted,
## so a log line holding one is a log line holding a credential. A ``requests``
## exception message quotes the url it failed on, which is how they get there
## without anybody deciding to log them.
##
## As in the rest of P18 the mitigation is not a scrubber. A regular expression
## that recognises today's parameter names misses tomorrow's, and truncation
## keeps the first hundred characters of exactly the thing that must not be
## kept. The diagnostics are built from a closed set of fields instead, so a
## url, a response body, a header dict or an exception message has no parameter
## to arrive through.
##
from contextlib import contextmanager
from backend.src.library.loglib import get_logger
import io
import logging
import sys
import unittest


##
## Values that appear nowhere else in this codebase, so finding one in captured
## output can only mean the code under test put it there.
##
SECRET_POST_SHARE_URL = "https://v.douyin.test/SECRET_POST_SHARE_URL_P18/"
SECRET_SIGNED_QUERY = "a_bogus=SECRET_SIGNED_QUERY_P18&msToken=SECRET_SIGNED_QUERY_P18"
SECRET_POST_COOKIE = "SECRET_POST_COOKIE_P18"
SECRET_POST_RESPONSE_BODY = "SECRET_POST_RESPONSE_BODY_P18"
SECRET_POST_CONFIG = "SECRET_POST_CONFIG_P18"
SECRET_POST_EXCEPTION = "SECRET_POST_EXCEPTION_P18"

ALL_SENTINELS = (
  "SECRET_POST_SHARE_URL_P18",
  "SECRET_SIGNED_QUERY_P18",
  SECRET_POST_COOKIE,
  SECRET_POST_RESPONSE_BODY,
  SECRET_POST_CONFIG,
  SECRET_POST_EXCEPTION,
)

LEVELS = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)

SIGNED_URL = (
  "https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=7123456789012345678"
  "&" + SECRET_SIGNED_QUERY + "&verifyFp=SECRET_SIGNED_QUERY_P18"
)


class Captured:
  def __init__(self):
    self.log = io.StringIO()
    self.out = io.StringIO()
    self.err = io.StringIO()

  def visible(self) -> str:
    return self.log.getvalue() + self.out.getvalue() + self.err.getvalue()


@contextmanager
def capture(level):
  """Logger, stdout and stderr together, at one configured level."""
  captured = Captured()
  ##
  ## The logger the production code will actually write through, asked for the
  ## same way it asks. Hard-coding "bootstrap" is right only until something
  ## earlier in a suite initialises the logger manager, after which the handler
  ## would be attached to a logger nothing uses and every absence assertion
  ## would pass by capturing nothing at all.
  ##
  logger = get_logger()
  handler = logging.StreamHandler(captured.log)
  handler.setLevel(level)
  handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
  previous_level = logger.level
  previous_stdout, previous_stderr = sys.stdout, sys.stderr
  logger.addHandler(handler)
  logger.setLevel(level)
  sys.stdout, sys.stderr = captured.out, captured.err
  try:
    yield captured
  finally:
    sys.stdout, sys.stderr = previous_stdout, previous_stderr
    logger.removeHandler(handler)
    logger.setLevel(previous_level)


class PlatformError(RuntimeError):
  """Shaped like a real transport failure: the signed url is in the message."""


def platform_error():
  return PlatformError(
    "HTTPSConnectionPool: Max retries exceeded with url: {} ({})".format(
      SIGNED_URL, SECRET_POST_EXCEPTION
    )
  )


class PostDiagnosticTestCase(unittest.TestCase):
  def assert_no_sentinel(self, captured, where):
    visible = captured.visible()
    for sentinel in ALL_SENTINELS:
      self.assertNotIn(
        sentinel,
        visible,
        "{} leaked {} into visible output:\n{}".format(where, sentinel, visible),
      )

  def assert_has_safe_event(self, captured, where):
    visible = captured.visible()
    self.assertIn(
      "post diagnostic",
      visible,
      "{} produced no safe diagnostic at all:\n{}".format(where, visible),
    )


##
## >>========================== the resolver ==========================>>
##


def resolver_with(request_function):
  from backend.src.platform.douyin.douyin_aweme_resolver import DouyinAwemeResolver

  return DouyinAwemeResolver(request_function=request_function)


class ResolverDiagnosticTest(PostDiagnosticTestCase):
  def test_a_failing_detail_request_never_logs_the_signed_url(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        def exploding(*unused, **also_unused):
          raise platform_error()

        resolver = resolver_with(exploding)
        with capture(level) as captured:
          resolution = resolver.resolve(
            "https://www.douyin.com/video/7123456789012345678"
          )
        self.assertFalse(resolution.ok)
        self.assert_no_sentinel(captured, "resolver detail failure")

  def test_a_failing_resolution_still_reports_a_safe_event(self):
    def exploding(*unused, **also_unused):
      raise platform_error()

    resolver = resolver_with(exploding)
    with capture(logging.WARNING) as captured:
      resolver.resolve("https://www.douyin.com/video/7123456789012345678")

    self.assert_has_safe_event(captured, "resolver detail failure")
    visible = captured.visible()
    self.assertIn("error=PlatformError", visible)


##
## >>========================== the downloader ==========================>>
##


def downloader():
  from backend.src.platform.douyin.douyin_aweme_downloader import (
    DouyinAwemeDownloader,
  )

  return DouyinAwemeDownloader()


class RefusingResolver:
  def __init__(self, resolution):
    self._resolution = resolution

  def resolve(self, *unused, **also_unused):
    return self._resolution

  def pause(self):
    return None


class DownloaderDiagnosticTest(PostDiagnosticTestCase):
  def unresolvable(self, reason):
    from backend.src.platform.douyin.douyin_aweme_resolver import AwemeResolution

    return AwemeResolution(ok=False, reason=reason)

  def test_an_unresolvable_link_is_never_logged_verbatim(self):
    for level in LEVELS:
      with self.subTest(level=logging.getLevelName(level)):
        active = downloader()
        active.resolver = RefusingResolver(
          self.unresolvable("url does not point at a single post")
        )
        with capture(level) as captured:
          result = active.run({"url": SECRET_POST_SHARE_URL})
        self.assertFalse(result.ok)
        self.assert_no_sentinel(captured, "unresolvable link")

  def test_an_unresolvable_link_still_reports_a_safe_event(self):
    active = downloader()
    active.resolver = RefusingResolver(
      self.unresolvable("url does not point at a single post")
    )
    with capture(logging.INFO) as captured:
      active.run({"url": SECRET_POST_SHARE_URL})

    self.assert_has_safe_event(captured, "unresolvable link")
    self.assertIn("host=v.douyin.test", captured.visible())

  def test_a_refusal_reason_is_never_free_text_from_the_platform(self):
    ##
    ## ``reason`` reaches the caller as an API field and is written by the
    ## platform's own error text. It has no business in the log.
    ##
    active = downloader()
    active.resolver = RefusingResolver(
      self.unresolvable(SECRET_POST_RESPONSE_BODY)
    )
    with capture(logging.INFO) as captured:
      active.run({"url": SECRET_POST_SHARE_URL})

    self.assert_no_sentinel(captured, "platform refusal reason")


##
## >>=================== the unreachable legacy copy ===================>>
##


class LegacyPostDownloaderTest(PostDiagnosticTestCase):
  ##
  ## ``douyin_post_downloader`` is imported by nothing the server runs - the
  ## production post path is ``douyin_aweme_downloader``. It is hardened anyway
  ## because "unreachable" is one import away from "reachable", and this copy
  ## holds the worst of the leaks: a signed url, an entire response body and a
  ## header dict that carries a cookie on a logged-in deployment.
  ##
  def test_it_never_logs_a_response_body_a_signed_url_or_a_header(self):
    from backend.src.platform.douyin import douyin_post_downloader as module

    source = module.__file__
    with open(source, "r", encoding="utf-8") as handle:
      text = handle.read()

    for forbidden in (
      "get_logger().info(response.url)",
      "get_logger().info(response.json())",
      "get_logger().info(response.status_code)",
      'get_logger().info("response url {}".format(response.url))',
      "dump_header()",
    ):
      ##
      ## Asserted on a boolean rather than with ``assertNotIn`` so a failure
      ## names the offending line instead of printing the whole module.
      ##
      self.assertFalse(
        forbidden in text,
        "the legacy post downloader still writes {}".format(forbidden),
      )

  def test_it_builds_every_diagnostic_from_the_closed_field_helper(self):
    import ast
    from pathlib import Path

    source = (
      Path(__file__).resolve().parents[1]
      / "platform" / "douyin" / "douyin_post_downloader.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    offenders = []
    for node in ast.walk(tree):
      if not isinstance(node, ast.Call):
        continue
      method = node.func
      if not isinstance(method, ast.Attribute):
        continue
      if method.attr not in ("debug", "info", "warning", "error", "exception"):
        continue
      receiver = method.value
      if not (
        isinstance(receiver, ast.Call)
        and isinstance(receiver.func, ast.Name)
        and receiver.func.id == "get_logger"
      ):
        continue
      if not node.args:
        continue
      first = node.args[0]
      if isinstance(first, ast.Constant) and isinstance(first.value, str):
        continue
      if (
        isinstance(first, ast.Call)
        and isinstance(first.func, ast.Name)
        and first.func.id == "post_diagnostic"
      ):
        continue
      offenders.append(node.lineno)

    self.assertEqual([], offenders)


if __name__ == "__main__":
  unittest.main()


##
## >>================= the invariant, not just the instances =================>>
##
##
## The sentinel tests above prove that today's call sites do not leak. This one
## refuses the *shape*, so a new failure path added next month cannot reopen the
## boundary just because no sentinel test knows it exists.
##
import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

##
## Everything a post download logs through. ``douyin_post_downloader`` is here
## even though nothing the server imports reaches it: it holds the worst of the
## leaks, and "unreachable" is one import away from "reachable".
##
POST_MODULES = (
  "backend/src/platform/douyin/douyin_aweme_downloader.py",
  "backend/src/platform/douyin/douyin_aweme_resolver.py",
  "backend/src/platform/douyin/douyin_post_downloader.py",
)

LOG_METHODS = frozenset({"debug", "info", "warning", "error", "exception", "critical"})


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
    and node.func.id == "post_diagnostic"
  )


class PostDiagnosticSourceInvariantTest(unittest.TestCase):
  def test_no_post_log_message_is_built_from_a_value(self):
    offenders = []
    for relative in POST_MODULES:
      tree = ast.parse((PROJECT_ROOT / relative).read_text(encoding="utf-8"))
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
      "post diagnostics must be a plain literal or post_diagnostic(...), "
      "never a formatted value: {}".format(offenders),
    )

  def test_the_post_builder_has_no_escape_hatch(self):
    from backend.src.library import safe_diagnostics

    tree = ast.parse(
      Path(safe_diagnostics.__file__).read_text(encoding="utf-8")
    )
    builder = next(
      node for node in ast.walk(tree)
      if isinstance(node, ast.FunctionDef) and node.name == "post_diagnostic"
    )
    self.assertIsNone(builder.args.kwarg, "**kwargs would reopen the boundary")
    self.assertIsNone(builder.args.vararg, "*args would reopen the boundary")
    self.assertEqual(
      ["event"],
      [argument.arg for argument in builder.args.args],
      "every field beyond the event must be keyword-only and named",
    )

  def test_an_unknown_post_event_is_refused_rather_than_rendered(self):
    from backend.src.library.safe_diagnostics import post_diagnostic

    with self.assertRaises(ValueError):
      post_diagnostic("anything_a_caller_wants_to_say")

  def test_a_url_renders_as_a_host_and_never_as_a_query(self):
    from backend.src.library.safe_diagnostics import post_diagnostic

    rendered = post_diagnostic("post_request_failed", url=SIGNED_URL)

    self.assertIn("host=www.douyin.com", rendered)
    for forbidden in ("a_bogus", "msToken", "verifyFp", "aweme_id=7123"):
      self.assertNotIn(forbidden, rendered)

  def test_free_text_identifiers_render_as_unknown(self):
    from backend.src.library.safe_diagnostics import post_diagnostic

    rendered = post_diagnostic(
      "post_complete",
      aweme_id="某个昵称",
      owner_user_id=SECRET_POST_SHARE_URL,
      kind="passport",
      saved=True,
      total=-1,
    )
    self.assertNotIn("SECRET_POST_SHARE_URL_P18", rendered)
    self.assertIn("aweme_id=unknown", rendered)
    self.assertIn("owner_user_id=unknown", rendered)
    self.assertIn("kind=unknown", rendered)
    self.assertIn("saved=unknown", rendered)
    self.assertIn("total=unknown", rendered)

  def test_the_legacy_dump_no_longer_reaches_a_header_or_a_login(self):
    source = (
      PROJECT_ROOT / "backend/src/platform/douyin/douyin_post_downloader.py"
    ).read_text(encoding="utf-8")

    ##
    ## A configuration dump that carries a cookie, msToken, verifyFp and the
    ## signed parameter set has no safe rendering, so it has none.
    ##
    for forbidden in (
      "self.header.dump_header()",
      "self.login.dump_config()",
      "self.API.dump_config()",
      "self.config.dump_config()",
    ):
      self.assertFalse(
        forbidden in source,
        "the legacy dump still calls {}".format(forbidden),
      )
