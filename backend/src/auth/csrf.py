##<<Base>>
import hashlib
import hmac


CSRF_MESSAGE = b"smsd-csrf-v1"


def csrf_token_for_session(raw_session_token: str) -> str:
  """Derive a stable, one-way CSRF proof for one opaque session token."""
  if not isinstance(raw_session_token, str) or not raw_session_token:
    raise ValueError("a non-empty session token is required")
  return hmac.new(
    raw_session_token.encode("utf-8"),
    CSRF_MESSAGE,
    hashlib.sha256,
  ).hexdigest()


def csrf_tokens_match(expected, received) -> bool:
  """Safely compare an untrusted request proof with the derived token."""
  if not isinstance(expected, str) or not expected:
    return False
  if not isinstance(received, str) or not received:
    return False
  try:
    return hmac.compare_digest(expected, received)
  except (TypeError, ValueError):
    return False
