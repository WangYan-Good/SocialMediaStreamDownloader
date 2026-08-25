import unittest
from unittest.mock import patch

from flask import Flask, g

from backend.src.auth.context import RequestAuthContext
from backend.src.auth.roles import ROLE_USER
from backend.src.auth.service import AuthenticatedUser
from backend.src.platform.resource_resolution import (
  RESOURCE_TYPE_LIVE,
  RESOURCE_TYPE_OWNER,
  RESOURCE_TYPE_POST,
  ResourceResolution,
  ShortLinkUnavailable,
  UnsupportedPlatform,
  UnsupportedResource,
  UntrustedRedirect,
)
from backend.src.service.resource_resolve import (
  ResolveStore,
  ResourceResolveService,
)
from backend.src.unit_test.auth_context import install_test_auth
from backend.src.web.resolve_routes import (
  RESOLVE_SERVICE_KEY,
  build_resolve_blueprint,
  install_resolve_service,
)


##
## The ids from the real share links used during design verification.
##
SEC_UID = "MS4wLjABAAAAGZkW5n1EHZD_TFyQ-QiaISBPemtKFxVVdhLSeoXhh-U"
AWEME_ID = "7657271784144009946"

SHORT_LINK = "https://v.douyin.com/M-kmspLye0o/"
POST_URL = "https://www.douyin.com/video/" + AWEME_ID
OWNER_URL = "https://www.douyin.com/user/" + SEC_UID
LIVE_URL = "https://live.douyin.com/123456"


def resolution(resource_type=RESOURCE_TYPE_POST, identity=None,
               source_url=SHORT_LINK, resolved_url=POST_URL):
  return ResourceResolution(
    platform="douyin",
    resource_type=resource_type,
    source_url=source_url,
    resolved_url=resolved_url,
    identity=identity if identity is not None else {"aweme_id": AWEME_ID},
  )


class StubResolver:
  """Stands in for a platform resolver, answering from a table."""

  platform = "douyin"

  def __init__(self, answers=None, error=None):
    self.answers = dict(answers or {})
    self.error = error

  def claims(self, url):
    return "douyin.com" in (url or "")

  def resolve(self, url):
    if self.error is not None:
      raise self.error
    answer = self.answers.get(url)
    if answer is None:
      raise UnsupportedResource("无法识别该链接指向的资源")
    return answer


def build_app(resolver=None, service=None, retention_seconds=600.0):
  """A bare app carrying only the resolve blueprint, as the route sees it."""
  if service is None:
    resolver = resolver if resolver is not None else StubResolver(
      {
        SHORT_LINK: resolution(),
        POST_URL: resolution(source_url=POST_URL),
        OWNER_URL: resolution(
          RESOURCE_TYPE_OWNER,
          {"sec_user_id": SEC_UID},
          source_url=OWNER_URL,
          resolved_url=OWNER_URL,
        ),
        LIVE_URL: resolution(
          RESOURCE_TYPE_LIVE, {}, source_url=LIVE_URL, resolved_url=LIVE_URL
        ),
      }
    )
    service = ResourceResolveService(
      resolvers=(resolver,),
      store=ResolveStore(retention_seconds=retention_seconds),
    )
  app = Flask(__name__)
  app.config["TESTING"] = True
  install_test_auth(app)
  install_resolve_service(app, service)
  app.register_blueprint(build_resolve_blueprint())
  return app, service


def post_resolve(app, body):
  return app.test_client().post("/api/resolve", json=body)


def post_batch_resolve(app, body):
  return app.test_client().post("/api/resolve/batch", json=body)


class FakeClock:
  def __init__(self):
    self.mono = 0.0

  def monotonic(self):
    return self.mono

  def advance(self, seconds):
    self.mono += seconds


