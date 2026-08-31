##<<Base>>
import unittest
from unittest.mock import patch

##<<Third-part>>
import server
from backend.src.auth.login_abuse import (
  LOGIN_ABUSE_GUARD_EXTENSION,
  LoginAbuseGuard,
  LoginAttemptOutcome,
)
from backend.src.unit_test.config_fixture import unified_config
from backend.src.web.auth_routes import SESSION_COOKIE_NAME, build_auth_runtime


##
## >>============================= the startup invariant =============================>>
##
##
## This project runs with the database switched off - the container smoke test
## does exactly that, and so does anybody trying it out before configuring
## MySQL.  Authentication is the first feature that cannot work at all without
## a database, which makes it the first one that could plausibly take the whole
## server down with it on boot.
##
## It must not.  A server with no database still resolves links, still downloads
## and still serves the interface; it simply has nobody signed in.  So the auth
## runtime is built lazily and answers "unavailable" when asked, rather than
## refusing to be constructed.
##


class TestAuthenticationDoesNotBlockStartup(unittest.TestCase):
  def test_the_runtime_is_built_even_with_the_database_disabled(self):
    config = unified_config()
    config["database"]["enable"] = False

    runtime = build_auth_runtime(lambda: config)

    self.assertIsNotNone(runtime)

  def test_asking_it_for_a_service_is_unavailable_rather_than_a_crash(self):
    ##
    ## AuthUnavailable is what the routes turn into a 503.  Any other exception
    ## would become a 500, which says "this server is broken" about a server
    ## that is working exactly as configured.
    ##
    from backend.src.auth.errors import AuthUnavailable

    config = unified_config()
    config["database"]["enable"] = False
    runtime = build_auth_runtime(lambda: config)

    with self.assertRaises(AuthUnavailable):
      runtime.service()

  def test_the_cookie_policy_is_read_from_configuration(self):
    config = unified_config()
    config["auth"] = {"session_ttl_seconds": 900, "cookie_secure": True}

    runtime = build_auth_runtime(lambda: config)

    self.assertTrue(runtime.cookie_secure())
    self.assertEqual(900, runtime.session_ttl_seconds())

  def test_a_configuration_without_auth_still_yields_a_usable_runtime(self):
    ##
    ## The config contract requires the section, so this is not the supported
    ## path - but a runtime that raised KeyError while being *built* would turn
    ## a configuration problem into a server that will not start at all.
    ##
    config = unified_config()
    config.pop("auth", None)

    runtime = build_auth_runtime(lambda: config)

    self.assertIsInstance(runtime.cookie_secure(), bool)
    self.assertGreater(runtime.session_ttl_seconds(), 0)

  def test_the_secure_flag_is_not_silently_true_when_unconfigured(self):
    ##
    ## Whichever way this defaults is wrong somewhere, so the value is
    ## configured rather than assumed - and the default is the one that fails
    ## visibly (a cookie that works on http) rather than invisibly (a cookie
    ## the browser silently drops).
    ##
    config = unified_config()
    config.pop("auth", None)

    self.assertFalse(build_auth_runtime(lambda: config).cookie_secure())


class TestTheCookieNameIsStable(unittest.TestCase):
  def test_it_is_the_documented_name(self):
    ##
    ## Renaming this signs everybody out at once, because a browser holding the
    ## old name presents a cookie nothing looks for.
    ##
    self.assertEqual("smsd_session", SESSION_COOKIE_NAME)


class TestLoginAbuseGuardWiring(unittest.TestCase):
  def configured_app(self):
    config = unified_config()
    config["database"]["enable"] = False
    with patch.object(
      server.RecordingRecoveryReconciler,
      "reconcile_once",
      return_value=None,
    ):
      return server.create_app(
        config,
        schema_guard_factory=lambda unused_config: object(),
      )

  def test_application_factory_passes_the_exact_extension_instance_to_auth(self):
    original = server.build_auth_blueprint
    with patch.object(server, "build_auth_blueprint", wraps=original) as build:
      app = self.configured_app()

    guard = app.extensions[LOGIN_ABUSE_GUARD_EXTENSION]
    self.assertIsInstance(guard, LoginAbuseGuard)
    self.assertIs(guard, build.call_args.kwargs["abuse_guard"])

  def test_two_applications_never_share_limiter_state(self):
    first = self.configured_app()
    second = self.configured_app()
    first_guard = first.extensions[LOGIN_ABUSE_GUARD_EXTENSION]
    second_guard = second.extensions[LOGIN_ABUSE_GUARD_EXTENSION]

    self.assertIsNot(first_guard, second_guard)
    first_attempt = first_guard.begin("127.0.0.1", "alice")
    first_guard.finish(first_attempt.ticket, LoginAttemptOutcome.INVALID_CREDENTIALS)
    self.assertEqual(1, first_guard.username_state_size)
    self.assertEqual(0, second_guard.username_state_size)

  def test_lazy_application_build_constructs_no_database_or_configuration_work(self):
    with patch.object(server, "load_config") as load, patch.object(
      server, "LoginAbuseGuard", wraps=LoginAbuseGuard
    ) as guard_factory:
      app = server._new_flask_app(lazy_config=True)

    load.assert_not_called()
    guard_factory.assert_called_once_with()
    self.assertIsInstance(
      app.extensions[LOGIN_ABUSE_GUARD_EXTENSION],
      LoginAbuseGuard,
    )


if __name__ == "__main__":
  unittest.main()
