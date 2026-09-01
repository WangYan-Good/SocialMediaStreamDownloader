##<<Base>>
from datetime import datetime
from functools import wraps

##<<Extension>>
from flask import Blueprint, g, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

##<<Third-part>>
from backend.src.auth.context import RequestAuthContext, RequestAuthStatus
from backend.src.auth.credentials import hash_session_token  # noqa: F401  (re-exported for callers)
from backend.src.auth.credentials import MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH
from backend.src.auth.csrf import csrf_token_for_session, csrf_tokens_match
from backend.src.auth.errors import AuthUnavailable, InvalidCredentials
from backend.src.auth.login_abuse import (
  LOGIN_MAX_REQUEST_BYTES,
  LoginAbuseGuard,
  LoginAttemptOutcome,
)
from backend.src.auth.roles import ROLE_ADMIN, role_satisfies, validate_role
from backend.src.auth.repository import AuthRepository
from backend.src.auth.service import AuthenticationService
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.database.schema_guard import require_database_write_ready
from backend.src.database.table.share_url import DouyinShareUrlTable


##
## The browser's whole proof of identity.
##
## In a cookie rather than in a response body on purpose: a body would have to
## be stored by the page, and anywhere a page can store it, an XSS can read it.
## A HttpOnly cookie is the one place the page itself cannot reach.
##
SESSION_COOKIE_NAME = "smsd_session"
CSRF_COOKIE_NAME = "smsd_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

##
## One answer for no-such-account, wrong-password and disabled alike.  Any
## difference between them - in the text, the status or the timing - turns
## login into a way of discovering which usernames exist.
##
INVALID_CREDENTIALS_MESSAGE = "用户名或密码错误"

##
## The database is unreachable, or its schema is behind the code.  Deliberately
## not the message above: "I could not check" is not "that was wrong", and
## saying the second sends somebody to reset a password that was never the
## problem.
##
UNAVAILABLE_MESSAGE = "认证服务暂时不可用，请稍后重试"
CSRF_INVALID_MESSAGE = "请求验证失败，请刷新页面后重试"
FORBIDDEN_MESSAGE = "没有权限执行此操作"
RATE_LIMITED_MESSAGE = "登录尝试过于频繁，请稍后重试"
LOGOUT_UNAVAILABLE_MESSAGE = "退出登录暂时无法完成，请稍后重试"


def _ok(data, status=200):
  return jsonify({"status": "success", "data": data}), status


def _error(message, status, *, kind=None):
  ##
  ## The message is always one this module wrote.  An exception's own text can
  ## carry a driver string, a host name or a query, and none of that belongs in
  ## a response to an unauthenticated caller.
  ##
  body = {"status": "error", "code": status, "message": message}
  if kind is not None:
    body["kind"] = kind
  return jsonify(body), status


def request_auth_context() -> RequestAuthContext:
  return getattr(g, "auth_context", RequestAuthContext.anonymous())


_request_auth_context = request_auth_context


def require_authenticated(view):
  """Refuse a view unless this request's one auth resolution succeeded."""

  @wraps(view)
  def authenticated_view(*args, **kwargs):
    context = _request_auth_context()
    if context.status == RequestAuthStatus.UNAVAILABLE:
      return _error(UNAVAILABLE_MESSAGE, 503)
    if context.status != RequestAuthStatus.AUTHENTICATED:
      return _error("未登录", 401)
    return view(*args, **kwargs)

  return authenticated_view


def require_role(required_role):
  """Require a capability from the request's already-resolved principal."""
  required = validate_role(required_role)

  def decorate(view):
    @wraps(view)
    def role_protected_view(*args, **kwargs):
      context = _request_auth_context()
      if context.status == RequestAuthStatus.UNAVAILABLE:
        return _error(UNAVAILABLE_MESSAGE, 503)
      if context.status != RequestAuthStatus.AUTHENTICATED:
        return _error("未登录", 401)
      if not role_satisfies(context.user.role, required):
        return _error(FORBIDDEN_MESSAGE, 403, kind="forbidden")
      return view(*args, **kwargs)

    return role_protected_view

  return decorate


def require_admin(view):
  """Thin ADMIN specialization of ``require_role``."""
  return require_role(ROLE_ADMIN)(view)


