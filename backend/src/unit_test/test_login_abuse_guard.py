import threading
import unittest
from unittest.mock import patch

from backend.src.auth import login_abuse
from backend.src.auth.login_abuse import (
  LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW,
  LOGIN_MAX_CONCURRENT_AUTHENTICATIONS,
  LOGIN_MAX_TRACKED_PEERS,
  LOGIN_MAX_TRACKED_USERNAMES,
  LOGIN_PEER_ATTEMPTS_PER_WINDOW,
  LOGIN_RATE_WINDOW_SECONDS,
  LOGIN_USERNAME_STATE_TTL_SECONDS,
  LoginAbuseGuard,
  LoginAttemptOutcome,
)


class FakeMonotonicClock:
  def __init__(self):
    self.value = 1000.0

  def __call__(self):
    return self.value

  def advance(self, seconds):
    self.value += seconds


class TestLoginAbuseGuard(unittest.TestCase):
  def setUp(self):
    self.clock = FakeMonotonicClock()
    self.guard = LoginAbuseGuard(clock=self.clock)

  def finish(self, decision, outcome=LoginAttemptOutcome.NEUTRAL):
    self.assertTrue(decision.allowed)
    self.guard.finish(decision.ticket, outcome)

  def attempt(self, peer="127.0.0.1", username="alice"):
    return self.guard.begin(peer, username)

  def test_constants_pin_the_release_contract(self):
    self.assertEqual(60, LOGIN_RATE_WINDOW_SECONDS)
    self.assertEqual(60, LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW)
    self.assertEqual(20, LOGIN_PEER_ATTEMPTS_PER_WINDOW)
    self.assertEqual(2, LOGIN_MAX_CONCURRENT_AUTHENTICATIONS)
    self.assertEqual(600, LOGIN_USERNAME_STATE_TTL_SECONDS)
    self.assertEqual(1024, LOGIN_MAX_TRACKED_PEERS)
    self.assertEqual(4096, LOGIN_MAX_TRACKED_USERNAMES)

  def test_global_window_refuses_the_sixty_first_attempt(self):
    for index in range(LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW):
      decision = self.attempt(peer=f"peer-{index}", username=f"user-{index}")
      self.finish(decision)

    refused = self.attempt(peer="last-peer", username="last-user")

    self.assertFalse(refused.allowed)
    self.assertEqual(60, refused.retry_after_seconds)

  def test_global_window_uses_monotonic_expiry(self):
    for index in range(LOGIN_GLOBAL_ATTEMPTS_PER_WINDOW):
      self.finish(self.attempt(peer=f"peer-{index}", username=f"user-{index}"))
    self.clock.advance(LOGIN_RATE_WINDOW_SECONDS)

    allowed = self.attempt(peer="new-peer", username="new-user")

    self.finish(allowed)

  def test_peer_window_refuses_the_twenty_first_attempt(self):
    for index in range(LOGIN_PEER_ATTEMPTS_PER_WINDOW):
      self.finish(self.attempt(username=f"user-{index}"))

    refused = self.attempt(username="one-too-many")

    self.assertFalse(refused.allowed)
    self.assertGreaterEqual(refused.retry_after_seconds, 1)

  def test_different_peer_labels_have_independent_windows(self):
    for index in range(LOGIN_PEER_ATTEMPTS_PER_WINDOW):
      self.finish(self.attempt(peer="first", username=f"user-{index}"))

    allowed = self.attempt(peer="second", username="someone")

    self.finish(allowed)

  def test_third_expensive_authentication_is_refused_without_waiting(self):
    first = self.attempt(peer="one", username="one")
    second = self.attempt(peer="two", username="two")

    third = self.attempt(peer="three", username="three")

    self.assertTrue(first.allowed)
    self.assertTrue(second.allowed)
    self.assertFalse(third.allowed)
    self.assertEqual(2, self.guard.inflight)
    self.finish(first)
    self.finish(second)
    self.assertEqual(0, self.guard.inflight)

  def test_concurrent_begin_is_atomic(self):
    barrier = threading.Barrier(8)
    decisions = []
    decisions_lock = threading.Lock()

    def enter(index):
      barrier.wait()
      decision = self.attempt(peer=f"peer-{index}", username=f"user-{index}")
      with decisions_lock:
        decisions.append(decision)

    threads = [threading.Thread(target=enter, args=(index,)) for index in range(8)]
    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()

    allowed = [decision for decision in decisions if decision.allowed]
    self.assertEqual(2, len(allowed))
    self.assertEqual(2, self.guard.inflight)
    for decision in allowed:
      self.finish(decision)

  def test_finish_is_exactly_once_for_a_ticket(self):
    decision = self.attempt()
    self.finish(decision)

    self.guard.finish(decision.ticket, LoginAttemptOutcome.NEUTRAL)

    self.assertEqual(0, self.guard.inflight)

  def test_three_failures_start_one_second_backoff_then_double_to_cap(self):
    expected = [0, 0, 1, 2, 4, 8, 16, 32, 60, 60]
    for index, delay in enumerate(expected, start=1):
      decision = self.attempt()
      self.finish(decision, LoginAttemptOutcome.INVALID_CREDENTIALS)
      blocked = self.attempt()
      if delay == 0:
        self.assertTrue(blocked.allowed, index)
        self.finish(blocked, LoginAttemptOutcome.NEUTRAL)
      else:
        self.assertFalse(blocked.allowed, index)
        self.assertEqual(delay, blocked.retry_after_seconds, index)
        self.clock.advance(delay)

  def test_success_clears_username_failure_state(self):
    for index in range(3):
      decision = self.attempt()
      self.finish(decision, LoginAttemptOutcome.INVALID_CREDENTIALS)
      if index < 2:
        neutral = self.attempt()
        self.finish(neutral)
    self.clock.advance(1)
    successful = self.attempt()
    self.finish(successful, LoginAttemptOutcome.SUCCESS)

    next_attempt = self.attempt()

    self.finish(next_attempt, LoginAttemptOutcome.INVALID_CREDENTIALS)
    immediate = self.attempt()
    self.assertTrue(immediate.allowed)
    self.finish(immediate)

  def test_neutral_outcome_neither_penalizes_nor_leaks_a_slot(self):
    for _ in range(5):
      self.finish(self.attempt(), LoginAttemptOutcome.NEUTRAL)

    self.assertEqual(0, self.guard.inflight)
    decision = self.attempt()
    self.assertTrue(decision.allowed)
    self.finish(decision)

  def test_username_key_is_a_fixed_length_fingerprint_and_never_raw(self):
    decision = self.attempt(username="Sensitive Account Name")
    self.finish(decision, LoginAttemptOutcome.INVALID_CREDENTIALS)

    keys = self.guard._username_keys_for_test()

    self.assertEqual(1, len(keys))
    self.assertEqual(64, len(keys[0]))
    self.assertNotIn("Sensitive", keys[0])

  def test_oversized_usernames_share_one_fixed_scope(self):
    first = self.attempt(username="a" * 10000)
    self.finish(first, LoginAttemptOutcome.INVALID_CREDENTIALS)
    second = self.attempt(username="b" * 12000)
    self.finish(second, LoginAttemptOutcome.INVALID_CREDENTIALS)

    self.assertEqual(1, self.guard.username_state_size)

  def test_peer_state_is_hard_bounded_and_new_key_fails_closed(self):
    with patch.object(login_abuse, "LOGIN_MAX_TRACKED_PEERS", 3):
      for index in range(3):
        self.finish(self.attempt(peer=f"peer-{index}", username="shared"))
      refused = self.attempt(peer="overflow", username="shared")

    self.assertFalse(refused.allowed)
    self.assertEqual(3, self.guard.peer_state_size)

  def test_username_state_is_hard_bounded_and_new_key_fails_closed(self):
    with patch.object(login_abuse, "LOGIN_MAX_TRACKED_USERNAMES", 3):
      for index in range(3):
        self.finish(self.attempt(peer="shared", username=f"user-{index}"))
      refused = self.attempt(peer="shared", username="overflow")

    self.assertFalse(refused.allowed)
    self.assertEqual(3, self.guard.username_state_size)

  def test_lazy_expiry_reclaims_bounded_peer_and_username_state(self):
    self.finish(self.attempt(peer="old-peer", username="old-user"))
    self.clock.advance(LOGIN_USERNAME_STATE_TTL_SECONDS)

    self.finish(self.attempt(peer="new-peer", username="new-user"))

    self.assertEqual(1, self.guard.peer_state_size)
    self.assertEqual(1, self.guard.username_state_size)


if __name__ == "__main__":
  unittest.main()
