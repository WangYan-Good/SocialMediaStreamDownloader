# Vue Cutover and P16 Recovery Runbook

P15 made Vue the default document. P16 retires the public Legacy interface and
its raw-URL dispatcher without changing database schema or business data.

## Current routing

| Request | Current owner |
| --- | --- |
| `GET /` | Vue SPA |
| `GET /overview`, `/new`, `/creators`, `/library`, `/tasks`, `/system` | Vue SPA |
| `GET /assets/*` | Vue production bundle |
| `GET /legacy`, `/legacy/*` | retired 404 tombstone |
| `GET /static`, `/static/*` | retired 404 tombstone |
| `POST /` | retired; Flask returns 405 |
| `GET /app[/<path>]` | retained temporary 302 to the equivalent root path |
| `/api/*` | JSON APIs |

The SPA fallback refuses `api`, `static`, and `legacy` before any dist lookup.
Missing scripts and styles return 404 instead of the Vue index. The old owner
job polling route is no longer registered; owner download creation exposes a
Task Center `task_id` only.

## Runtime failure and recovery

If `frontend/app/dist/index.html` is absent, `GET /` and Vue deep links return
503. They never fall back to a retired page. Operators should inspect the image
build/deployment and deploy a known-good image.

To undo P16 code, revert its change or redeploy the last known-good P15 image.
P16 has no schema migration, so do not roll back or modify database data. A P15
image restores Legacy code as part of the whole image; the current P16 image
does not contain an emergency `/legacy/` UI.

The `/app/*` responses remain 302 rather than 301/308, so browsers do not cache
this compatibility mapping permanently. `/app/*` is old Vue URL compatibility,
not Legacy UI, and is intentionally retained after P16.

## Retained internal execution

The owner-download internals are not a rollback surface. `JobStore`,
`PostDownloadJobService`, `OwnerTaskMirror`, internal `job_id` correlation and
`legacy_job_id` task metadata remain active behind the public task contract.
Removing or unifying them requires a separate migration and is outside P16.

The complete caller audit and retired-test ledger are in
[`legacy-retirement.md`](legacy-retirement.md).
