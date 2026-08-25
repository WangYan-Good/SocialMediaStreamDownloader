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

## Enforced backend boundary

The backend enforces role and ownership on every business API. Frontend route
guards and role-based navigation remain UX work; they are not a security
boundary.

The canonical, route-complete policy matrix is
`backend/src/auth/policy.py`. Every entry records:

`METHOD | PATH | CURRENT | PRINCIPAL | DATA SCOPE | CSRF | ENFORCEMENT`

A unit test compares that inventory with every registered `/api` method/path;
adding a route without classifying it fails CI.

The actual policy groups are:

| Target | Routes / scope |
| --- | --- |
| Public | Login; anonymous-idempotent logout semantics; SPA shell, assets, and compatibility redirects |
| Authenticated user/admin | Current principal, resolve/batch resolve, and task creation |
| Role-scoped shared | Task list/detail, downloaded posts, and persistent recordings: user owns-only, admin global |
| Admin | Person, owner, history, live probe, system status, and global live observations |

Resolve receipts are process-local and bound to the `app_user` that created
them. A receipt owned by another user is indistinguishable from an unknown or
expired receipt. User Task and Post responses use explicit safe serializers;
recording responses never expose `output_path`.

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
