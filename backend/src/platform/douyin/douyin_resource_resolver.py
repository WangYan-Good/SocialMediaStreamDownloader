##<<Base>>
from urllib.parse import urljoin, urlparse

##<<Extension>>
from requests import request

##<<Third-part>>
from backend.src.library.loglib import get_logger
from backend.src.platform.douyin.douyin_aweme_url import classify_aweme_url
from backend.src.platform.douyin.douyin_owner_url import classify_owner_url
from backend.src.platform.douyin.douyin_url_hosts import (
  host_of,
  is_content_host,
  is_live_host,
  is_short_link_host,
)
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
  RedirectLoop,
  ResourceResolution,
  ShortLinkUnavailable,
  TooManyRedirects,
  UnsupportedPlatform,
  UnsupportedResource,
  UnsupportedScheme,
  UntrustedRedirect,
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

  @staticmethod
  def _allowed_host(netloc: str) -> bool:
    ##
    ## The one allow list, borrowed from douyin_url_hosts.  A second copy here
    ## would eventually disagree with that one about a host like
    ## ``douyin.com.evil.test``, and the disagreement would be a hole.
    ##
    return (
      is_live_host(netloc)
      or is_content_host(netloc)
      or is_short_link_host(netloc)
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

  @staticmethod
  def _location(response):
    ##
    ## Header names are case-insensitive, and ``requests`` hands back a mapping
    ## that knows that.  Reading ``headers["Location"]`` would work there and
    ## quietly fail against anything else, so the case-folding happens here.
    ##
    headers = getattr(response, "headers", None) or {}
    for key, value in headers.items():
      if isinstance(key, str) and key.lower() == "location":
        return value
    return None

  def _hop(self, url: str):
    """Make one request and return where it points next, or ``None``.

    The status code is deliberately not consulted.  Douyin answers a share link
    opened outside the app with 444 *after* redirecting it perfectly well, so
    what decides the outcome is whether a ``Location`` arrived, never what the
    hop said about itself.
    """
    try:
      response = self._request(
        method="GET",
        url=url,
        allow_redirects=False,
        timeout=self._timeout,
        proxies=self._proxies,
      )
    except Exception as e:
      ##
      ## The host, not the url: a share url may carry a signature, and an error
      ## log is the last place it should be written down.
      ##
      get_logger().warning(
        "short link hop failed: host={} error={}".format(
          host_of(url), type(e).__name__
        )
      )
      ##
      ## A fixed message.  This text reaches the browser, and the underlying
      ## exception carries internal addresses and ports.
      ##
      raise ShortLinkUnavailable("无法解析该短链接，请稍后重试")
    return self._location(response)

  def _follow_short_link(self, url: str) -> str:
    """Walk a short link to the first url that can be named.

    Every hop is inspected here rather than handed to the http library, because
    the library would follow a redirect off the platform before anyone could
    object.  The checks that make this endpoint safe to expose all live in this
    loop: scheme, host, loop detection and a hop ceiling.
    """
    current = url
    visited = {current}
    for _ in range(self._max_redirects):
      location = self._hop(current)
      if location is None:
        ##
        ## Nothing further to follow.  Whether this url can be named is decided
        ## by the caller, which is the same decision it makes for a long url.
        ##
        return current

      ##
      ## Relative targets are legal - ``Location: /share/video/1`` means the
      ## same host - and resolving them against the hop they arrived on is what
      ## keeps them from being read as a bare path against something else.
      ##
      target = urljoin(current, location)
      parsed = urlparse(target)
      if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UntrustedRedirect("该链接跳转到了不受支持的地址")
      if not self._allowed_host(parsed.netloc):
        ##
        ## Refused *before* the request, not after.  A trusted host handing back
        ## an internal address is the whole pivot this endpoint has to be immune
        ## to, so the target is checked while it is still just a string.
        ##
        get_logger().warning(
          "short link redirected off platform: host={}".format(host_of(target))
        )
        raise UntrustedRedirect("该链接跳转到了非抖音地址")
      if target in visited:
        raise RedirectLoop("该短链接的跳转形成了循环")

      visited.add(target)
      current = target
      if self._classify(current) is not None:
        ##
        ## Named.  Stop here: another request could only confirm what this url
        ## already says, and the whole reason this resolver exists is that the
        ## owner path, the post resolver and the live prober each used to follow
        ## the same share link in turn.
        ##
        return current

    raise TooManyRedirects("该短链接的跳转次数过多")

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
    return self._allowed_host(parsed.netloc)

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
    if not self._allowed_host(parsed.netloc):
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