def require_session_csrf(view):
  """Require a valid CSRF proof when auth has not disproved the session.

  Anonymous requests pass so logout remains idempotent for missing, expired,
  revoked and unknown sessions.  ``unavailable`` still validates because the
  expected proof was derived before the database lookup and does not depend on
  the backend being healthy.
  """

  @wraps(view)
  def csrf_protected_view(*args, **kwargs):
    context = _request_auth_context()
    if context.status in (
      RequestAuthStatus.AUTHENTICATED,
      RequestAuthStatus.UNAVAILABLE,
    ) and not csrf_tokens_match(
      context.csrf_expected,
      request.headers.get(CSRF_HEADER_NAME),
    ):
      return _error(CSRF_INVALID_MESSAGE, 403, kind="csrf_invalid")
    return view(*args, **kwargs)

  return csrf_protected_view


def require_authenticated_csrf(view):
  """Thin composition for an authenticated state-changing endpoint."""
  return require_authenticated(require_session_csrf(view))


def require_admin_csrf(view):
  """Thin composition for an ADMIN state-changing endpoint."""
  return require_admin(require_session_csrf(view))


def _set_csrf_cookie(response, token, runtime):
  response.set_cookie(
    CSRF_COOKIE_NAME,
    token,
    max_age=runtime.session_ttl_seconds(),
    httponly=False,
    samesite="Strict",
    secure=runtime.cookie_secure(),
    path="/",
  )


def _clear_auth_cookies(response, runtime):
  response.delete_cookie(
    SESSION_COOKIE_NAME,
    path="/",
    httponly=True,
    samesite="Strict",
    secure=runtime.cookie_secure(),
  )
  response.delete_cookie(
    CSRF_COOKIE_NAME,
    path="/",
    httponly=False,
    samesite="Strict",
    secure=runtime.cookie_secure(),
  )


class AuthRuntime:
  """Assembles the authentication service against the live database.

  Everything is resolved on use, never at construction.  The application is
  built with configuration deliberately unread - see ``lazy_config`` in
  server.py - so a runtime that loaded settings in its constructor would make
  importing the server fail on a configuration problem, long before anything
  had a chance to report it usefully.
  """

  def __init__(self, *, service_factory, settings_provider=None):
    self._service_factory = service_factory
    self._settings_provider = settings_provider
    self._settings = None

  def _config(self) -> dict:
    if self._settings is None and self._settings_provider is not None:
      self._settings = self._settings_provider()
    return self._settings or {}

  def service(self):
    return self._service_factory()

  def cookie_secure(self) -> bool:
    return _cookie_secure_of(self._config())

  def session_ttl_seconds(self) -> int:
    return _ttl_of(self._config())


def _serialize(user) -> dict:
  ##
  ## An allow list of identity fields, not the row. The row carries password_hash,
  ## and a serializer that dumped it would put the hash in every login
  ## response.
  ##
  return {
    "user_id": user.user_id,
    "username": user.username,
    "role": user.role,
  }


