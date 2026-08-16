# Vue Cutover Readiness and Execution Record

Cutover executed at stage P15 on `feat/legacy-cutover`, based on `develop` at
`6a5d0c9` (P14 merged). The parity audit below remains the evidence that
authorised that action.

This document answers one question: **can `GET /` stop serving the legacy Jinja
interface and start serving the Vue application?**

It is an audit, not a summary of the roadmap. Every row was produced by reading
the code on both sides and following each capability to the effect it actually
has — a database write, a downloaded file, a background thread — rather than to
the button that starts it. Where the two interfaces differ, the difference is
recorded even when it is inconvenient.

Current ownership is now explicit: `GET /` and root deep links serve Vue,
`GET /legacy` and `GET /legacy/` serve the retained Legacy fallback, and
`GET /app/*` temporarily redirects to the equivalent root path. `POST /`
remains the unchanged Legacy compatibility endpoint until P16.

## How to read the status column

| Status | Meaning |
| --- | --- |
| `PARITY` | The Vue interface does the same thing, with the same effect. |
| `SUPERSEDED` | The Vue interface reaches the same goal by a different, deliberate mechanism. Not a gap. |
| `NON_FUNCTIONAL_LEGACY` | The legacy interface appears to offer this, but the code does nothing. Nothing to match. |
| `GAP` | The legacy interface has a real capability the Vue interface does not. |
| `DECISION_REQUIRED` | The capabilities differ in a way that needs a product decision before either can be called correct. |

"Blocking" means: cutting `/` over to Vue would remove a working capability
from users, or silently change what an existing workflow does.

---

## 1. Download submission (legacy home page)

The legacy home page is one text box, a favourite checkbox, a 0–100 slider and a
submit button, wired by `frontend/src/static/js/submit.js`.

### 1.1 Single URL download

| | |
| --- | --- |
| **Legacy evidence** | `frontend/src/static/js/submit.js::processLink` → `POST /` with `{urls, score, favorite}`; `server.py::process_request` → `runtime["dispatcher"].dispatch(...)` |
| **Vue evidence** | `frontend/app/src/views/NewDownloadView.vue`, `src/composables/useNewDownloadFlow.ts` → `POST /api/resolve` then `POST /api/tasks` |
| **Status** | `SUPERSEDED` |
| **Blocking** | No |

The Vue path resolves the pasted text into a receipt first and creates a task
from that receipt. The legacy path hands the raw string to a handler which
follows it itself. Same user goal, stronger mechanism — see 1.7.

### 1.2 Multiple URLs in one submission

| | |
| --- | --- |
| **Legacy evidence** | `submit.js::processLink` — `link.match(/https?:\/\/[^\s]+/g)` returns **every** url in the pasted text, and `submit.js:15-22` posts the whole array as `{urls: [...]}`. `platform_dispatcher.py` iterates the list. |
| **Vue evidence** | Explicit batch mode in `NewDownloadView.vue` → `POST /api/resolve/batch`; `ResourceResolveService.resolve_many()` reuses `extract_urls()`, the installed platform resolver and `ResolveStore`; `useBatchDownloadFlow.ts` reviews/selects results and calls the existing `POST /api/tasks` once per selected receipt. |
| **Status** | `SUPERSEDED` |
| **Blocking** | No |

The multi-resource goal is retained and its unsafe immediate-execution semantics
are replaced deliberately. The user selects batch mode explicitly, the backend
extracts and deduplicates at most 20 links, and expected failures stay on their
own rows without reflecting the failed URL. Every success has its own ordinary
P5 receipt. Posts and live rooms are selected by default; each owner is opt-in
and requires its own whole-catalogue confirmation.

Creation then proceeds in input order through the existing task endpoint. A
failure does not roll back tasks already created, and there is no parent task,
batch task or second task poller: progress remains the Task Centre's job.

**Performance boundary / follow-up.** Batch resolution currently processes at
most 20 resources sequentially. This avoids cross-call shared-state risk, keeps
response ordering natural and applies the lowest pressure to platform
endpoints. The trade-off is that several slow or failing short links can make
network timeouts accumulate linearly. If real usage shows that wait to be a
problem, the next optimisation should be bounded concurrency (at most 2–3
resolves) while restoring results to input order; unbounded fan-out must not be
introduced. The current resolver keeps per-resolution redirect state local and
`ResolveStore` protects receipt writes with its lock, so that direction can be
evaluated without changing the batch contract, but it is not part of P14.

