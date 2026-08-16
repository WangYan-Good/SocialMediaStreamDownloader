# Vue Cutover Runbook

P15 changes default document ownership without changing database schema or
business data. This runbook separates an immediate UI fallback from a code
rollback and records the compatibility debt intentionally retained for the
stabilization period.

## Current routing

| Request | Current owner |
| --- | --- |
| `GET /` | Vue SPA |
| `GET /overview`, `/new`, `/creators`, `/library`, `/tasks`, `/system` | Vue SPA |
| `GET /assets/*` | Vue production bundle |
| `GET /legacy`, `GET /legacy/` | Legacy Jinja fallback |
| `GET /static/*` | Legacy static files |
| `POST /` | Legacy dispatcher compatibility |
| `GET /app[/<path>]` | temporary 302 to the equivalent root path |
| `/api/*` | existing JSON APIs |

The SPA fallback explicitly refuses the `api`, `static`, and `legacy`
namespaces before attempting to read the build directory. Missing scripts and
styles return 404 instead of the Vue index.

## Immediate fallback

If the Vue UI is impaired but the backend is healthy, open `/legacy/`
directly. It uses the retained `/static/*` files and submits through the
temporary Legacy `POST /` endpoint. No database change, migration or downgrade
is required.

A missing Vue `dist/index.html` is deliberately not an automatic fallback:
`GET /` returns 503 so CI and operators can see the deployment failure, while
the manually selected `/legacy/` route remains available.

## Code rollback

To restore P14 root ownership, revert the P15 merge commit or redeploy the last
known-good P14 image. P15 has no schema migration, so do not roll back or modify
database data.

The `/app/*` compatibility responses are 302 rather than 301/308. Browsers
therefore are not instructed to permanently cache the P15 mapping, which keeps
a code rollback viable during stabilization.

## Intentional compatibility debt

The following remain by design, not by omission:

- `/legacy/` and the Legacy Jinja templates;
- root `POST /` and its dispatcher path;
- `/static/*` and `frontend/src/**`;
- Legacy-only compatibility/job APIs still used by the fallback;
- temporary `/app/*` redirects.

The Vue client must continue using `/api/resolve`, `/api/resolve/batch`, opaque
receipts and `/api/tasks`; it must never call root POST.

## P16 boundary

After P15 has run stably, P16 Legacy Retirement / Cleanup may audit callers and
then decide whether to remove the fallback, root POST, Legacy source/static,
dispatcher paths and Legacy-only APIs, and whether `/app/*` should become
permanent or disappear. None of those removals belongs in P15.