def build_auth_blueprint(
  *,
  runtime: AuthRuntime,
  abuse_guard: LoginAbuseGuard,
) -> Blueprint:
  blueprint = Blueprint("auth", __name__, url_prefix="/api")

  @blueprint.before_app_request
  def resolve_request_authentication():
    """Work out who is making this request, once.

    Establishes identity and role, then stops. Individual routes consume this
    one context through the authorization helpers; no route resolves the
    session a second time.

    A failure to resolve is retained as the distinct ``unavailable`` state so
    protected routes fail closed with 503 instead of guessing a scope.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
      g.auth_context = RequestAuthContext.anonymous()
      return
    csrf_expected = csrf_token_for_session(token)
    try:
      user = runtime.service().resolve_session(token)
    except AuthUnavailable:
      ##
      ## Deliberately swallowed here and nowhere else.  /api/auth/me answers
      ## 503 for this case, because there the question *is* "who am I"; the
      ## explicit context keeps other routes from mistaking an outage for a
      ## confirmed anonymous request.
      ##
      g.auth_context = RequestAuthContext.unavailable(
        csrf_expected=csrf_expected
      )
      return
    if user is None:
      g.auth_context = RequestAuthContext.anonymous(
        csrf_expected=csrf_expected
      )
      return
    g.auth_context = RequestAuthContext.authenticated(
      user,
      csrf_expected=csrf_expected,
    )

  @blueprint.after_app_request
  def repair_authenticated_csrf_cookie(response):
    context = _request_auth_context()
    if context.status != RequestAuthStatus.AUTHENTICATED:
      return response
    if getattr(g, "auth_cookies_managed", False):
      return response
    received = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf_tokens_match(context.csrf_expected, received):
      _set_csrf_cookie(response, context.csrf_expected, runtime)
    return response

  @blueprint.route("/auth/login", methods=["POST"])
  def login():
    # This is a route-local limit. Other upload and media routes retain their
    # own contracts, while an unauthenticated login can never make Flask read
    # an unbounded request body into memory.
    request.max_content_length = LOGIN_MAX_REQUEST_BYTES
    try:
      body = request.get_json(silent=True)
    except RequestEntityTooLarge:
      return _error("请求体过大", 413, kind="request_too_large")
    if not isinstance(body, dict):
      return _error("请求格式不正确", 400)

    username = body.get("username")
    password = body.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
      return _error("请求格式不正确", 400)
    if not username or not password:
      return _error("请求格式不正确", 400)

    decision = abuse_guard.begin(request.remote_addr, username)
    if not decision.allowed:
      response = jsonify({
        "status": "error",
        "code": 429,
        "message": RATE_LIMITED_MESSAGE,
        "kind": "rate_limited",
      })
      response.headers["Retry-After"] = str(decision.retry_after_seconds)
      # Suppress the global CSRF repair hook too. A refusal must never create
      # either authentication cookie, even if the caller sent an old session.
      g.auth_cookies_managed = True
      return response, 429

    if (
      len(username) > MAX_USERNAME_LENGTH
      or len(password) > MAX_PASSWORD_LENGTH
    ):
      abuse_guard.finish(
        decision.ticket,
        LoginAttemptOutcome.INVALID_CREDENTIALS,
      )
      return _error(INVALID_CREDENTIALS_MESSAGE, 401)

    try:
      service = runtime.service()
      user = service.authenticate(username, password)
    except InvalidCredentials:
      abuse_guard.finish(
        decision.ticket,
        LoginAttemptOutcome.INVALID_CREDENTIALS,
      )
      return _error(INVALID_CREDENTIALS_MESSAGE, 401)
    except AuthUnavailable:
      abuse_guard.finish(decision.ticket, LoginAttemptOutcome.NEUTRAL)
      return _error(UNAVAILABLE_MESSAGE, 503)
    except BaseException:
      abuse_guard.finish(decision.ticket, LoginAttemptOutcome.NEUTRAL)
      raise
    else:
      abuse_guard.finish(decision.ticket, LoginAttemptOutcome.SUCCESS)

    try:
      issued = service.create_session(user.user_id)
    except AuthUnavailable:
      return _error(UNAVAILABLE_MESSAGE, 503)

    response = jsonify({"status": "success", "data": {"user": _serialize(user)}})
    response.set_cookie(
      SESSION_COOKIE_NAME,
      issued.token,
      max_age=runtime.session_ttl_seconds(),
      ##
      ## The page's own script cannot read this.
      ##
      httponly=True,
      ##
      ## Strict: the browser will not attach this cookie to a request another
      ## origin caused. With cookie authentication that is the first line
      ## against CSRF - see the note in the phase report about why it is not
      ## the last one.
      ##
      samesite="Strict",
      ##
      ## Configured, never assumed. Secure on plain HTTP means the browser
      ## silently drops the cookie and login appears to do nothing at all;
      ## missing in production means the session travels in clear text.
      ##
      secure=runtime.cookie_secure(),
      path="/",
    )
    _set_csrf_cookie(response, csrf_token_for_session(issued.token), runtime)
    g.auth_cookies_managed = True
    return response, 200

  @blueprint.route("/auth/me", methods=["GET"])
  @require_authenticated
  def me():
    return _ok({"user": _serialize(_request_auth_context().user)})

  @blueprint.route("/auth/logout", methods=["POST"])
  @require_session_csrf
  def logout():
    """End the current session.

    Idempotent, and deliberately incurious: a second click, a retried request
    and a cookie for a session that is already gone all end the same way, with
    the same body. Reporting whether anything was actually revoked would say
    whether a token was valid.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    context = _request_auth_context()
    if token and context.status in (
      RequestAuthStatus.AUTHENTICATED,
      RequestAuthStatus.UNAVAILABLE,
    ):
      try:
        runtime.service().revoke_session(token)
      except AuthUnavailable:
        get_logger().warning("logout revocation unavailable")
        ##
        ## This response must leave the browser credential pair untouched.
        ## In particular, suppress the after-request CSRF repair hook: an
        ## authenticated request with a missing or stale readable cookie must
        ## not turn a failed revoke into any Set-Cookie mutation.
        ##
        g.auth_cookies_managed = True
        return _error(
          LOGOUT_UNAVAILABLE_MESSAGE,
          503,
          kind="logout_unavailable",
        )

    response = jsonify({"status": "success", "data": None})
    if token:
      ##
      ## A cross-site request does not carry a Strict session cookie.  Do not
      ## answer that cookie-less request with a deletion cookie: doing so could
      ## turn an anonymous, idempotent endpoint into forced browser logout.
      ## Unknown or expired credentials *are* sent on same-site requests and
      ## may still be cleaned up because ``token`` is present.
      ##
      _clear_auth_cookies(response, runtime)
    g.auth_cookies_managed = True
    return response, 200

  return blueprint