### 1.3 Favourite + score

| | |
| --- | --- |
| **Legacy evidence** | `submit.js::isFavorite` / `::processScoring` → `POST /` `{favorite, score}` → `platform_dispatcher.py:151-152` sets `token.$.score` and `token.$.favorite` → `douyin_live_downloader.py:577-585` `insert_owner_score` / `update_owner_score` → `douyin_live_downloader.py:1036 download_live_stream_by_score()` reads `get_douyin_favorite_live_url()` |
| **Vue evidence** | Creator Account overview → `CreatorPreferenceEditor.vue` → `creators.ts::savePreference()` → `PATCH /api/history/owners/<owner_user_id>/preference` → `OwnerPreferenceService` → guarded parameterised upsert/delete on `favorite_owner`. |
| **Status** | `SUPERSEDED` |
| **Blocking** | No |

This is the most consequential row in the document, and the easiest to
underestimate, because on screen it looks like a checkbox and a slider.

It is a complete business chain:

```
user sets favorite + score on a submission
  → score persisted against the owner (favorite_owner)
  → owner joins the favourite list
  → download_live_stream_by_score() reads that list
  → automated live listening / recording for those owners
```

The Vue interface now manages that persistent account fact directly rather than
requiring another live submission. Only an account already present in
`share_url` may be changed, the platform is fixed server-side to `douyin`,
`score=0` remains a favourite, and cancelling removes only that account's
`favorite_owner` preference. Writes pass the schema guard and use a single
`INSERT ... ON DUPLICATE KEY UPDATE` or a scoped `DELETE`.

After a successful write, the current filtered History page is read again, so
the server remains the displayed authority and an account naturally leaves the
page when it no longer matches. This does not claim a live reconcile contract:
the score-based listener reads the ordered preference list when its entrypoint
builds `ListenerItem`s, but this page does not rebuild a listener already
running.

### 1.4 Clipboard button

| | |
| --- | --- |
| **Legacy evidence** | `frontend/src/static/js/clipboard.js:7` — `navigator.clipboard.readText()`, wired in `index.html:196` |
| **Vue evidence** | None. The Vue input is typed or pasted into normally. |
| **Status** | `GAP` |
| **Blocking** | No |

A convenience with no persistent effect. Recorded so it is not lost, but it does
not belong at the same risk level as 1.3.

### 1.5 Live download from a share link

| | |
| --- | --- |
| **Legacy evidence** | `submit.js` → `POST /` → `douyin_handler.py` → live downloader |
| **Vue evidence** | `POST /api/resolve` → `resource_type === 'live'` → `POST /api/tasks {task_type: 'live_record'}`; also from the creators workspace after a live probe |
| **Status** | `PARITY` |
| **Blocking** | No |

### 1.6 Post download from a share link

| | |
| --- | --- |
| **Legacy evidence** | `submit.js` → `POST /` → `douyin_handler.py` post path |
| **Vue evidence** | resolve → `POST /api/tasks {task_type: 'post_download'}` |
| **Status** | `PARITY` |
| **Blocking** | No |

### 1.7 The root POST security model

| | |
| --- | --- |
| **Legacy evidence** | `server.py::process_request` accepts `{urls: [...]}` and dispatches; each handler follows short links itself |
| **Vue evidence** | `backend/src/web/resolve_routes.py` — host allow list, redirect validation, hop limit, then a receipt redeemed by `POST /api/tasks` |
| **Status** | `SUPERSEDED` |
| **Blocking** | No |

The Vue interface deliberately does not offer the legacy shape. Reintroducing it
for the sake of "api parity" would undo the resolver. `POST /` remains only so
the explicit `/legacy/` fallback can submit during the stabilization period;
the Vue client never calls it.

### 1.8 Non-douyin platforms

| | |
| --- | --- |
| **Legacy evidence** | `backend/src/platform/other/other_handler.py` — the function body is `pass` |
| **Vue evidence** | `POST /api/resolve` refuses hosts outside the allow list |
| **Status** | `NON_FUNCTIONAL_LEGACY` |
| **Blocking** | No |

The legacy interface accepts such a url and does nothing with it. Accepting a
url is not support, and there is no working behaviour here for the Vue interface
to match.

---

## 2. History (legacy) → Creators · Accounts (Vue)

