from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

from requests import exceptions as request_exceptions
from requests import request

from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import safe_url_host
from backend.src.platform.douyin.douyin_aweme_url import classify_aweme_url
from backend.src.platform.douyin.douyin_owner_url import classify_owner_url
from backend.src.platform.douyin.douyin_url_hosts import (
  is_content_host,
  is_live_host,
  is_short_link_host,
)
from backend.src.platform.resource_resolution import (
  RedirectLoop,
  RedirectTimeout,
  ShortLinkUnavailable,
  TooManyRedirects,
  UnsupportedPlatform,
  UnsupportedScheme,
  UntrustedRedirect,
)


_ALLOWED_SCHEMES = frozenset({"http", "https"})


@dataclass(frozen=True)
class RedirectDocument:
  """The trusted final URL and response produced by a document walk."""

  url: str
  response: object


def _allowed_host(host: str) -> bool:
  """Use the platform's one host authority; never maintain another list."""
  return (
    is_live_host(host)
    or is_content_host(host)
    or is_short_link_host(host)
  )


def _identifiable(url: str) -> bool:
  parsed = urlsplit(url)
  return (
    is_live_host(parsed.hostname or "")
    or classify_aweme_url(url) is not None
    or classify_owner_url(url) is not None
  )


class DouyinRedirectTrust:
  """Walk client-originated Douyin redirects without automatic redirects.

  This is deliberately a narrow platform boundary, not a general outbound
  firewall. It applies one shared host authority before the initial request and
  again before every redirect target is contacted.
  """

  def __init__(
    self,
    request_function=None,
    max_redirects: int = 5,
  ) -> None:
    self._request = request if request_function is None else request_function
    self._max_redirects = max_redirects

  @classmethod
  def trusts(cls, url: str) -> bool:
    """Whether an initial client URL is safe to contact under this boundary."""
    try:
      cls._validate(url, initial=True)
    except (UnsupportedPlatform, UnsupportedScheme):
      return False
    return True

  @staticmethod
  def _location(response):
    headers = getattr(response, "headers", None) or {}
    for key, value in headers.items():
      if isinstance(key, str) and key.lower() == "location":
        return value
    return None

  @staticmethod
  def _copy_request_options(request_options):
    options = dict(request_options)
    headers = options.get("headers")
    if headers is not None:
      options["headers"] = dict(headers)
    return options

  @staticmethod
  def _origin(url: str):
    parsed = urlsplit(url)
    port = parsed.port
    if port is None:
      port = 443 if parsed.scheme.lower() == "https" else 80
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), port

  @classmethod
  def _redirect_request_options(cls, request_options, current, target):
    """Copy redirect options while narrowing credential propagation."""
    options = cls._copy_request_options(request_options)
    headers = options.get("headers")
    if headers is None:
      return options
    removed = {"cookie"}
    if cls._origin(current) != cls._origin(target):
      removed.add("authorization")
    options["headers"] = {
      key: value
      for key, value in headers.items()
      if not isinstance(key, str) or key.lower() not in removed
    }
    return options

  @staticmethod
  def _validate(url: str, *, initial: bool) -> str:
    error_type = UnsupportedPlatform if initial else UntrustedRedirect
    if not isinstance(url, str) or not url.strip():
      raise error_type("该链接不是受信任的抖音地址")
    candidate = url.strip()
    if any(ord(character) < 32 or ord(character) == 127 for character in candidate):
      raise error_type("该链接不是受信任的抖音地址")
    try:
      parsed = urlsplit(candidate)
      scheme = parsed.scheme.lower()
      if scheme not in _ALLOWED_SCHEMES:
        if initial:
          raise UnsupportedScheme("请粘贴一个 http(s) 链接")
        raise UntrustedRedirect("该链接跳转到了不受支持的地址")
      parsed.port
      host = parsed.hostname
    except (TypeError, ValueError):
      raise error_type("该链接不是受信任的抖音地址")
    if (
      host is None
      or parsed.username is not None
      or parsed.password is not None
      or not _allowed_host(host)
    ):
      raise error_type("该链接不是受信任的抖音地址")
    return candidate

  def _request_hop(self, url, after_request=None, **request_options):
    options = self._copy_request_options(request_options)
    options.update({
      "method": "GET",
      "url": url,
      "allow_redirects": False,
    })
    try:
      response = self._request(**options)
    except Exception as error:
      get_logger().warning(
        "douyin redirect request failed: host={} error={}".format(
          safe_url_host(url),
          type(error).__name__,
        )
      )
      failure = (
        RedirectTimeout
        if isinstance(error, (TimeoutError, request_exceptions.Timeout))
        else ShortLinkUnavailable
      )
      raise failure("无法解析该短链接，请稍后重试") from None
    if after_request is not None:
      after_request()
    return response

  @staticmethod
  def _target(current: str, location) -> str:
    if not isinstance(location, str) or not location.strip():
      raise UntrustedRedirect("该链接跳转到了不受支持的地址")
    raw_location = location.strip()
    try:
      parsed_location = urlsplit(raw_location)
      if parsed_location.scheme and not parsed_location.netloc:
        raise UntrustedRedirect("该链接跳转到了不受支持的地址")
      target = urljoin(current, raw_location)
    except (TypeError, ValueError):
      raise UntrustedRedirect("该链接跳转到了不受支持的地址")
    try:
      return DouyinRedirectTrust._validate(target, initial=False)
    except UntrustedRedirect:
      get_logger().warning(
        "douyin redirect refused: host={} class=untrusted_redirect".format(
          safe_url_host(target)
        )
      )
      raise

  def resolve_identity(
    self,
    url: str,
    *,
    is_terminal=None,
    after_request=None,
    **request_options
  ) -> str:
    """Return the first identifiable trusted URL without fetching that target."""
    current = self._validate(url, initial=True)
    options = self._copy_request_options(request_options)
    terminal = _identifiable if is_terminal is None else is_terminal
    visited = {current}
    for _ in range(self._max_redirects):
      response = self._request_hop(
        current,
        after_request=after_request,
        **options
      )
      location = self._location(response)
      if location is None:
        return current
      target = self._target(current, location)
      if target in visited:
        raise RedirectLoop("该短链接的跳转形成了循环")
      if terminal(target):
        return target
      options = self._redirect_request_options(options, current, target)
      visited.add(target)
      current = target
    raise TooManyRedirects("该短链接的跳转次数过多")

  def fetch_document(
    self,
    url: str,
    *,
    after_request=None,
    **request_options
  ) -> RedirectDocument:
    """Fetch a trusted document, validating every redirect before its request."""
    current = self._validate(url, initial=True)
    options = self._copy_request_options(request_options)
    visited = {current}
    for _ in range(self._max_redirects):
      response = self._request_hop(
        current,
        after_request=after_request,
        **options
      )
      location = self._location(response)
      if location is None:
        return RedirectDocument(url=current, response=response)
      target = self._target(current, location)
      if target in visited:
        raise RedirectLoop("该短链接的跳转形成了循环")
      options = self._redirect_request_options(options, current, target)
      visited.add(target)
      current = target
    raise TooManyRedirects("该短链接的跳转次数过多")
