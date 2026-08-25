import unittest

from backend.src.auth.roles import (
  APP_USER_ROLES,
  ROLE_ADMIN,
  ROLE_USER,
  RoleValidationError,
  role_satisfies,
  validate_role,
)


class TestRoleVocabulary(unittest.TestCase):
  def test_only_user_and_admin_are_valid(self):
    self.assertEqual(("user", "admin"), APP_USER_ROLES)
    self.assertEqual(ROLE_USER, validate_role("user"))
    self.assertEqual(ROLE_ADMIN, validate_role("admin"))

  def test_unknown_and_malformed_roles_are_rejected(self):
    for role in ("root", "administrator", "superuser", "", " user ", None, 1):
      with self.subTest(role=role):
        with self.assertRaises(RoleValidationError):
          validate_role(role)

  def test_admin_is_a_superset_of_user_capability(self):
    self.assertTrue(role_satisfies(ROLE_USER, ROLE_USER))
    self.assertTrue(role_satisfies(ROLE_ADMIN, ROLE_USER))
    self.assertTrue(role_satisfies(ROLE_ADMIN, ROLE_ADMIN))
    self.assertFalse(role_satisfies(ROLE_USER, ROLE_ADMIN))


if __name__ == "__main__":
  unittest.main()