Legacy: `frontend/src/static/js/owner_history.js`, rendered by
`frontend/src/templates/content/history/*`.
Vue: `frontend/app/src/views/CreatorsView.vue` accounts tab,
`src/stores/creators.ts`, `src/components/creators/*`.

Both call the same backend, which is why most of this section is `PARITY`: P10
did not reimplement history, it re-presented it.

| Capability | Legacy evidence | Vue evidence | Status | Blocking |
| --- | --- | --- | --- | --- |
| Owner list | `owner_history.js:128` `GET /api/history/owners` | `src/api/history.ts::listHistoryOwners` | `PARITY` | No |
| Keyword search `q` | `owner_history.js::filterParams` | `history.ts:26` `q` | `PARITY` | No |
| Favourite filter | `filterParams` | `history.ts:27` `favorite` (three-state) | `PARITY` | No |
| Score range | `filterParams` | `history.ts:28-29` `score_min` / `score_max` | `PARITY` | No |
| Last-live window | `filterParams` | `history.ts:30` `last_live_within` | `PARITY` | No |
| User status | `filterParams` | `history.ts:31` `user_status` | `PARITY` | No |
| Sorting | `filterParams` | `history.ts:32-33` `sort` / `order` | `PARITY` | No |
| Server pagination | `filterParams` | `history.ts:34-35`; `creators.ts` uses the server `total` | `PARITY` | No |
| Live sessions | `owner_history.js:346` `GET .../sessions?limit=20` | `history.ts::listOwnerSessions` | `PARITY` | No |
| Live probe submit | `owner_history.js:224` `POST /api/live/probe` | `history.ts::submitLiveProbe` | `PARITY` | No |
| Live probe poll | `owner_history.js:256` `GET /api/live/probe/<id>` | `history.ts::getLiveProbe`, recursive timeout, one read in flight | `PARITY` | No |
| Start recording from history | `owner_history.js:314` — `POST /` `{urls: [share_url], score: 0, favorite: false}` | `creators.ts::startRecording` — resolve → `POST /api/tasks {task_type: 'live_record'}` | `SUPERSEDED` | No |

Two rows deserve a note rather than a tick.

**Probe semantics.** The legacy page read "nothing ticked" as "check the whole
page". The Vue page offers two explicit actions instead. That is a deliberate
behaviour change, not a missing capability: a probe is one real platform
conversation per account.

**Recording from history.** The legacy button reuses the root POST shape with
`score: 0, favorite: false` hard-coded — which is worth noticing in the context
of 1.3, because it means the legacy recording button *cannot* set a favourite
either. The Vue equivalent goes through the resolver. Superseded, not missing.

---

## 3. Posts (legacy) → Creators · Posts (Vue)

Legacy: `frontend/src/static/js/owner_posts.js`.
Vue: creators workspace posts section plus the task centre.

| Capability | Legacy evidence | Vue evidence | Status | Blocking |
| --- | --- | --- | --- | --- |
| Open an owner by url | `owner_posts.js:102` `GET /api/owner?url=` | `creators.ts::openProfile` — resolve first, then `readOwner(resolution.resolved_url)` | `SUPERSEDED` | No |
| Profile details | `owner_posts.js:102` response | `CreatorAccountPanel.vue` profile card | `PARITY` | No |
| Post pagination | `owner_posts.js:134` `GET /api/owner/posts` with cursor | `owners.ts::readOwnerPosts`, `next_cursor` / `has_more`, deduplicated by `aweme_id` | `PARITY` | No |
| Selected post download | `owner_posts.js:365` `POST /api/owner/download` | `owners.ts::startOwnerSelectedDownload` — same endpoint, ids only | `PARITY` | No |
| Whole-catalogue download | same endpoint, `{all: true}` | `owners.ts::startOwnerAllDownload`, behind an explicit confirmation | `PARITY` | No |
| Expired payload cache | legacy reports the failure | `creators.ts` clears the selection and asks for a re-read | `PARITY` | No |
| Download progress | `owner_posts.js:392` polls `GET /api/owner/download/<job_id>` | `task_id` from the same response → task centre | `SUPERSEDED` | No |

**Why the progress row is superseded rather than a gap.** The legacy page polls
a job record that exists only for that page. The same endpoint now also returns
`task_id`, and the unified task service records the work alongside every other
kind. The Vue interface uses that and deliberately does not implement the job
poll — one progress model, not two. The legacy job endpoint is untouched and
still answers.

