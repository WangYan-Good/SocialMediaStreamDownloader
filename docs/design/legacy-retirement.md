# P16 Legacy Retirement Record

P16 retires the public Legacy Flask/Jinja interface without rewriting the
modern task architecture. This is a surface retirement: internal components
are removed only when the caller audit proves that no modern path uses them.

## Final public contract

| Request or capability | P16 state |
| --- | --- |
| `GET /` and root deep links | Vue SPA |
| `GET /legacy`, `/legacy/*` | 404 tombstone, never Vue fallback |
| `GET /static`, `/static/*` | 404 tombstone, never Vue fallback |
| `POST /` | 405; no replacement or redirect |
| `GET /app[/<path>]` | retained temporary 302 to the root equivalent |
| `POST /api/owner/download` | returns `{ "task_id": string \| null }` |
| `GET /api/owner/download/<job_id>` | route not registered |
| `POST /api/live/probe`, `GET /api/live/probe/<batch_id>` | retained |

The Flask application is constructed with `static_folder=None` and
`template_folder=None`. This makes the retired routes absent rather than
pointing them at deleted directories. `static` and `legacy` remain reserved in
the SPA catch-all so route deletion cannot accidentally convert them into
successful Vue deep links.

## Caller audit and disposition

| Component or surface | Observed caller before P16 | Modern caller | P16 action | Reason |
| --- | --- | --- | --- | --- |
| `frontend/src/**` | Flask Legacy templates/static routes | none | `REMOVE` | Public Legacy UI only |
| `/legacy*` | manual Legacy fallback | none | `REMOVE_ROUTE`, retain 404 tombstone | Vue is the sole UI |
| `/static*` | Legacy templates | none | `REMOVE_ROUTE`, retain 404 tombstone | Legacy assets removed |
| root `POST /` | `submit.js`, `owner_history.js` | none | `REMOVE` | Retires raw-URL dispatcher trust model |
| `PlatformDispatcher` | root `POST /` | none | `REMOVE` | No remaining production caller |
| `douyin_handler` / `other_handler` | `PlatformDispatcher` | none | `REMOVE` | Dispatcher-only handlers |
| `DirectPostDownloadTaskService` | `/api/tasks` through `TaskCreationService` | yes | `KEEP_MODERN` | Receipt-backed post tasks |
| `LiveRecordingTaskService` | `/api/tasks` through `TaskCreationService` | yes | `KEEP_MODERN` | Receipt-backed live tasks |
| owner GET job polling route | Legacy `owner_posts.js` | none | `REMOVE_ROUTE` | Vue tracks the returned task in Task Center |
| `JobStore` | owner download service | yes, internal | `KEEP_INTERNAL` | Owns current owner-job execution state |
| `PostDownloadJobService` | owner download POST | yes | `KEEP_MODERN` | Current owner batch executor |
| `OwnerTaskMirror` | owner download service | yes | `KEEP_MODERN` | Mirrors internal job progress to unified tasks |
| internal `job_id` | store/service/mirror correlation | yes, internal | `KEEP_INTERNAL` | Not a public identifier after P16 |
| task metadata `legacy_job_id` | mirror correlation and diagnostics | yes, internal | `KEEP_INTERNAL` | Metadata migration is outside P16 |
| live probe polling | Vue Creators flow | yes | `KEEP_MODERN` | Unrelated modern capability |
| `/app/*` redirect | old Vue bookmarks | yes, compatibility | `KEEP_TEMPORARY` | Separate from Legacy UI retirement |

The owner POST response deliberately exposes no `job_id`. Its nullable
`task_id` is the only public tracking handle. Internally, the service still
creates a job, stores it in `JobStore`, correlates it through
`OwnerTaskMirror`, and records `legacy_job_id` in task metadata. P16 does not
introduce a second execution model or migrate task metadata.

## Retired-test ledger

P15 collected 1,919 Python tests. P16 retires 93 obsolete test functions and
adds/replaces 13 retirement assertions; the verified net change is -80 and the
final count is 1,839. Test count is evidence here, not a target.

| Change | Count | Replacement or reason |
| --- | ---: | --- |
| delete direct-post dispatcher tests | -17 | modern `TaskCreationService` post tests retained |
| delete Douyin handler routing tests | -37 | resolver + receipt + task creation tests retained |
| delete live dispatcher tests | -11 | modern live task service tests retained |
| delete Legacy page reachability tests | -3 | SPA retirement/tombstone tests replace them |
| simplify server wiring tests | -9 net | schema guard, per-app modern runners, lazy WSGI and shutdown remain |
| replace SPA coexistence assertions | +1 net | root Vue, 404 tombstones, no static endpoint, POST 405 |
| replace owner public job polling assertions | -2 net | exact POST schema + URL-map absence; internal job/mirror suites remain |
| remove obsolete root-POST assertions elsewhere | -2 | root POST 405 is asserted at the routing boundary |
| **Net Python change** | **-80** | **1,919 → 1,839** |

The Vue suite changes from 810 to 809 passing tests: two sidebar fallback
behaviour tests become one stronger absence assertion. Owner API fixtures and
types also prove that `job_id` is no longer part of the browser contract.

Important retained suites cover `JobStore`, `PostDownloadJobService`,
`OwnerTaskMirror`, direct post task creation, live recording task creation and
live probe polling. Tests whose names mention `legacy_job_id` remain because
they describe internal correlation debt, not the retired public surface.

## Production evidence

CI builds and starts the production image with database and real transfers
disabled, then verifies the route matrix above. It additionally executes:

```bash
docker exec smsd-ci-smoke test ! -d /app/frontend/src
```

and equivalent absence checks for the retired dispatcher modules. This proves
retirement in the shipped filesystem, not merely in a source grep.

## Recovery boundary

A missing Vue bundle still makes root and Vue deep links return 503. There is
no automatic or manual in-image Legacy fallback after P16. Recovery means
deploying a known-good image or reverting the P16 change. P16 contains no
database migration, so database rollback is neither required nor appropriate.
