import unittest

from backend.src.service.owner_preference import (
  OwnerNotFound,
  OwnerPreferenceService,
  OwnerPreferenceValidationError,
)


class FakePreferenceRepository:
  def __init__(self, owners=("owner-1",)):
    self.owners = set(owners)
    self.upserts = []
    self.deletes = []

  def owner_exists(self, owner_user_id):
    return owner_user_id in self.owners

  def upsert_owner_preference(self, owner_user_id, score, platform="douyin"):
    self.upserts.append((owner_user_id, score, platform))

  def delete_owner_preference(self, owner_user_id, platform="douyin"):
    self.deletes.append((owner_user_id, platform))


class OwnerPreferenceValidationTest(unittest.TestCase):
  def setUp(self):
    self.repository = FakePreferenceRepository()
    self.service = OwnerPreferenceService(self.repository)

  def assert_invalid(self, payload):
    with self.assertRaises(OwnerPreferenceValidationError):
      self.service.update("owner-1", payload)

  def test_only_favorite_and_score_are_accepted(self):
    self.assert_invalid({"favorite": True, "score": 80, "platform": "other"})

  def test_favorite_must_be_a_real_boolean(self):
    for value in ("false", 0, 1, None):
      with self.subTest(value=value):
        self.assert_invalid({"favorite": value})

  def test_favorite_requires_an_integer_score_between_zero_and_one_hundred(self):
    for payload in (
      {"favorite": True},
      {"favorite": True, "score": True},
      {"favorite": True, "score": 1.5},
      {"favorite": True, "score": -1},
      {"favorite": True, "score": 101},
    ):
      with self.subTest(payload=payload):
        self.assert_invalid(payload)

  def test_removal_rejects_a_score_instead_of_silently_ignoring_it(self):
    self.assert_invalid({"favorite": False, "score": 50})


class OwnerPreferenceMutationTest(unittest.TestCase):
  def test_score_zero_remains_a_favorite_and_uses_the_fixed_platform(self):
    repository = FakePreferenceRepository()

    result = OwnerPreferenceService(repository).update(
      "owner-1", {"favorite": True, "score": 0}
    )

    self.assertTrue(result.favorite)
    self.assertEqual(0, result.score)
    self.assertEqual([("owner-1", 0, "douyin")], repository.upserts)
    self.assertEqual([], repository.deletes)

  def test_removal_deletes_only_the_douyin_preference(self):
    repository = FakePreferenceRepository()

    result = OwnerPreferenceService(repository).update(
      "owner-1", {"favorite": False}
    )

    self.assertFalse(result.favorite)
    self.assertIsNone(result.score)
    self.assertEqual([("owner-1", "douyin")], repository.deletes)
    self.assertEqual([], repository.upserts)

  def test_an_unknown_owner_cannot_create_an_orphan_preference(self):
    repository = FakePreferenceRepository(owners=())

    with self.assertRaises(OwnerNotFound):
      OwnerPreferenceService(repository).update(
        "missing", {"favorite": True, "score": 70}
      )

    self.assertEqual([], repository.upserts)
    self.assertEqual([], repository.deletes)

  def test_missing_owner_identity_is_rejected_before_repository_access(self):
    repository = FakePreferenceRepository()

    with self.assertRaises(OwnerPreferenceValidationError):
      OwnerPreferenceService(repository).update(" ", {"favorite": False})

    self.assertEqual([], repository.upserts)
    self.assertEqual([], repository.deletes)


if __name__ == "__main__":
  unittest.main()
