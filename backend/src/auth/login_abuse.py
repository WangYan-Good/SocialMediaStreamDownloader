"""Process-local, bounded protection for the one unauthenticated login route."""

from dataclasses import dataclass
from enum import Enum
import hashlib
import math
import threading
import time

from backend.src.auth.credentials import MAX_USERNAME_LENGTH


LOGIN_MAX_REQUEST_BYTES = 4096
LOGIN_RATE_WINDOW_SECONDS = 60
LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW = 60
LOGIN_PEER_ATTEMPTS_PER_WINDOW = 20
LOGIN_MAX_CONCURRENT_AUTHENTICATIONS = 2
LOGIN_USERNAME_BACKOFF_START_FAILURES = 3
LOGIN_USERNAME_BACKOFF_MAX_SECONDS = 60
LOGIN_USERNAME_STATE_TTL_SECONDS = 600
LOGIN_MAX_TRACKED_PEERS = 1024
LOGIN_MAX_TRACKED_USERNAMES = 4096
LOGIN_ABUSE_GUARD_EXTENSION = "smsd_login_abuse_guard"


class LoginAttemptOutcome(Enum):
  SUCCESS = "success"
  INVALID_CREDENTIALS = "invalid_credentials"
  NEUTRAL = "neutral"


@dataclass(frozen=True)
class LoginAttemptTicket:
  _identifier: int
  _username_key: str


@dataclass(frozen=True)
class LoginAttemptDecision:
  allowed: bool
  retry_after_seconds: int
  ticket: LoginAttemptTicket | None = None


@dataclass
class _WindowState:
  window_started: float
  attempts: int
  last_seen: float


@dataclass
class _UsernameState:
  failures: int
  blocked_until: float
  last_seen: float


def _fingerprint(value: str) -> str:
  return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _positive_seconds(value: float) -> int:
  return max(1, int(math.ceil(value)))


