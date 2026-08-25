# Authentication, ownership, roles, and authorization

These are four separate facts:

- Authentication answers **who is making this request**. The browser holds an
  opaque session cookie; the server resolves it once per request.
- Ownership answers **whose resource this is**. Task, downloaded-post, and
  persistent-recording ownership are stored independently of roles.
- Role is a server-side identity fact on `app_user`. The complete vocabulary is
  `user` and `admin`; `admin` includes ordinary user capability.
- Authorization answers **what the authenticated principal may access** by
  combining role with the resource's ownership scope.

`auth_session` never stores role. Session resolution reads the current
`app_user` row on every request, so promotion and demotion take effect for an
existing session on its next request. A disabled account remains unable to
authenticate regardless of role.

## Phase 8A boundary

Phase 8A provides the role schema, operator provisioning, role-aware principal,
reusable `require_role` / `require_admin` helpers, and an authorization policy
inventory. It does **not** apply role enforcement to existing business APIs and
does not add frontend route guards. The presence of a role field must not be
read as completed security isolation.

The canonical, route-complete policy matrix is
`backend/src/auth/policy.py`. Every entry records:

`METHOD | PATH | CURRENT | TARGET PRINCIPAL | DATA SCOPE | CSRF | PHASE 8B ACTION`

A unit test compares that inventory with every registered `/api` method/path;
adding a route without classifying it fails CI.

The target policy groups are:

| Target | Routes / scope |
| --- | --- |
| Public | Login; anonymous-idempotent logout semantics; SPA shell, assets, and compatibility redirects |
| Authenticated user/admin | Current principal, resolve/batch resolve, and task creation |
| Role-scoped shared | Task list/detail and downloaded posts: user owns-only, admin global |
| Admin | Person, owner, history, live probe, system status, and global live observations |
| Phase 8B addition | `GET /api/library/recordings`: user persistent recordings only, admin global |

The deployment health check uses `/`, not `/api/system/status`. The SPA shell
and build assets must remain available without authentication even when the
authentication database is unavailable.

## Operator bootstrap

Accounts are still created by an operator; there is no public registration or
browser role-management API.

```bash
python -m backend.src.auth_cli create-user USERNAME
python -m backend.src.auth_cli create-user USERNAME --role admin
python -m backend.src.auth_cli set-role USERNAME admin
python -m backend.src.auth_cli set-role USERNAME user
```

Existing accounts migrate to `user`. No account is automatically promoted to
administrator; an operator must explicitly run `set-role`.
