##<<Base>>
import re
import urllib.parse as up
from datetime import datetime


##
## Douyin refuses a request made with a dead session by *withholding* the answer
## rather than reporting an error: HTTP 200 with an empty body, or a body carrying
## a human-verification bundle.  Read literally, that looks identical to "this
## owner has no posts".
##
## During design verification an expired cookie produced exactly that, and the
## empty answer was mistaken for a platform-level block on the endpoint for over
## an hour.  Everything in this module exists so no one repeats that.
##
class SessionExpired(RuntimeError):
  """The platform refused because our login session is not valid."""


class UpstreamRejected(RuntimeError):
  """The platform refused for a reason that is not our session."""


##
## Scripts the verification challenge pulls in.  Their presence in a response
## body means a human is being asked to pass a check.
##
_VERIFY_MARKERS = ("verifycenter", "nocaptcha", "captcha", "secsdk")

##
## The signature validator's own name, seen on 403 responses.
##
_ARGUS_MARKER = "argussecurityplugin"

_BLOCKED_STATUS_MESSAGES = ("blocked",)


def read_payload(response, endpoint: str = "") -> dict:
  """Return the response JSON, or raise with the real reason.

  ``SessionExpired`` for anything that means "log in again"; ``UpstreamRejected``
  for a refusal that a new cookie would not fix.  Never returns an empty payload
  dressed up as a valid answer.
  """
  where = " ({})".format(endpoint) if endpoint else ""
  body = response.text if isinstance(response.text, str) else ""
  lowered = body.lower()

  if response.status_code == 403 and _ARGUS_MARKER in lowered:
    raise SessionExpired(
      "signature validation rejected the request{}".format(where)
    )

  if not body.strip():
    ##
    ## The empty-body refusal.  Named explicitly because it is the one that reads
    ## as "no data" instead of "no access".
    ##
    raise SessionExpired(
      "the platform returned an empty body{}".format(where)
    )

  try:
    payload = response.json()
  except ValueError:
    if any(marker in lowered for marker in _VERIFY_MARKERS):
      raise SessionExpired(
        "the platform asked for human verification{}".format(where)
      )
    raise UpstreamRejected(
      "the platform returned a non-JSON body{}".format(where)
    )

  if not isinstance(payload, dict):
    raise UpstreamRejected(
      "the platform returned a non-object payload{}".format(where)
    )

  status_msg = payload.get("status_msg")
  if isinstance(status_msg, str) and status_msg.lower() in _BLOCKED_STATUS_MESSAGES:
    raise SessionExpired(
      "the platform reported status_msg={!r}{}".format(status_msg, where)
    )

  if response.status_code != 200:
    raise UpstreamRejected(
      "the platform returned status {}{}".format(response.status_code, where)
    )

  return payload


##
## sid_guard carries the session lifetime, so the cookie can say how long it has
## left before anything is requested:
##   <token>|<issued unix seconds>|<lifetime seconds>|<expiry text>
##
_SID_GUARD = re.compile(r"(?:^|;)\s*sid_guard=([^;]+)")


def credential_expiry(cookie: str):
  """Return when the login cookie expires, or ``None`` if it cannot be read."""
  if not isinstance(cookie, str) or not cookie.strip():
    return None
  matched = _SID_GUARD.search(cookie)
  if matched is None:
    return None
  parts = up.unquote(matched.group(1)).split("|")
  if len(parts) < 3:
    return None
  try:
    issued = int(parts[1])
    lifetime = int(parts[2])
  except (TypeError, ValueError):
    return None
  if issued <= 0 or lifetime <= 0:
    return None
  try:
    return datetime.fromtimestamp(issued + lifetime)
  except (OverflowError, OSError, ValueError):
    return None


def credential_days_left(cookie: str, now=None):
  """Whole days until the login cookie expires; negative once it has.

  ``None`` when the cookie carries no readable lifetime.  Surfaced in the UI so
  an expiry is noticed before it turns into an empty post list.
  """
  expiry = credential_expiry(cookie)
  if expiry is None:
    return None
  moment = now if now is not None else datetime.now()
  return (expiry - moment).days
