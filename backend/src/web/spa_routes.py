##<<Base>>
from pathlib import Path

##<<Extension>>
from flask import Blueprint, jsonify, send_from_directory
from werkzeug.exceptions import NotFound


##
## Where ``vite build`` leaves the application shell.  The new frontend lives
## beside the legacy one rather than replacing it - see the blueprint below for
## why - so this points into ``frontend/app`` and never into ``frontend/src``.
##
SPA_DIST_DIR = Path(__file__).resolve().parents[3] / "frontend" / "app" / "dist"

##
## The shell itself.  Every client-side route resolves to this one document.
##
INDEX_FILE = "index.html"

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
  if requested.startswith("assets/"):
    return True
  return "." in requested.rsplit("/", 1)[-1]


def build_spa_blueprint(dist_dir=None) -> Blueprint:
  """Serve the Vue application shell under ``/app``.

  Deliberately mounted on a prefix rather than as a global catch-all.  ``/`` is
  still the working product - the legacy interface has features the new one has
  not reached yet - and ``/api`` must keep answering JSON, so a
  ``/<path:path>`` route would break both to serve one.

  The three surfaces therefore coexist:

  * ``/``      - the legacy Jinja interface, unchanged
  * ``/app/*`` - this shell
  * ``/api/*`` - the JSON api both of them use
  """
  ##
  ## Resolved once at build time so every request compares against the same
  ## absolute path, and a relative working directory cannot move the root a
  ## traversal check is measured from.
  ##
  root = Path(dist_dir) if dist_dir is not None else SPA_DIST_DIR
  blueprint = Blueprint("spa", __name__, url_prefix="/app")

  def _send_index():
    index = root / INDEX_FILE
    if not index.is_file():
      ##
      ## Answered rather than raised: the legacy interface and the api are
      ## unaffected by a missing frontend build, and this endpoint saying so
      ## plainly is what keeps that obvious.
      ##
      return (
        jsonify({"status": "error", "message": NOT_BUILT_MESSAGE, "code": 503}),
        503,
      )
    return send_from_directory(root, INDEX_FILE)

  @blueprint.route("", methods=["GET"])
  @blueprint.route("/", methods=["GET"])
  def shell():
    return _send_index()

  @blueprint.route("/<path:requested>", methods=["GET"])
  def shell_or_asset(requested: str):
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
