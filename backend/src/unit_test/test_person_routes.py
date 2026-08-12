import json
import unittest

from flask import Flask

from backend.src.database.table.person_identity import UnknownRole
from backend.src.web.person_routes import PersonRuntime, build_person_blueprint


##
## 真实长度的 sec_uid：分类器要求它符合平台格式，短的会被正确拒绝
##
SEC_UID = "MS4wLjABAAAAz5gVpriut-_sF81x172gu_GrJoeaqaXlT8S0U2wXI93qj5IodEakZpVQGpyl_dG3"


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
    self.aligned = []

  def _guard(self):
    if self.failure is not None:
      raise self.failure

  def list_persons(self):
    self._guard()
    return self.persons

  def search_accounts(self, keyword, limit=30):
    self._guard()
    return self.accounts

  def create_person(self, display_name, note=None):
    self._guard()
    self.created.append((display_name, note))
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

  def align_accounts_to_main(self, person_id):
    self._guard()
    self.aligned.append(person_id)

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
      {"display_name": "张三"},
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["data"]["person_id"], 11)
    ##
    ## 不接收目录：它是主账号的，随第一个被标为主号的账号而来
    ##
    self.assertEqual(table.created, [("张三", None)])

  def test_a_missing_name_is_rejected(self):
    client, table = self.build_client()

    response = self.post(client, "/api/person", {"note": "x"})

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


class AttachByLinkTest(RouteTestCase):
  """从没直播过的主播，也要能在下载之前标记。

  直播分享短链会在下载判断之前就写入 share_url，所以那类主播本来就搜得到。
  但只有主页链接、从没开过播的主播不会有行——而目录在下载一开始就定死了，
  于是首批文件必然落在昵称目录。粘链接挂载补的正是这一段：解析出账号身份
  直接挂载，不要求它已经在库里（person_account 本就没有指向 share_url 的
  外键）。
  """

  class Resolved:
    def __init__(self, uid="acc-9", nickname="主播甲", sec="MS4wLjABAAAA"):
      self.uid = uid
      self.nickname = nickname
      self.sec_user_id = sec

  class SeedingTable(StubTable):
    def __init__(self, **kwargs):
      super().__init__(**kwargs)
      self.identities = []

    def upsert_account_identity(self, owner_user_id, sec_user_id=None,
                                nickname=None):
      self._guard()
      self.identities.append((owner_user_id, sec_user_id, nickname))

  IDENTITY = {
    "owner_user_id": "acc-9",
    "sec_user_id": "MS4wLjABAAAA",
    "nickname": "主播甲",
  }

  def build_link_client(self, resolver=None, detail=None, table=None,
                        identity=None):
    table = table if table is not None else self.SeedingTable()
    runtime = PersonRuntime(table_factory=lambda: table)
    if resolver is not None:
      runtime.resolve_owner_identity = lambda url: (
        None if resolver(url) is None else dict(self.IDENTITY)
      )
    elif detail is not None:
      runtime.resolve_owner_identity = lambda url: {
        "owner_user_id": (detail(None).uid or ""),
        "sec_user_id": "MS4wLjABAAAA",
        "nickname": "主播甲",
      }
    else:
      runtime.resolve_owner_identity = lambda url: (
        dict(identity) if identity is not None else dict(self.IDENTITY)
      )
    app = Flask(__name__)
    app.register_blueprint(build_person_blueprint(runtime))
    return app.test_client(), table

  def test_a_never_downloaded_owner_can_be_marked(self):
    client, table = self.build_link_client()

    response = self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    self.assertEqual(response.status_code, 200)
    self.assertEqual(table.attached, [("douyin", "acc-9", 3, "main")])
    self.assertEqual(self.body(response)["data"]["nickname"], "主播甲")

  def test_the_identity_is_recorded_so_the_page_can_name_the_account(self):
    client, table = self.build_link_client()

    self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    self.assertEqual(table.identities, [("acc-9", "MS4wLjABAAAA", "主播甲")])

  def test_the_identity_is_recorded_before_the_attachment(self):
    """反过来会先造出一条指向未知账号的归属记录。"""
    order = []
    table = self.SeedingTable()
    table.upsert_account_identity = lambda *a, **k: order.append("identity")
    table.attach_account = lambda *a, **k: order.append("attach")
    client, _ = self.build_link_client(table=table)

    self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    self.assertEqual(order, ["identity", "attach"])

  def test_whole_share_text_is_accepted(self):
    """抖音复制给你的是一整段文字，不是纯链接。"""
    client, table = self.build_link_client()

    response = self.post(client, "/api/person/account/by-link", {
      "url": "0.58 复制打开抖音 https://v.douyin.com/abc/ 08/01",
      "person_id": 3,
      "role": "alt",
    })

    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(table.attached), 1)

  def test_a_link_that_resolves_to_nothing_is_a_field_error(self):
    client, table = self.build_link_client(resolver=lambda url: None)

    response = self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    self.assertEqual(response.status_code, 400)
    self.assertEqual(table.attached, [])

  def test_an_owner_without_a_uid_cannot_be_attached(self):
    """person_account 按 owner_user_id 键，空 id 会造出谁也匹配不上的行。"""
    client, table = self.build_link_client(
      detail=lambda sec: AttachByLinkTest.Resolved(uid="")
    )

    response = self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    self.assertEqual(response.status_code, 502)
    self.assertEqual(table.attached, [])

  def test_an_unknown_role_is_still_a_field_error(self):
    client, table = self.build_link_client()

    response = self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "boss",
    })

    self.assertEqual(response.status_code, 400)
    self.assertEqual(table.attached, [])


