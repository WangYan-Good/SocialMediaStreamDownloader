import unittest

from flask import Flask

from backend.src.auth.policy import (
  AUTHORIZATION_POLICY,
  BUSINESS_ENDPOINT_ENFORCEMENT_ENABLED,
  CsrfPolicy,
  PHASE_8B_NEW_ENDPOINTS,
  TargetPrincipal,
  policy_keys,
)
from backend.src.web.auth_routes import AuthRuntime, build_auth_blueprint
from backend.src.web.history_routes import build_history_blueprint
from backend.src.web.library_routes import build_library_blueprint
from backend.src.web.owner_routes import build_owner_blueprint
from backend.src.web.person_routes import build_person_blueprint
from backend.src.web.resolve_routes import build_resolve_blueprint
from backend.src.web.system_routes import build_system_blueprint
from backend.src.web.task_routes import build_task_blueprint


def registered_api_routes():
  app = Flask(__name__, static_folder=None)
  runtime = AuthRuntime(service_factory=lambda: None)
  for blueprint in (
    build_history_blueprint(),
    build_owner_blueprint(),
    build_person_blueprint(),
    build_library_blueprint(),
    build_system_blueprint(),
    build_task_blueprint(),
    build_auth_blueprint(runtime=runtime),
    build_resolve_blueprint(),
  ):
    app.register_blueprint(blueprint)

  return frozenset(
    (method, rule.rule)
    for rule in app.url_map.iter_rules()
    if rule.rule.startswith("/api/")
    for method in rule.methods
    if method not in {"HEAD", "OPTIONS"}
  )


class TestAuthorizationPolicyInventory(unittest.TestCase):
  def test_every_registered_api_method_and_path_is_classified_once(self):
    keys = [policy.key for policy in AUTHORIZATION_POLICY]

    self.assertEqual(len(keys), len(set(keys)))
    self.assertEqual(registered_api_routes(), policy_keys())
    self.assertEqual(40, len(keys))

  def test_every_authenticated_unsafe_target_has_a_csrf_policy(self):
    for policy in AUTHORIZATION_POLICY:
      if policy.method in {"POST", "PATCH", "DELETE"} and policy.path != "/api/auth/login":
        with self.subTest(key=policy.key):
          self.assertIn(
            policy.csrf,
            {CsrfPolicy.REQUIRED, CsrfPolicy.SESSION_IF_PRESENT},
          )

  def test_media_download_is_scoped_exactly_like_the_metadata_it_serves(self):
    """The bytes cannot be reachable on weaker terms than the listing.

    An asset id is not a capability.  If the download route were classified
    any wider than the metadata route beside it, the id handed out in a list
    would become a bearer token - which is the one thing Phase 10A's asset id
    docstring says it must never be.
    """
    downloads = {
      ("GET", "/api/library/posts/<platform>/<aweme_id>/assets/<asset_id>/download"),
      ("GET", "/api/library/recordings/<int:recording_id>/assets/<asset_id>/download"),
    }
    listed = {one.key for one in AUTHORIZATION_POLICY}

    self.assertTrue(downloads.issubset(listed))

    for key in downloads:
      policy = next(one for one in AUTHORIZATION_POLICY if one.key == key)
      with self.subTest(key=key):
        ##
        ## The same principal and the same scope as the metadata endpoint one
        ## path segment above it.
        ##
        self.assertEqual(TargetPrincipal.ROLE_SCOPED, policy.target_principal)
        ##
        ## A read, so no CSRF - and deliberately so, because the alternative is
        ## a token in a url that the browser would then put in history.
        ##
        self.assertEqual(CsrfPolicy.EXEMPT, policy.csrf)
        self.assertIn("404", policy.data_scope)

  def test_media_preview_is_scoped_exactly_like_the_download_beside_it(self):
    """Inline delivery is not a weaker door onto the same bytes.

    A preview endpoint that authorized differently from the download endpoint
    would be the easier one to reach, and it is the one whose response a page
    renders rather than saves.
    """
    previews = {
      ("GET", "/api/library/posts/<platform>/<aweme_id>/assets/<asset_id>/preview"),
      ("GET", "/api/library/recordings/<int:recording_id>/assets/<asset_id>/preview"),
    }
    listed = {one.key for one in AUTHORIZATION_POLICY}

    self.assertTrue(previews.issubset(listed))

    for key in previews:
      policy = next(one for one in AUTHORIZATION_POLICY if one.key == key)
      with self.subTest(key=key):
        self.assertEqual(TargetPrincipal.ROLE_SCOPED, policy.target_principal)
        self.assertEqual(CsrfPolicy.EXEMPT, policy.csrf)
        self.assertIn("404", policy.data_scope)

  def test_preview_and_download_are_classified_identically(self):
    ##
    ## Same principal, same scope, same CSRF stance. The two differ in what the
    ## browser does with the bytes, never in who may ask for them.
    ##
    for parent in (
      "/api/library/posts/<platform>/<aweme_id>/assets/<asset_id>",
      "/api/library/recordings/<int:recording_id>/assets/<asset_id>",
    ):
      download = next(
        one for one in AUTHORIZATION_POLICY
        if one.key == ("GET", parent + "/download")
      )
      preview = next(
        one for one in AUTHORIZATION_POLICY
        if one.key == ("GET", parent + "/preview")
      )
      with self.subTest(parent=parent):
        self.assertEqual(download.target_principal, preview.target_principal)
        self.assertEqual(download.data_scope, preview.data_scope)
        self.assertEqual(download.csrf, preview.csrf)

  def test_no_download_route_is_reachable_without_its_parent_resource(self):
    """Every media path names the resource that owns it.

    A route like ``/api/files/<asset_id>`` would authorize on the id alone.
    There must not be one.
    """
    for policy in AUTHORIZATION_POLICY:
      if "/library/" not in policy.path:
        continue
      if "download" not in policy.path and "preview" not in policy.path:
        continue
      with self.subTest(key=policy.key):
        parent = policy.path.split("/assets/")[0]
        self.assertTrue(
          parent.endswith("<aweme_id>") or parent.endswith("<int:recording_id>"),
          "download path must be rooted in a parent resource identity",
        )

  def test_phase_8b_inventory_claims_real_enforcement(self):
    self.assertTrue(BUSINESS_ENDPOINT_ENFORCEMENT_ENABLED)

  def test_persistent_recording_read_is_now_a_real_route(self):
    self.assertEqual(0, len(PHASE_8B_NEW_ENDPOINTS))
    recording = next(
      one for one in AUTHORIZATION_POLICY
      if one.key == ("GET", "/api/library/recordings")
    )
    self.assertEqual(("GET", "/api/library/recordings"), recording.key)
    self.assertEqual(TargetPrincipal.ROLE_SCOPED, recording.target_principal)
    self.assertIn("recordings_for_user", recording.phase_8b_action)


if __name__ == "__main__":
  unittest.main()
