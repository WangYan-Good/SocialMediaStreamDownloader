from datetime import datetime
from types import SimpleNamespace
import unittest

from backend.src.service.recording_resource import (
  RecordingNotPersistable,
  RecordingPersistenceUnavailable,
  RecordingResourceService,
)


def recorded_result(**overrides):
  values = {
    "recorded": True,
    "test_mode": False,
    "room_id": "room-x",
    "owner_user_id": "owner-x",
    "title": "Live title",
    "protocol": "hls",
    "output_path": "/media/live/re_0_room.ts",
    "started_at": datetime(2026, 8, 25, 9, 0, 0, 123000),
    "finished_at": datetime(2026, 8, 25, 10, 0, 0, 456000),
  }
  values.update(overrides)
  return SimpleNamespace(**values)


class FakeRepository:
  def __init__(self):
    self.records = []

  def create_recording(self, record):
    self.records.append(dict(record))
    return len(self.records)


class RecordingResourceServiceTest(unittest.TestCase):
  def build(self):
    repository = FakeRepository()
    service = RecordingResourceService(repository_provider=lambda: repository)
    return service, repository

  def test_owned_recording_maps_only_resource_facts_and_returns_identity(self):
    service, repository = self.build()

    recording_id = service.record(
      recorded_result(),
      app_user_id=41,
      platform="douyin",
      source="task_api",
    )

    self.assertEqual(1, recording_id)
    self.assertEqual(
      {
        "app_user_id": 41,
        "platform": "douyin",
        "room_id": "room-x",
        "owner_user_id": "owner-x",
        "title": "Live title",
        "protocol": "hls",
        "output_path": "/media/live/re_0_room.ts",
        "started_at": datetime(2026, 8, 25, 9, 0, 0, 123000),
        "finished_at": datetime(2026, 8, 25, 10, 0, 0, 456000),
        "source": "task_api",
      },
      repository.records[0],
    )

  def test_anonymous_recording_is_preserved_with_null_owner(self):
    service, repository = self.build()

    service.record(
      recorded_result(),
      app_user_id=None,
      platform="douyin",
      source="direct",
    )

    self.assertIsNone(repository.records[0]["app_user_id"])

  def test_each_execution_creates_a_new_resource_even_for_the_same_room(self):
    service, repository = self.build()

    first = service.record(
      recorded_result(output_path="/media/live/room.ts"),
      app_user_id=1,
      platform="douyin",
      source="task_api",
    )
    second = service.record(
      recorded_result(output_path="/media/live/re_0_room.ts"),
      app_user_id=2,
      platform="douyin",
      source="task_api",
    )

    self.assertEqual((1, 2), (first, second))
    self.assertEqual([1, 2], [row["app_user_id"] for row in repository.records])
    self.assertEqual(2, len(repository.records))

  def test_actual_output_path_is_preserved_verbatim(self):
    service, repository = self.build()
    actual_path = " /media/live/room with spaces.ts "

    service.record(
      recorded_result(output_path=actual_path),
      app_user_id=1,
      platform="douyin",
      source="task_api",
    )

    self.assertEqual(actual_path, repository.records[0]["output_path"])

  def test_only_a_real_recording_with_an_actual_path_is_persistable(self):
    service, repository = self.build()
    rejected = (
      recorded_result(recorded=False),
      recorded_result(test_mode=True),
      recorded_result(output_path=None),
      recorded_result(output_path="  "),
      recorded_result(output_path=123),
    )

    for result in rejected:
      with self.subTest(result=result):
        with self.assertRaises(RecordingNotPersistable):
          service.record(
            result,
            app_user_id=1,
            platform="douyin",
            source="task_api",
          )

    self.assertEqual([], repository.records)

  def test_a_stream_credential_cannot_be_copied_into_the_record(self):
    service, repository = self.build()
    result = recorded_result()
    result.stream_url = "https://stream.test/live?sign=SECRET&token=SECRET"
    result.headers = {"Cookie": "SECRET"}

    service.record(result, app_user_id=1, platform="douyin", source="task_api")

    rendered = repr(repository.records[0])
    self.assertNotIn("stream_url", rendered)
    self.assertNotIn("sign=", rendered)
    self.assertNotIn("Cookie", rendered)

  def test_construction_does_not_load_configuration_or_open_a_database(self):
    calls = []

    def load():
      calls.append("config")
      return {"database": {"enable": False}}

    def database_factory(**unused):
      calls.append("database")
      raise AssertionError("database must stay lazy")

    RecordingResourceService(
      config_loader=load,
      database_factory=database_factory,
    )

    self.assertEqual([], calls)

  def test_database_disabled_is_unavailable_only_when_persistence_is_attempted(self):
    calls = []

    def database_factory(**unused):
      calls.append("database")
      raise AssertionError("disabled configuration must not construct a database")

    service = RecordingResourceService(
      config_loader=lambda: {"database": {"enable": False}},
      database_factory=database_factory,
    )

    with self.assertRaises(RecordingPersistenceUnavailable):
      service.record(
        recorded_result(),
        app_user_id=None,
        platform="douyin",
        source="direct",
      )

    self.assertEqual([], calls)


if __name__ == "__main__":
  unittest.main()
