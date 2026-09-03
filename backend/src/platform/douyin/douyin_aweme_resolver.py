##<<Base>>
import json
import re
from dataclasses import dataclass
from random import randint
from time import sleep
from urllib.parse import unquote

##<<Extension>>
from requests import request

##<<Third-part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.library.safe_diagnostics import post_diagnostic
from backend.src.platform.douyin.douyin_api import DouyinApi
from backend.src.platform.douyin.douyin_aweme_config import DouyinAwemeConfig
from backend.src.platform.douyin.douyin_aweme_external_info import (
  SOURCE_API,
  SOURCE_HTML,
  AwemeUnavailable,
  build_aweme_detail,
)
from backend.src.platform.douyin.douyin_aweme_url import (
  classify_aweme_url,
  needs_resolution,
)
from backend.src.platform.douyin.douyin_header import DouyinPostInfoHeader
from backend.src.platform.douyin.douyin_login import DouyinLogin
from backend.src.platform.douyin.douyin_redirect_trust import DouyinRedirectTrust


##
## Embedded payloads on a share page.  Both forms have been used; take whichever
## is present rather than betting on one.
##
_ROUTER_DATA_PATTERN = re.compile(
  r"window\._ROUTER_DATA\s*=\s*(\{.*?\})\s*;?\s*</script>",
  re.DOTALL,
)
_RENDER_DATA_PATTERN = re.compile(
  r"<script[^>]+id=\"RENDER_DATA\"[^>]*>(.*?)</script>",
  re.DOTALL,
)

##
## A payload is recognised as a post by its own shape rather than by its position
## in the document.  The nesting path has changed before, and a shape check keeps
## working when it changes again.
##
_AWEME_MARKERS = ("video", "images", "music", "author")

##
## How deep to walk an embedded payload before giving up.  Guards against a
## pathological or hostile document; real payloads nest far shallower.
##
_MAX_SEARCH_DEPTH = 40


@dataclass(frozen=True)
class AwemeResolution:
  """Outcome of asking the platform about one post link.

  Expected failures - a timeout, a rejection, a deleted post - come back as
  ``ok=False`` with a reason rather than as an exception, because they are
  ordinary answers when resolving a link the user pasted.
  """

  ok: bool
  aweme_id: str = None
  detail: object = None
  reason: str = None
  api_error: str = None
  html_error: str = None

  @property
  def source(self):
    return None if self.detail is None else self.detail.source


def _looks_like_aweme(candidate, aweme_id=None) -> bool:
  if not isinstance(candidate, dict):
    return False
  found_id = candidate.get("aweme_id")
  if not isinstance(found_id, str) or not found_id.strip():
    return False
  if aweme_id is not None and found_id.strip() != aweme_id:
    return False
  return any(marker in candidate for marker in _AWEME_MARKERS)


def find_aweme_payload(source, aweme_id=None, _depth=0):
  """Search an embedded payload for the post object.

  Returns the first dict that carries an ``aweme_id`` plus at least one media
  key.  When ``aweme_id`` is given, only that post matches - a share page can
  embed related posts alongside the one that was asked for.
  """
  if _depth > _MAX_SEARCH_DEPTH:
    return None
  if _looks_like_aweme(source, aweme_id):
    return source
  if isinstance(source, dict):
    for value in source.values():
      found = find_aweme_payload(value, aweme_id, _depth + 1)
      if found is not None:
        return found
    return None
  if isinstance(source, (list, tuple)):
    for value in source:
      found = find_aweme_payload(value, aweme_id, _depth + 1)
      if found is not None:
        return found
  return None


def _decode_embedded(raw: str):
  """Parse one embedded blob, tolerating the URI-encoded RENDER_DATA form."""
  candidates = [raw]
  if "%" in raw:
    try:
      candidates.append(unquote(raw))
    except Exception:
      pass
  for candidate in candidates:
    try:
      return json.loads(candidate.strip())
    except (ValueError, TypeError):
      continue
  return None


