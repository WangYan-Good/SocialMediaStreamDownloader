##<<Base>>
from pathlib import Path

##<<Extension>>
from flask import Blueprint, jsonify, redirect, request, send_from_directory
from werkzeug.exceptions import NotFound


##
## Where ``vite build`` leaves the application shell.  P16 removed the old
## ``frontend/src`` tree; the runtime serves only this production bundle.
##
SPA_DIST_DIR = Path(__file__).resolve().parents[3] / "frontend" / "app" / "dist"

##
## The shell itself.  Every client-side route resolves to this one document.
##
INDEX_FILE = "index.html"

##
## These namespaces belong to other Flask surfaces.  The check happens before
## any dist lookup so an accidentally emitted ``dist/api/...`` file can never
## impersonate an API response. ``static`` and ``legacy`` remain retired
## namespace tombstones: deleting their old Flask routes must never turn them
## into Vue client routes.
## ``app`` is handled separately as a temporary compatibility redirect.
##
RESERVED_PREFIXES = frozenset(("api", "static", "legacy"))

##
## What a checkout that has never built the frontend is told.  A 404 would read
## as "wrong url" when the url is right and the build output is simply absent,
## which is a one-command fix if the answer says which command.
##
NOT_BUILT_MESSAGE = (
  "前端尚未构建，请在 frontend/app 下执行 npm ci && npm run build"
)


def _is_asset_request(requested: str) -> bool:
  """Whether ``requested`` names a file rather than a client-side route.

  A route is a word - ``tasks``, ``new`` - while a build artefact carries an
  extension.  The distinction matters because falling back to the shell for a
  missing script would hand the browser HTML where it asked for JavaScript, and
  that surfaces as a syntax error in a file that is perfectly fine, a long way
  from the missing build output that actually caused it.
  """
  if not requested:
    return False
  if requested == "assets" or requested.startswith("assets/"):
    return True
  return "." in requested.rsplit("/", 1)[-1]


def build_spa_blueprint(dist_dir=None) -> Blueprint:
  """Serve the Vue shell at root without taking another namespace's paths."""
  ##
  ## Resolved once at build time so every request compares against the same
  ## absolute path, and a relative working directory cannot move the root a
  ## traversal check is measured from.
  ##
  root = Path(dist_dir) if dist_dir is not None else SPA_DIST_DIR
  blueprint = Blueprint("spa", __name__)

  def _send_index():
    index = root / INDEX_FILE
    if not index.is_file():
      ##
      ## Root ownership remains Vue even when its deployment is broken.  A
      ## visible 503 is intentional: silently rendering Legacy here would hide
      ## a bad image from both CI and operators.  P16 retired the Legacy
      ## fallback, so recovery now requires an image/code rollback.
      ##
      return (
        jsonify({"status": "error", "message": NOT_BUILT_MESSAGE, "code": 503}),
        503,
      )
    return send_from_directory(root, INDEX_FILE)

  def _redirect_from_app(requested: str = ""):
    ##
    ## Always one leading slash.  In particular, ``/app//evil.example`` must
    ## not produce the protocol-relative ``//evil.example`` form browsers
    ## interpret as an external host.
    ##
    target = "/" + requested.lstrip("/")
    query = request.query_string.decode("latin-1")
    if query:
      target = "{}?{}".format(target, query)
    return redirect(target, code=302)

  @blueprint.route("/", methods=["GET"])
  def shell():
    return _send_index()

  @blueprint.route("/app", methods=["GET"])
  @blueprint.route("/app/", methods=["GET"])
  def old_app_entry():
    return _redirect_from_app()

  @blueprint.route("/app/<path:requested>", methods=["GET"])
  def old_app_path(requested: str):
    return _redirect_from_app(requested)

  ## Werkzeug normally merges a doubled slash with a permanent 308 before a
  ## view runs.  This explicit rule keeps the compatibility contract temporary
  ## and lets our local-target construction handle the security-sensitive form.
  @blueprint.route(
    "/app//<path:requested>", methods=["GET"], merge_slashes=False
  )
  def old_app_double_slash_path(requested: str):
    return _redirect_from_app(requested)

  @blueprint.route("/<path:requested>", methods=["GET"])
  def shell_or_asset(requested: str):
    first_segment = requested.partition("/")[0]
    if first_segment == "app":
      return _redirect_from_app(requested[len("app"):])
    if first_segment in RESERVED_PREFIXES:
      raise NotFound()

    ##
    ## ``send_from_directory`` is what makes this safe: it rejects anything that
    ## escapes the directory it was given, so a traversal is a 404 rather than a
    ## file read.  Joining the path by hand and opening it would be the bug this
    ## whole route has to not have.
    ##
    try:
      return send_from_directory(root, requested)
    except NotFound:
      pass

    if _is_asset_request(requested):
      ##
      ## A build artefact that is not there.  Say so, rather than answering with
      ## the shell.
      ##
      raise NotFound()

    ##
    ## A client-side route.  The server has never heard of it and does not need
    ## to: handing back the shell is what lets the router resolve it, which is
    ## what makes a refresh on a deep link work.
    ##
    return _send_index()

  return blueprint
