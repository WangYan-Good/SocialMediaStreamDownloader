##<<Base>>
import unittest

##<<Third-part>>
from backend.src.auth.credentials import (
  MAX_PASSWORD_LENGTH,
  MIN_PASSWORD_LENGTH,
  PasswordTooLong,
  PasswordTooShort,
  UsernameInvalid,
  canonical_username,
  hash_password,
  hash_session_token,
  new_session_token,
  validate_password,
  verify_password,
)


class TestPasswordStorage(unittest.TestCase):
  def test_a_stored_password_is_never_the_password(self):
    ##
    ## The property everything else here depends on.  If the plaintext can be
    ## found anywhere in what gets written, the hash is decorative.
    ##
    secret = "correct horse battery staple"

    stored = hash_password(secret)

    self.assertNotIn(secret, stored)
    self.assertNotEqual(secret, stored)

  def test_it_uses_a_deliberately_slow_modern_method(self):
    ##
    ## Named rather than left to the library default, so an upgrade that changes
    ## that default is a decision someone makes here rather than a surprise.
    ##
    ## Not MD5, SHA1 or a bare SHA-256: those are fast, which is exactly the
    ## wrong property for something an attacker gets to guess at offline.
    ##
    stored = hash_password("correct horse battery staple")

    self.assertTrue(stored.startswith("scrypt:"))

  def test_two_identical_passwords_do_not_produce_the_same_hash(self):
    ##
    ## Per-password salt.  Without it, equal hashes advertise equal passwords,
    ## and one cracked row unlocks every account that shared it.
    ##
    first = hash_password("same password")
    second = hash_password("same password")

    self.assertNotEqual(first, second)

  def test_the_right_password_verifies(self):
    stored = hash_password("correct horse battery staple")

    self.assertTrue(verify_password(stored, "correct horse battery staple"))

  def test_a_wrong_password_does_not(self):
    stored = hash_password("correct horse battery staple")

    self.assertFalse(verify_password(stored, "Correct horse battery staple"))
    self.assertFalse(verify_password(stored, ""))
    self.assertFalse(verify_password(stored, "correct horse battery stapl"))

  def test_a_malformed_stored_hash_is_a_refusal_rather_than_a_crash(self):
    ##
    ## A row edited by hand, or written by an older method that has since been
    ## removed.  It must not authenticate, and it must not take the request
    ## down either - a 500 here would be an availability bug triggered by one
    ## bad row.
    ##
    for damaged in ("", "not-a-hash", "scrypt:", "$2b$12$truncated"):
      self.assertFalse(verify_password(damaged, "anything"))


class TestPasswordPolicy(unittest.TestCase):
  def test_it_asks_for_length_rather_than_character_classes(self):
    ##
    ## No "must contain an uppercase and a symbol".  Those rules push people
    ## towards P@ssw0rd1 and are worth less than a few more characters.
    ##
    validate_password("a" * MIN_PASSWORD_LENGTH)

  def test_a_short_password_is_refused(self):
    with self.assertRaises(PasswordTooShort):
      validate_password("a" * (MIN_PASSWORD_LENGTH - 1))

  def test_an_empty_password_is_refused(self):
    with self.assertRaises(PasswordTooShort):
      validate_password("")

  def test_an_enormous_password_is_refused_before_it_is_hashed(self):
    ##
    ## scrypt's cost is a function of its input.  Without a ceiling, a
    ## multi-megabyte "password" is a way to make the server do unbounded work
    ## on an unauthenticated endpoint - which is a denial of service with extra
    ## steps.
    ##
    with self.assertRaises(PasswordTooLong):
      validate_password("a" * (MAX_PASSWORD_LENGTH + 1))

  def test_the_ceiling_is_generous_enough_for_a_real_passphrase(self):
    self.assertGreaterEqual(MAX_PASSWORD_LENGTH, 128)


class TestUsernameCanonicalisation(unittest.TestCase):
  def test_surrounding_whitespace_is_not_part_of_a_name(self):
    self.assertEqual("alice", canonical_username("  alice  "))

  def test_case_does_not_make_a_second_account(self):
    ##
    ## Folded here rather than left to the database collation, so the stored
    ## value is already the canonical one and the UNIQUE means what it looks
    ## like it means on any collation.
    ##
    self.assertEqual("alice", canonical_username("Alice"))
    self.assertEqual("alice", canonical_username("ALICE"))

  def test_an_empty_name_is_refused(self):
    for empty in ("", "   ", "\t\n"):
      with self.assertRaises(UsernameInvalid):
        canonical_username(empty)

  def test_an_over_long_name_is_refused(self):
    with self.assertRaises(UsernameInvalid):
      canonical_username("a" * 191)

  def test_inner_whitespace_is_refused_rather_than_silently_removed(self):
    ##
    ## Rewriting "al ice" to "alice" would let somebody sign in as a name they
    ## did not type, and would make two visibly different names one account.
    ##
    with self.assertRaises(UsernameInvalid):
      canonical_username("al ice")


class TestSessionTokens(unittest.TestCase):
  def test_a_token_is_long_and_unpredictable(self):
    ##
    ## From secrets, not random: this is the entire credential a browser
    ## presents, so a predictable one is a login for everybody.
    ##
    token = new_session_token()

    self.assertGreaterEqual(len(token), 32)

  def test_two_tokens_are_never_the_same(self):
    tokens = {new_session_token() for _ in range(200)}

    self.assertEqual(200, len(tokens))

  def test_a_token_is_safe_to_put_in_a_cookie(self):
    ##
    ## No quoting, no escaping, nothing a Set-Cookie header would have to think
    ## about - url-safe base64 is already cookie-safe.
    ##
    token = new_session_token()

    for awkward in (";", ",", " ", '"', "\\", "\n"):
      self.assertNotIn(awkward, token)

  def test_the_hash_is_what_the_database_will_hold(self):
    token = new_session_token()

    digest = hash_session_token(token)

    self.assertEqual(64, len(digest))
    self.assertNotIn(token, digest)

  def test_the_same_token_always_hashes_the_same_way(self):
    ##
    ## Unsalted on purpose, unlike a password.  The lookup is by hash, so it
    ## has to be deterministic - and a token already carries far more entropy
    ## than any password, so there is nothing for a salt to protect against.
    ##
    token = new_session_token()

    self.assertEqual(hash_session_token(token), hash_session_token(token))

  def test_different_tokens_hash_differently(self):
    self.assertNotEqual(
      hash_session_token(new_session_token()),
      hash_session_token(new_session_token()),
    )


if __name__ == "__main__":
  unittest.main()
