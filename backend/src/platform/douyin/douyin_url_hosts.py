##<<Base>>
from urllib.parse import urlparse

##
## Which douyin hosts mean what.  Shared by every url classifier so the allow
## list exists once: the dispatcher routes on ``'douyin' in netloc``, so a host
## like ``douyin.com.example.test`` reaches those classifiers, and a second copy
## of this list would eventually disagree with the first about it.
##

##
## Hosts that serve post and profile pages.  An allow list rather than a shape
## check, for the reason above.
##
CONTENT_DOMAINS = ("douyin.com", "iesdouyin.com")

##
## Live rooms belong to the live path.  These sit inside the domains above, so
## they have to be named explicitly.
##
LIVE_HOSTS = ("live.douyin.com", "webcast.amemv.com")

##
## The short share form.  A douyin.com subdomain like any other, but it carries
## no id of its own: it only redirects, so it has to be followed before any
## verdict is possible.
##
SHORT_LINK_HOSTS = ("v.douyin.com",)


def hostname(netloc: str) -> str:
  """Return the bare host from a netloc, without credentials or port.

  ``user@evil.test`` must not read as ``user``: a url like
  ``https://www.douyin.com@evil.test/...`` has ``evil.test`` as its real host.
  """
  host = netloc.lower().rsplit("@", 1)[-1]
  return host.split(":")[0].rstrip(".")


def matches(host: str, domain: str) -> bool:
  """Whether ``host`` is ``domain`` or a subdomain of it."""
  return host == domain or host.endswith("." + domain)


def is_live_host(netloc: str) -> bool:
  host = hostname(netloc)
  return any(matches(host, live_host) for live_host in LIVE_HOSTS)


def is_content_host(netloc: str) -> bool:
  host = hostname(netloc)
  return any(matches(host, domain) for domain in CONTENT_DOMAINS)


def is_short_link_host(netloc: str) -> bool:
  host = hostname(netloc)
  return any(matches(host, short) for short in SHORT_LINK_HOSTS)


def host_of(url: str) -> str:
  """Convenience for callers holding a whole url rather than a netloc."""
  if not isinstance(url, str) or not url.strip():
    return ""
  return hostname(urlparse(url.strip()).netloc)