---

## 4. Person (legacy) → Creators · People (Vue)

Legacy: `frontend/src/static/js/person_manager.js`.
Vue: creators workspace people tab, `src/stores/people.ts`.

| Capability | Legacy evidence | Vue evidence | Status | Blocking |
| --- | --- | --- | --- | --- |
| List people | `person_manager.js:82` `GET /api/person` | `people.ts::listPeople` | `PARITY` | No |
| Create | `person_manager.js:263` `POST /api/person` | `people.ts::createPerson` | `PARITY` | No |
| Edit | `PATCH /api/person/<id>` | `people.ts::updatePerson`, changed fields only | `PARITY` | No |
| Delete | `person_manager.js:131` `DELETE /api/person/<id>` | `people.ts::deletePerson`, behind a confirmation naming what is not deleted | `PARITY` | No |
| Person detail | `person_manager.js:159` `GET /api/person/<id>/detail` | `people.ts::getPersonDetail` | `PARITY` | No |
| Search known accounts | `person_manager.js:316` `GET /api/person/accounts` | `people.ts::searchAccounts` | `PARITY` | No |
| Attach account | `person_manager.js:346` `POST /api/person/account` | `people.ts::attachAccount` | `PARITY` | No |
| Move an attached account | same endpoint (upsert) | same endpoint, behind an explicit "this moves it" confirmation | `PARITY` | No |
| Detach | `person_manager.js:363` `DELETE /api/person/account` | `people.ts::detachAccount` | `PARITY` | No |
| Attach by link | `person_manager.js:299` `POST /api/person/account/by-link` with the raw paste | `people.ts::attachAccountByLink` with `resolution.resolved_url` | `SUPERSEDED` | No |
| Collaboration | `person_manager.js:244` `POST /api/person/collaboration` | `people.ts::addCollaboration`, direction named rather than positional | `PARITY` | No |
| Person works | `person_manager.js:202` `GET /api/person/<id>/works` | `people.ts::getPersonWorks`, shown in the library with an attribution disclaimer | `PARITY` | No |

One Vue-side rule has no legacy counterpart and is worth recording as a
behaviour difference: the Vue interface refuses to attach a second `main`
account to a person, because the folder resolver joins on `role = 'main'` and
takes `LIMIT 1` with no ordering. The legacy page allows it. This is a Vue
restriction that prevents a real defect, not a legacy capability being lost.

---

## 5. Log and Settings (legacy)

| | |
| --- | --- |
| **Legacy evidence** | `frontend/src/templates/index.html:176` — `<p>Log</p>`; `:180` — `<p>Settings</p>`. Sidebar entries at `:98` and `:111`. There is no viewer, no editor and no endpoint behind either. |
| **Vue evidence** | `/system` — database schema state, safe runtime/download/logging summary, built from an explicit whitelist |
| **Status** | `SUPERSEDED` |
| **Blocking** | No |

The legacy sections are headings. The Vue system page is the first
implementation of either idea in this project, and it deliberately stops short
of a log viewer — see `backend/src/web/system_routes.py` and the reasoning in
`backend/src/service/system_status.py`.

---

## 6. Vue supersets and improvements

These are not parity requirements. They are recorded separately so that a
reader comparing the two interfaces does not mistake them for obligations the
legacy side has, and so that a cutover plan can list what is gained as well as
what is at risk.

| Capability | Where | Note |
| --- | --- | --- |
| Unified task centre | `/tasks`, `backend/src/service/task_*` | Every kind of work in one record, with progress and per-item state. The legacy interface has a per-page job poller for owner downloads and nothing at all for the rest. |
| Hardened resolver | `backend/src/web/resolve_routes.py` | Host allow list, redirect validation, hop limit, single-use receipt. The legacy path follows short links inside each handler. |
| Media library | `/library` | An index of downloaded posts, live observations and collaboration associations. No legacy equivalent. |
| Safe system status | `/system` | Database schema state and a whitelisted configuration summary. The legacy sections are headings. |
| Stale-response protection | creators, library, tasks, system, overview stores | Generation tokens and abort controllers across every asynchronous path. The legacy pages write whichever response lands last. |
| Explicit destructive confirmations | whole-catalogue download, person delete, account move | The legacy interface performs the equivalent actions without asking. |
| Safe multi-resource workflow | `/new` batch mode | Resolve-many and per-owner confirmation preserve the goal without immediate legacy dispatch; each task remains independent. |
| Direct creator preferences | Creator Account overview | Known History accounts can persist or remove `favorite_owner` metadata without coupling it to a download submission. |
| Recorded-vs-current language | library and overview | Cached and historical values are labelled as such; the present tense is reserved for a live probe. |