class ResolveSuccessTest(unittest.TestCase):
  """The shape the browser reads, for each kind of resource."""

  def test_a_short_link_answers_the_documented_envelope(self):
    app, service = build_app()

    response = post_resolve(app, {"input": SHORT_LINK})
    body = response.get_json()

    self.assertEqual(response.status_code, 200)
    self.assertEqual(body["status"], "success")
    self.assertEqual(body["code"], 200)
    data = body["data"]
    self.assertEqual(data["platform"], "douyin")
    self.assertEqual(data["resource_type"], "post")
    self.assertEqual(data["source_url"], SHORT_LINK)
    self.assertEqual(data["resolved_url"], POST_URL)
    self.assertEqual(data["identity"], {"aweme_id": AWEME_ID})
    self.assertEqual(data["expires_in_seconds"], 600)
    self.assertTrue(data["resolve_id"])


class ResolveAuthorizationTest(unittest.TestCase):
  def app_for(self, context):
    service = ResourceResolveService(
      resolvers=(StubResolver({SHORT_LINK: resolution()}),)
    )
    app = Flask(__name__)

    @app.before_request
    def request_identity():
      g.auth_context = context

    install_resolve_service(app, service)
    app.register_blueprint(build_resolve_blueprint())
    return app, service

  def test_anonymous_single_and_batch_resolve_are_401(self):
    app, service = self.app_for(RequestAuthContext.anonymous())
    client = app.test_client()

    self.assertEqual(401, client.post("/api/resolve", json={}).status_code)
    self.assertEqual(401, client.post("/api/resolve/batch", json={}).status_code)
    self.assertEqual(0, service._store.tracked())

  def test_authenticated_resolve_requires_csrf_before_resolving(self):
    user = AuthenticatedUser(71, "alice", ROLE_USER)
    app, service = self.app_for(
      RequestAuthContext.authenticated(user, csrf_expected="proof")
    )

    response = app.test_client().post(
      "/api/resolve", json={"input": SHORT_LINK}
    )

    self.assertEqual(403, response.status_code)
    self.assertEqual("csrf_invalid", response.get_json()["kind"])
    self.assertEqual(0, service._store.tracked())

  def test_authenticated_resolve_binds_receipt_to_context_user(self):
    user = AuthenticatedUser(71, "alice", ROLE_USER)
    app, service = self.app_for(
      RequestAuthContext.authenticated(user, csrf_expected="proof")
    )

    response = app.test_client().post(
      "/api/resolve",
      json={"input": SHORT_LINK},
      headers={"X-CSRF-Token": "proof"},
    )
    resolve_id = response.get_json()["data"]["resolve_id"]

    self.assertIsNotNone(service.get_for_user(resolve_id, 71))
    self.assertIsNone(service.get_for_user(resolve_id, 72))

  def test_auth_unavailable_fails_closed_without_resolving(self):
    app, service = self.app_for(
      RequestAuthContext.unavailable(csrf_expected="proof")
    )

    response = app.test_client().post(
      "/api/resolve",
      json={"input": SHORT_LINK},
      headers={"X-CSRF-Token": "proof"},
    )

    self.assertEqual(503, response.status_code)
    self.assertEqual(0, service._store.tracked())

  def test_the_answer_carries_exactly_the_documented_fields(self):
    """No extras: every field here becomes something the frontend depends on."""
    app, _ = build_app()

    data = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]

    self.assertEqual(
      sorted(data.keys()),
      sorted([
        "resolve_id", "platform", "resource_type", "source_url",
        "resolved_url", "identity", "expires_in_seconds",
      ]),
    )

  def test_an_owner_link_answers_with_its_sec_user_id(self):
    app, _ = build_app()

    data = post_resolve(app, {"input": OWNER_URL}).get_json()["data"]

    self.assertEqual(data["resource_type"], "owner")
    self.assertEqual(data["identity"], {"sec_user_id": SEC_UID})

  def test_a_live_link_answers_with_an_empty_identity(self):
    app, _ = build_app()

    data = post_resolve(app, {"input": LIVE_URL}).get_json()["data"]

    self.assertEqual(data["resource_type"], "live")
    self.assertEqual(data["identity"], {})

  def test_a_long_url_reports_itself_as_its_own_resolved_url(self):
    app, _ = build_app()

    data = post_resolve(app, {"input": POST_URL}).get_json()["data"]

    self.assertEqual(data["source_url"], POST_URL)
    self.assertEqual(data["resolved_url"], POST_URL)

  def test_the_share_sentence_is_not_echoed_back(self):
    """Only the link is kept, so only the link can come back."""
    app, _ = build_app()
    text = "4.33 复制打开抖音，看看【xxx的作品】 " + SHORT_LINK + " :0pm"

    body = post_resolve(app, {"input": text}).get_json()

    self.assertNotIn("复制打开抖音", str(body))
    self.assertEqual(body["data"]["source_url"], SHORT_LINK)

  def test_every_resolve_gets_its_own_receipt(self):
    app, _ = build_app()

    first = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]
    second = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]

    self.assertNotEqual(first["resolve_id"], second["resolve_id"])

  def test_the_receipt_is_not_the_resource_id(self):
    app, _ = build_app()

    data = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]

    self.assertNotEqual(data["resolve_id"], AWEME_ID)
    self.assertNotIn(AWEME_ID, data["resolve_id"])


