##<<Base>>
from datetime import datetime

##<<Extension>>
from flask import Blueprint, g, jsonify, request

##<<Third-part>>
from backend.src.auth.credentials import hash_session_token  # noqa: F401  (re-exported for callers)
from backend.src.auth.errors import AuthUnavailable, InvalidCredentials
from backend.src.auth.repository import AuthRepository
from backend.src.auth.service import AuthenticationService
from backend.src.library.baselib import get_dict_attr
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


def _ok(data, status=200):
  return jsonify({"status": "success", "data": data}), status


def _error(message, status):
  ##
  ## The message is always one this module wrote.  An exception's own text can
  ## carry a driver string, a host name or a query, and none of that belongs in
  ## a response to an unauthenticated caller.
  ##
  return jsonify({"status": "error", "code": status, "message": message}), status


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
  ## An allow list of two fields, not the row.  The row carries password_hash,
  ## and a serializer that dumped it would put the hash in every login
  ## response.
  ##
  return {"user_id": user.user_id, "username": user.username}


def build_auth_blueprint(*, runtime: AuthRuntime) -> Blueprint:
  blueprint = Blueprint("auth", __name__, url_prefix="/api")

  @blueprint.before_app_request
  def resolve_current_user():
    """Work out who is making this request, once.

    Establishes identity and stops there.  Nothing is refused here: this phase
    has no authorization, and an anonymous request must still reach its route
    exactly as it did before authentication existed.

    A failure to resolve is also not a refusal - if the database cannot answer,
    the request proceeds as anonymous rather than failing wholesale, because
    every existing endpoint works perfectly well without knowing who is asking.
    """
    g.current_user = None
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
      return
    try:
      g.current_user = runtime.service().resolve_session(token)
    except AuthUnavailable:
      ##
      ## Deliberately swallowed here and nowhere else.  /api/auth/me answers
      ## 503 for this case, because there the question *is* "who am I"; for
      ## every other route the honest answer is that identity is unknown and
      ## nothing depends on it yet.
      ##
      g.current_user = None

  @blueprint.route("/auth/login", methods=["POST"])
  def login():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
      return _error("请求格式不正确", 400)

    username = body.get("username")
    password = body.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
      return _error("请求格式不正确", 400)
    if not username or not password:
      return _error("请求格式不正确", 400)

    try:
      service = runtime.service()
      user = service.authenticate(username, password)
      issued = service.create_session(user.user_id)
    except InvalidCredentials:
      return _error(INVALID_CREDENTIALS_MESSAGE, 401)
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
    return response, 200

  @blueprint.route("/auth/me", methods=["GET"])
  def me():
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
      return _error("未登录", 401)

    try:
      user = runtime.service().resolve_session(token)
    except AuthUnavailable:
      ##
      ## Here the outage matters. "Not signed in" would make every browser
      ## believe it had been logged out by a database hiccup.
      ##
      return _error(UNAVAILABLE_MESSAGE, 503)

    if user is None:
      return _error("未登录", 401)
    return _ok({"user": _serialize(user)})

  @blueprint.route("/auth/logout", methods=["POST"])
  def logout():
    """End the current session.

    Idempotent, and deliberately incurious: a second click, a retried request
    and a cookie for a session that is already gone all end the same way, with
    the same body. Reporting whether anything was actually revoked would say
    whether a token was valid.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
      try:
        runtime.service().revoke_session(token)
      except AuthUnavailable:
        ##
        ## The cookie is cleared regardless. The browser end of signing out
        ## must not depend on the database being reachable.
        ##
        pass

    response = jsonify({"status": "success", "data": None})
    response.delete_cookie(
      SESSION_COOKIE_NAME,
      path="/",
      httponly=True,
      samesite="Strict",
      secure=runtime.cookie_secure(),
    )
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