def extract_embedded_payloads(html: str):
  """Return every embedded JSON document found in ``html``."""
  if not isinstance(html, str) or not html:
    return []
  payloads = []
  for pattern in (_ROUTER_DATA_PATTERN, _RENDER_DATA_PATTERN):
    for matched in pattern.finditer(html):
      decoded = _decode_embedded(matched.group(1))
      if decoded is not None:
        payloads.append(decoded)
  return payloads


class DouyinAwemeResolver:
  """Resolves a single-post link into an ``AwemeDetail``.

  Two routes, one result shape.  The signed detail API is tried first; when it
  is unavailable the share page's embedded payload is parsed instead.  Both feed
  ``build_aweme_detail``, so nothing downstream can tell them apart beyond the
  recorded ``source``.
  """

  def __init__(self, config=None, sleeper=None, request_function=None) -> None:
    self.config = (
      config if isinstance(config, DouyinAwemeConfig)
      else DouyinAwemeConfig(config)
    )
    self.API = DouyinApi(
      self.config.get_config_dict_attr("$.platform.douyin.api")
    )
    self.login = DouyinLogin(
      self.config.get_config_dict_attr("$.platform.douyin.login")
    )
    self._sleeper = sleeper if sleeper is not None else self._random_pause
    self._request = request if request_function is None else request_function
    self._redirects = DouyinRedirectTrust(request_function=self._request)

  def proxies(self):
    """Proxies from ``$.platform.douyin.login.proxies``, passed explicitly.

    Without this ``requests`` would fall back to HTTP_PROXY/HTTPS_PROXY, which
    would quietly ignore the configured value the live path honours.
    """
    return self.login.proxies.get_proxies_dict()

  @staticmethod
  def _random_pause():
    sleep(randint(15, 45) * 0.1)

  def pause(self):
    self._sleeper()

  def _headers(self) -> dict:
    header = DouyinPostInfoHeader(
      self.config.get_config_dict_attr("$.platform.douyin.headers")
    )
    header.init_header(self.config.login)
    return {
      key: value
      for key, value in header.to_dict().items()
      if isinstance(value, str)
    }

  def _detail_params(self, aweme_id: str) -> dict:
    params = self.config.post_params()
    params["aweme_id"] = aweme_id
    self.config.update_verifyFp()
    verify_fp = self.config.get_config_dict_attr(
      "$.platform.douyin.post.verifyFp"
    )
    if verify_fp is not None:
      params["verifyFp"] = verify_fp
      params["fp"] = verify_fp
    ms_token = self.config.get_config_dict_attr(
      "$.platform.douyin.login.msToken"
    )
    if ms_token is not None:
      params["msToken"] = ms_token
    a_bogus = self.config.update_a_bogus(params)
    if a_bogus is not None:
      params["a_bogus"] = a_bogus
    return params

##
## >>============================= API route =============================>>
##
  def _request_detail(self, aweme_id: str):
    api = self.API.get_config_dict_attr("$.POST_DETAIL")
    response = self._request(
      method="GET",
      url=api,
      params=self._detail_params(aweme_id),
      timeout=self.config.max_timeout,
      headers=self._headers(),
      proxies=self.proxies(),
    )
    self.pause()
    if response.status_code != 200:
      raise ValueError(
        "detail api returned status {}".format(response.status_code)
      )
    payload = response.json()
    if not isinstance(payload, dict):
      raise ValueError("detail api returned a non-object payload")

    status_code = payload.get("status_code")
    if status_code not in (None, 0):
      raise ValueError("detail api reported status_code {}".format(status_code))

    detail = payload.get("aweme_detail")
    if not isinstance(detail, dict) or not detail:
      raise ValueError("detail api returned no aweme_detail")
    return detail

