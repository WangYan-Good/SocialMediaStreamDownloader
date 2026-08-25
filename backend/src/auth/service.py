##<<Base>>
from dataclasses import dataclass
from datetime import datetime, timedelta

##<<Third-part>>
from backend.src.auth.credentials import (
  canonical_username,
  hash_password,
  hash_session_token,
  new_session_token,
  validate_password,
  verify_password,
)
from backend.src.auth.errors import (
  AuthUnavailable,
  DuplicateUsername,
  InvalidCredentials,
  UnknownUsername,
)
from backend.src.auth.roles import ROLE_USER, validate_role


##
## A hash of nothing anybody knows, verified against when no account matched.
##
## Without it, an unknown username returns as soon as the lookup misses, while
## a known one pays for a full scrypt verification - and the difference is
## measurable from outside.  That would hand back exactly the information the
## identical error message exists to withhold.
##
## Computed once at import: it is the *cost* that has to match, not the value.
##
_DUMMY_PASSWORD_HASH = hash_password("dummy password for timing equalisation")


@dataclass(frozen=True)
class AuthenticatedUser:
  """Server-resolved identity and role for the current request."""

  user_id: int
  username: str
  role: str


@dataclass(frozen=True)
class IssuedSession:
  """A newly created session.

  ``token`` exists only here and in the response that sets the cookie. It is
  never stored, never logged and never returned again - the database holds only
  its hash, and there is no way back from that to this.
  """

  token: str
  expires_at: datetime


class AuthenticationService:
  """Who is signing in, and which browsers are currently signed in.

  Everything about passwords and sessions lives behind this class so that no
  route has to know how either is stored.  A route parses HTTP, maps an
  exception to a status and sets a cookie; it does not hash, compare or expire
  anything.
  """

  def __init__(self, repository, *, session_ttl_seconds: int, clock=datetime.utcnow):
    self._repository = repository
    self._ttl = int(session_ttl_seconds)
    self._clock = clock
    ##
    ## Held as an attribute so a test can observe that the dummy verification
    ## really happens on the miss path.
    ##
    self._verify = verify_password

  ##
  ## >>============================= accounts =============================>>
  ##

  def create_user(
    self,
    username: str,
    password: str,
    *,
    role: str = ROLE_USER,
  ) -> AuthenticatedUser:
    """Create an account. Only ever called deliberately - there is no sign-up."""
    canonical = canonical_username(username)
    selected_role = validate_role(role)
    ##
    ## Policy before work: an over-long password is refused before scrypt is
    ## asked to hash it, and a refused password writes no row.
    ##
    validate_password(password)

    user_id = self._repository.insert_user(
      canonical,
      hash_password(password),
      selected_role,
    )
    return AuthenticatedUser(
      user_id=user_id,
      username=canonical,
      role=selected_role,
    )

  def set_role(self, username: str, role: str) -> AuthenticatedUser:
    """Set one account's role; existing sessions observe it on their next read."""
    canonical = canonical_username(username)
    selected_role = validate_role(role)
    row = self._repository.find_user_by_username(canonical)
    if row is None:
      raise UnknownUsername(canonical)
    if row["role"] != selected_role:
      if not self._repository.set_user_role(row["user_id"], selected_role):
        raise UnknownUsername(canonical)
    return AuthenticatedUser(
      user_id=row["user_id"],
      username=row["username"],
      role=selected_role,
    )

  ##
  ## >>============================= signing in =============================>>
  ##

  def authenticate(self, username: str, password: str) -> AuthenticatedUser:
    """Identify an account from a username and password.

    Raises ``InvalidCredentials`` for no-such-account, wrong-password and
    disabled alike.  The three are one answer on purpose.
    """
    try:
      canonical = canonical_username(username)
    except ValueError:
      ##
      ## A malformed name cannot match any stored account, and is answered the
      ## same way as one that simply does not exist - a distinct error here
      ## would be a probe for what the canonical form is.
      ##
      self._verify(_DUMMY_PASSWORD_HASH, password or "")
      raise InvalidCredentials("用户名或密码错误")

    row = self._repository.find_user_by_username(canonical)

    if row is None:
      ##
      ## Pay the same cost as a real check before refusing. See the note on
      ## _DUMMY_PASSWORD_HASH.
      ##
      self._verify(_DUMMY_PASSWORD_HASH, password or "")
      raise InvalidCredentials("用户名或密码错误")

    if not self._verify(row["password_hash"], password or ""):
      raise InvalidCredentials("用户名或密码错误")

    if not row.get("is_active"):
      ##
      ## Checked after the password, so a disabled account is not distinguishable
      ## from a wrong password by how long the answer takes.
      ##
      raise InvalidCredentials("用户名或密码错误")

    return AuthenticatedUser(
      user_id=row["user_id"],
      username=row["username"],
      role=validate_role(row["role"]),
    )

  ##
  ## >>============================= sessions =============================>>
  ##

  def create_session(self, user_id: int) -> IssuedSession:
    token = new_session_token()
    expires_at = self._clock() + timedelta(seconds=self._ttl)
    ##
    ## The hash goes in; the token goes back to the caller and nowhere else.
    ##
    self._repository.insert_session(hash_session_token(token), user_id, expires_at)
    return IssuedSession(token=token, expires_at=expires_at)

  def resolve_session(self, token) -> AuthenticatedUser | None:
    """Who this token belongs to, or None if it belongs to nobody.

    ``None`` means anonymous - unknown, expired, or belonging to an account
    that has since been disabled.  It never means "the database is down": that
    raises, because treating an outage as "signed out" would log everybody out
    whenever the database hiccuped.
    """
    if not token or not isinstance(token, str):
      return None

    row = self._repository.find_session(hash_session_token(token))
    if row is None:
      return None

    if row["expires_at"] <= self._clock():
      return None

    user = self._repository.find_user_by_id(row["user_id"])
    if user is None or not user.get("is_active"):
      ##
      ## Disabling an account has to take effect on the sessions it already
      ## holds, or "disabled" means nothing until they happen to expire.
      ##
      return None

    self._repository.touch_session(row["token_hash"], self._clock())
    return AuthenticatedUser(
      user_id=user["user_id"],
      username=user["username"],
      role=validate_role(user["role"]),
    )

  def revoke_session(self, token) -> bool:
    """End one session. Idempotent: signing out twice is not an error."""
    if not token or not isinstance(token, str):
      return False
    return self._repository.delete_session(hash_session_token(token))
