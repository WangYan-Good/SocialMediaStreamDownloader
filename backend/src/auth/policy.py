"""Auditable authorization policy for every registered API route."""
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

  _policy("POST", "/api/resolve", "authenticated", P.AUTHENTICATED, "current-user receipt", C.REQUIRED, "enforced"),
  _policy("POST", "/api/resolve/batch", "authenticated", P.AUTHENTICATED, "current-user receipts", C.REQUIRED, "enforced"),

  _policy("POST", "/api/tasks", "authenticated", P.AUTHENTICATED, "create for current user", C.REQUIRED, "enforced"),
  _policy("GET", "/api/tasks", "role scoped", P.ROLE_SCOPED, "user own / admin global", C.EXEMPT, "enforced"),
  _policy("GET", "/api/tasks/<task_id>", "role scoped", P.ROLE_SCOPED, "user own (404 otherwise) / admin global", C.EXEMPT, "enforced"),

  _policy("GET", "/api/library/posts", "role scoped", P.ROLE_SCOPED, "user own / admin global", C.EXEMPT, "enforced"),
  _policy("GET", "/api/library/recordings", "role scoped", P.ROLE_SCOPED, "user own / admin global persistent recordings", C.EXEMPT, "enforced via recordings_for_user/recordings"),
  ##
  ## Media asset discovery. Read-only metadata about what is on disk for one
  ## already-authorized resource - never the bytes, and never a path.
  ##
  ## Scoped exactly like the list endpoints above, and for the same reason: the
  ## scoped database lookup runs before the filesystem is touched at all, so a
  ## refused request cannot be used to probe which files exist on the host.
  ##
  _policy("GET", "/api/library/posts/<platform>/<aweme_id>/assets", "role scoped", P.ROLE_SCOPED, "user own post (404 otherwise) / admin global", C.EXEMPT, "enforced"),
  _policy("GET", "/api/library/recordings/<int:recording_id>/assets", "role scoped", P.ROLE_SCOPED, "user own recording (404 otherwise) / admin global", C.EXEMPT, "enforced"),
  ##
  ## Authorized media delivery. The bytes, on exactly the terms the metadata
  ## endpoint one segment above was served on.
  ##
  ## The parent resource is named in the path on purpose. An asset id is a
  ## stable name for a file, not a capability to read it - a route keyed on the
  ## id alone would authorize whoever holds it, turning a value handed out in a
  ## listing into a bearer token that never expires.
  ##
  ## CSRF exempt because a download is a read. The alternative - a token in the
  ## url - would put a credential into browser history, referrer headers and
  ## any proxy log on the path.
  ##
  _policy("GET", "/api/library/posts/<platform>/<aweme_id>/assets/<asset_id>/download", "role scoped", P.ROLE_SCOPED, "user own post (404 otherwise) / admin global", C.EXEMPT, "enforced"),
  _policy("GET", "/api/library/recordings/<int:recording_id>/assets/<asset_id>/download", "role scoped", P.ROLE_SCOPED, "user own recording (404 otherwise) / admin global", C.EXEMPT, "enforced"),
  _policy("GET", "/api/library/lives", "admin", P.ADMIN, "global live observations", C.EXEMPT, "enforced"),
  _policy("GET", "/api/system/status", "admin", P.ADMIN, "deployment configuration/status summary", C.EXEMPT, "enforced"),

  _policy("GET", "/api/history/owners", "admin", P.ADMIN, "global creator history", C.EXEMPT, "enforced"),
  _policy("GET", "/api/history/owners/<owner_user_id>/sessions", "admin", P.ADMIN, "global creator sessions", C.EXEMPT, "enforced"),
  _policy("PATCH", "/api/history/owners/<owner_user_id>/preference", "admin", P.ADMIN, "global creator preference", C.REQUIRED, "enforced"),
  _policy("POST", "/api/live/probe", "admin", P.ADMIN, "global live observation/probe", C.REQUIRED, "enforced"),
  _policy("GET", "/api/live/probe/<batch_id>", "admin", P.ADMIN, "global probe batch", C.EXEMPT, "enforced"),

  _policy("GET", "/api/owner", "admin", P.ADMIN, "global creator/platform data", C.EXEMPT, "enforced"),
  _policy("GET", "/api/owner/posts", "admin", P.ADMIN, "global creator/platform data", C.EXEMPT, "enforced"),
  _policy("POST", "/api/owner/download", "admin", P.ADMIN, "global legacy creator download workflow", C.REQUIRED, "enforced"),

  _policy("GET", "/api/person", "admin", P.ADMIN, "global person directory", C.EXEMPT, "enforced"),
  _policy("POST", "/api/person", "admin", P.ADMIN, "global person directory", C.REQUIRED, "enforced"),
  _policy("PATCH", "/api/person/<int:person_id>", "admin", P.ADMIN, "global person directory", C.REQUIRED, "enforced"),
  _policy("DELETE", "/api/person/<int:person_id>", "admin", P.ADMIN, "global person directory", C.REQUIRED, "enforced"),
  _policy("GET", "/api/person/<int:person_id>/detail", "admin", P.ADMIN, "global person/account relations", C.EXEMPT, "enforced"),
  _policy("GET", "/api/person/<int:person_id>/works", "admin", P.ADMIN, "global collaboration-derived works", C.EXEMPT, "enforced"),
  _policy("GET", "/api/person/accounts", "admin", P.ADMIN, "global account directory", C.EXEMPT, "enforced"),
  _policy("POST", "/api/person/account", "admin", P.ADMIN, "global account assignment", C.REQUIRED, "enforced"),
  _policy("POST", "/api/person/account/by-link", "admin", P.ADMIN, "global account assignment", C.REQUIRED, "enforced"),
  _policy("POST", "/api/person/assignment", "admin", P.ADMIN, "global person/account assignment", C.REQUIRED, "enforced"),
  _policy("POST", "/api/person/inspect", "admin", P.ADMIN, "global assignment inspection", C.REQUIRED, "enforced"),
  _policy("DELETE", "/api/person/account", "admin", P.ADMIN, "global account assignment", C.REQUIRED, "enforced"),
  _policy("POST", "/api/person/collaboration", "admin", P.ADMIN, "global collaboration graph", C.REQUIRED, "enforced"),
  _policy("DELETE", "/api/person/collaboration", "admin", P.ADMIN, "global collaboration graph", C.REQUIRED, "enforced"),
)

# Kept as a compatibility export for the Phase 8A inventory tests. Every Phase
# 8B endpoint is now registered and belongs in AUTHORIZATION_POLICY itself.
PHASE_8B_NEW_ENDPOINTS = ()

BUSINESS_ENDPOINT_ENFORCEMENT_ENABLED = True


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
