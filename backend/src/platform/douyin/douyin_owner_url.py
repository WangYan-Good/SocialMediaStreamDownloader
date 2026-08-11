##<<Base>>
import re
from urllib.parse import parse_qs, urlparse

##<<Third-part>>
from backend.src.platform.douyin.douyin_url_hosts import (
  is_content_host,
  is_live_host,
  is_short_link_host,
)


##
## A profile share link is resolved by following its redirect first; what arrives
## here is the *resolved* url.  These are the forms an owner profile lands on.
##
_PATH_PATTERNS = (
  ##
  ## PC profile page
  ##
  re.compile(r"^/user/([A-Za-z0-9_\-]+)"),
  ##
  ## mobile share page.  A real "查看TA的更多作品" link from the app lands here,
  ## carrying the id in both the path and a sec_uid query parameter.
  ##
  re.compile(r"^/share/user/([A-Za-z0-9_\-]+)"),
)

##
## Some profile urls carry the id only in the query string.
##
_QUERY_KEYS = ("sec_uid", "sec_user_id")

##
## Owner ids are opaque base64url-ish tokens that begin with a fixed marker.
## Requiring it keeps a path like /user/settings from reading as an owner.
##
_ID_PREFIX = "MS4wLjABAAAA"
_MIN_ID_LENGTH = 20


def _is_owner_id(value) -> bool:
  if not isinstance(value, str):
    return False
  value = value.strip()
  if len(value) < _MIN_ID_LENGTH:
    return False
  if not value.startswith(_ID_PREFIX):
    return False
  return re.fullmatch(r"[A-Za-z0-9_\-]+", value) is not None


##
## Sharing from the app copies a sentence, not a bare link:
##   0- 长按复制此条消息，打开抖音搜索，查看TA的更多作品。 https://v.douyin.com/xxx/ 4@1.com :0pm
## The browser trims this before sending, but an api is not entitled to assume its
## input was cleaned - so the same extraction happens here.
##
_URL_IN_TEXT = re.compile(r"https?://[^\s]+")

##
## Chinese full stops and brackets sit flush against a url that ends a sentence.
##
_TRAILING_NOISE = ")]}>,.;:!?，。；：！？、）】》"


def extract_url(text: str) -> str:
  """Return the first url inside ``text``, or ``text`` itself if it is one.

  Never invents a url: if there is no ``http(s)://`` in the input, the result is
  empty.
  """
  if not isinstance(text, str) or not text.strip():
    return ""
  matched = _URL_IN_TEXT.search(text)
  if matched is None:
    return ""
  return matched.group(0).rstrip(_TRAILING_NOISE)


def classify_owner_url(url: str):
  """Return the ``sec_user_id`` ``url`` points at, or ``None``.

  ``None`` covers live rooms, single posts and anything unrecognised.  It is not
  an error: the caller decides what to do with a url this module does not claim.

  The id is required to carry the owner-id marker.  Without that check a path
  like ``/user/settings`` would read as an owner and turn into a platform request
  that could only fail confusingly.
  """
  if not isinstance(url, str) or not url.strip():
    return None

  parsed = urlparse(url.strip())
  if not is_content_host(parsed.netloc) or is_live_host(parsed.netloc):
    return None

  for pattern in _PATH_PATTERNS:
    matched = pattern.match(parsed.path or "")
    if matched is not None and _is_owner_id(matched.group(1)):
      return matched.group(1).strip()

  ##
  ## Fall back to the query string.  The mobile share form carries sec_uid there
  ## as well, and some entry points carry it *only* there.
  ##
  query = parse_qs(parsed.query)
  for key in _QUERY_KEYS:
    for value in query.get(key) or []:
      if _is_owner_id(value):
        return value.strip()

  return None


def is_owner_url(url: str) -> bool:
  """Whether ``url`` points at an owner profile."""
  return classify_owner_url(url) is not None


def needs_resolution(url: str) -> bool:
  """Whether ``url`` has to be followed before it can be classified.

  True only for the short share form, which carries no id and only redirects.
  A profile page, a post page and a live room are each already a verdict, and
  following one would spend a request to learn nothing.
  """
  if not isinstance(url, str) or not url.strip():
    return False
  if classify_owner_url(url) is not None:
    return False
  return is_short_link_host(urlparse(url.strip()).netloc)
