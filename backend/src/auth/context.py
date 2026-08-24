##<<Base>>
from dataclasses import dataclass
from enum import Enum
from typing import Optional

##<<Third-part>>
from backend.src.auth.service import AuthenticatedUser


class RequestAuthStatus(str, Enum):
  """The three answers authentication can give for one request."""

  ANONYMOUS = "anonymous"
  AUTHENTICATED = "authenticated"
  UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class RequestAuthContext:
  """Authentication facts established once at the HTTP request boundary.

  The raw session credential deliberately does not live here.  The request
  hook derives the only later value CSRF needs and then leaves the credential
  in Flask's cookie parser, outside the context consumed by application code.
  """

  status: RequestAuthStatus
  user: Optional[AuthenticatedUser] = None
  csrf_expected: Optional[str] = None

  @classmethod
  def anonymous(cls, *, csrf_expected=None):
    return cls(RequestAuthStatus.ANONYMOUS, csrf_expected=csrf_expected)

  @classmethod
  def authenticated(cls, user, *, csrf_expected):
    return cls(
      RequestAuthStatus.AUTHENTICATED,
      user=user,
      csrf_expected=csrf_expected,
    )

  @classmethod
  def unavailable(cls, *, csrf_expected):
    return cls(RequestAuthStatus.UNAVAILABLE, csrf_expected=csrf_expected)
