"""Test-only request identity for route tests focused on business behaviour."""
from flask import g
from flask.testing import FlaskClient
from werkzeug.datastructures import Headers

from backend.src.auth.context import RequestAuthContext
from backend.src.auth.roles import ROLE_ADMIN
from backend.src.auth.service import AuthenticatedUser
from backend.src.web.auth_routes import CSRF_HEADER_NAME


TEST_CSRF_PROOF = "test-csrf-proof"
TEST_ADMIN = AuthenticatedUser(user_id=9001, username="test-admin", role=ROLE_ADMIN)


class AuthenticatedTestClient(FlaskClient):
  """Adds the proof used by ``install_test_auth`` to legacy route calls."""

  def open(self, *args, **kwargs):
    headers = Headers(kwargs.pop("headers", None))
    if CSRF_HEADER_NAME not in headers:
      headers[CSRF_HEADER_NAME] = TEST_CSRF_PROOF
    kwargs["headers"] = headers
    return super().open(*args, **kwargs)


def install_test_auth(app, user=TEST_ADMIN):
  """Install an explicit Admin request context without a database session."""
  app.test_client_class = AuthenticatedTestClient

  @app.before_request
  def authenticated_test_request():
    g.auth_context = RequestAuthContext.authenticated(
      user, csrf_expected=TEST_CSRF_PROOF
    )

  return app