class ResolveIsIdentityOnlyTest(unittest.TestCase):
  """A resolve says which resource, never what is currently in it."""

  def test_no_preview_fields_are_invented(self):
    """Nickname, cover, live status each need a request and each expire.

    Answering them here would make "what did I paste?" fail whenever the login
    cookie went stale, which is the one question that must keep working.
    """
    app, _ = build_app()

    for url in (SHORT_LINK, OWNER_URL, LIVE_URL):
      with self.subTest(url=url):
        data = post_resolve(app, {"input": url}).get_json()["data"]
        for absent in ("nickname", "avatar_url", "desc", "cover_url",
                       "follower_count", "room_title", "live_status",
                       "is_living", "room_id"):
          self.assertNotIn(absent, data)
          self.assertNotIn(absent, data["identity"])


class ResolveReadBackTest(unittest.TestCase):
  """The receipt has to be worth something after the request that made it."""

  def test_the_resolution_is_readable_from_the_service_afterwards(self):
    app, service = build_app()

    resolve_id = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"][
      "resolve_id"
    ]

    stored = service.get(resolve_id)
    self.assertIsNotNone(stored)
    self.assertEqual(stored.resource_type, RESOURCE_TYPE_POST)
    self.assertEqual(stored.identity, {"aweme_id": AWEME_ID})

  def test_it_survives_a_second_request(self):
    """The store belongs to the application, not to a request context."""
    app, service = build_app()
    client = app.test_client()

    resolve_id = client.post("/api/resolve", json={"input": SHORT_LINK}).get_json()[
      "data"
    ]["resolve_id"]
    client.post("/api/resolve", json={"input": OWNER_URL})

    self.assertIsNotNone(service.get(resolve_id))

  def test_the_server_never_has_to_believe_the_browser(self):
    """What a later stage reads comes from the store, not from the response.

    A browser could send back any resource_type it liked; the receipt is what
    makes that irrelevant.
    """
    app, service = build_app()

    data = post_resolve(app, {"input": OWNER_URL}).get_json()["data"]

    stored = service.get(data["resolve_id"])
    self.assertEqual(stored.resource_type, RESOURCE_TYPE_OWNER)
    self.assertEqual(stored.identity["sec_user_id"], SEC_UID)


class ResolveBadRequestTest(unittest.TestCase):
  """Every refusal the endpoint owes the user an explanation for."""

  def assertRefused(self, body, code=400):
    app, _ = build_app()

    response = post_resolve(app, body)

    self.assertEqual(response.status_code, code)
    payload = response.get_json()
    self.assertEqual(payload["status"], "error")
    self.assertEqual(payload["code"], code)
    self.assertTrue(payload["message"])
    return payload

  def test_a_missing_input_field(self):
    self.assertRefused({})

  def test_an_empty_input(self):
    self.assertRefused({"input": "   "})

  def test_an_input_that_is_not_a_string(self):
    self.assertRefused({"input": ["https://www.douyin.com/video/1"]})

  def test_prose_without_a_link(self):
    self.assertRefused({"input": "这段文字里没有链接"})

  def test_two_links_at_once(self):
    payload = self.assertRefused(
      {"input": SHORT_LINK + " 还有 https://v.douyin.com/BBBBBBB/"}
    )

    self.assertIn("一次只能解析一个链接", payload["message"])

  def test_a_non_http_scheme(self):
    self.assertRefused({"input": "file:///etc/passwd"})

  def test_an_empty_body(self):
    app, _ = build_app()

    response = app.test_client().post(
      "/api/resolve", data="", content_type="application/json"
    )

    self.assertEqual(response.status_code, 400)

  def test_a_body_that_is_not_json(self):
    app, _ = build_app()

    response = app.test_client().post("/api/resolve", data="input=x")

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.get_json()["status"], "error")

  def test_a_json_body_that_is_not_an_object(self):
    app, _ = build_app()

    response = app.test_client().post("/api/resolve", json=["a"])

    self.assertEqual(response.status_code, 400)


