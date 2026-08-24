##<<Base>>
import hashlib
import hmac
import secrets

##<<Extension>>
from werkzeug.security import check_password_hash, generate_password_hash


##
## >>============================= the two secrets =============================>>
##
##
## This module handles both, and they are not the same kind of thing.
##
## A *password* is chosen by a person, is therefore low in entropy, and is
## guessed at offline by anybody who obtains the table.  It gets a deliberately
## slow hash with a per-password salt, so that guessing is expensive.
##
## A *session token* is generated here from ``secrets``, carries far more
## entropy than any password, and is looked up on every authenticated request.
## It gets a single fast SHA-256 with no salt: there is nothing to guess, the
## lookup must be deterministic, and a slow hash would only make every request
## slower.
##
## Using one strategy for both would be wrong in one direction or the other.
##


##
## Named rather than left to Werkzeug's default, so an upgrade that changes
## that default is a decision made here rather than a surprise in a release.
##
PASSWORD_METHOD = "scrypt"

##
## Long enough to be worth having, short enough not to be a wall.  No character
## classes: "must contain a symbol" pushes people towards P@ssw0rd1, which is
## worth less than a few more characters of anything.
##
MIN_PASSWORD_LENGTH = 10

##
## A ceiling, because scrypt's cost is a function of its input and login is
## unauthenticated.  Without this, a multi-megabyte "password" is a way to make
## the server burn CPU on demand.
##
MAX_PASSWORD_LENGTH = 1024

MAX_USERNAME_LENGTH = 190


class CredentialPolicyError(ValueError):
  """A credential this program will not accept, for a reason it can name."""


class PasswordTooShort(CredentialPolicyError):
  pass


class PasswordTooLong(CredentialPolicyError):
  pass


class UsernameInvalid(CredentialPolicyError):
  pass


def validate_password(password: str) -> None:
  """Refuse a password before anything expensive happens to it."""
  if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
    raise PasswordTooShort(
      "密码至少需要 {} 个字符".format(MIN_PASSWORD_LENGTH)
    )
  if len(password) > MAX_PASSWORD_LENGTH:
    raise PasswordTooLong(
      "密码不能超过 {} 个字符".format(MAX_PASSWORD_LENGTH)
    )


def hash_password(password: str) -> str:
  """What gets stored. Never the password itself."""
  return generate_password_hash(password, method=PASSWORD_METHOD)


def verify_password(stored_hash: str, password: str) -> bool:
  """Whether this password produced that hash.

  A malformed stored hash is a refusal rather than an exception.  A row edited
  by hand, or written by a method since removed, must not authenticate - and
  must not take the request down either, which would turn one bad row into an
  availability bug.
  """
  if not stored_hash or not isinstance(stored_hash, str):
    return False
  try:
    return check_password_hash(stored_hash, password)
  except (ValueError, TypeError):
    return False


def canonical_username(username: str) -> str:
  """The one form of a name that gets stored and compared.

  Folded here rather than left to the database collation, so the stored value
  is already canonical and the UNIQUE index means what it appears to mean on
  any collation.

  Inner whitespace is refused rather than stripped: rewriting "al ice" to
  "alice" would let somebody sign in under a name they did not type, and would
  quietly make two visibly different names into one account.
  """
  if not isinstance(username, str):
    raise UsernameInvalid("用户名无效")
  trimmed = username.strip()
  if not trimmed:
    raise UsernameInvalid("用户名不能为空")
  if len(trimmed) > MAX_USERNAME_LENGTH:
    raise UsernameInvalid(
      "用户名不能超过 {} 个字符".format(MAX_USERNAME_LENGTH)
    )
  if any(character.isspace() for character in trimmed):
    raise UsernameInvalid("用户名不能包含空格")
  return trimmed.casefold()


##
## 32 bytes of entropy, url-safe base64 encoded - which is already cookie-safe,
## so no quoting or escaping is ever needed in a Set-Cookie header.
##
SESSION_TOKEN_BYTES = 32


def new_session_token() -> str:
  """The credential a browser will hold.

  From ``secrets``, never ``random``: this single string is the whole proof of
  identity, so a predictable one is a login for everybody.
  """
  return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
  """What the database holds instead of the token.

  Deterministic and unsalted, unlike a password: the lookup is *by* this value,
  and the token it covers already has more entropy than any salt would add
  protection for.
  """
  return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_equal(left: str, right: str) -> bool:
  """Constant-time comparison, for wherever two digests are compared by hand."""
  return hmac.compare_digest(left, right)
