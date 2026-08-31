##<<Base>>
from datetime import datetime, timedelta
import unittest

##<<Third-part>>
from backend.src.auth.credentials import hash_password, hash_session_token
from backend.src.auth.errors import (
  AuthUnavailable,
  DuplicateUsername,
  InvalidCredentials,
  UnknownUsername,
)
from backend.src.auth.roles import ROLE_ADMIN, ROLE_USER, RoleValidationError
from backend.src.auth.service import AuthenticationService


##
## >>============================= a fake store =============================>>
##
##
## In memory, and deliberately not a mock.  Every assertion below is about what
## the service *did* - which row exists, what is in it, what a later call sees -
## rather than about which method it happened to call, so the fake behaves like
## a store instead of recording calls.
##

NOW = datetime(2026, 8, 24, 12, 0, 0)


class FakeRepository:
  def __init__(self, *, unavailable=False):
    self.users = {}
    self.sessions = {}
    self.unavailable = unavailable
    self._next_user_id = 1

  def _check(self):
    if self.unavailable:
      raise AuthUnavailable("database is not reachable")

  def find_user_by_username(self, username):
    self._check()
    for row in self.users.values():
      if row["username"] == username:
        return dict(row)
    return None

  def find_user_by_id(self, user_id):
    self._check()
    row = self.users.get(user_id)
    return dict(row) if row else None

  def insert_user(self, username, password_hash, role):
    self._check()
    if any(row["username"] == username for row in self.users.values()):
      raise DuplicateUsername(username)
    user_id = self._next_user_id
    self._next_user_id += 1
    self.users[user_id] = {
      "user_id": user_id,
      "username": username,
      "password_hash": password_hash,
      "is_active": True,
      "role": role,
    }
    return user_id

  def set_user_role(self, user_id, role):
    self._check()
    if user_id not in self.users:
      return False
    self.users[user_id]["role"] = role
    return True

  def insert_session(self, token_hash, user_id, expires_at):
    self._check()
    self.sessions[token_hash] = {
      "token_hash": token_hash,
      "user_id": user_id,
      "expires_at": expires_at,
    }

  def find_session(self, token_hash):
    self._check()
    row = self.sessions.get(token_hash)
    return dict(row) if row else None

  def delete_session(self, token_hash):
    self._check()
    return self.sessions.pop(token_hash, None) is not None

  def touch_session(self, token_hash, seen_at):
    self._check()


def service(repository=None, *, ttl_seconds=3600, now=NOW):
  return AuthenticationService(
    repository or FakeRepository(),
    session_ttl_seconds=ttl_seconds,
    clock=lambda: now,
  )


class TestCreatingAnAccount(unittest.TestCase):
  def test_the_safe_default_role_is_user(self):
    repository = FakeRepository()

    created = service(repository).create_user("alice", "correct horse battery")

    self.assertEqual(ROLE_USER, created.role)
    self.assertEqual(ROLE_USER, repository.users[1]["role"])

  def test_an_admin_must_be_created_explicitly(self):
    repository = FakeRepository()

    created = service(repository).create_user(
      "alice", "correct horse battery", role=ROLE_ADMIN
    )

    self.assertEqual(ROLE_ADMIN, created.role)
    self.assertEqual(ROLE_ADMIN, repository.users[1]["role"])

  def test_an_invalid_role_is_refused_before_a_row_is_written(self):
    repository = FakeRepository()

    with self.assertRaises(RoleValidationError):
      service(repository).create_user(
        "alice", "correct horse battery", role="superuser"
      )

    self.assertEqual({}, repository.users)

  def test_the_password_is_stored_only_as_a_hash(self):
    repository = FakeRepository()
    auth = service(repository)

    auth.create_user("alice", "correct horse battery")

    stored = repository.users[1]
    self.assertNotIn("correct horse battery", str(stored))
    self.assertNotIn("password", stored)
    self.assertTrue(stored["password_hash"].startswith("scrypt:"))

  def test_the_username_is_stored_canonically(self):
    repository = FakeRepository()
    auth = service(repository)

    auth.create_user("  Alice  ", "correct horse battery")

    self.assertEqual("alice", repository.users[1]["username"])

  def test_the_same_name_cannot_be_taken_twice(self):
    repository = FakeRepository()
    auth = service(repository)
    auth.create_user("alice", "correct horse battery")

    with self.assertRaises(DuplicateUsername):
      auth.create_user("ALICE", "a different password")

  def test_a_weak_password_is_refused_before_a_row_is_written(self):
    repository = FakeRepository()
    auth = service(repository)

    with self.assertRaises(ValueError):
      auth.create_user("alice", "short")

    self.assertEqual({}, repository.users)


