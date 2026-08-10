##<<Base>>
import re
from urllib.parse import parse_qs, urlparse

##
## A share link is resolved by following its redirect first; what arrives here is
## the *resolved* url.  These are the forms a single post lands on.
##
_PATH_PATTERNS = (
  ##
  ## PC video and image-note pages
  ##
  re.compile(r"^/video/(\d+)"),
  re.compile(r"^/note/(\d+)"),
  ##
  ## mobile share pages
  ##
  re.compile(r"^/share/video/(\d+)"),
  re.compile(r"^/share/note/(\d+)"),
)

##
## The recommendation feed opens a post in a modal instead of navigating, so the
## id sits in the query string.
##
_MODAL_PATHS = ("/discover", "/search", "/root/search")
_MODAL_QUERY_KEY = "modal_id"

##
## Hosts that serve post pages.  An allow list rather than a shape check: the
## dispatcher routes on ``'douyin' in netloc``, so a host like
## ``douyin.com.example.test`` reaches this module, and matching on the path
## alone would hand it to the post pipeline.
##
_POST_DOMAINS = ("douyin.com", "iesdouyin.com")

##
## Live rooms are handled by the live path.  These hosts sit inside the domains
## above, so they have to be named explicitly.
##
_LIVE_HOSTS = ("live.douyin.com", "webcast.amemv.com")

##
## The short share form.  It is a douyin.com subdomain like any other, but it
## carries no post id: it only redirects, so it has to be followed before any
## verdict is possible.
##
_SHORT_LINK_HOSTS = ("v.douyin.com",)


def _hostname(netloc: str) -> str:
  ##
  ## drop credentials and port
  ##
  host = netloc.lower().rsplit("@", 1)[-1]
  return host.split(":")[0].rstrip(".")


def _matches(host: str, domain: str) -> bool:
  return host == domain or host.endswith("." + domain)


def _is_live_host(netloc: str) -> bool:
  host = _hostname(netloc)
  return any(_matches(host, live_host) for live_host in _LIVE_HOSTS)


def _is_post_host(netloc: str) -> bool:
  host = _hostname(netloc)
  return any(_matches(host, domain) for domain in _POST_DOMAINS)


def classify_aweme_url(url: str):
  """Return the aweme id ``url`` points at, or ``None`` if it points elsewhere.

  ``None`` is the answer for live rooms, user home pages and anything
  unrecognised.  It is not an error: the caller decides what to do with a url
  this module does not claim.

  Ids are required to be digits.  A non-numeric capture means the url shape
  matched something that is not a post id, and passing that on would only turn
  into a confusing platform error later.
  """
  if not isinstance(url, str) or not url.strip():
    return None

  parsed = urlparse(url.strip())
  if not _is_post_host(parsed.netloc) or _is_live_host(parsed.netloc):
    return None

  path = parsed.path or ""
  for pattern in _PATH_PATTERNS:
    matched = pattern.match(path)
    if matched is not None:
      return matched.group(1)

  ##
  ## strip a trailing slash so "/discover/" matches too
  ##
  normalised_path = path.rstrip("/") or "/"
  if normalised_path in _MODAL_PATHS:
    values = parse_qs(parsed.query).get(_MODAL_QUERY_KEY) or []
    for value in values:
      if value.isdigit():
        return value

  return None


def is_aweme_url(url: str) -> bool:
  """Whether ``url`` points at a single post."""
  return classify_aweme_url(url) is not None


def needs_resolution(url: str) -> bool:
  """Whether ``url`` has to be followed before it can be classified.

  True only for the short share form, which carries no id and only redirects.
  Everything else is already a verdict: a live room, a user home page and a post
  page all mean something definite, and following one would spend a request to
  learn nothing.
  """
  if not isinstance(url, str) or not url.strip():
    return False
  if classify_aweme_url(url) is not None:
    return False
  host = _hostname(urlparse(url.strip()).netloc)
  return any(_matches(host, short) for short in _SHORT_LINK_HOSTS)
