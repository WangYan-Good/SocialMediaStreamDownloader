import json
import unittest

from flask import Flask
from backend.src.unit_test.auth_context import install_test_auth

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
    self.assignments = []
    self.assignment_failure = None
    self.unknown_accounts = ()

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

  ##
  ## The guarded entry points.  ``assignment_failure`` lets a test make the
  ## transaction refuse exactly as the real one would, so the route's job -
  ## turning that refusal into a status - is what gets exercised.
  ##
  def account_exists(self, owner_user_id):
    self._guard()
    return owner_user_id not in self.unknown_accounts

  def assign_account(self, **kwargs):
    self._guard()
    if kwargs["role"] not in ("main", "alt", "matrix"):
      raise UnknownRole("bad role")
    self.assignments.append(kwargs)
    if self.assignment_failure is not None:
      raise self.assignment_failure
    return {
      "person_id": kwargs.get("person_id") or 11,
      "created_person": kwargs.get("person_id") is None,
      "owner_user_id": kwargs["owner_user_id"],
      "role": kwargs["role"],
      "display_name": "现有的人",
    }

  def detach_account_guarded(self, platform, owner_user_id):
    self._guard()
    if self.assignment_failure is not None:
      raise self.assignment_failure
    self.detached.append((platform, owner_user_id))
    return {"owner_user_id": owner_user_id, "person_id": 12, "role": "alt"}

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
    install_test_auth(app)
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
    ##
    ## 走的是那个带 main 检查与对齐的事务，不再是裸 upsert
    ##
    self.assertEqual(table.attached, [])
    self.assertEqual(len(table.assignments), 1)
    self.assertEqual(table.assignments[0]["owner_user_id"], "acc-1")
    self.assertEqual(table.assignments[0]["person_id"], 3)
    self.assertEqual(table.assignments[0]["role"], "alt")

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
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))
    return app.test_client(), table

  def test_a_never_downloaded_owner_can_be_marked(self):
    client, table = self.build_link_client()

    response = self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(table.assignments), 1)
    self.assertEqual(table.assignments[0]["owner_user_id"], "acc-9")
    self.assertEqual(table.assignments[0]["person_id"], 3)
    self.assertEqual(table.assignments[0]["role"], "main")
    self.assertEqual(self.body(response)["data"]["nickname"], "主播甲")

  def test_the_identity_is_recorded_so_the_page_can_name_the_account(self):
    """否则页面上只有一个裸 id，直到第一次下载才填上——而"从没下载过的主播也能
    标记"正是这条路由存在的理由。"""
    client, table = self.build_link_client()

    self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    assignment = table.assignments[0]
    self.assertEqual(assignment["sec_user_id"], "MS4wLjABAAAA")
    self.assertEqual(assignment["nickname"], "主播甲")

  def test_the_identity_and_the_attachment_are_one_transaction(self):
    """以前是两次提交：先写身份，再挂载。中间失败就留下一条"这个账号存在、但
    不属于任何人"的记录，而且没人会回头清理。

    现在两件事在同一个事务里，所以"谁先谁后"不再是可以问的问题——要么都发生，
    要么都不发生。
    """
    client, table = self.build_link_client()

    self.post(client, "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    })

    self.assertEqual(table.identities, [])
    self.assertEqual(len(table.assignments), 1)
    self.assertEqual(table.assignments[0]["owner_user_id"], "acc-9")
    self.assertEqual(table.assignments[0]["nickname"], "主播甲")

  def test_whole_share_text_is_accepted(self):
    """抖音复制给你的是一整段文字，不是纯链接。"""
    client, table = self.build_link_client()

    response = self.post(client, "/api/person/account/by-link", {
      "url": "0.58 复制打开抖音 https://v.douyin.com/abc/ 08/01",
      "person_id": 3,
      "role": "alt",
    })

    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(table.assignments), 1)

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

  对齐现在发生在挂载的**同一个事务里**，不再是挂载之后另起一次提交。因此这里
  验证的是"这条路由走的是那个带对齐的事务"，而不是"路由自己又调了一次对齐"——
  后者中间有一个窗口：账号已经挂上，目录还指着别处。
  """

  def test_attaching_by_search_goes_through_the_aligning_transaction(self):
    client, table = self.build_client()

    self.post(client, "/api/person/account", {
      "owner_user_id": "acc-1", "person_id": 3, "role": "alt",
    })

    self.assertEqual(len(table.assignments), 1)
    self.assertEqual(table.assignments[0]["person_id"], 3)
    ##
    ## 没有第二次提交：对齐是那个事务的最后一条语句
    ##
    self.assertEqual(table.aligned, [])

  def test_attaching_by_link_goes_through_the_aligning_transaction(self):
    inner = AttachByLinkTest.SeedingTable()
    runtime = PersonRuntime(table_factory=lambda: inner)
    runtime.resolve_owner_identity = lambda url: dict(AttachByLinkTest.IDENTITY)
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))

    self.post(app.test_client(), "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 5, "role": "main",
    })

    self.assertEqual(len(inner.assignments), 1)
    self.assertEqual(inner.assignments[0]["person_id"], 5)
    self.assertEqual(inner.aligned, [])


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

    def __init__(self):
      pass

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
    ##
    ## The platform call is what gets stood in for, not the step that reads an
    ## identity out of its answer: that step is DouyinOwnerIdentityReader's, and
    ## the assignment endpoint runs the very same one.
    ##
    runtime = self.runtime_resolving_to(
      "https://www.douyin.com/note/7672710351788455034"
    )
    resolution = self.Resolution()
    resolution.detail = self.Detail()
    runtime._post_resolution = lambda url, aweme_id: resolution

    identity = runtime.resolve_owner_identity("https://v.douyin.com/b/")

    self.assertEqual(identity["owner_user_id"], "acc-post")
    self.assertEqual(identity["nickname"], "作品作者")

  def test_a_live_link_identifies_the_room_owner(self):
    runtime = self.runtime_resolving_to("https://live.douyin.com/123456")
    runtime._live_probe = lambda url: self.Probe()

    identity = runtime.resolve_owner_identity("https://v.douyin.com/c/")

    self.assertEqual(identity["owner_user_id"], "acc-live")
    self.assertEqual(identity["nickname"], "直播主播")

  def test_a_link_leading_nowhere_identifies_nobody(self):
    runtime = self.runtime_resolving_to("https://example.test/nothing")

    self.assertIsNone(runtime.resolve_owner_identity("https://v.douyin.com/d/"))

  def test_an_unfollowable_link_identifies_nobody(self):
    runtime = self.runtime_resolving_to(None)

    self.assertIsNone(runtime.resolve_owner_identity("   "))


##
## >>============================= link-first assignment =============================>>
##
class AssignmentRouteTestCase(RouteTestCase):
  """Shared wiring for the two classes below, and no tests of its own.

  Split out rather than subclassed from a test class: inheriting one re-runs
  every test it holds under a second name, which reports the same failure twice
  and makes the suite's count meaningless.
  """

  class StubService:
    def __init__(self, result=None, failure=None):
      self._result = result
      self._failure = failure
      self.requests = []
      self.app_user_ids = []

    def assign(self, request, *, app_user_id):
      self.requests.append(request)
      self.app_user_ids.append(app_user_id)
      if self._failure is not None:
        raise self._failure
      return self._result

  def build_assignment_client(self, service=None):
    from backend.src.service.person_assignment import PersonAssignmentResult

    service = service if service is not None else self.StubService(
      result=PersonAssignmentResult(
        person_id=12,
        owner_user_id="acc-9",
        role="alt",
        created_person=True,
        display_name="张三",
      )
    )
    runtime = PersonRuntime(table_factory=lambda: StubTable())
    runtime.assignment_service = lambda: service
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))
    return app.test_client(), service


class AssignmentRouteTest(AssignmentRouteTestCase):
  """One request that resolves to a person: create or merge, and pick a role.

  The route does http and nothing else - reading the body, mapping a refusal to
  a status, serialising an answer.  Deciding what the link names, what the
  person should be called and whether the assignment is allowed all belong to
  the service, where they can be tested without a request context.
  """

  def test_an_assignment_is_carried_out(self):
    client, service = self.build_assignment_client()

    response = self.post(client, "/api/person/assignment", {
      "resolve_id": "receipt-1",
      "target": {"kind": "new", "display_name": "张三"},
      "role": "alt",
    })

    self.assertEqual(response.status_code, 200)
    data = self.body(response)["data"]
    self.assertEqual(data, {
      "person_id": 12,
      "owner_user_id": "acc-9",
      "role": "alt",
      "created_person": True,
      "display_name": "张三",
    })
    self.assertEqual(service.app_user_ids, [9001])

  def test_the_whole_body_reaches_the_service_unedited(self):
    """Validating it twice, in two places, is how the two come to disagree."""
    client, service = self.build_assignment_client()
    body = {
      "resolve_id": "receipt-1",
      "target": {"kind": "existing", "person_id": 12},
      "role": "main",
      "allow_move": True,
      "replace_main": {"demote_to": "alt"},
    }

    self.post(client, "/api/person/assignment", body)

    self.assertEqual(service.requests, [body])

  def test_a_body_that_is_not_json_is_refused(self):
    client, service = self.build_assignment_client()

    response = client.post("/api/person/assignment", data="resolve_id=1")

    self.assertEqual(response.status_code, 400)
    self.assertEqual(service.requests, [])

  def test_a_body_that_is_not_an_object_is_refused(self):
    client, service = self.build_assignment_client()

    response = client.post(
      "/api/person/assignment",
      data=json.dumps(["receipt-1"]),
      content_type="application/json",
    )

    self.assertEqual(response.status_code, 400)
    self.assertEqual(service.requests, [])

  def test_an_unwired_service_answers_that_it_is_unavailable(self):
    runtime = PersonRuntime(table_factory=lambda: StubTable())
    runtime.assignment_service = lambda: None
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))

    response = self.post(app.test_client(), "/api/person/assignment", {
      "resolve_id": "receipt-1",
      "target": {"kind": "new"},
      "role": "alt",
    })

    self.assertEqual(response.status_code, 503)


class AssignmentRefusalRouteTest(AssignmentRouteTestCase):
  """Each refusal answers with the status it carries, never one derived here."""

  def refuse_with(self, failure):
    client, _ = self.build_assignment_client(self.StubService(failure=failure))
    return self.post(client, "/api/person/assignment", {
      "resolve_id": "receipt-1",
      "target": {"kind": "existing", "person_id": 12},
      "role": "main",
    })

  def test_a_field_error_answers_400(self):
    from backend.src.service.person_assignment import InvalidAssignment

    response = self.refuse_with(InvalidAssignment("role 必须是三者之一"))

    self.assertEqual(response.status_code, 400)
    self.assertEqual(self.body(response)["kind"], "invalid_assignment")

  def test_an_expired_receipt_answers_404(self):
    from backend.src.service.person_assignment import ResolutionNotFound

    response = self.refuse_with(ResolutionNotFound("解析结果不存在或已过期"))

    self.assertEqual(response.status_code, 404)
    self.assertEqual(self.body(response)["kind"], "resolution_not_found")

  def test_an_unknown_person_answers_404(self):
    from backend.src.service.person_assignment import PersonNotFound

    response = self.refuse_with(PersonNotFound("人物不存在"))

    self.assertEqual(response.status_code, 404)

  def test_a_link_naming_no_owner_answers_400(self):
    from backend.src.service.person_assignment import OwnerIdentityUnavailable

    response = self.refuse_with(OwnerIdentityUnavailable("识别不到主播"))

    self.assertEqual(response.status_code, 400)
    self.assertEqual(self.body(response)["kind"], "owner_identity_unavailable")

  def test_an_account_held_elsewhere_answers_409_and_says_by_whom(self):
    """So the page can offer the move rather than only reporting a refusal."""
    from backend.src.service.person_assignment import AccountAlreadyAttached

    response = self.refuse_with(
      AccountAlreadyAttached("该账号已归属其他人物", person_id=7,
                             display_name="原来的人")
    )

    self.assertEqual(response.status_code, 409)
    body = self.body(response)
    self.assertEqual(body["kind"], "account_already_attached")
    self.assertEqual(
      body["current_person"], {"person_id": 7, "display_name": "原来的人"}
    )

  def test_a_second_main_answers_409_and_names_the_current_one(self):
    from backend.src.service.person_assignment import MainAccountConflict

    response = self.refuse_with(
      MainAccountConflict("该人物已有大号", owner_user_id="acc-1",
                          nickname="主号")
    )

    self.assertEqual(response.status_code, 409)
    body = self.body(response)
    self.assertEqual(body["kind"], "main_account_conflict")
    self.assertEqual(
      body["current_main"], {"owner_user_id": "acc-1", "nickname": "主号"}
    )

  def test_a_blocked_schema_answers_503(self):
    from backend.src.service.person_assignment import AssignmentUnavailable

    response = self.refuse_with(AssignmentUnavailable("写入暂时不可用"))

    self.assertEqual(response.status_code, 503)

  def test_an_unexpected_failure_answers_500_without_saying_why(self):
    """The message of an unexpected failure carries paths and internals that
    belong in the log and not in a browser."""
    response = self.refuse_with(RuntimeError("/srv/secret/path exploded"))

    self.assertEqual(response.status_code, 500)
    self.assertNotIn("secret", self.body(response)["message"])


##
## >>============================= the older ways in =============================>>
##
class LegacyAttachHardeningTest(RouteTestCase):
  """The endpoints the current page still uses answer to the same invariant.

  Hardening only ``/api/person/assignment`` would have been theatre.  The Vue
  page has its own ``conflictingMain`` check, but a browser cannot be an
  invariant: anything that can issue an http request could put a second main on
  a person, and the folder resolution would then have two answers to "where do
  this person's files go".

  So these routes stopped calling ``attach_account`` - a bare upsert that knows
  nothing about mains - and go through the same guarded transaction.  Their
  request and success shapes are unchanged; what is new is that they can now
  refuse.
  """

  def build(self, table=None):
    table = table if table is not None else StubTable()
    runtime = PersonRuntime(table_factory=lambda: table)
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))
    return app.test_client(), table

  def attach(self, client, **overrides):
    body = {"owner_user_id": "acc-2", "person_id": 12, "role": "main"}
    body.update(overrides)
    return self.post(client, "/api/person/account", body)

  def test_a_known_account_is_still_attached(self):
    client, table = self.build()

    response = self.attach(client, role="alt")

    self.assertEqual(response.status_code, 200)
    data = self.body(response)["data"]
    self.assertEqual(data["owner_user_id"], "acc-2")
    self.assertEqual(data["person_id"], 12)

  def test_it_goes_through_the_guarded_transaction(self):
    """Not ``attach_account`` followed by ``align_accounts_to_main``.  Those are
    two commits with a gap in between, and neither of them checks anything."""
    client, table = self.build()

    self.attach(client, role="alt")

    self.assertEqual(len(table.assignments), 1)
    self.assertEqual(table.attached, [])
    self.assertEqual(table.aligned, [])

  def test_a_second_main_is_refused(self):
    from backend.src.database.table.person_identity import MainAlreadyAssigned

    table = StubTable()
    table.assignment_failure = MainAlreadyAssigned("acc-1", "主号")
    client, _ = self.build(table)

    response = self.attach(client, role="main")

    self.assertEqual(response.status_code, 409)
    body = self.body(response)
    self.assertEqual(body["kind"], "main_account_conflict")
    self.assertEqual(
      body["current_main"], {"owner_user_id": "acc-1", "nickname": "主号"}
    )

  def test_demoting_the_last_main_is_refused(self):
    """The same rule from the other direction, reachable from this route too:
    re-attaching the current main as an alt empties the main slot."""
    from backend.src.database.table.person_identity import LastMainRemoval

    table = StubTable()
    table.assignment_failure = LastMainRemoval(
      12, display_name="李四", owner_user_id="acc-2", nickname="主号"
    )
    client, _ = self.build(table)

    response = self.attach(client, role="alt")

    self.assertEqual(response.status_code, 409)
    self.assertEqual(self.body(response)["kind"], "last_main_removal_conflict")

  def test_moving_an_account_still_needs_no_receipt(self):
    """This endpoint names an account the server already knows, so it never had
    a resolution and must not start needing one."""
    client, table = self.build()

    response = self.attach(client, role="alt")

    self.assertEqual(response.status_code, 200)

  def test_an_account_the_server_never_heard_of_is_refused(self):
    """It would otherwise mint a ``share_url`` row for an id a client made up -
    which the old bare upsert could not do, and this must not start doing."""
    table = StubTable()
    table.unknown_accounts = ("acc-made-up",)
    client, _ = self.build(table)

    response = self.attach(client, owner_user_id="acc-made-up", role="alt")

    self.assertEqual(response.status_code, 404)
    self.assertEqual(table.assignments, [])

  def test_an_unknown_role_is_still_a_field_error(self):
    client, table = self.build()

    response = self.attach(client, role="boss")

    self.assertEqual(response.status_code, 400)
    self.assertEqual(table.assignments, [])

  def test_a_missing_person_id_is_still_a_field_error(self):
    client, _ = self.build()

    response = self.post(
      client, "/api/person/account", {"owner_user_id": "acc-2", "role": "alt"}
    )

    self.assertEqual(response.status_code, 400)

  def test_a_missing_owner_user_id_is_still_a_field_error(self):
    client, _ = self.build()

    response = self.post(
      client, "/api/person/account", {"person_id": 12, "role": "alt"}
    )

    self.assertEqual(response.status_code, 400)

  def test_an_unknown_person_answers_404(self):
    from backend.src.database.table.person_identity import PersonMissing

    table = StubTable()
    table.assignment_failure = PersonMissing(999)
    client, _ = self.build(table)

    response = self.attach(client, role="alt")

    self.assertEqual(response.status_code, 404)

  def test_an_account_held_by_somebody_else_is_refused(self):
    from backend.src.database.table.person_identity import (
      AccountAttachedElsewhere,
    )

    table = StubTable()
    table.assignment_failure = AccountAttachedElsewhere(7, "原来的人")
    client, _ = self.build(table)

    response = self.attach(client, role="alt")

    self.assertEqual(response.status_code, 409)
    self.assertEqual(self.body(response)["kind"], "account_already_attached")


class LegacyByLinkHardeningTest(RouteTestCase):
  """The link endpoint answers to the same invariant as the receipt one.

  It follows the link itself rather than redeeming a resolution, and it keeps
  doing so - its callers never had a receipt and this is not the round to make
  them get one.  What changes is what happens after: the identity it read and
  the attachment it wants are handed to the one guarded transaction, instead of
  being written as two commits that check nothing.
  """

  IDENTITY = {
    "owner_user_id": "acc-9",
    "sec_user_id": "MS4wLjABAAAA",
    "nickname": "主播甲",
  }

  def build(self, table=None):
    table = table if table is not None else StubTable()
    runtime = PersonRuntime(table_factory=lambda: table)
    runtime.resolve_owner_identity = lambda url: dict(self.IDENTITY)
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))
    return app.test_client(), table

  def mark(self, client, **overrides):
    body = {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "main",
    }
    body.update(overrides)
    return self.post(client, "/api/person/account/by-link", body)

  def test_a_never_downloaded_owner_can_still_be_marked(self):
    client, table = self.build()

    response = self.mark(client, role="alt")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["data"]["nickname"], "主播甲")

  def test_it_goes_through_the_guarded_transaction(self):
    client, table = self.build()

    self.mark(client, role="alt")

    self.assertEqual(len(table.assignments), 1)
    self.assertEqual(table.attached, [])
    self.assertEqual(table.aligned, [])

  def test_the_resolved_identity_is_carried_into_the_transaction(self):
    """Recorded in the same transaction as the attachment, not before it.

    Two commits meant an identity row could survive an attach that failed - an
    account this program had heard of, marked as belonging to nobody.
    """
    client, table = self.build()

    self.mark(client, role="alt")

    assignment = table.assignments[0]
    self.assertEqual(assignment["owner_user_id"], "acc-9")
    self.assertEqual(assignment["nickname"], "主播甲")
    self.assertEqual(assignment["sec_user_id"], "MS4wLjABAAAA")

  def test_a_second_main_is_refused(self):
    from backend.src.database.table.person_identity import MainAlreadyAssigned

    table = StubTable()
    table.assignment_failure = MainAlreadyAssigned("acc-1", "主号")
    client, _ = self.build(table)

    response = self.mark(client, role="main")

    self.assertEqual(response.status_code, 409)
    self.assertEqual(self.body(response)["kind"], "main_account_conflict")

  def test_demoting_the_last_main_is_refused(self):
    from backend.src.database.table.person_identity import LastMainRemoval

    table = StubTable()
    table.assignment_failure = LastMainRemoval(
      3, display_name="李四", owner_user_id="acc-9", nickname="主号"
    )
    client, _ = self.build(table)

    response = self.mark(client, role="alt")

    self.assertEqual(response.status_code, 409)
    self.assertEqual(self.body(response)["kind"], "last_main_removal_conflict")

  def test_the_link_is_followed_before_the_transaction(self):
    """A request made between BEGIN and COMMIT would hold every row lock the
    transaction has taken for as long as douyin takes to answer."""
    order = []
    table = StubTable()
    runtime = PersonRuntime(table_factory=lambda: table)
    runtime.resolve_owner_identity = lambda url: (
      order.append("platform") or dict(self.IDENTITY)
    )
    original = table.assign_account

    def watched(**kwargs):
      order.append("database")
      return original(**kwargs)

    table.assign_account = watched
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))

    self.post(app.test_client(), "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "alt",
    })

    self.assertEqual(order, ["platform", "database"])

  def test_an_unknown_role_is_still_refused_before_the_link_is_followed(self):
    followed = []
    table = StubTable()
    runtime = PersonRuntime(table_factory=lambda: table)
    runtime.resolve_owner_identity = lambda url: (
      followed.append(url) or dict(self.IDENTITY)
    )
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))

    response = self.post(app.test_client(), "/api/person/account/by-link", {
      "url": "https://v.douyin.com/abc/", "person_id": 3, "role": "boss",
    })

    self.assertEqual(response.status_code, 400)
    self.assertEqual(followed, [])


class LegacyDetachHardeningTest(RouteTestCase):
  """Unmarking answers to the last-main rule too.

  It is the shortest road to the same damage: one click beside the main account
  strands every sibling that was aligned to its folder.
  """

  def build(self, table=None):
    table = table if table is not None else StubTable()
    runtime = PersonRuntime(table_factory=lambda: table)
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))
    return app.test_client(), table

  def test_an_account_is_still_detached(self):
    client, table = self.build()

    response = client.delete("/api/person/account?owner_user_id=acc-1")

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["data"]["owner_user_id"], "acc-1")
    self.assertEqual(table.detached, [("douyin", "acc-1")])

  def test_detaching_the_last_main_is_refused(self):
    from backend.src.database.table.person_identity import LastMainRemoval

    table = StubTable()
    table.assignment_failure = LastMainRemoval(
      12, display_name="李四", owner_user_id="acc-1", nickname="主号"
    )
    client, _ = self.build(table)

    response = client.delete("/api/person/account?owner_user_id=acc-1")

    self.assertEqual(response.status_code, 409)
    body = self.body(response)
    self.assertEqual(body["kind"], "last_main_removal_conflict")
    self.assertEqual(
      body["source_person"], {"person_id": 12, "display_name": "李四"}
    )
    self.assertEqual(table.detached, [])

  def test_detaching_an_unmarked_account_says_so(self):
    from backend.src.database.table.person_identity import NotAttached

    table = StubTable()
    table.assignment_failure = NotAttached("acc-1")
    client, _ = self.build(table)

    response = client.delete("/api/person/account?owner_user_id=acc-1")

    self.assertEqual(response.status_code, 404)
    self.assertEqual(self.body(response)["kind"], "account_not_attached")

  def test_a_missing_owner_user_id_is_still_a_field_error(self):
    client, _ = self.build()

    response = client.delete("/api/person/account")

    self.assertEqual(response.status_code, 400)


class AssignmentWiringTest(unittest.TestCase):
  """The service is built per request from *this* application's resolve store.

  A receipt issued by one application must not be redeemable in another, and a
  person blueprint holding its own store would answer "expired" to every
  receipt this server ever issued.
  """

  def test_it_reads_the_resolve_service_installed_on_the_application(self):
    from backend.src.web.resolve_routes import install_resolve_service

    runtime = PersonRuntime(table_factory=lambda: StubTable())
    app = Flask(__name__)
    install_test_auth(app)
    resolve_service = install_resolve_service(app)
    app.register_blueprint(build_person_blueprint(runtime))

    with app.test_request_context("/api/person/assignment"):
      service = runtime.assignment_service()

    self.assertIsNotNone(service)
    self.assertIs(service.resolve_service, resolve_service)

  def test_without_one_installed_there_is_no_service(self):
    runtime = PersonRuntime(table_factory=lambda: StubTable())
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))

    with app.test_request_context("/api/person/assignment"):
      self.assertIsNone(runtime.assignment_service())

  def test_the_real_application_redeems_its_own_receipts(self):
    """The assembly itself, not a stand-in for it.

    ``server.create_app`` registers this blueprint *before* it installs the
    resolve store, so a service built at registration time would hold nothing
    and every receipt would read as expired.  Reading the store per request is
    what makes the order harmless - and the order is not this module's to fix,
    so it has to be the thing that is tested.

    Nothing is requested from a platform here: the service is asked for, not
    driven, so the assertion stops at the store it would redeem against.
    """
    import server
    from backend.src.unit_test.config_fixture import unified_config
    from backend.src.web.resolve_routes import RESOLVE_SERVICE_KEY

    app = server.create_app(
      config=unified_config(), schema_guard_factory=lambda config: object()
    )
    runtime = PersonRuntime(table_factory=lambda: StubTable())

    with app.test_request_context("/api/person/assignment"):
      service = runtime.assignment_service()

    self.assertIsNotNone(service)
    ##
    ## The same object, not an equivalent one.  A second store would be
    ## indistinguishable from an expired receipt on every single request.
    ##
    self.assertIs(service.resolve_service, app.extensions[RESOLVE_SERVICE_KEY])

  def test_the_real_application_serves_the_route(self):
    import server
    from backend.src.unit_test.config_fixture import unified_config

    app = server.create_app(
      config=unified_config(), schema_guard_factory=lambda config: object()
    )

    routes = {str(rule) for rule in app.url_map.iter_rules()}

    self.assertIn("/api/person/assignment", routes)
    ##
    ## And the endpoints the page still uses are all still there: this step
    ## adds a way in, it does not take one away.
    ##
    for existing in (
      "/api/person",
      "/api/person/account",
      "/api/person/account/by-link",
      "/api/person/accounts",
    ):
      self.assertIn(existing, routes)



##
## >>============================= existing identity =============================>>
##
class InspectRouteTestCase(RouteTestCase):
  """Shared wiring, and no tests of its own.

  Split out rather than subclassed from a test class: inheriting one re-runs
  every test it holds under a second name, which reports the same failure twice
  and makes the suite's count meaningless.
  """

  class StubService:
    def __init__(self, result=None, failure=None):
      self._result = result
      self._failure = failure
      self.requests = []
      self.app_user_ids = []

    def inspect(self, request, *, app_user_id):
      self.requests.append(request)
      self.app_user_ids.append(app_user_id)
      if self._failure is not None:
        raise self._failure
      return self._result

  def inspection(self, **overrides):
    from backend.src.service.person_assignment import PersonIdentityInspection

    fields = {
      "owner_user_id": "acc-9",
      "sec_user_id": "MS4wLjABAAAA",
      "nickname": "程儿",
      "known_account": True,
      "person_id": 12,
      "display_name": "程儿",
      "role": "main",
    }
    fields.update(overrides)
    return PersonIdentityInspection(**fields)

  def build_inspect_client(self, service=None):
    service = service if service is not None else self.StubService(
      result=self.inspection()
    )
    runtime = PersonRuntime(table_factory=lambda: StubTable())
    runtime.assignment_service = lambda: service
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))
    return app.test_client(), service


class InspectRouteTest(InspectRouteTestCase):
  """Ask what a receipt names before offering to file it anywhere.

  The route does http and nothing else - reading the body, mapping a refusal to
  a status, serialising an answer.  What the link names and whether this server
  already holds it are the service's business, where they can be tested without
  a request context.
  """

  def test_a_filed_account_reports_the_person_holding_it(self):
    client, service = self.build_inspect_client()

    response = self.post(client, "/api/person/inspect", {
      "resolve_id": "receipt-1",
    })

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["data"], {
      "owner": {
        "owner_user_id": "acc-9",
        "sec_user_id": "MS4wLjABAAAA",
        "nickname": "程儿",
      },
      "known_account": True,
      "assignment": {
        "person_id": 12,
        "display_name": "程儿",
        "role": "main",
      },
    })
    self.assertEqual(service.app_user_ids, [9001])

  def test_a_known_account_nobody_filed_carries_no_assignment(self):
    client, _ = self.build_inspect_client(
      self.StubService(
        result=self.inspection(person_id=None, display_name=None, role=None)
      )
    )

    response = self.post(client, "/api/person/inspect", {
      "resolve_id": "receipt-1",
    })

    data = self.body(response)["data"]
    self.assertTrue(data["known_account"])
    self.assertIsNone(data["assignment"])

  def test_an_account_this_server_never_saw_is_reported_as_new(self):
    client, _ = self.build_inspect_client(
      self.StubService(
        result=self.inspection(
          known_account=False, person_id=None, display_name=None, role=None
        )
      )
    )

    data = self.body(
      self.post(client, "/api/person/inspect", {"resolve_id": "receipt-1"})
    )["data"]

    self.assertFalse(data["known_account"])
    self.assertIsNone(data["assignment"])
    self.assertEqual(data["owner"]["owner_user_id"], "acc-9")

  def test_an_account_that_already_exists_is_not_an_error(self):
    """The product decision, stated as a test.  The user is looking, not
    writing, and "you already have this" is the answer they asked for - a 409
    would make the page treat a successful check as a failure."""
    client, _ = self.build_inspect_client()

    response = self.post(client, "/api/person/inspect", {
      "resolve_id": "receipt-1",
    })

    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.body(response)["status"], "success")

  def test_the_whole_body_reaches_the_service_unedited(self):
    """Validating it twice, in two places, is how the two come to disagree -
    and the field list is the trust boundary here."""
    client, service = self.build_inspect_client()
    body = {"resolve_id": "receipt-1"}

    self.post(client, "/api/person/inspect", body)

    self.assertEqual(service.requests, [body])

  def test_a_client_naming_the_account_is_passed_on_to_be_refused(self):
    """The route does not strip it.  Silently dropping a field a client sent
    would answer as though the request had said something else."""
    client, service = self.build_inspect_client()

    self.post(client, "/api/person/inspect", {
      "resolve_id": "receipt-1",
      "owner_user_id": "acc-1",
    })

    self.assertEqual(service.requests[0].get("owner_user_id"), "acc-1")

  def test_nothing_about_folders_or_urls_is_returned(self):
    """A folder is the download paths' business and a resolved url can carry a
    signature.  Neither is needed to say "you have already added this"."""
    client, _ = self.build_inspect_client()

    payload = response = self.post(
      client, "/api/person/inspect", {"resolve_id": "receipt-1"}
    )

    text = payload.data.decode("utf-8")
    for leak in ("directory_name", "resolved_url", "source_url", "save_dir"):
      self.assertNotIn(leak, text)

  def test_a_body_that_is_not_json_is_refused(self):
    client, service = self.build_inspect_client()

    response = client.post("/api/person/inspect", data="resolve_id=1")

    self.assertEqual(response.status_code, 400)
    self.assertEqual(service.requests, [])

  def test_a_body_that_is_not_an_object_is_refused(self):
    client, service = self.build_inspect_client()

    response = client.post(
      "/api/person/inspect",
      data=json.dumps(["receipt-1"]),
      content_type="application/json",
    )

    self.assertEqual(response.status_code, 400)
    self.assertEqual(service.requests, [])

  def test_an_unwired_service_answers_that_it_is_unavailable(self):
    runtime = PersonRuntime(table_factory=lambda: StubTable())
    runtime.assignment_service = lambda: None
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))

    response = self.post(app.test_client(), "/api/person/inspect", {
      "resolve_id": "receipt-1",
    })

    self.assertEqual(response.status_code, 503)

  def test_the_route_is_registered(self):
    runtime = PersonRuntime(table_factory=lambda: StubTable())
    app = Flask(__name__)
    install_test_auth(app)
    app.register_blueprint(build_person_blueprint(runtime))

    routes = {str(rule) for rule in app.url_map.iter_rules()}

    self.assertIn("/api/person/inspect", routes)


class InspectRefusalRouteTest(InspectRouteTestCase):
  """Each refusal answers with the status it carries, never one derived here."""

  def refuse_with(self, failure):
    client, _ = self.build_inspect_client(self.StubService(failure=failure))
    return self.post(client, "/api/person/inspect", {
      "resolve_id": "receipt-1",
    })

  def test_a_bad_field_is_a_field_error(self):
    from backend.src.service.person_assignment import InvalidAssignment

    response = self.refuse_with(InvalidAssignment("不支持的字段: owner_user_id"))

    self.assertEqual(response.status_code, 400)
    self.assertEqual(self.body(response)["kind"], "invalid_assignment")

  def test_an_expired_receipt_answers_404(self):
    from backend.src.service.person_assignment import ResolutionNotFound

    response = self.refuse_with(ResolutionNotFound("过期了"))

    self.assertEqual(response.status_code, 404)
    self.assertEqual(self.body(response)["kind"], "resolution_not_found")

  def test_a_link_naming_nobody_answers_400(self):
    from backend.src.service.person_assignment import OwnerIdentityUnavailable

    response = self.refuse_with(OwnerIdentityUnavailable("读不到"))

    self.assertEqual(response.status_code, 400)
    self.assertEqual(self.body(response)["kind"], "owner_identity_unavailable")

  def test_an_unreadable_database_answers_503_rather_than_new(self):
    """The one that matters.  Answering "unknown account" during an outage is
    an invitation to create a duplicate person for every link pasted."""
    from backend.src.service.person_assignment import PersonLookupUnavailable

    response = self.refuse_with(PersonLookupUnavailable("查不了"))

    self.assertEqual(response.status_code, 503)
    self.assertEqual(self.body(response)["kind"], "person_lookup_unavailable")
    self.assertNotIn("known_account", self.body(response))

  def test_an_unexpected_failure_is_answered_without_its_message(self):
    """Its text carries paths and internals that belong in the log."""
    client, _ = self.build_inspect_client(
      self.StubService(failure=RuntimeError("/srv/smsd/config.yaml missing"))
    )

    response = self.post(client, "/api/person/inspect", {
      "resolve_id": "receipt-1",
    })

    self.assertEqual(response.status_code, 500)
    self.assertNotIn("config.yaml", response.data.decode("utf-8"))


if __name__ == "__main__":
  unittest.main()