class BatchResolveApiTest(unittest.TestCase):
  def test_non_json_and_non_object_bodies_are_rejected(self):
    app, _ = build_app()
    client = app.test_client()

    responses = (
      client.post("/api/resolve/batch", data="input=x"),
      client.post("/api/resolve/batch", json=["a"]),
    )

    for response in responses:
      with self.subTest(response=response):
        self.assertEqual(400, response.status_code)
        self.assertEqual("error", response.get_json()["status"])

  def test_successes_keep_the_existing_receipt_shape(self):
    app, service = build_app()

    response = post_batch_resolve(app, {"input": POST_URL + "\n" + OWNER_URL})
    body = response.get_json()

    self.assertEqual(200, response.status_code)
    self.assertEqual((2, 2, 0), (
      body["data"]["total"],
      body["data"]["resolved_count"],
      body["data"]["failed_count"],
    ))
    items = body["data"]["items"]
    self.assertEqual([0, 1], [item["index"] for item in items])
    self.assertEqual(["resolved", "resolved"], [item["status"] for item in items])
    for item in items:
      resolution_data = item["resolution"]
      self.assertTrue(resolution_data["resolve_id"])
      self.assertIsNotNone(service.get(resolution_data["resolve_id"]))

  def test_partial_and_all_failed_batches_still_answer_200(self):
    app, _ = build_app()
    private = "https://example.test/private?signature=secret"

    partial = post_batch_resolve(app, {"input": POST_URL + "\n" + private})
    failed = post_batch_resolve(app, {"input": private})

    self.assertEqual(200, partial.status_code)
    self.assertEqual(1, partial.get_json()["data"]["failed_count"])
    self.assertEqual(200, failed.status_code)
    item = failed.get_json()["data"]["items"][0]
    self.assertEqual("failed", item["status"])
    self.assertEqual("unsupported_platform", item["error"]["kind"])
    self.assertNotIn("source_url", item)
    self.assertNotIn("signature=secret", str(item))

  def test_missing_no_url_and_too_many_are_whole_request_errors(self):
    app, _ = build_app()
    too_many = "\n".join(
      "https://www.douyin.com/video/{}".format(index) for index in range(21)
    )

    for payload in ({}, {"input": "没有链接"}, {"input": too_many}):
      with self.subTest(payload=payload):
        self.assertEqual(400, post_batch_resolve(app, payload).status_code)

  def test_missing_service_and_unexpected_failure_are_503_and_generic_500(self):
    missing = Flask(__name__)
    install_test_auth(missing)
    missing.register_blueprint(build_resolve_blueprint())

    class BrokenService:
      retention_seconds = 600

      def resolve_many(self, unused):
        raise RuntimeError("private input leaked")

    broken, unused = build_app(service=BrokenService())

    self.assertEqual(
      503,
      post_batch_resolve(missing, {"input": POST_URL}).status_code,
    )
    response = post_batch_resolve(broken, {"input": POST_URL})
    self.assertEqual(500, response.status_code)
    self.assertNotIn("private", str(response.get_json()))

  def test_only_post_is_accepted(self):
    app, _ = build_app()
    client = app.test_client()

    for method in (client.get, client.patch, client.delete):
      with self.subTest(method=method.__name__):
        self.assertEqual(405, method("/api/resolve/batch").status_code)

  def test_single_resolve_still_rejects_two_distinct_urls(self):
    app, _ = build_app()

    response = post_resolve(app, {"input": POST_URL + "\n" + OWNER_URL})

    self.assertEqual(400, response.status_code)
    self.assertIn("一次只能解析一个链接", response.get_json()["message"])


