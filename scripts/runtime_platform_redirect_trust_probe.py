"""No-network runtime proof for the Douyin redirect trust boundary."""

import io
import logging
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if not (PROJECT_ROOT / "backend").is_dir():
  PROJECT_ROOT = Path("/app")
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.platform.douyin import douyin_redirect_trust as redirect_module
from backend.src.platform.douyin.douyin_redirect_trust import DouyinRedirectTrust
from backend.src.platform.resource_resolution import (
  RedirectLoop,
  ShortLinkUnavailable,
  TooManyRedirects,
  UntrustedRedirect,
)


SHORT = "https://v.douyin.com/runtime-17a/"
POST = "https://www.douyin.com/video/7123456789012345678"


class Response:
  def __init__(self, location=None, text=""):
    self.status_code = 200 if location is None else 302
    self.headers = {}
    if location is not None:
      self.headers["Location"] = location
    self.text = text


class Transport:
  def __init__(self, responses=None, error=None):
    self.responses = dict(responses or {})
    self.error = error
    self.calls = []

  def __call__(self, **options):
    recorded = dict(options)
    if options.get("headers") is not None:
      recorded["headers"] = dict(options["headers"])
    self.calls.append(recorded)
    if self.error is not None:
      raise self.error
    url = options["url"]
    if url not in self.responses:
      raise AssertionError("unexpected redirect request")
    return self.responses[url]


def require(condition, message):
  if not condition:
    raise SystemExit("FAIL: " + message)


def require_refusal(error_type, operation, message):
  try:
    operation()
  except error_type:
    return
  raise SystemExit("FAIL: " + message)


def main():
  diagnostics = io.StringIO()
  logger = logging.Logger("phase17a-runtime")
  logger.propagate = False
  logger.addHandler(logging.StreamHandler(diagnostics))
  redirect_module.get_logger = lambda: logger

  loopback = Transport({
    SHORT: Response(
      "http://127.0.0.1/path?token=SECRET_REDIRECT_QUERY_17A"
    )
  })
  sensitive_headers = {
    "Cookie": "session=SECRET_COOKIE_HEADER_17A",
    "Authorization": "Bearer SECRET_AUTHORIZATION_HEADER_17A",
    "X-Safe": "preserved",
  }
  original_headers = dict(sensitive_headers)
  trust = DouyinRedirectTrust(request_function=loopback)
  require_refusal(
    UntrustedRedirect,
    lambda: trust.resolve_identity(SHORT, headers=sensitive_headers),
    "loopback redirect was accepted",
  )
  require(len(loopback.calls) == 1, "loopback target was requested")
  require(sensitive_headers == original_headers, "caller headers were mutated")

  outside = Transport({
    SHORT: Response(
      "https://outside.example/path?token=SECRET_LOCATION_17A"
    )
  })
  require_refusal(
    UntrustedRedirect,
    lambda: DouyinRedirectTrust(outside).resolve_identity(SHORT),
    "off-platform redirect was accepted",
  )
  require(len(outside.calls) == 1, "off-platform target was requested")

  middle = "https://v.douyin.com/runtime-17a/middle"
  relative = Transport({
    SHORT: Response("/runtime-17a/middle"),
    middle: Response(POST),
  })
  identity = DouyinRedirectTrust(relative).resolve_identity(SHORT)
  require(identity == POST, "safe relative identity redirect failed")
  require(len(relative.calls) == 2, "identity target request count drifted")

  credential_target = "https://www.douyin.com/runtime-17a/credential-hop"
  credential_headers = dict(original_headers)
  credential_redirect = Transport({
    SHORT: Response(credential_target),
    credential_target: Response(),
  })
  DouyinRedirectTrust(credential_redirect).resolve_identity(
    SHORT,
    is_terminal=lambda unused: False,
    headers=credential_headers,
  )
  require(len(credential_redirect.calls) == 2, "credential proof did not redirect")
  redirected_headers = credential_redirect.calls[1]["headers"]
  require("Cookie" not in redirected_headers, "redirect retained Cookie")
  require(
    "Authorization" not in redirected_headers,
    "cross-origin redirect retained Authorization",
  )
  require(redirected_headers.get("X-Safe") == "preserved", "safe header missing")
  require(credential_headers == original_headers, "redirect mutated caller headers")

  doc_middle = "https://www.douyin.com/runtime-17a/document"
  doc_final = "https://www.iesdouyin.com/share/video/7123456789012345678"
  document_transport = Transport({
    POST: Response("/runtime-17a/document"),
    doc_middle: Response(doc_final),
    doc_final: Response(text="phase17a document body"),
  })
  document = DouyinRedirectTrust(document_transport).fetch_document(POST)
  require(document.url == doc_final, "document final URL drifted")
  require(document.response.text == "phase17a document body", "document body missing")

  loop = Transport({
    SHORT: Response(middle),
    middle: Response(SHORT),
  })
  require_refusal(
    RedirectLoop,
    lambda: DouyinRedirectTrust(loop).resolve_identity(SHORT),
    "redirect loop was accepted",
  )
  require(len(loop.calls) == 2, "redirect loop was not bounded")

  capped = Transport({
    SHORT: Response("https://v.douyin.com/runtime-17a/hop-1"),
    "https://v.douyin.com/runtime-17a/hop-1": Response(
      "https://v.douyin.com/runtime-17a/hop-2"
    ),
  })
  require_refusal(
    TooManyRedirects,
    lambda: DouyinRedirectTrust(capped, max_redirects=2).resolve_identity(SHORT),
    "redirect cap was not enforced",
  )
  require(len(capped.calls) == 2, "redirect cap requested max plus one")

  failed = Transport(error=OSError("SECRET_EXCEPTION_17A"))
  require_refusal(
    ShortLinkUnavailable,
    lambda: DouyinRedirectTrust(failed).resolve_identity(SHORT),
    "transport failure was not closed",
  )

  transports = (
    loopback,
    outside,
    relative,
    credential_redirect,
    document_transport,
    loop,
    capped,
    failed,
  )
  require(
    all(
      call.get("allow_redirects") is False
      for transport in transports
      for call in transport.calls
    ),
    "a redirect hop enabled automatic redirects",
  )
  visible = diagnostics.getvalue()
  for sentinel in (
    "SECRET_REDIRECT_QUERY_17A",
    "SECRET_LOCATION_17A",
    "SECRET_EXCEPTION_17A",
    "SECRET_COOKIE_HEADER_17A",
    "SECRET_AUTHORIZATION_HEADER_17A",
  ):
    require(sentinel not in visible, "redirect diagnostics leaked a sentinel")
  require("host=outside.example" in visible, "safe refused host diagnostic missing")
  require("error=OSError" in visible, "safe exception class diagnostic missing")

  print("ok   runtime platform redirect trust boundary")


if __name__ == "__main__":
  main()
