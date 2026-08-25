"""Auditable target authorization policy for every registered API route.

This inventory describes Phase 8B's target. It is deliberately data only:
Phase 8A does not apply these policies to business routes.
"""
from dataclasses import dataclass
from enum import Enum


class TargetPrincipal(str, Enum):
  PUBLIC = "public"
  SESSION_AWARE = "session_aware"
  AUTHENTICATED = "authenticated_user_or_admin"
  ROLE_SCOPED = "role_scoped_user_or_admin"
  ADMIN = "admin"


class CsrfPolicy(str, Enum):
  EXEMPT = "exempt"
  REQUIRED = "required"
  SESSION_IF_PRESENT = "required_if_session_cookie_present"


@dataclass(frozen=True)
class EndpointPolicy:
  method: str
  path: str
  current: str
  target_principal: TargetPrincipal
  data_scope: str
  csrf: CsrfPolicy
  phase_8b_action: str

  @property
  def key(self):
    return self.method, self.path


def _policy(method, path, current, target, scope, csrf, action):
  return EndpointPolicy(method, path, current, target, scope, csrf, action)


P = TargetPrincipal
C = CsrfPolicy

# One entry per explicit /api method/path registered by the Flask application.
AUTHORIZATION_POLICY = (
  _policy("POST", "/api/auth/login", "public", P.PUBLIC, "-", C.EXEMPT, "unchanged"),
  _policy("GET", "/api/auth/me", "authenticated", P.AUTHENTICATED, "current principal", C.EXEMPT, "unchanged"),
  _policy("POST", "/api/auth/logout", "session-aware", P.SESSION_AWARE, "current browser session", C.SESSION_IF_PRESENT, "unchanged"),

  _policy("POST", "/api/resolve", "public", P.AUTHENTICATED, "server-issued receipt", C.REQUIRED, "require authenticated + CSRF"),
  _policy("POST", "/api/resolve/batch", "public", P.AUTHENTICATED, "server-issued receipts", C.REQUIRED, "require authenticated + CSRF"),

  _policy("POST", "/api/tasks", "anonymous allowed; conditional CSRF", P.AUTHENTICATED, "create for current user", C.REQUIRED, "require authenticated; preserve ownership"),
  _policy("GET", "/api/tasks", "public global", P.ROLE_SCOPED, "user own / admin global", C.EXEMPT, "select list_tasks_for_user or list_tasks by role"),
  _policy("GET", "/api/tasks/<task_id>", "public global", P.ROLE_SCOPED, "user own (404 otherwise) / admin global", C.EXEMPT, "select get_task_for_user or get_task by role"),

  _policy("GET", "/api/library/posts", "public global", P.ROLE_SCOPED, "user own / admin global", C.EXEMPT, "select posts_for_user or posts by role"),
  _policy("GET", "/api/library/lives", "public global", P.ADMIN, "global live observations", C.EXEMPT, "require admin; user library moves to persistent recordings"),
  _policy("GET", "/api/system/status", "public", P.ADMIN, "deployment configuration/status summary", C.EXEMPT, "require admin; do not use as health probe"),

  _policy("GET", "/api/history/owners", "public global", P.ADMIN, "global creator history", C.EXEMPT, "require admin"),
  _policy("GET", "/api/history/owners/<owner_user_id>/sessions", "public global", P.ADMIN, "global creator sessions", C.EXEMPT, "require admin"),
  _policy("PATCH", "/api/history/owners/<owner_user_id>/preference", "public", P.ADMIN, "global creator preference", C.REQUIRED, "require admin + CSRF"),
  _policy("POST", "/api/live/probe", "public", P.ADMIN, "global live observation/probe", C.REQUIRED, "require admin + CSRF"),
  _policy("GET", "/api/live/probe/<batch_id>", "public", P.ADMIN, "global probe batch", C.EXEMPT, "require admin"),

  _policy("GET", "/api/owner", "public", P.ADMIN, "global creator/platform data", C.EXEMPT, "require admin"),
  _policy("GET", "/api/owner/posts", "public", P.ADMIN, "global creator/platform data", C.EXEMPT, "require admin"),
  _policy("POST", "/api/owner/download", "public", P.ADMIN, "global legacy creator download workflow", C.REQUIRED, "require admin + CSRF"),

  _policy("GET", "/api/person", "public global", P.ADMIN, "global person directory", C.EXEMPT, "require admin"),
  _policy("POST", "/api/person", "public", P.ADMIN, "global person directory", C.REQUIRED, "require admin + CSRF"),
  _policy("PATCH", "/api/person/<int:person_id>", "public", P.ADMIN, "global person directory", C.REQUIRED, "require admin + CSRF"),
  _policy("DELETE", "/api/person/<int:person_id>", "public", P.ADMIN, "global person directory", C.REQUIRED, "require admin + CSRF"),
  _policy("GET", "/api/person/<int:person_id>/detail", "public global", P.ADMIN, "global person/account relations", C.EXEMPT, "require admin"),
  _policy("GET", "/api/person/<int:person_id>/works", "public global", P.ADMIN, "global collaboration-derived works", C.EXEMPT, "require admin"),
  _policy("GET", "/api/person/accounts", "public global", P.ADMIN, "global account directory", C.EXEMPT, "require admin"),
  _policy("POST", "/api/person/account", "public", P.ADMIN, "global account assignment", C.REQUIRED, "require admin + CSRF"),
  _policy("POST", "/api/person/account/by-link", "public", P.ADMIN, "global account assignment", C.REQUIRED, "require admin + CSRF"),
  _policy("POST", "/api/person/assignment", "public", P.ADMIN, "global person/account assignment", C.REQUIRED, "require admin + CSRF"),
  _policy("POST", "/api/person/inspect", "public", P.ADMIN, "global assignment inspection", C.REQUIRED, "require admin + CSRF"),
  _policy("DELETE", "/api/person/account", "public", P.ADMIN, "global account assignment", C.REQUIRED, "require admin + CSRF"),
  _policy("POST", "/api/person/collaboration", "public", P.ADMIN, "global collaboration graph", C.REQUIRED, "require admin + CSRF"),
  _policy("DELETE", "/api/person/collaboration", "public", P.ADMIN, "global collaboration graph", C.REQUIRED, "require admin + CSRF"),
)

# Phase 8B must introduce this resource endpoint; it is not part of the current
# route-inventory equality until the route actually exists.
PHASE_8B_NEW_ENDPOINTS = (
  _policy(
    "GET",
    "/api/library/recordings",
    "not registered",
    P.ROLE_SCOPED,
    "user own persistent recordings / admin global persistent recordings",
    C.EXEMPT,
    "add endpoint; select recordings_for_user or recordings by role",
  ),
)

BUSINESS_ENDPOINT_ENFORCEMENT_ENABLED = False


def policy_keys():
  return frozenset(policy.key for policy in AUTHORIZATION_POLICY)


__all__ = [
  "AUTHORIZATION_POLICY",
  "BUSINESS_ENDPOINT_ENFORCEMENT_ENABLED",
  "CsrfPolicy",
  "EndpointPolicy",
  "PHASE_8B_NEW_ENDPOINTS",
  "TargetPrincipal",
  "policy_keys",
]