##
## >>============================= HTML route =============================>>
##
  def _request_share_page(self, url: str) -> str:
    document = self._redirects.fetch_document(
      url,
      timeout=self.config.max_timeout,
      headers=self._headers(),
      proxies=self.proxies(),
      after_request=self.pause,
    )
    response = document.response
    if response.status_code != 200:
      raise ValueError(
        "share page returned status {}".format(response.status_code)
      )
    response.encoding = "utf-8"
    return response.text

  def _resolve_from_html(self, url: str, aweme_id: str):
    html = self._request_share_page(url)
    payloads = extract_embedded_payloads(html)
    if not payloads:
      raise ValueError("share page carried no embedded payload")
    for payload in payloads:
      found = find_aweme_payload(payload, aweme_id)
      if found is not None:
        return found
    ##
    ## the id-specific search found nothing; accept any post-shaped object in
    ## case the page labels the id differently than the url did
    ##
    for payload in payloads:
      found = find_aweme_payload(payload, None)
      if found is not None:
        return found
    raise ValueError("share page held no post payload")

##
## >>============================= entry point =============================>>
##
  def _follow_share_link(self, url: str):
    """Follow a short share link and return where it landed.

    A ``v.douyin.com`` link carries no post id of its own, so it has to be
    followed before it can be classified.  The handler normally does this and
    passes the result down; this covers the standalone call.
    """
    return self._redirects.resolve_identity(
      url,
      timeout=self.config.max_timeout,
      headers=self._headers(),
      proxies=self.proxies(),
      after_request=self.pause,
    )

  def resolve(self, url: str, aweme_id: str = None) -> AwemeResolution:
    """Resolve ``url`` into an ``AwemeResolution``."""
    resolved_url = url
    resolved_id = aweme_id if aweme_id is not None else classify_aweme_url(url)
    if resolved_id is None and needs_resolution(url):
      try:
        resolved_url = self._follow_share_link(url)
        resolved_id = classify_aweme_url(resolved_url)
      except Exception as e:
        return AwemeResolution(
          ok=False,
          reason="could not follow the share link",
          api_error="{}: {}".format(type(e).__name__, e),
        )
    if resolved_id is None:
      return AwemeResolution(
        ok=False,
        reason="url does not point at a single post",
      )

    switches = self.config.media_switches
    quality = self.config.video_quality

    api_error = None
    try:
      payload = self._request_detail(resolved_id)
      detail = build_aweme_detail(
        payload,
        aweme_id=resolved_id,
        switches=switches,
        quality=quality,
        source=SOURCE_API,
      )
      return AwemeResolution(ok=True, aweme_id=resolved_id, detail=detail)
    except AwemeUnavailable as e:
      ##
      ## The API answered and the answer was "nothing to download".  A second
      ## route cannot change that, so stop here instead of spending a request.
      ##
      return AwemeResolution(
        ok=False,
        aweme_id=resolved_id,
        reason=str(e),
        api_error=str(e),
      )
    except Exception as e:
      api_error = "{}: {}".format(type(e).__name__, e)
      ##
      ## ``api_error`` is kept on the resolution because a caller may show it to
      ## the person who asked, and deliberately not written here: a transport
      ## exception quotes the signed url it failed on.
      ##
      get_logger().warning(
        post_diagnostic(
          "post_detail_api_failed",
          aweme_id=resolved_id,
          error=e,
        )
      )

    if not self.config.html_fallback:
      return AwemeResolution(
        ok=False,
        aweme_id=resolved_id,
        reason="detail api failed and html fallback is disabled",
        api_error=api_error,
      )

    try:
      payload = self._resolve_from_html(resolved_url, resolved_id)
      detail = build_aweme_detail(
        payload,
        aweme_id=resolved_id,
        switches=switches,
        quality=quality,
        source=SOURCE_HTML,
      )
      return AwemeResolution(
        ok=True,
        aweme_id=resolved_id,
        detail=detail,
        api_error=api_error,
      )
    except AwemeUnavailable as e:
      return AwemeResolution(
        ok=False,
        aweme_id=resolved_id,
        reason=str(e),
        api_error=api_error,
        html_error=str(e),
      )
    except Exception as e:
      html_error = "{}: {}".format(type(e).__name__, e)
      get_logger().error(
        post_diagnostic(
          "post_html_fallback_failed",
          aweme_id=resolved_id,
          error=e,
        )
      )
      return AwemeResolution(
        ok=False,
        aweme_id=resolved_id,
        reason="could not resolve the post through either route",
        api_error=api_error,
        html_error=html_error,
      )
