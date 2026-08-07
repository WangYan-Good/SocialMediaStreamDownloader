import unittest


class MigrationTestSafetyTest(unittest.TestCase):
  def load_validator(self):
    try:
      from backend.src.integration_test.test_orm_migrations import (
        validate_test_database_name,
      )
    except ModuleNotFoundError as exc:
      raise AssertionError("migration integration safety validator is missing") from exc
    return validate_test_database_name

  def test_accepts_only_generated_disposable_database_names(self):
    validate = self.load_validator()
    name = "smsd_migration_test_012345abcdef"
    self.assertEqual(name, validate(name))

  def test_rejects_unsafe_database_names(self):
    validate = self.load_validator()
    for name in (
      "",
      "smsd",
      "smsd_migration_test_012345abcde",
      "smsd_migration_test_012345abcdef0",
      "smsd_migration_test_*",
      "smsd_migration_test_012345abcdeG",
      "smsd_migration_test_012345abcdef/other",
      "`smsd_migration_test_012345abcdef`",
    ):
      with self.subTest(name=name), self.assertRaises(ValueError):
        validate(name)


if __name__ == "__main__":
  unittest.main()