class ResolveFailureMappingTest(unittest.TestCase):
  """Each platform failure reaches the browser as the status it means."""

  def build(self, error):
    service = ResourceResolveService(
      resolvers=(StubResolver(error=error),), store=ResolveStore()
    )
    app, _ = build_app(service=service)
    return app

  def test_an_unsupported_platform_is_a_bad_request(self):
    app, _ = build_app()

    response = post_resolve(app, {"input": "https://www.bilibili.com/video/BV1"})

    self.assertEqual(response.status_code, 400)

  def test_a_douyin_link_we_cannot_name_is_a_bad_request(self):
    app = self.build(UnsupportedResource("无法识别该链接指向的资源"))

    response = post_resolve(app, {"input": "https://www.douyin.com/"})

    self.assertEqual(response.status_code, 400)

  def test_a_short_link_that_cannot_be_followed_is_a_gateway_error(self):
    app = self.build(ShortLinkUnavailable("无法解析该短链接，请稍后重试"))

    response = post_resolve(app, {"input": SHORT_LINK})

    self.assertEqual(response.status_code, 502)
    self.assertEqual(response.get_json()["code"], 502)

  def test_a_redirect_off_the_platform_is_a_bad_request(self):
    app = self.build(UntrustedRedirect("该链接跳转到了非抖音地址"))

    response = post_resolve(app, {"input": SHORT_LINK})

    self.assertEqual(response.status_code, 400)

  def test_an_unexpected_failure_is_a_generic_five_hundred(self):
    app = self.build(RuntimeError("boom: /srv/app/config/config.yml line 12"))

    response = post_resolve(app, {"input": SHORT_LINK})
    body = response.get_json()

    self.assertEqual(response.status_code, 500)
    self.assertEqual(body["status"], "error")
    self.assertNotIn("boom", body["message"])
    self.assertNotIn("config.yml", str(body))
    self.assertNotIn("traceback", body)

  def test_no_failure_leaks_internal_state(self):
    """Error text reaches a browser; headers, cookies and paths must not."""
    app = self.build(UnsupportedPlatform("暂不支持该平台的链接"))

    body = str(post_resolve(app, {"input": SHORT_LINK}).get_json())

    for secret in ("cookie", "Cookie", "msToken", "Authorization",
                   "config.yml", "Traceback"):
      self.assertNotIn(secret, body)