##
## Defaults, used only when the configuration does not say.
##
## The contract requires the section, so this is not the supported path - but a
## runtime that raised while being *built* would turn a configuration problem
## into a server that refuses to start, and authentication is not important
## enough to take the download service down with it.
##
DEFAULT_SESSION_TTL_SECONDS = 604800

##
## False rather than True when unconfigured.  Whichever way this defaults is
## wrong somewhere, so it is configured - and the default is the one that fails
## visibly (a cookie that works over http, which a reviewer notices) rather
## than invisibly (a Secure cookie the browser silently discards over http,
## which looks like login being broken for no reason).
##
DEFAULT_COOKIE_SECURE = False


def build_auth_runtime(settings_provider) -> AuthRuntime:
  """Assemble the authentication runtime from configuration.

  Lazily: nothing here touches the database.  A deployment with the database
  switched off - the container smoke test does exactly that - must still start
  and serve everything that does not need one, and simply have nobody signed
  in.  The database is reached on the first login attempt, and answers
  ``AuthUnavailable`` if it cannot be.
  """

  def service_factory():
    settings = settings_provider()
    if get_dict_attr(settings, "$.database.enable") is not True:
      raise AuthUnavailable("authentication requires the database")

    ##
    ## The same gate every other write goes through.  A schema behind the code
    ## has no app_user table to read, and authentication must not be the one
    ## caller that decides the guard does not apply to it.
    ##
    try:
      require_database_write_ready()
    except Exception as e:
      raise AuthUnavailable("authentication schema is not ready") from e

    try:
      database = DouyinShareUrlTable(
        host=get_dict_attr(settings, "$.database.host"),
        user=get_dict_attr(settings, "$.database.username"),
        passwd=get_dict_attr(settings, "$.database.password"),
        database=get_dict_attr(settings, "$.database.name"),
      )
    except Exception as e:
      raise AuthUnavailable("authentication storage is unavailable") from e

    ttl = _ttl_of(settings_provider())
    return AuthenticationService(
      AuthRepository(database), session_ttl_seconds=ttl
    )

  ##
  ## No settings are read here.  See AuthRuntime: construction must not depend
  ## on configuration being loadable, or an invalid config.yml stops the server
  ## from importing rather than from serving.
  ##
  return AuthRuntime(
    service_factory=service_factory,
    settings_provider=settings_provider,
  )


def _ttl_of(settings) -> int:
  value = get_dict_attr(settings, "$.auth.session_ttl_seconds")
  try:
    ttl = int(value)
  except (TypeError, ValueError):
    return DEFAULT_SESSION_TTL_SECONDS
  return ttl if ttl > 0 else DEFAULT_SESSION_TTL_SECONDS


def _cookie_secure_of(settings) -> bool:
  value = get_dict_attr(settings, "$.auth.cookie_secure")
  if isinstance(value, bool):
    return value
  return DEFAULT_COOKIE_SECURE
