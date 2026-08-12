import json
import unittest

from flask import Flask

from backend.src.database.table.person_identity import UnknownRole
from backend.src.web.person_routes import PersonRuntime, build_person_blueprint


class StubTable:
  def __init__(self, persons=(), accounts=(), failure=None):
    self.persons = list(persons)
    self.accounts = list(accounts)
    self.failure = failure
    self.created = []
    self.updated = []
    self.deleted = []
    self.attached = []
    self.detached = []
    self.collaborations = []
    self.removed_collaborations = []

  def _guard(self):
    if self.failure is not None:
      raise self.failure

  def list_persons(self):
    self._guard()
    return self.persons

  def search_accounts(self, keyword, limit=30):
    self._guard()
    return self.accounts

  def create_person(self, display_name, directory_name=None, note=None):
    self._guard()
    self.created.append((display_name, directory_name, note))
    return 11

  def update_person(self, person_id, **fields):
    self._guard()
    self.updated.append((person_id, fields))

  def delete_person(self, person_id):
    self._guard()
    self.deleted.append(person_id)

  def attach_account(self, platform, owner_user_id, person_id, role):
    self._guard()
    if role not in ("main", "alt", "matrix"):
      raise UnknownRole("bad role")
    self.attached.append((platform, owner_user_id, person_id, role))

  def detach_account(self, platform, owner_user_id):
    self._guard()
    self.detached.append((platform, owner_user_id))

  def add_collaboration(self, photographer_id, subject_id, note=None):
    self._guard()
    if photographer_id == subject_id:
      raise ValueError("self")
    self.collaborations.append((photographer_id, subject_id, note))

  def remove_collaboration(self, photographer_id, subject_id):
    self._guard()
    self.removed_collaborations.append((photographer_id, subject_id))


class RouteTestCase(unittest.TestCase):
  def build_client(self, table=None):
    table = table if table is not None else StubTable()
    app = Flask(__name__)
    app.register_blueprint(
      build_person_blueprint(PersonRuntime(table_factory=lambda: table))
    )
    return app.test_client(), table

  def post(self, client, path, payload):
    return client.post(
      path,
      data=json.dumps(payload),
      content_type="application/json",
    )

  def body(self, response):
    return json.loads(response.data.decode("utf-8"))


class PersonListingRouteTest(RouteTestCase):
  def test_the_listing_is_returned(self):
    client, _ = self.build_client(
      StubTable(persons=[{"person_id": 1, "display_name": "张三"}])
    )

    response = client.get("/api/person")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["data"]["persons"][0]["display_name"], "张三")

  def test_a_database_failure_is_reported_rather_than_crashing(self):
    client, _ = self.build_client(StubTable(failure=RuntimeError("gone")))

    response = client.get("/api/person")

    self.assertEqual(response.status_code, 502)


class CreatePersonRouteTest(RouteTestCase):
  def test_a_person_is_created(self):
    client, table = self.build_client()

    response = self.post(
      client,
      "/api/person",
      {"display_name": "张三", "directory_name": "张三_合并"},
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["data"]["person_id"], 11)
    self.assertEqual(table.created, [("张三", "张三_合并", None)])

  def test_a_missing_name_is_rejected(self):
    client, table = self.build_client()

    response = self.post(client, "/api/person", {"directory_name": "x"})

    self.assertEqual(response.status_code, 400)
    self.assertEqual(table.created, [])


class AttachAccountRouteTest(RouteTestCase):
  def test_an_account_is_attached(self):
    client, table = self.build_client()

    response = self.post(
      client,
      "/api/person/account",
      {"owner_user_id": "acc-1", "person_id": 3, "role": "alt"},
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(table.attached, [("douyin", "acc-1", 3, "alt")])

  def test_an_unknown_role_is_a_field_error_not_a_server_error(self):
    """用户是从一个很短的列表里选的，选错该由字段提示，不是 500。"""
    client, _ = self.build_client()

    response = self.post(
      client,
      "/api/person/account",
      {"owner_user_id": "acc-1", "person_id": 3, "role": "boss"},
    )

    self.assertEqual(response.status_code, 400)

  def test_detaching_an_account(self):
    client, table = self.build_client()

    response = client.delete("/api/person/account?owner_user_id=acc-1")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(table.detached, [("douyin", "acc-1")])


class AccountSearchRouteTest(RouteTestCase):
  def test_accounts_are_searched(self):
    client, _ = self.build_client(
      StubTable(accounts=[{"owner_user_id": "acc-1", "nickname": "昵称"}])
    )

    response = client.get("/api/person/accounts?keyword=昵称")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(self.body(response)["data"]["accounts"]), 1)

  def test_an_empty_keyword_is_rejected(self):
    client, _ = self.build_client()

    response = client.get("/api/person/accounts?keyword=")

    self.assertEqual(response.status_code, 400)


class CollaborationRouteTest(RouteTestCase):
  def test_a_collaboration_is_recorded(self):
    client, table = self.build_client()

    response = self.post(
      client,
      "/api/person/collaboration",
      {"photographer_id": 2, "subject_id": 9},
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(table.collaborations, [(2, 9, None)])

  def test_photographing_oneself_is_a_field_error(self):
    client, _ = self.build_client()

    response = self.post(
      client,
      "/api/person/collaboration",
      {"photographer_id": 4, "subject_id": 4},
    )

    self.assertEqual(response.status_code, 400)


class DeletePersonRouteTest(RouteTestCase):
  def test_a_person_is_deleted(self):
    client, table = self.build_client()

    response = client.delete("/api/person/3")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(table.deleted, [3])



class PersonDetailRouteTest(RouteTestCase):
  class DetailTable(StubTable):
    def list_person_accounts(self, person_id):
      self._guard()
      return [{"owner_user_id": "acc-1", "nickname": "昵称", "role": "main"}]

    def person_summary(self, person_id):
      self._guard()
      return {"aweme_count": 12, "live_count": 47}

    def list_subjects_of(self, person_id):
      self._guard()
      return [{"person_id": 9, "display_name": "主播甲", "note": None}]

    def list_photographers_of(self, person_id):
      self._guard()
      return []

    def list_works_by_photographer(self, person_id, limit=200):
      self._guard()
      return [{
        "aweme_id": "7",
        "desc": "描述",
        "save_dir": "/mnt/video/x",
        "downloaded_at": None,
        "owner_display_name": "主播甲",
      }]

  def test_the_detail_carries_accounts_counts_and_both_relation_sides(self):
    """两个方向都返回：一个人可能既拍别人又被别人拍。"""
    client, _ = self.build_client(self.DetailTable())

    response = client.get("/api/person/3/detail")
    data = self.body(response)["data"]

    self.assertEqual(response.status_code, 200)
    self.assertEqual(data["summary"]["aweme_count"], 12)
    self.assertEqual(data["accounts"][0]["role"], "main")
    self.assertEqual(data["subjects"][0]["display_name"], "主播甲")
    self.assertIn("photographers", data)

  def test_works_by_a_photographer_are_returned(self):
    client, _ = self.build_client(self.DetailTable())

    response = client.get("/api/person/2/works")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["data"]["works"][0]["aweme_id"], "7")

  def test_a_failure_is_reported_rather_than_crashing(self):
    client, _ = self.build_client(self.DetailTable(failure=RuntimeError("x")))

    self.assertEqual(client.get("/api/person/3/detail").status_code, 502)

if __name__ == "__main__":
  unittest.main()
