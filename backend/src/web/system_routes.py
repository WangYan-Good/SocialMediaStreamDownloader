##>> Test
import os
import sys
sys.path.append(os.getcwd())
##<< Test

## <<Extension>>
from flask import Blueprint, current_app, jsonify

## <<Third-Part>>
from backend.src.library.baselib import get_dict_attr
from backend.src.library.loglib import get_logger
from backend.src.service.system_status import (
  build_safe_config_snapshot,
  describe_database,
)
from backend.src.web.auth_routes import require_admin


##
## Where this application keeps its own safe configuration summary.
##
## Installed on the application rather than kept as a module global for the same
## reason the task and resolve services are: two applications can exist in one
## interpreter - the lazy wsgi app and a test's app - and each must report its
## own settings. A process global here would make one of them describe the
## other, which on this page means describing the wrong server.
##
SYSTEM_CONFIG_KEY = "smsd_system_config"

SCHEMA_GUARD_KEY = "smsd_schema_guard"


def _error(message: str, code: int):
  return jsonify({"status": "error", "message": message, "code": code}), code


def _success(data: dict):
  return jsonify({"status": "success", "code": 200, "data": data}), 200


def install_system_config(app, config) -> dict:
  """Store the publishable summary of one application's configuration.

  The reduction happens here, at install time, so what the application holds is
  already safe. The route below therefore has no full configuration to leak even
  if it tried - the process that had it never handed it over.
  """
  snapshot = build_safe_config_snapshot(config)
  app.extensions[SYSTEM_CONFIG_KEY] = snapshot
  ##
  ## Whether persistence is switched on at all is a separate question from
  ## whether the schema is usable, and the guard only answers the second. Kept
  ## beside the snapshot as a plain boolean rather than as part of it, because
  ## it belongs to the database section of the response.
  ##
  app.extensions[SYSTEM_CONFIG_KEY + "_database_enabled"] = (
    get_dict_attr(config or {}, "$.database.enable") is True
  )
  return snapshot


def build_system_blueprint() -> Blueprint:
  blueprint = Blueprint("system", __name__, url_prefix="/api")

  @blueprint.route("/system/status", methods=["GET"])
  @require_admin
  def system_status():
    ##
    ## GET only, and there is no sibling route that writes. The configuration is
    ## loaded once at startup and held per process, so an endpoint that appeared
    ## to change it would answer "saved" while every worker kept running on the
    ## old values - a worse outcome than having no such endpoint.
    ##
    settings = current_app.extensions.get(SYSTEM_CONFIG_KEY)
    if settings is None:
      ##
      ## The application was built without its system wiring. A server problem,
      ## reported as one, and without naming what was missing.
      ##
      get_logger().error("system status requested before its wiring was installed")
      return _error("系统状态暂时不可用", 503)

    enabled = current_app.extensions.get(
      SYSTEM_CONFIG_KEY + "_database_enabled", False
    )

    ##
    ## A degraded database is one of the two things this page exists to report,
    ## so none of what follows may turn into a failed request: an unreachable
    ## database answers 200 describing itself as unreachable.
    ##
    snapshot = None
    guard = current_app.extensions.get(SCHEMA_GUARD_KEY)
    if guard is not None:
      try:
        ##
        ## Never forced. The guard keeps its own retry window and a probe is a
        ## real round trip; forcing here would turn a refresh button into one
        ## probe per click.
        ##
        snapshot = guard.refresh()
      except Exception as e:
        ##
        ## Logged in full, reported as "unknown". Whatever the probe raised may
        ## name a host or carry a driver message, and neither belongs here.
        ##
        get_logger().warning("system status could not read the schema guard: {}".format(e))
        snapshot = None

    return _success(
      {
        "database": describe_database(enabled=enabled, snapshot=snapshot),
        "settings": settings,
      }
    )

  return blueprint