class AlignAfterAttachTest(RouteTestCase):
  """挂载之后必须把子账号那一列对齐到主账号。

  落盘用的是主账号的目录；子账号自己那一行若还写着别的名字，库里就有两种说法，
  读到哪一种都可能是错的。
  """

  def test_attaching_by_search_aligns(self):
    client, table = self.build_client()

    self.post(client, "/api/person/account", {
      "owner_user_id": "acc-1", "person_id": 3, "role": "alt",
    })

    self.assertEqual(table.aligned, [3])

  def test_attaching_by_link_aligns(self):
    inner = AttachByLinkTest.SeedingTable()
    inner.aligned = []
    inner.align_accounts_to_main = lambda pid: inner.aligned.append(pid)
    runtime = PersonRuntime(table_factory=lambda: inner)
    runtime.resolve_owner_identity = lambda url: dict(AttachByLinkTest.IDENTITY)
    app = Flask(__name__)
    app.register_blueprint(build_person_blueprint(runtime))

    self.post(app.test_client(), "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 5, "role": "main",
    })

    self.assertEqual(inner.aligned, [5])


class OwnerRuntimeWiringTest(unittest.TestCase):
  """真实装配必须被测到，哪怕它只有一行。

  之前每个链接挂载测试都把 runtime.resolve_owner 整个替换掉，于是这行装配
  从未被执行过——而它是错的：OwnerRuntime 的第一个参数是 config_loader（可
  调用），传进去一个 config 字典（生产环境下是 None）会让 settings() 去调用
  None()，挂载在生产环境 100% 失败。
  """

  SETTINGS = {
    "platform": {"douyin": {"headers": {}, "owner": {"max_timeout": 5}}},
    "database": {"enable": False},
  }

  def test_the_owner_runtime_reads_the_supplied_settings(self):
    runtime = PersonRuntime(config=self.SETTINGS)

    self.assertEqual(self.SETTINGS, runtime.owner_runtime().settings())

  def test_the_owner_runtime_is_built_once(self):
    runtime = PersonRuntime(config=self.SETTINGS)

    self.assertIs(runtime.owner_runtime(), runtime.owner_runtime())

  def test_without_a_config_it_falls_back_to_the_process_wide_loader(self):
    """生产路径：不传 config 时必须仍然可用，而不是把 None 当成 loader。"""
    runtime = PersonRuntime()
    owner = runtime.owner_runtime()

    self.assertTrue(callable(owner._config_loader))


class AnyShareLinkIdentifiesTheOwnerTest(unittest.TestCase):
  """主页、作品、直播三种分享链接都指向同一件事：一个主播。

  三者都该能用来标记，否则「我手上有这个人的链接」和「我能标记这个人」之间
  就多出一道没有道理的门槛。

  身份一律以 owner_user_id 为准。短链本身绝不能当身份：同一个作品的分享短链
  每次可能都不一样，拿它匹配会把同一个东西当成两个。
  """

  class Detail:
    owner_user_id = "acc-post"
    sec_user_id = "sec-post"
    nickname = "作品作者"

  class Resolution:
    ok = True
    detail = None

  class Probe:
    owner_user_id = "acc-live"
    sec_user_id = "sec-live"
    nickname = "直播主播"

  class Owner:
    uid = "acc-profile"
    sec_user_id = "sec-profile"
    nickname = "主页主播"

  def runtime_resolving_to(self, resolved_url):
    runtime = PersonRuntime(config={"database": {"enable": False}})
    runtime.owner_runtime = lambda: type(
      "Stub", (), {"follow_share_link": staticmethod(lambda url: resolved_url)}
    )()
    return runtime

  def test_a_profile_link_identifies_the_owner(self):
    runtime = self.runtime_resolving_to(
      "https://www.iesdouyin.com/share/user/" + SEC_UID
    )
    runtime.owner_detail = lambda sec: self.Owner()

    identity = runtime.resolve_owner_identity("https://v.douyin.com/a/")

    self.assertEqual(identity["owner_user_id"], "acc-profile")

  def test_a_post_link_identifies_its_author(self):
    runtime = self.runtime_resolving_to(
      "https://www.douyin.com/note/7672710351788455034"
    )
    resolution = self.Resolution()
    resolution.detail = self.Detail()
    runtime._identity_from_post = lambda url, aweme_id: {
      "owner_user_id": resolution.detail.owner_user_id,
      "sec_user_id": resolution.detail.sec_user_id,
      "nickname": resolution.detail.nickname,
    }

    identity = runtime.resolve_owner_identity("https://v.douyin.com/b/")

    self.assertEqual(identity["owner_user_id"], "acc-post")

  def test_a_live_link_identifies_the_room_owner(self):
    runtime = self.runtime_resolving_to("https://live.douyin.com/123456")
    runtime._identity_from_live = lambda url: {
      "owner_user_id": self.Probe.owner_user_id,
      "sec_user_id": self.Probe.sec_user_id,
      "nickname": self.Probe.nickname,
    }

    identity = runtime.resolve_owner_identity("https://v.douyin.com/c/")

    self.assertEqual(identity["owner_user_id"], "acc-live")

  def test_a_link_leading_nowhere_identifies_nobody(self):
    runtime = self.runtime_resolving_to("https://example.test/nothing")

    self.assertIsNone(runtime.resolve_owner_identity("https://v.douyin.com/d/"))

  def test_an_unfollowable_link_identifies_nobody(self):
    runtime = self.runtime_resolving_to(None)

    self.assertIsNone(runtime.resolve_owner_identity("   "))

if __name__ == "__main__":
  unittest.main()