---

## 7. Blocking items

None found in the P14 re-audit.

The two P13 blockers are closed as deliberate supersessions: creator preference
management is independent account metadata, and multi-resource submission is a
receipt-based review-and-create workflow. The clipboard convenience remains a
`GAP`, explicitly non-blocking, and was not expanded into P14.

---

## 8. Production runtime verification

Performed at this stage, because a readiness answer that has never seen the
image start is not an answer.

| Check | Result |
| --- | --- |
| `docker build` on `develop` (`ce7e95e`) | **passes** |
| `docker run` on that same image | **fails — container exits immediately** |
| Root cause | `FileNotFoundError: /app/docs/design/config.yml.example` |

The container entrypoint validates the mounted configuration against the
canonical example before staging it — `scripts/runtime_config.py:55`
(`stage_container_config`) → `:103` (`validate_runtime_config`) — and
`.dockerignore` excluded `docs/`. The image therefore built cleanly and could
never start, which build-only CI could not detect.

**Fix.** One exception in `.dockerignore` for that single file. Verified by
listing the image contents: `/app/docs/design/config.yml.example` is present and
it is the only file under `/app/docs`. The alternative — moving the contract to
a runtime-owned path — was rejected: it has fifteen references across the
runtime, the unit tests, CI, the README and `docs/security.md`, and a second
copy beside the image would be a second source of truth that nothing keeps in
step.

After the fix, with a database-disabled test configuration:

| Smoke check | Result |
| --- | --- |
| container reaches ready | yes, ~4s |
| `GET /` | 200, legacy markup, not the Vue bundle |
| `GET /app/` and all six deep links | 200 |
| `GET /app/assets/<missing>.js` | 404, no index.html fallback |
| `GET /api/system/status` | 200, `success`, `database.state = disabled` |
| `GET /api/tasks?limit=1` | 200 |

This is now part of CI: the image job builds and then runs the image against a
generated safe configuration.

P14 repeated the production gate against image `smsd:p14`. The build completed,
the container reached ready, root still returned legacy markup, `/app/` and all
six deep links returned 200, a missing asset returned 404, and the tasks and
system-status endpoints returned 200 with persistence correctly reported as
disabled.

P15 executed the authorised ownership change and repeated the gate against the
production image:

| P15 smoke check | Result |
| --- | --- |
| `GET /` and six root deep links | 200, Vue shell, no Legacy marker |
| emitted `/assets/*.js` | root path, fetched successfully as JavaScript |
| `GET /legacy` and `/legacy/` | 200, Legacy marker |
| Legacy `/static/js/submit.js` | 200 |
| `GET /app/*` | 302 to safe root equivalent, query preserved |
| missing Vue asset | 404, no shell fallback |
| unknown `/api/*`, `/static/*`, `/legacy/*` | 404, never Vue HTML |
| safe empty `POST /` | 400, compatibility route present, no platform request |
| tasks and system-status APIs | 200, database disabled reported honestly |

If the Vue index is absent, root and Vue deep links return an explicit 503.
They do not fall back automatically, while `/legacy/` remains independently
available. This makes a broken deployment visible without removing the manual
rollback surface.

---

## Decision and execution

```
EXECUTED
```

- **Default UI:** Vue.
- **Legacy fallback:** available at `/legacy/`.
- **Old Vue URLs:** temporary 302 from `/app/*`.
- **Legacy POST:** temporarily retained.

The P13 favourite/score and multi-resource blockers are both closed, no new
blocking gap was found, the full backend and frontend suites pass, and the
production image serves the Legacy entry plus every Vue route. The remaining
clipboard gap is a non-blocking convenience.

The P14 `READY` decision has now been acted on. P15 changes routing ownership
only: no migration, business data, resolver, task model, preference semantics
or downloader changed. Legacy source, static files, dispatcher support and root
POST remain intentional rollback compatibility debt.

After a stabilization period, P16 may audit and retire those surfaces. P15 does
not delete them.
