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
    self.assertEqual(33, len(keys))

  def test_every_authenticated_unsafe_target_has_a_csrf_policy(self):
    for policy in AUTHORIZATION_POLICY:
      if policy.method in {"POST", "PATCH", "DELETE"} and policy.path != "/api/auth/login":
        with self.subTest(key=policy.key):
          self.assertIn(
            policy.csrf,
            {CsrfPolicy.REQUIRED, CsrfPolicy.SESSION_IF_PRESENT},
          )

  def test_phase_8a_inventory_does_not_claim_enforcement(self):
    self.assertFalse(BUSINESS_ENDPOINT_ENFORCEMENT_ENABLED)

  def test_phase_8b_has_one_explicit_persistent_recording_read(self):
    self.assertEqual(1, len(PHASE_8B_NEW_ENDPOINTS))
    recording = PHASE_8B_NEW_ENDPOINTS[0]
    self.assertEqual(("GET", "/api/library/recordings"), recording.key)
    self.assertEqual(TargetPrincipal.ROLE_SCOPED, recording.target_principal)
    self.assertIn("recordings_for_user", recording.phase_8b_action)


if __name__ == "__main__":
  unittest.main()