class LoginAbuseGuard:
  """One application's thread-safe login admission state.

  The guard deliberately has no background worker and never sleeps. Every
  refusal is decided while holding one short-lived lock and returned to the
  caller immediately. Only fixed-size fingerprints are retained.
  """

  _OVERSIZED_USERNAME_SCOPE = _fingerprint("smsd-login-oversized-username-v1")

  def __init__(self, *, clock=time.monotonic):
    self._clock = clock
    self._lock = threading.Lock()
    now = self._clock()
    self._global_window_started = now
    self._global_attempts = 0
    self._peers: dict[str, _WindowState] = {}
    self._usernames: dict[str, _UsernameState] = {}
    self._inflight = 0
    self._next_ticket_identifier = 1
    self._active_tickets: set[int] = set()

  @staticmethod
  def _peer_key(peer: str | None) -> str:
    safe_peer = peer if isinstance(peer, str) and peer else "unknown"
    return _fingerprint(safe_peer)

  @classmethod
  def _username_key(cls, username: str) -> str:
    if len(username) > MAX_USERNAME_LENGTH:
      return cls._OVERSIZED_USERNAME_SCOPE
    return _fingerprint(username.strip().casefold())

  def _prune(self, now: float) -> None:
    expiry = now - LOGIN_USERNAME_STATE_TTL_SECONDS
    self._peers = {
      key: state for key, state in self._peers.items()
      if state.last_seen > expiry
    }
    self._usernames = {
      key: state for key, state in self._usernames.items()
      if state.last_seen > expiry
    }

  def _capacity_retry(self, states, now: float) -> int:
    if not states:
      return 1
    earliest = min(state.last_seen for state in states.values())
    return _positive_seconds(
      earliest + LOGIN_USERNAME_STATE_TTL_SECONDS - now
    )

  def begin(self, peer: str | None, username: str) -> LoginAttemptDecision:
    """Atomically admit one expensive authentication or return a fast refusal."""
    now = self._clock()
    peer_key = self._peer_key(peer)
    username_key = self._username_key(username)

    with self._lock:
      self._prune(now)

      if now - self._global_window_started >= LOGIN_RATE_WINDOW_SECONDS:
        self._global_window_started = now
        self._global_attempts = 0
      if self._global_attempts >= LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW:
        return LoginAttemptDecision(
          False,
          _positive_seconds(
            self._global_window_started + LOGIN_RATE_WINDOW_SECONDS - now
          ),
        )

      peer_state = self._peers.get(peer_key)
      if peer_state is None:
        if len(self._peers) >= LOGIN_MAX_TRACKED_PEERS:
          return LoginAttemptDecision(
            False, self._capacity_retry(self._peers, now)
          )
        peer_state = _WindowState(now, 0, now)
        self._peers[peer_key] = peer_state
      elif now - peer_state.window_started >= LOGIN_RATE_WINDOW_SECONDS:
        peer_state.window_started = now
        peer_state.attempts = 0

      username_state = self._usernames.get(username_key)
      if username_state is None:
        if len(self._usernames) >= LOGIN_MAX_TRACKED_USERNAMES:
          return LoginAttemptDecision(
            False, self._capacity_retry(self._usernames, now)
          )
        username_state = _UsernameState(0, 0.0, now)
        self._usernames[username_key] = username_state

      if peer_state.attempts >= LOGIN_PEER_ATTEMPTS_PER_WINDOW:
        return LoginAttemptDecision(
          False,
          _positive_seconds(
            peer_state.window_started + LOGIN_RATE_WINDOW_SECONDS - now
          ),
        )
      if username_state.blocked_until > now:
        return LoginAttemptDecision(
          False,
          _positive_seconds(username_state.blocked_until - now),
        )

      # A saturated authentication pool still consumes the cheap fixed-window
      # allowance. Repeated concurrency probes cannot be made free requests.
      self._global_attempts += 1
      peer_state.attempts += 1
      peer_state.last_seen = now
      username_state.last_seen = now

      if self._inflight >= LOGIN_MAX_CONCURRENT_AUTHENTICATIONS:
        return LoginAttemptDecision(False, 1)

      identifier = self._next_ticket_identifier
      self._next_ticket_identifier += 1
      self._active_tickets.add(identifier)
      self._inflight += 1
      return LoginAttemptDecision(
        True,
        0,
        LoginAttemptTicket(identifier, username_key),
      )

  def finish(
    self,
    ticket: LoginAttemptTicket | None,
    outcome: LoginAttemptOutcome,
  ) -> None:
    """Release a ticket once and apply only the named credential outcome."""
    if ticket is None or not isinstance(outcome, LoginAttemptOutcome):
      return
    now = self._clock()
    with self._lock:
      if ticket._identifier not in self._active_tickets:
        return
      self._active_tickets.remove(ticket._identifier)
      self._inflight -= 1

      state = self._usernames.get(ticket._username_key)
      if state is None:
        return
      state.last_seen = now
      if outcome is LoginAttemptOutcome.SUCCESS:
        self._usernames.pop(ticket._username_key, None)
        return
      if outcome is not LoginAttemptOutcome.INVALID_CREDENTIALS:
        return

      state.failures += 1
      if state.failures >= LOGIN_USERNAME_BACKOFF_START_FAILURES:
        exponent = max(
          0, state.failures - LOGIN_USERNAME_BACKOFF_START_FAILURES
        )
        delay = min(
          2 ** exponent,
          LOGIN_USERNAME_BACKOFF_MAX_SECONDS,
        )
        state.blocked_until = now + delay

  @property
  def inflight(self) -> int:
    with self._lock:
      return self._inflight

  @property
  def peer_state_size(self) -> int:
    with self._lock:
      return len(self._peers)

  @property
  def username_state_size(self) -> int:
    with self._lock:
      return len(self._usernames)

  def _username_keys_for_test(self) -> tuple[str, ...]:
    with self._lock:
      return tuple(self._usernames)


__all__ = [
  "LOGIN_ABUSE_GUARD_EXTENSION",
  "LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW",
  "LOGIN_MAX_CONCURRENT_AUTHENTICATIONS",
  "LOGIN_MAX_REQUEST_BYTES",
  "LOGIN_MAX_TRACKED_PEERS",
  "LOGIN_MAX_TRACKED_USERNAMES",
  "LOGIN_PEER_ATTEMPTS_PER_WINDOW",
  "LOGIN_RATE_WINDOW_SECONDS",
  "LOGIN_USERNAME_BACKOFF_MAX_SECONDS",
  "LOGIN_USERNAME_BACKOFF_START_FAILURES",
  "LOGIN_USERNAME_STATE_TTL_SECONDS",
  "LoginAbuseGuard",
  "LoginAttemptDecision",
  "LoginAttemptOutcome",
  "LoginAttemptTicket",
]