class TestSigningIn(unittest.TestCase):
  def setUp(self):
    self.repository = FakeRepository()
    self.auth = service(self.repository)
    self.auth.create_user("alice", "correct horse battery")

  def test_the_right_password_identifies_the_account(self):
    user = self.auth.authenticate("alice", "correct horse battery")

    self.assertEqual(1, user.user_id)
    self.assertEqual("alice", user.username)
    self.assertEqual(ROLE_USER, user.role)

  def test_the_name_is_canonicalised_on_the_way_in(self):
    user = self.auth.authenticate("  ALICE ", "correct horse battery")

    self.assertEqual(1, user.user_id)

  def test_a_wrong_password_is_refused(self):
    with self.assertRaises(InvalidCredentials):
      self.auth.authenticate("alice", "wrong password entirely")

  def test_an_unknown_account_is_refused_the_same_way(self):
    ##
    ## The same exception type as a wrong password, so that no caller can
    ## accidentally tell them apart and turn login into an account-enumeration
    ## oracle.
    ##
    with self.assertRaises(InvalidCredentials):
      self.auth.authenticate("nobody", "correct horse battery")

  def test_an_unknown_account_still_pays_for_a_hash_check(self):
    ##
    ## Timing.  Returning early for an unknown name makes "no such user"
    ## measurably faster than "wrong password", which is the same disclosure
    ## the identical message was written to avoid.  A dummy verification keeps
    ## both paths doing the same expensive thing.
    ##
    seen = []
    original = self.auth._verify

    def counting(stored_hash, password):
      seen.append(stored_hash)
      return original(stored_hash, password)

    self.auth._verify = counting

    with self.assertRaises(InvalidCredentials):
      self.auth.authenticate("nobody", "correct horse battery")

    self.assertEqual(1, len(seen))
    self.assertTrue(seen[0].startswith("scrypt:"))

  def test_a_bounded_malformed_username_still_pays_for_one_dummy_hash_check(self):
    seen = []
    original = self.auth._verify

    def counting(stored_hash, password):
      seen.append(stored_hash)
      return original(stored_hash, password)

    self.auth._verify = counting

    with self.assertRaises(InvalidCredentials):
      self.auth.authenticate("mal formed", "correct horse battery")

    self.assertEqual(1, len(seen))
    self.assertTrue(seen[0].startswith("scrypt:"))

  def test_a_disabled_account_cannot_sign_in(self):
    self.repository.users[1]["is_active"] = False

    with self.assertRaises(InvalidCredentials):
      self.auth.authenticate("alice", "correct horse battery")

  def test_a_database_that_cannot_answer_is_not_a_wrong_password(self):
    ##
    ## "I could not check" and "that was wrong" are different facts, and only
    ## one of them should ever be shown to somebody typing their own password.
    ##
    auth = service(FakeRepository(unavailable=True))

    with self.assertRaises(AuthUnavailable):
      auth.authenticate("alice", "correct horse battery")