class ResolveWiringTest(unittest.TestCase):
  """One service per application, reachable the way every extension is."""

  def test_the_service_is_reachable_through_the_app_extensions(self):
    app, service = build_app()

    self.assertIs(app.extensions[RESOLVE_SERVICE_KEY], service)

  def test_installing_without_a_service_still_provides_one(self):
    app = Flask(__name__)

    service = install_resolve_service(app)

    self.assertIsInstance(service, ResourceResolveService)
    self.assertIs(app.extensions[RESOLVE_SERVICE_KEY], service)

  def test_a_missing_service_is_reported_not_crashed(self):
    """Registering the blueprint without wiring is a deployment bug, not a 500."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    install_test_auth(app)
    app.register_blueprint(build_resolve_blueprint())

    response = app.test_client().post("/api/resolve", json={"input": SHORT_LINK})

    self.assertEqual(response.status_code, 503)
    self.assertEqual(response.get_json()["status"], "error")

  def test_two_applications_do_not_share_their_resolutions(self):
    """A receipt from one app must mean nothing to another in the same process."""
    first, first_service = build_app()
    second, second_service = build_app()

    resolve_id = post_resolve(first, {"input": SHORT_LINK}).get_json()["data"][
      "resolve_id"
    ]

    self.assertIsNotNone(first_service.get(resolve_id))
    self.assertIsNone(second_service.get(resolve_id))

  def test_the_stated_lifetime_follows_the_store(self):
    app, _ = build_app(retention_seconds=42.0)

    data = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]

    self.assertEqual(data["expires_in_seconds"], 42)

  def test_only_post_is_accepted(self):
    app, _ = build_app()

    self.assertEqual(app.test_client().get("/api/resolve").status_code, 405)


class ExpiryContractTest(unittest.TestCase):
  """What the browser is told about the lifetime has to *be* the lifetime.

  The number travels store -> service -> route.  A constant written at the
  route would keep answering 600 after someone shortened the store to 120, and
  the browser would go on offering a confirm button against a receipt that had
  already been evicted.
  """

  def build(self, retention_seconds, clock=None):
    store = ResolveStore(
      retention_seconds=retention_seconds,
      **({"clock": clock.monotonic} if clock is not None else {})
    )
    service = ResourceResolveService(
      resolvers=(StubResolver({SHORT_LINK: resolution()}),), store=store
    )
    app, _ = build_app(service=service)
    return app, service

  def test_the_number_answered_is_the_retention_actually_configured(self):
    for retention in (17.0, 120.0, 600.0):
      with self.subTest(retention=retention):
        app, _ = self.build(retention)

        data = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]

        self.assertEqual(data["expires_in_seconds"], int(retention))

  def test_the_stated_lifetime_is_when_the_receipt_really_dies(self):
    """Ties the number to observed eviction, not merely to a property read."""
    clock = FakeClock()
    app, service = self.build(17.0, clock)

    data = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]
    stated = data["expires_in_seconds"]

    self.assertEqual(stated, 17)
    clock.advance(stated - 1)
    self.assertIsNotNone(service.get(data["resolve_id"]))
    clock.advance(2)
    self.assertIsNone(service.get(data["resolve_id"]))

  def test_the_store_is_the_authority_when_the_service_default_disagrees(self):
    """A store with its own retention must not be described by the default.

    ``retention_seconds`` on the service only builds a default store; once a
    store is handed in, it owns the answer.  Otherwise the two could drift and
    the api would report the one that is not enforcing anything.
    """
    service = ResourceResolveService(
      resolvers=(StubResolver({SHORT_LINK: resolution()}),),
      store=ResolveStore(retention_seconds=17.0),
      retention_seconds=600.0,
    )
    app, _ = build_app(service=service)

    data = post_resolve(app, {"input": SHORT_LINK}).get_json()["data"]

    self.assertEqual(data["expires_in_seconds"], 17)
    self.assertEqual(service.retention_seconds, 17.0)


class DuplicateLinkTest(unittest.TestCase):
  """One resource named twice is one resource, not an ambiguous request.

  The rule is *distinct* links, not link occurrences.  The business constraint
  is "one resource per resolve"; how many times the user's clipboard happened
  to repeat it is not the api's concern.
  """

  def test_the_same_link_on_several_lines_resolves(self):
    app, _ = build_app()
    text = SHORT_LINK + "\n一些文字\n" + SHORT_LINK

    response = post_resolve(app, {"input": text})

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.get_json()["data"]["source_url"], SHORT_LINK)

  def test_the_same_link_with_different_trailing_punctuation_resolves(self):
    """Noise trimming happens before the comparison, so ``A。`` and ``A`` match."""
    app, _ = build_app()

    response = post_resolve(app, {"input": SHORT_LINK + "。 又贴一次 " + SHORT_LINK})

    self.assertEqual(response.status_code, 200)

  def test_two_different_links_are_still_refused(self):
    app, _ = build_app()

    response = post_resolve(app, {"input": SHORT_LINK + "\n" + OWNER_URL})

    self.assertEqual(response.status_code, 400)
    self.assertIn("一次只能解析一个链接", response.get_json()["message"])

  def test_sameness_is_the_link_as_written_not_a_guess_about_it(self):
    """``/abc/`` and ``/abc`` may well be one resource - but only the platform
    knows that, and treating them as equal here would mean resolving a url
    nobody pasted.  Two spellings, two candidates, one refusal.
    """
    app, _ = build_app()

    response = post_resolve(
      app, {"input": SHORT_LINK + " " + SHORT_LINK.rstrip("/")}
    )

    self.assertEqual(response.status_code, 400)


class ApplicationFactoryTest(unittest.TestCase):
  """The resolve endpoint must be wired by the factory, not by each caller."""

  def build_app(self):
    import server
    from backend.src.unit_test.config_fixture import unified_config

    app = server.create_app(
      config=unified_config(),
      schema_guard_factory=lambda config: object(),
    )
    return install_test_auth(app)

  def test_a_configured_app_carries_one_resolve_service(self):
    app = self.build_app()

    self.assertIsInstance(
      app.extensions[RESOLVE_SERVICE_KEY], ResourceResolveService
    )

  def test_a_configured_app_resolves_each_kind_of_link(self):
    app = self.build_app()
    expected = {
      POST_URL: ("post", {"aweme_id": AWEME_ID}),
      OWNER_URL: ("owner", {"sec_user_id": SEC_UID}),
      LIVE_URL: ("live", {}),
    }

    for url, (resource_type, identity) in expected.items():
      with self.subTest(url=url):
        response = post_resolve(app, {"input": url})

        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertEqual(data["resource_type"], resource_type)
        self.assertEqual(data["identity"], identity)
        self.assertEqual(data["resolved_url"], url)

  def test_the_receipt_is_redeemable_on_the_application_that_issued_it(self):
    app = self.build_app()

    resolve_id = post_resolve(app, {"input": OWNER_URL}).get_json()["data"][
      "resolve_id"
    ]

    stored = app.extensions[RESOLVE_SERVICE_KEY].get(resolve_id)
    self.assertEqual(stored.resource_type, RESOURCE_TYPE_OWNER)
    self.assertEqual(stored.identity, {"sec_user_id": SEC_UID})

  def test_two_apps_do_not_share_their_resolutions(self):
    """Each application owns its own store, as every other extension does."""
    first = self.build_app()
    second = self.build_app()

    resolve_id = post_resolve(first, {"input": POST_URL}).get_json()["data"][
      "resolve_id"
    ]

    self.assertIsNotNone(first.extensions[RESOLVE_SERVICE_KEY].get(resolve_id))
    self.assertIsNone(second.extensions[RESOLVE_SERVICE_KEY].get(resolve_id))

  def test_the_two_services_are_distinct_objects(self):
    first = self.build_app()
    second = self.build_app()

    self.assertIsNot(
      first.extensions[RESOLVE_SERVICE_KEY],
      second.extensions[RESOLVE_SERVICE_KEY],
    )


class ResolveStartsNothingTest(unittest.TestCase):
  """Resolving is a question.  Nothing may act on the answer yet."""

  def build_app(self):
    return ApplicationFactoryTest().build_app()

  def task_count(self, app):
    return app.test_client().get("/api/tasks").get_json()["data"]["total"]

  def test_no_task_is_created_for_any_kind_of_link(self):
    """P6 creates tasks.  Until then a mistyped link must leave no trace."""
    app = self.build_app()
    before = self.task_count(app)

    for url in (POST_URL, OWNER_URL, LIVE_URL):
      with self.subTest(url=url):
        self.assertEqual(post_resolve(app, {"input": url}).status_code, 200)

    self.assertEqual(before, 0)
    self.assertEqual(self.task_count(app), 0)

  def test_a_refused_resolve_creates_no_task_either(self):
    """A failed classification is an api error, never a failed task."""
    app = self.build_app()

    for bad in ("这段文字里没有链接", "https://www.bilibili.com/video/BV1",
                "https://www.douyin.com/", POST_URL + " " + OWNER_URL):
      with self.subTest(bad=bad):
        post_resolve(app, {"input": bad})

    self.assertEqual(self.task_count(app), 0)

  def test_a_long_link_is_resolved_without_a_single_request(self):
    """No downloader, no live probe, no owner api - and no http at all.

    Every one of those needs a credential or produces state that expires, and
    none of them is needed to say which resource a url names.
    """
    app = self.build_app()

    with patch(
      "backend.src.platform.douyin.douyin_resource_resolver.request",
      side_effect=AssertionError("resolve must not make a request"),
    ) as never:
      for url in (POST_URL, OWNER_URL, LIVE_URL):
        with self.subTest(url=url):
          self.assertEqual(post_resolve(app, {"input": url}).status_code, 200)

    never.assert_not_called()

if __name__ == "__main__":
  unittest.main()
