##<<Base>>
from urllib.parse import urlparse

##<<Extension>>
from requests import request

##<<Third-part>>
from backend.src.platform.douyin.douyin_aweme_url import classify_aweme_url
from backend.src.platform.douyin.douyin_owner_url import classify_owner_url
from backend.src.platform.douyin.douyin_redirect_trust import DouyinRedirectTrust
from backend.src.platform.douyin.douyin_url_hosts import (
  is_live_host,
  is_short_link_host,
)
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
  ResourceResolution,
  UnsupportedPlatform,
  UnsupportedResource,
  UnsupportedScheme,
)


PLATFORM_DOUYIN = "douyin"

##
## The only schemes that could be followed even in principle.  Checked before
## the host, so ``file:///etc/passwd`` is refused as a scheme rather than being
## carried into host matching where its empty netloc would mean nothing.
##
_ALLOWED_SCHEMES = ("http", "https")


class DouyinResourceResolver:
  """Answers what one douyin link points at, and nothing more.

  Identity only: a post id, an owner id, or the fact that a url is a live room.
  Reading the post's detail, the owner's profile or the room's current status is
  deliberately out of scope - each costs a platform request, two of the three
  need a valid cookie, and the third changes minute to minute, so none of them
  can be part of a stable answer to "what is this link?".

  Depends on nothing but url parsing and one injectable request function: no
  Flask, no task service, no database, no downloader.
  """

##
## >>============================= private method =============================>>
##
  platform = PLATFORM_DOUYIN

  def __init__(
    self,
    request_function=None,
    timeout: float = 10.0,
    max_redirects: int = 5,
    proxies=None,
  ) -> None:
    ##
    ## Injected rather than reached for, so every test in this suite proves what
    ## was *not* requested as easily as what was.
    ##
    self._request = request_function if request_function is not None else request
    self._timeout = timeout
    self._max_redirects = max_redirects
    self._proxies = proxies
    self._redirects = DouyinRedirectTrust(
      request_function=self._request,
      max_redirects=max_redirects,
    )

  @staticmethod
  def _classify(url: str):
    """Return ``(resource_type, identity)`` for ``url``, or ``None``.

    Live is tested first because a live host is not a content host for
    ``webcast.amemv.com`` and *is* one for ``live.douyin.com``; asking the post
    and owner classifiers first would work only by relying on their internal
    live checks.  Order stated here means one url can only ever produce one
    verdict, whatever those classifiers do later.
    """
    parsed = urlparse(url)
    if is_live_host(parsed.netloc):
      ##
      ## Identity is deliberately empty.  The number in ``live.douyin.com/123``
      ## is the room's *web* id, which is not the ``room_id`` the live payload
      ## and every table use; putting it in ``identity`` would mint an id that
      ## looks server-verified and is not.  The real one comes from a live
      ## probe, which answers a different question and whose answer expires.
      ##
      return RESOURCE_TYPE_LIVE, {}

    aweme_id = classify_aweme_url(url)
    if aweme_id is not None:
      return RESOURCE_TYPE_POST, {"aweme_id": aweme_id}

    sec_user_id = classify_owner_url(url)
    if sec_user_id is not None:
      return RESOURCE_TYPE_OWNER, {"sec_user_id": sec_user_id}

    return None

  def _follow_short_link(self, url: str) -> str:
    """Walk through the shared trust authority to the first named URL."""
    return self._redirects.resolve_identity(
      url,
      is_terminal=lambda candidate: self._classify(candidate) is not None,
      timeout=self._timeout,
      proxies=self._proxies,
    )

##
## >>============================= sub class method =============================>>
##
  def claims(self, url) -> bool:
    """Whether ``url`` is on a host this resolver speaks for.

    Asked before ``resolve`` so the service can tell "we do not support that
    platform yet" from "that douyin link points at something we cannot name".
    """
    if not isinstance(url, str) or not url.strip():
      return False
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
      return False
    return self._redirects.trusts(url.strip())

  def resolve(self, url) -> ResourceResolution:
    """Name the resource ``url`` points at, or say why it cannot be named.

    A url that already carries its own id is answered from the url alone - no
    request is made, because following it could only rediscover what is already
    written in it.
    """
    if not isinstance(url, str) or not url.strip():
      raise UnsupportedScheme("请粘贴一个 http(s) 链接")

    source_url = url.strip()
    parsed = urlparse(source_url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
      raise UnsupportedScheme("请粘贴一个 http(s) 链接")
    if not self._redirects.trusts(source_url):
      ##
      ## Refused without being contacted.  This endpoint takes whatever a
      ## browser sends, so a host that merely reads like ours - a lookalike
      ## domain, loopback, the cloud metadata address - must never become a
      ## request this server makes on someone else's behalf.
      ##
      raise UnsupportedPlatform("暂不支持该平台的链接")

    resolved_url = source_url
    verdict = self._classify(resolved_url)

    if verdict is None and is_short_link_host(parsed.netloc):
      ##
      ## The one form worth a request.  A short link carries no id of its own -
      ## it only redirects - so it cannot be classified without being followed.
      ## Every other form already states what it is, and following one would
      ## spend a request to learn nothing.
      ##
      resolved_url = self._follow_short_link(source_url)
      verdict = self._classify(resolved_url)

    if verdict is None:
      raise UnsupportedResource("无法识别该链接指向的资源")

    resource_type, identity = verdict
    return ResourceResolution(
      platform=PLATFORM_DOUYIN,
      resource_type=resource_type,
      source_url=source_url,
      resolved_url=resolved_url,
      identity=identity,
    )