class TestSessions(unittest.TestCase):
  def setUp(self):
    self.repository = FakeRepository()
    self.auth = service(self.repository)
    self.auth.create_user("alice", "correct horse battery")
    self.user = self.auth.authenticate("alice", "correct horse battery")

  def test_creating_one_returns_a_token_the_database_does_not_hold(self):
    ##
    ## The core asymmetry: the browser gets the token, the table gets its hash.
    ## A dump of this table cannot be replayed as a cookie.
    ##
    issued = self.auth.create_session(self.user.user_id)

    self.assertNotIn(issued.token, self.repository.sessions)
    self.assertIn(hash_session_token(issued.token), self.repository.sessions)
    for row in self.repository.sessions.values():
      self.assertNotIn(issued.token, str(row))

  def test_the_session_expires_after_the_configured_lifetime(self):
    auth = service(self.repository, ttl_seconds=900)

    issued = auth.create_session(self.user.user_id)

    self.assertEqual(NOW + timedelta(seconds=900), issued.expires_at)

  def test_a_valid_token_resolves_to_its_user(self):
    issued = self.auth.create_session(self.user.user_id)

    resolved = self.auth.resolve_session(issued.token)

    self.assertIsNotNone(resolved)
    self.assertEqual(self.user.user_id, resolved.user_id)
    self.assertEqual("alice", resolved.username)
    self.assertEqual(ROLE_USER, resolved.role)

  def test_role_changes_are_visible_to_an_existing_session(self):
    issued = self.auth.create_session(self.user.user_id)

    promoted = self.auth.set_role("alice", ROLE_ADMIN)
    self.assertEqual(ROLE_ADMIN, promoted.role)
    self.assertEqual(ROLE_ADMIN, self.auth.resolve_session(issued.token).role)

    demoted = self.auth.set_role("alice", ROLE_USER)
    self.assertEqual(ROLE_USER, demoted.role)
    self.assertEqual(ROLE_USER, self.auth.resolve_session(issued.token).role)

  def test_a_disabled_admin_cannot_use_an_existing_session(self):
    issued = self.auth.create_session(self.user.user_id)
    self.auth.set_role("alice", ROLE_ADMIN)
    self.repository.users[1]["is_active"] = False

    self.assertIsNone(self.auth.resolve_session(issued.token))

  def test_an_unknown_token_resolves_to_nobody(self):
    self.assertIsNone(self.auth.resolve_session("not-a-real-token"))

  def test_an_empty_token_resolves_to_nobody(self):
    self.assertIsNone(self.auth.resolve_session(""))
    self.assertIsNone(self.auth.resolve_session(None))

  def test_an_expired_token_resolves_to_nobody(self):
    issued = self.auth.create_session(self.user.user_id)
    later = service(self.repository, now=NOW + timedelta(seconds=3601))

    self.assertIsNone(later.resolve_session(issued.token))

  def test_a_session_belonging_to_a_disabled_account_stops_working(self):
    ##
    ## Disabling an account has to take effect on the sessions it already has,
    ## or "disabled" means nothing until they happen to expire.
    ##
    issued = self.auth.create_session(self.user.user_id)
    self.repository.users[1]["is_active"] = False

    self.assertIsNone(self.auth.resolve_session(issued.token))

  def test_revoking_a_session_stops_it_immediately(self):
    issued = self.auth.create_session(self.user.user_id)

    self.assertTrue(self.auth.revoke_session(issued.token))
    self.assertIsNone(self.auth.resolve_session(issued.token))

  def test_revoking_twice_is_not_an_error(self):
    ##
    ## Signing out is idempotent.  A second click, a retried request, or a
    ## cookie for a session that has already gone must all end the same way.
    ##
    issued = self.auth.create_session(self.user.user_id)
    self.auth.revoke_session(issued.token)

    self.assertFalse(self.auth.revoke_session(issued.token))

  def test_revoking_something_that_was_never_a_session_is_not_an_error(self):
    self.assertFalse(self.auth.revoke_session("never-existed"))

  def test_resolving_when_the_database_is_down_says_so(self):
    ##
    ## Distinguished from "no session" for the same reason a failed login is
    ## distinguished from a wrong password: silently treating an outage as
    ## "anonymous" would log everybody out whenever the database hiccuped.
    ##
    auth = service(FakeRepository(unavailable=True))

    with self.assertRaises(AuthUnavailable):
      auth.resolve_session("anything")

  def test_every_session_gets_a_different_token(self):
    tokens = {self.auth.create_session(self.user.user_id).token for _ in range(50)}

    self.assertEqual(50, len(tokens))


class TestChangingRoles(unittest.TestCase):
  def setUp(self):
    self.repository = FakeRepository()
    self.auth = service(self.repository)
    self.auth.create_user("alice", "correct horse battery")

  def test_setting_the_same_role_is_an_idempotent_success(self):
    user = self.auth.set_role("alice", ROLE_USER)

    self.assertEqual(ROLE_USER, user.role)

  def test_an_unknown_user_is_a_clear_domain_failure(self):
    with self.assertRaises(UnknownUsername):
      self.auth.set_role("nobody", ROLE_ADMIN)

  def test_an_invalid_role_is_refused(self):
    with self.assertRaises(RoleValidationError):
      self.auth.set_role("alice", "root")


if __name__ == "__main__":
  unittest.main()
