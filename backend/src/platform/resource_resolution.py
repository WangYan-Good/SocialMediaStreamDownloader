##<<Base>>
import re
from dataclasses import dataclass, field


##
## The vocabulary ``POST /api/resolve`` answers in, and the failures it can
## answer with.  Platform-neutral on purpose: the wire contract names the
## platform in its own field, so a resource type stays ``post`` rather than
## becoming ``douyin_post`` and having to be re-minted for every platform added
## later.  This module therefore knows about no platform at all - the douyin
## resolver imports it, not the other way round.
##

RESOURCE_TYPE_POST = "post"
RESOURCE_TYPE_OWNER = "owner"
RESOURCE_TYPE_LIVE = "live"

##
## Closed on purpose.  "unsupported" is deliberately absent: a url this program
## cannot act on is a failed resolve, not a fourth kind of resource, and giving
## it a success shape would push the decision onto every later consumer.
##
RESOURCE_TYPES = (RESOURCE_TYPE_POST, RESOURCE_TYPE_OWNER, RESOURCE_TYPE_LIVE)


##
## >>============================= failures =============================>>
##

class ResourceResolveError(Exception):
  """One of the known ways resolving a pasted link can fail.

  Every failure carries the ``kind`` that logs record and the ``status_code``
  the api answers with, so neither is re-derived from the message text at the
  edge.  ``kind`` is a category, never the pasted input: a resolve failure must
  be diagnosable from the log without the log holding the user's clipboard.
  """

  kind = "resolve_failed"
  status_code = 400


class InputMissing(ResourceResolveError):
  kind = "input_missing"


class NoUrlFound(ResourceResolveError):
  kind = "no_url"


class MultipleUrls(ResourceResolveError):
  """More than one distinct link.  ``/api/resolve`` answers about exactly one.

  Silently taking the first would make the server's verdict disagree with what
  the user believes they submitted, and the mistake would only surface once a
  task started against the wrong resource.
  """

  kind = "multiple_urls"


class BatchTooLarge(ResourceResolveError):
  kind = "batch_too_large"


class UnsupportedScheme(ResourceResolveError):
  kind = "unsupported_scheme"


class UnsupportedPlatform(ResourceResolveError):
  kind = "unsupported_platform"


class UnsupportedResource(ResourceResolveError):
  """A host this program knows, pointing at something it cannot name."""

  kind = "unsupported_resource"


class UntrustedRedirect(ResourceResolveError):
  """A short link tried to leave the platform's own hosts.

  Answered as a bad request rather than a gateway error: nothing upstream
  malfunctioned, the link simply does not lead where a douyin share link may
  lead, and that is a property of the input.
  """

  kind = "untrusted_redirect"


class ShortLinkUnavailable(ResourceResolveError):
  """The short link could not be followed - a timeout, a refused connection.

  The one family of failures that is genuinely upstream's, so the one that
  answers 502.  The two below are subclasses rather than separate types so a
  caller which only cares that the short link did not resolve catches one thing,
  while the log still records which of the three it was.
  """

  kind = "short_link_unavailable"
  status_code = 502


class RedirectLoop(ShortLinkUnavailable):
  """The chain came back to a url it had already visited."""

  kind = "redirect_loop"


class TooManyRedirects(ShortLinkUnavailable):
  """The chain did not end within the hop limit."""

  kind = "too_many_redirects"


##
## >>============================= input parsing =============================>>
##

##
## Sharing from the app copies a sentence, not a bare link:
##   4.33 复制打开抖音，看看【xxx的作品】 https://v.douyin.com/xxx/ :0pm
## Only ``http(s)`` is a link here.  A ``file://`` or ``javascript:`` string is
## not something this api could follow even if it wanted to, so it never reaches
## the point of being rejected as a host.
##
_URL_IN_TEXT = re.compile(r"https?://[^\s]+")

##
## Chinese full stops and brackets sit flush against a url that ends a sentence.
##
_TRAILING_NOISE = ")]}>,.;:!?，。；：！？、）】》"


def extract_urls(text) -> list:
  """Return every distinct url inside ``text``, in the order they appear.

  Distinct rather than every occurrence: a doubled paste names one resource, and
  reporting it as two would refuse a request the user is perfectly clear about.
  Never invents a url - prose without ``http(s)://`` yields nothing.

  Kept separate from ``extract_url``, which answers "the first one" and is what
  the existing owner and handler paths rely on.  This one exists because
  ``/api/resolve`` has to be able to say *how many* there were.
  """
  if not isinstance(text, str) or not text.strip():
    return []
  found = []
  for matched in _URL_IN_TEXT.finditer(text):
    url = matched.group(0).rstrip(_TRAILING_NOISE)
    if url and url not in found:
      found.append(url)
  return found


##
## >>============================= resolution =============================>>
##

@dataclass(frozen=True)
class ResourceResolution:
  """What one pasted link turned out to be.

  Identity-level on purpose: it says *which* resource the input names, not what
  that resource currently contains.  Reading a title, a nickname or a live
  status costs a platform request, depends on a valid cookie and changes minute
  to minute, and none of that belongs in an answer to "what did I just paste?".

  ``source_url`` is the link lifted out of the user's input; ``resolved_url`` is
  the url the verdict was actually read from.  They differ only when a short
  link had to be followed.  The pasted text itself is deliberately not kept:
  the share sentence carries nothing the later stages need, and holding it would
  only be one more place a user's clipboard could leak from.
  """

  platform: str
  resource_type: str
  source_url: str
  resolved_url: str
  identity: dict = field(default_factory=dict)

  def __post_init__(self):
    if self.resource_type not in RESOURCE_TYPES:
      raise ValueError(
        "unknown resource type: {!r}".format(self.resource_type)
      )
    ##
    ## Copied on the way in, so a caller that keeps and later edits the dict it
    ## handed over cannot reach into a value that is otherwise frozen.
    ##
    object.__setattr__(self, "identity", dict(self.identity or {}))
