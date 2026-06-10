## Low Level Design Document

v1.0  |  Multi-Person Collaborative Development Edition

| **Field**        | **Value**                                        |
| ---------------- | ------------------------------------------------ |
| Document Version | 1.0                                              |
| Product          | ImagiLab — Gamified Children AI Collaboration OS |
| Tech Stack       | Flutter + FastAPI + Dify + DeepSeek + FLUX       |
| Target Platform  | iOS / Android / iPad                             |
| Author           | Engineering Team                                 |
| Status           | DRAFT — Ready for Development                    |
| Last Updated     | 2026-04-08                                       |

This document provides full low-level design specifications for ImagiLab, covering system architecture, module breakdown, data models, API contracts, interaction logic, and team task assignments. It is intended to be directly actionable for a multi-engineer team.

# 1. System Architecture Overview
## 1.1 Architecture Principles

- Mobile-first, offline-tolerant (asset caching for characters and sounds)
- Async-first backend — all AI calls are queued via Celery, never blocking HTTP
- Stateless API servers — session state lives in Redis, not app memory
- Feature-flagged rollout — L1/L2/L3 modes toggled server-side per user tier
- Multi-tenant ready — each child account is isolated at data layer

## 1.2 High-Level Component Map
CLIENT (Flutter) → API Gateway (FastAPI) → Task Queue (Celery/Redis) → AI Services (Dify / DeepSeek / FLUX) → Object Storage (S3-compatible) → DB (PostgreSQL) → CDN

## 1.3 Layer-by-Layer Responsibilities

| **Layer**             | **Technology**               | **Responsibility**                                                                            |
| --------------------- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| Mobile Client         | Flutter 3.x                  | UI rendering, voice capture, local caching, WebSocket listener, Crew vector animations (Rive) |
| API Gateway           | FastAPI (Python 3.11)        | Auth, routing, request validation, rate limiting                                              |
| Security & Compliance | Aliyun Green / Tencent API   | Mandatory NSFW image detection, text sensitive word filtering, child safety guards            |
| Task Queue& Scheduler | Celery + Redis+ Celery Beat  | Async AI job dispatch, retry logic, result storage, Cron jobs for Pseudo-MiroFish             |
| AI Orchestration      | Dify (self-hosted)           | Prompt chaining, agent routing, Dify Workflow engine                                          |
| LLM — Logic           | DeepSeek API                 | NLU: voice → structured prompt, copy-dog logic                                                |
| Image Gen             | FLUX via Replicate/API       | Text-to-image, style transfer, inpainting                                                     |
| Video Synthesis       | Kling API + FFmpeg + MoviePy | Frame assembly, subtitle burn-in, PDF export                                                  |
| Object Storage        | MinIO / AWS S3               | Generated images, audio uploads, PDF exports                                                  |
| Primary DB            | PostgreSQL 15                | Users, projects, crew data, analytics events, Daily quests                                    |
| Cache / Queue         | Redis 7                      | Session tokens, Celery broker, pub-sub for WS                                                 |
| CDN                   | Cloudflare / Alibaba CDN     | Static assets, character animations, audio packs                                              |
| Business Integration  | WeChat SDK + Stripe/Alipay   | WeChat login, Social sharing (Posters), Subscriptions, Cloud-print routing                    |
| Monitoring            | Prometheus + Grafana         | Latency, queue depth, error rates, API cost tracking (Token usage)                            |

# 2. Module Breakdown & Ownership
Each module maps to one engineering workstream. Assign one lead + one reviewer per module for parallel development.

| **Module ID** | **Module Name**                       | **Owner Role**     | **Dependency** | **Priority** |
| ------------- | ------------------------------------- | ------------------ | -------------- | ------------ |
| MOD-01        | Auth & User Management                | Backend Lead       | None           | P0 — MVP     |
| MOD-02        | Voice Input Pipeline (L1)             | AI Engineer        | MOD-01         | P0 — MVP     |
| MOD-03        | Prompt Processing (DeepSeek NLU)      | AI Engineer        | MOD-02         | P0 — MVP     |
| MOD-04        | Image Generation (FLUX)               | AI Engineer        | MOD-03         | P0 — MVP     |
| MOD-05        | Digital Crew System                   | Frontend + Backend | MOD-01         | P0 — MVP     |
| MOD-06        | Guided Refinement UI (L2)             | Frontend           | MOD-04, MOD-05 | P1           |
| MOD-07        | Visual Workflow Engine (L3 Studio)    | Frontend + Backend | MOD-06         | P2           |
| MOD-08        | Task/Mission System (Pseudo-MiroFish) | Backend + AI       | MOD-01, MOD-03 | P1           |
| MOD-09        | Report & Analytics Engine             | Backend            | All            | P1           |
| MOD-10        | Export & Share (PDF/Poster)           | Backend + Frontend | MOD-04         | P0 — MVP     |
| MOD-11        | Payment & Subscription                | Backend            | MOD-01         | P1           |
| MOD-12        | Admin & Content CMS                   | Backend            | All            | P2           |
| MOD-13        | Notification System                   | Backend            | MOD-01         | P1           |
| MOD-14        | WebSocket Real-Time Updates           | Backend            | MOD-02..04     | P0 — MVP     |

# 3. Data Models (PostgreSQL Schema)
## 3.1 users
```sql
CREATE TABLE users (
id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
username      VARCHAR(64) UNIQUE NOT NULL,
display_name  VARCHAR(128),
avatar_url    TEXT,
role          ENUM('child','parent','admin') DEFAULT 'child',
parent_id     UUID REFERENCES users(id),          -- child links to parent
tier          ENUM('free','pro') DEFAULT 'free',
xp_total      INTEGER DEFAULT 0,
created_at    TIMESTAMPTZ DEFAULT NOW(),
last_active   TIMESTAMPTZ
);
```

## 3.2 crew_members  (Digital Employees)
```sql
CREATE TABLE crew_members (
id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
crew_type     ENUM('copy_dog','art_cat','director_bear') NOT NULL,
level         INTEGER DEFAULT 1,
xp            INTEGER DEFAULT 0,
unlocked_skills JSONB DEFAULT '[]',   -- e.g. ['cyberpunk_style','watercolor']
mood          ENUM('happy','thinking','error','dancing') DEFAULT 'happy',
updated_at    TIMESTAMPTZ DEFAULT NOW()
);
```

## 3.3 projects
```sql
CREATE TABLE projects (
id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
title         VARCHAR(256),
mode          ENUM('magic','guided','studio') NOT NULL,
status        ENUM('draft','processing','completed','failed') DEFAULT 'draft',
voice_input_url TEXT,            -- S3 key of original voice recording
raw_transcript  TEXT,            -- ASR result
structured_prompt JSONB,         -- DeepSeek NLU output
generated_images JSONB DEFAULT '[]',  -- [{url, style, version}]
final_output_url TEXT,           -- PDF / video / poster S3 key
workflow_graph  JSONB,           -- L3 Studio node/edge graph
created_at    TIMESTAMPTZ DEFAULT NOW(),
completed_at  TIMESTAMPTZ
);
```

## 3.4 tasks  (Mission System)
```sql
CREATE TABLE tasks (
id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id       UUID REFERENCES users(id),
title         VARCHAR(256),
description   TEXT,
context_tags  TEXT[],            -- ['cat','space'] from user history
status        ENUM('pending','active','completed','expired') DEFAULT 'pending',
reward_xp     INTEGER DEFAULT 50,
expires_at    TIMESTAMPTZ,
created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

## 3.5 analytics_events
```sql
CREATE TABLE analytics_events (
id            BIGSERIAL PRIMARY KEY,
user_id       UUID REFERENCES users(id),
event_type    VARCHAR(64),       -- 'prompt_submitted','image_approved',etc.
payload       JSONB,
scored_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ae_user_time ON analytics_events(user_id, scored_at DESC);
```

## 3.6 subscriptions
```sql
CREATE TABLE subscriptions (
id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id       UUID REFERENCES users(id) UNIQUE,
plan          ENUM('free','pro_monthly','pro_annual') DEFAULT 'free',
status        ENUM('active','cancelled','expired') DEFAULT 'active',
started_at    TIMESTAMPTZ,
expires_at    TIMESTAMPTZ,
payment_ref   VARCHAR(256)       -- external payment gateway ID
);
```

# 4. REST API Contract
Base URL: https://api.imagilab.app/v1  |  Auth: Bearer JWT in Authorization header  |  All responses: { data, error, meta }
## 4.1 Authentication
### POST /auth/register
| **Field**    | **Type** | **Required** | **Description**                         |
| ------------ | -------- | ------------ | --------------------------------------- |
| username     | string   | Yes          | Unique username                         |
| password     | string   | Yes          | Min 8 chars                             |
| display_name | string   | No           | Child's display name                    |
| role         | enum     | Yes          | 'child' or 'parent'                     |
| parent_code  | string   | Cond.        | Required if role=child, links to parent |

Response 201:
```json
{ "data": { "user_id": "uuid", "access_token": "jwt", "refresh_token": "jwt" } }
```

### POST /auth/login
```json
Body: { "username": "...", "password": "..." }
Response 200: { "data": { "access_token": "...", "refresh_token": "...", "user": {...} } }
```

### POST /auth/refresh
```json
Body: { "refresh_token": "..." }
Response 200: { "data": { "access_token": "..." } }
```

## 4.2 Voice & Creation Pipeline (Core MVP)
### POST /projects/voice-start
Initiates a creation session. Returns a pre-signed S3 upload URL for the voice file.

| **Field**   | **Type** | **Required** | **Notes**                         |
| ----------- | -------- | ------------ | --------------------------------- |
| mode        | enum     | Yes          | 'magic' \| 'guided' \| 'studio'   |
| duration_ms | integer  | Yes          | Expected recording duration in ms |

```json
Response 201: { "data": { "project_id": "uuid", "upload_url": "https://s3.../...", "expires_in": 300 } }
```

### POST /projects/{project_id}/voice-commit
Called after client finishes uploading voice to S3. Triggers async processing pipeline.

```json
Body: { "s3_key": "uploads/voice/abc.webm" }
Response 202: { "data": { "job_id": "...", "status": "processing" } }
```

Client subscribes to WebSocket channel ws://api.../ws/{project_id} for real-time updates.

### GET /projects/{project_id}

```json
Response 200: { "data": { "id":"...", "status":"...", "generated_images":[...], "final_output_url":"..." } }
```

### POST /projects/{project_id}/refine  (L2 Guided Mode)
```json
Response 202: { "data": { "job_id": "...", "status": "processing" } }
```

### GET /projects  (List user projects)
```json
Query: ?page=1&limit=20&status=completed
Response 200: { "data": [...], "meta": { "total": 42, "page": 1 } }
```

## 4.3 Digital Crew (MOD-05)
### GET /crew
```json
Response 200: { "data": [ { "crew_type":"copy_dog", "level":3, "xp":240, "unlocked_skills":["logic_v2"], "mood":"happy" }, ... ] }
```

### GET /crew/{crew_type}/dialogue
Returns context-aware dialogue line for current project state.

| **Query Param** | **Type** | **Notes**                            |
| --------------- | -------- | ------------------------------------ |
| state           | enum     | thinking \| success \| error \| idle |
| project_id      | string   | Optional — for context-aware lines   |
```json
Response 200: { "data": { "line": "老板，我没听懂，能说清楚点吗？", "animation": "error" } }
```

## 4.4 Mission System (MOD-08)
### GET /tasks/today
```json
Response 200: { "data": [ { "id":"...", "title":"...", "description":"...", "reward_xp":80, "expires_at":"..." } ] }
```

### POST /tasks/{task_id}/accept
```json
Response 200: { "data": { "task_id":"...", "status":"active" } }
```

### POST /tasks/{task_id}/complete
```json
Body: { "project_id": "..." }
Response 200: { "data": { "xp_earned": 80, "crew_reaction": "dancing" } }
```

## 4.5 Reports (MOD-09)
### GET /reports/weekly
```json
Response 200: { "data": { "period":"2024-W23", "logic_score":72, "creativity_score":85,
"clarity_score":68, "prompt_count":14, "streak_days":5,
"highlight_project_id":"...", "parent_summary":"恭喜您，孩子本周决策力提升20%..." } }
```

## 4.6 Export & Share (MOD-10)
### POST /projects/{project_id}/export

| **Field**     | **Type** | **Notes**                             |
| ------------- | -------- | ------------------------------------- |
| format        | enum     | 'pdf_book' \| 'poster' \| 'video_mp4' |
| director_name | string   | Child's name shown on poster/cover    |
| quality       | enum     | 'standard' (free) \| 'hd' (pro)       |
```json
Response 202: { "data": { "job_id": "...", "estimated_seconds": 15 } }
```

### GET /export/{job_id}
```json
Response 200: { "data": { "status":"completed", "download_url":"https://cdn.../poster_xxx.jpg", "expires_at":"..." } }
```

## 4.7 Subscriptions (MOD-11)
### POST /subscriptions/upgrade
```json
Body: { "plan": "pro_monthly", "payment_token": "stripe_token_..." }
Response 200: { "data": { "plan":"pro_monthly", "expires_at":"..." } }
```

### DELETE /subscriptions
```json
Response 200: { "data": { "status":"cancelled", "active_until":"..." } }
```

# 5. Async Processing Pipeline (Celery)
## 5.1 Pipeline: Voice → Image → Report

All AI work is async. HTTP endpoints return job_id immediately. Client polls or listens via WebSocket.

| **Step** | **Task Name**    | **Input**           | **Output**                | **Timeout** | **Retry** |
| -------- | ---------------- | ------------------- | ------------------------- | ----------- | --------- |
| 1        | transcribe_voice | S3 voice key        | raw_transcript text       | 30s         | 3x        |
| 2        | extract_intent   | transcript          | structured_prompt JSON    | 15s         | 2x        |
| 3        | generate_image   | structured_prompt   | image S3 keys (3 options) | 60s         | 2x        |
| 4        | score_clarity    | transcript + prompt | clarity_score int         | 10s         | 1x        |
| 5        | update_crew_xp   | user_id + score     | crew level update         | 5s          | 3x        |
| 6        | push_ws_event    | project_id + status | WebSocket broadcast       | 2s          | 5x        |
## 5.2 Celery Task Definitions (pseudocode)
```python
@celery_app.task(bind=True, max_retries=3, soft_time_limit=30)
def transcribe_voice(self, project_id: str, s3_key: str):
audio = s3.download(s3_key)
transcript = whisper_api.transcribe(audio)
db.projects.update(project_id, raw_transcript=transcript)
extract_intent.delay(project_id, transcript)
```

```python
@celery_app.task(bind=True, max_retries=2, soft_time_limit=15)
def extract_intent(self, project_id: str, transcript: str):
prompt_json = deepseek.chat([
system_prompt=INTENT_EXTRACTION_SYSTEM,
user=transcript
])
structured = json.loads(prompt_json)
db.projects.update(project_id, structured_prompt=structured)
generate_image.delay(project_id, structured)
```

## 5.3 WebSocket Event Schema
```json
// Event pushed to ws://api.imagilab.app/ws/{project_id}
{
	"event": "status_update",
	"project_id": "uuid",
	"status": "image_ready",          // transcribing|extracting|generating|image_ready|failed
	"payload": {
		"image_urls": ["https://cdn.../img_1.jpg", "..."],
		"crew_animation": "dancing",
		"crew_line": "老板，搞定！"
		}
}
```

# 6. Interaction Logic & State Machines
## 6.1 L1 Magic Mode — State Machine

| **State**    | **UI State**                            | **Trigger**           | **Next State** | **Side Effect**           |
| ------------ | --------------------------------------- | --------------------- | -------------- | ------------------------- |
| IDLE         | Mic button visible, crew idle           | User press & hold mic | RECORDING      | Start WebAudio capture    |
| RECORDING    | Sound wave animation, crew thinking     | User release mic      | UPLOADING      | Stop capture → upload S3  |
| UPLOADING    | Spinner on mic, crew thinking           | Upload success        | PROCESSING     | Call /voice-commit        |
| PROCESSING   | Copy-dog 'thinking' animation           | WS: transcribing      | TRANSCRIBING   | Show transcript bubble    |
| TRANSCRIBING | Art-cat 'eye becomes color-picker'      | WS: generating        | GENERATING     | Show 'drawing' fx         |
| GENERATING   | Progress bar, director 'reading script' | WS: image_ready       | RESULT         | Reveal images (3 options) |
| RESULT       | 3 image cards, full-crew dancing        | User tap image        | PREVIEW        | Select image              |
| PREVIEW      | Fullscreen image, share button          | Tap share             | EXPORT         | Call /export poster       |
| ERROR        | Crew error animation, retry button      | Any failure           | IDLE           | Show error dialogue       |

## 6.2 L2 Guided Mode — Decision Points
After image generation in L2, bottom sheet presents 3 sticker option cards. Each card is a refinement dimension:

| **Card Slot** | **Dimension**      | **Example Options**                | **UI Component**     |
| ------------- | ------------------ | ---------------------------------- | -------------------- |
| Slot A        | Accessory / Object | Sunglasses \| Hat \| Cape          | 3D rotating card     |
| Slot B        | Environment        | Space \| Forest \| City            | Landscape thumbnail  |
| Slot C        | Art Style          | Watercolor \| Cyberpunk \| Cartoon | Style preview swatch |

Selection triggers POST /projects/{id}/refine → new Celery task → WS push → image replaced with erase-redraw animation.

## 6.3 L3 Studio Mode — Workflow Graph Validation Rules
Studio Mode uses a directed acyclic graph (DAG). Invalid connections are rejected with crew dialogue.

| **Rule** | **Condition**                                   | **Error Dialogue** |
| -------- | ----------------------------------------------- | ------------------ |
| RULE-01  | art_cat node has no incoming copy_dog edge      | 没剧本怎么拍戏？先让文案狗写本子！  |
| RULE-02  | director_bear node has no incoming art_cat edge | 导演还没图，叫画师喵先交作业！    |
| RULE-03  | Cycle detected in graph                         | 哎，这死循环了，老板冷静想想！    |
| RULE-04  | More than 8 nodes on canvas (free tier)         | 老板，免费版只能8个节点，升级解锁！ |
| RULE-05  | Node has no output connection                   | 这个员工没活干，连根线给它！     |

## 6.4 Crew Mood State Machine

| **Mood** | **Trigger Condition**             | **Animation**                  | **Duration**           |
| -------- | --------------------------------- | ------------------------------ | ---------------------- |
| thinking | AI job in progress                | Eye animation, thought bubbles | Until job completes    |
| happy    | Job success, user active          | Idle bounce                    | Default state          |
| dancing  | Project completed + high score    | Full dance sequence            | 5 seconds              |
| error    | API failure or low-clarity prompt | Error animation + dialogue     | Until user retries     |
| sleeping | No user activity 5+ minutes       | Eyes close, Zzzs               | Until user interaction |

# 7. Flutter Frontend Architecture
## 7.1 State Management: Riverpod

Use Riverpod 2.x with AsyncNotifier. No setState in business logic. UI = pure function of state.

| **Provider**         | **Type**                            | **Responsible For**                       |
| -------------------- | ----------------------------------- | ----------------------------------------- |
| authProvider         | StateNotifier\<AuthState\>          | JWT storage, login/logout, user profile   |
| projectProvider      | AsyncNotifier\<Project\>            | Current project lifecycle, status polling |
| crewProvider         | StateNotifier\<List\<CrewMember\>\> | Crew levels, mood, dialogue lines         |
| wsProvider           | StreamProvider\<WsEvent\>           | WebSocket connection, event stream        |
| taskProvider         | AsyncNotifier\<List\<Task\>\>       | Daily missions, acceptance, completion    |
| exportProvider       | AsyncNotifier\<ExportJob\>          | Export job status, download URL           |
| subscriptionProvider | StateNotifier\<Subscription\>       | Tier gating for L2/L3 features            |

## 7.2 Screen & Route Map

| **Route**          | **Screen**              | **Auth Required**  | **Notes**                       |
| ------------------ | ----------------------- | ------------------ | ------------------------------- |
| /                  | SplashScreen            | No                 | Brand animation → router guard  |
| /onboard           | OnboardingScreen        | No                 | 3-screen swipe intro            |
| /auth/register     | RegisterScreen          | No                 | Parent code flow                |
| /home              | HomeScreen (The Lounge) | Yes                | Crew display + task capsules    |
| /create/magic      | MagicModeScreen         | Yes                | L1 voice flow                   |
| /create/guided/:id | GuidedModeScreen        | Yes                | L2 card selection               |
| /studio            | StudioScreen            | Yes + Pro          | L3 DAG canvas                   |
| /crew              | CrewScreen              | Yes                | Crew detail + skill tree        |
| /gallery           | GalleryScreen           | Yes                | Past projects grid              |
| /project/:id       | ProjectDetailScreen     | Yes                | Single project, export          |
| /report            | ReportScreen            | Yes (parent)       | Weekly AI literacy report       |
| /settings          | SettingsScreen          | Yes                | Account, subscription, language |
| /premiere/:id      | PremiereScreen          | Yes                | Fullscreen result + share       |


## 7.3 Core Widget Tree (HomeScreen)
```bash
HomeScreen
├── HomeAppBar (crew XP bar, notification bell)
├── CrewStageWidget
│   ├── CrewCharacterWidget(copy_dog)
│   ├── CrewCharacterWidget(art_cat)
│   └── CrewCharacterWidget(director_bear)
├── TaskCapsuleList
│   └── TaskCapsuleCard × N  (film-reel design)
├── QuickCreateButton  → /create/magic
└── BottomNavBar
	├── Tab: 片场 (Create)
	├── Tab: 员工室 (Crew)
	└── Tab: 成片库 (Gallery)
```

## 7.4 Folder Structure
```bash
lib/
├── main.dart
├── app/
│   ├── router.dart          # GoRouter config
│   └── theme.dart           # Design system tokens
├── core/
│   ├── api/                 # Dio HTTP client, interceptors
│   ├── ws/                  # WebSocket service
│   ├── storage/             # SecureStorage + Hive cache
│   └── utils/
├── features/
│   ├── auth/
│   ├── home/
│   ├── create/              # magic, guided, studio
│   ├── crew/
│   ├── gallery/
│   ├── report/
│   └── export/
└── shared/
	├── widgets/             # Reusable UI components
	└── models/              # Dart data classes (freezed)
```

# 8. Backend Service Design (FastAPI)
## 8.1 Project Structure
```bash
backend/
├── main.py                  # FastAPI app factory
├── config.py                # Pydantic settings (env vars)
├── db/
│   ├── session.py           # SQLAlchemy async session
│   └── models/              # ORM models
├── api/
│   ├── v1/
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── crew.py
│   │   ├── tasks.py
│   │   ├── reports.py
│   │   ├── exports.py
│   │   └── subscriptions.py
│   └── ws.py                # WebSocket endpoint
├── services/
│   ├── ai/
│   │   ├── transcriber.py   # Whisper integration
│   │   ├── intent.py        # DeepSeek NLU
│   │   ├── image_gen.py     # FLUX / Replicate
│   │   └── dify_client.py   # Dify Workflow calls
│   ├── storage.py           # S3/MinIO client
│   ├── report.py            # Analytics scoring
│   └── crew.py              # Crew XP & dialogue
├── tasks/                   # Celery task definitions
│   ├── pipeline.py          # transcribe → intent → image
│   ├── daily_missions.py    # Pseudo-MiroFish cron
│   └── export.py            # PDF/poster rendering
└── tests/
```

## 8.2 Environment Variables (Required)

| **Variable**      | **Description**               | **Example**                |
| ----------------- | ----------------------------- | -------------------------- |
| DATABASE_URL      |  PostgreSQL connection string |   postgresql+asyncpg://... |
| REDIS_URL         | Redis broker URL              |   redis://localhost:6379/0 |
| JWT_SECRET        |    JWT signing secret         | super-secret-key-256bit    |
| S3_BUCKET         | Object storage bucket name    | imagilab-assets            |
| S3_ENDPOINT       |   S3-compatible endpoint      | https://s3.amazonaws.com   |
| S3_ACCESS_KEY     | Access key ID                 | AKIAXXXXX                  |
| S3_SECRET_KEY     | Secret access key             | xxxxx                      |
| DEEPSEEK_API_KEY  |  DeepSeek API key             | sk-...                     |
| REPLICATE_API_KEY | Replicate.com key for FLUX    | r8_...                     |
| DIFY_BASE_URL     | Self-hosted Dify URL          | http://dify:8080           |
| DIFY_API_KEY      |  Dify app API key             | app-...                    |
| WHISPER_MODEL     | Whisper model size            | medium                     |
| CDN_BASE_URL      |  CDN prefix for asset URLs    | https://cdn.imagilab.app   |

---
# 9. AI Prompt Engineering
## 9.1 Intent Extraction Prompt (DeepSeek — Copy Dog)
	Goal: Convert child's raw voice transcript into a structured image generation prompt.

```markdown
SYSTEM: You are Copy-Dog (文案狗), an AI assistant helping children create art.
Extract intent from a child's voice description and return ONLY valid JSON.
Schema: { subject: string, action: string, environment: string,
style: string, mood: string, image_prompt_en: string }
Rules:
- image_prompt_en must be in English, suitable for FLUX text-to-image
- Keep it safe, colorful, child-appropriate
- If input is unclear, set unclear:true and add clarification_hint

USER: <child transcript here>

Example output:
{ "subject": "墨镜猫", "action": "驾驶飞船", "environment": "太空",
"style": "cartoon", "mood": "adventurous",
"image_prompt_en": "cute cartoon cat wearing sunglasses piloting a spaceship
in outer space, colorful stars, vibrant colors, child-friendly art style" }
```

## 9.2 Daily Mission Generation Prompt (Pseudo-MiroFish)
```markdown
SYSTEM: You are the ImagiLab mission director. Generate 1 creative daily task for a child.
Use their history tags to make it feel personalized.
Return JSON: { title: string, description: string, context_tags: string[] }
The description must sound like crew members discussed it overnight (e.g., '昨晚员工们...')

USER: Child's recent tags: ['cat','space','sunglasses']. Age: 8. Level: 3.

Example output:
{ "title": "墨镜猫的飞船设计大赛",
"description": "昨晚员工们开会讨论，文案狗说墨镜猫需要一艘飞船，今天能帮它设计一个吗？",
"context_tags": ["cat", "space", "vehicle"] }
```

## 9.3 Clarity Scoring Prompt (Analytics)
```markdown
SYSTEM: Score this child's voice command for AI instruction clarity.
Return JSON: { clarity_score: 0-100, logic_score: 0-100, creativity_score: 0-100,
feedback_en: string }
Criteria: clarity = specificity, logic = cause-effect, creativity = originality
```

## 9.4 FLUX Image Generation Parameters

|**Parameter**|**Value / Notes**|
|---|---|
|model|black-forest-labs/flux-schnell (free tier) / flux-dev (pro tier)|
|width|512 (free) / 1024 (pro)|
|height|512 (free) / 1024 (pro)|
|num_outputs|3 (always generate 3 options for user choice)|
|num_inference_steps|4 (schnell) / 25 (dev)|
|guidance_scale|3.5|
|negative_prompt|nsfw, violence, scary, realistic human faces, gore|
|output_format|webp|

# 10. Security & Compliance
## 10.1 Authentication & Authorization
- JWT access tokens: 1 hour TTL. Refresh tokens: 30 days TTL, rotated on use.
- Passwords: bcrypt with cost factor 12.
- Child accounts cannot access parent report endpoints (role check middleware).
- Rate limiting: 10 req/min per IP on /auth endpoints. 30 req/min per user on /projects.

## 10.2 Child Safety (COPPA / China PIPL)
- No PII collected from child accounts beyond display_name and age bracket.
- Voice recordings auto-deleted from S3 after transcription (within 24 hours).
- All generated content passes safety classifier before delivery to client.
- Parent account required to register a child account (parent_code linking).
- Content moderation: FLUX negative_prompt + post-generation AWS Rekognition moderation.

## 10.3 API Security
- All endpoints behind HTTPS/TLS 1.3.
- CORS whitelist: app.imagilab.app, localhost (dev only).
- S3 upload URLs are pre-signed, expire in 5 minutes, scoped to single key.
- SQL injection protection: SQLAlchemy ORM only, no raw queries.
- Input validation: Pydantic models on all request bodies.

## 10.4 Subscription Tier Enforcement

| **Feature**           | **Free Tier**      | **Pro Tier**          | **Enforcement Layer**            |
| --------------------- | ------------------ | --------------------- | -------------------------------- |
| Daily voice creations | 3 per day          | Unlimited             | Redis counter, reset at midnight |
| Image quality         | 512px WebP         | 1024px WebP           | FLUX param in Celery task        |
| Studio Mode (L3)      | Demo only, no save | Full access           | Route guard + API middleware     |
| PDF export            | Watermarked        | Full HD, no watermark | Export service checks tier       |
| Crew skill unlocks    | Max level 3        | Max level 10          | crew.py XP cap logic             |
| Advanced styles       | 3 styles           | 20+ styles            | Style list filtered by tier      |
# 11. Deployment & DevOps
## 11.1 Infrastructure Stack

|**Component**|**Service**|**Spec (MVP)**|
|---|---|---|
|API Servers|AWS ECS Fargate / Render.com|2 × 1vCPU 2GB RAM, auto-scale|
|Celery Workers|ECS Fargate (separate task def)|2 × 2vCPU 4GB RAM|
|PostgreSQL|AWS RDS Postgres 15 / Supabase|db.t3.medium, Multi-AZ|
|Redis|AWS ElastiCache / Upstash|r6g.medium|
|Object Storage|AWS S3 / MinIO self-hosted|Standard tier|
|CDN|Cloudflare / Alibaba CDN|Global edge|
|Dify (AI Orchestration)|Self-hosted on EC2 t3.large|Docker Compose|
|Monitoring|Prometheus + Grafana Cloud|Free tier|
|CI/CD|GitHub Actions|Test → Build → Deploy on merge to main|

## 11.2 CI/CD Pipeline
```CI/CD
on: [push to main]
jobs:
test:
- pytest backend/tests/ --cov
- flutter test
build:
- docker build → push to ECR
- flutter build apk --release && flutter build ipa
deploy:
- ecs update-service (API + Workers)
- fastlane beta (iOS TestFlight)
- fastlane supply (Android Play Store internal)
```

## 11.3 Monitoring & Alerting
|**Metric**|**Alert Threshold**|**Action**|
|---|---|---|
|API p95 latency|> 2000ms for 5min|PagerDuty alert to on-call|
|Celery queue depth|> 100 tasks for 3min|Auto-scale worker count|
|Image gen failure rate|> 5% per hour|Slack alert, fallback to cached samples|
|Daily active users drop|> 20% day-over-day|Product team Slack notification|
|S3 storage cost|> $50/day|Billing alert, auto-purge old temp files|

# 12. Design System Tokens
## 12.1 Color Palette

| **Token**                   | **Hex Value** | **Usage**                                    |
| --------------------------- | ------------- | -------------------------------------------- |
| --color-brand-primary       | \#6D5EF7      | Brand purple — AI energy bar, CTA highlights |
| --color-action-red          | \#FF6B6B      | Action buttons: Generate, Publish, Confirm   |
| --color-success-teal        | \#4ECDC4      | Task complete, correct feedback              |
| --color-highlight-yellow    | \#FFE66D      | Decision points, important info callouts     |
| --color-bg-dark             | \#1A1A2E      | Primary dark background (not pure black)     |
| --color-bg-surface          | \#16213E      | Card / sheet surfaces                        |
| --color-text-primary        | \#FFFFFF      | Primary text on dark backgrounds             |
| --color-text-secondary      | \#A0A0B8      | Secondary labels, timestamps                 |
| --color-copy-dog-blue       | \#4A90D9      | Copy Dog character accent                    |
| --color-art-cat-pink        | \#FF85A1      | Art Cat character accent                     |
| --color-director-bear-brown | \#8B5E3C      | Director Bear character accent               |

## 12.2 Typography Scale

|**Token**|**Font**|**Size**|**Usage**|
|---|---|---|---|
|--text-display|Varela Round|32sp|Screen titles, welcome text|
|--text-heading|Varela Round|24sp|Section headings|
|--text-body|PingFang SC / Noto Sans SC|16sp|Body copy, descriptions|
|--text-caption|PingFang SC / Noto Sans SC|12sp|Labels, timestamps|
|--text-mono|Roboto Mono|14sp|Prompt display, code-like elements|
|--text-crew-line|Varela Round|18sp|Crew dialogue bubbles|

## 12.3 Animation Tokens

|**Token**|**Value**|**Usage**|
|---|---|---|
|--anim-fast|150ms ease-out|Button tap feedback, micro-interactions|
|--anim-normal|300ms cubic-bezier(0.34,1.56,0.64,1)|Card transitions, modal open|
|--anim-slow|600ms ease-in-out|Image reveal (developer liquid effect)|
|--anim-crew-celebrate|1500ms spring|Crew dancing celebration|
|--haptic-light|UIImpactFeedbackGenerator.light|Sticker card selection|
|--haptic-medium|UIImpactFeedbackGenerator.medium|Generate button press|
|--haptic-magnetic|Custom vibration 50ms×3|Studio node snap-to-grid|

# 13. Team Task Assignment & Sprint Plan
## 13.1 Recommended Team Composition

|**Role**|**Count**|**Primary Responsibilities**|
|---|---|---|
|Flutter Developer|2|All mobile screens, state management, animations|
|Backend Engineer|1|FastAPI routes, DB models, auth, WebSocket|
|AI Engineer|1|Celery pipelines, DeepSeek integration, FLUX, Dify|
|DevOps / Full-Stack|1|Docker, CI/CD, S3, monitoring, deployment|
|Product / Design|1|Figma specs, user testing, copy, character scripts|

## 13.2 Sprint 1 — MVP Core (Days 1-7)
Goal: Ship 'Voice → Image → Poster' end-to-end on real device.

| **Task ID** | **Task**                                          | **Owner**    | **Day** |
| ----------- | ------------------------------------------------- | ------------ | ------- |
| S1-01       | Setup PostgreSQL schema (users, projects, crew)   | Backend      | 1       |
| S1-02       | FastAPI skeleton + JWT auth endpoints             | Backend      | 1-2     |
| S1-03       | Flutter project init + GoRouter + Riverpod setup  | Flutter-A    | 1       |
| S1-04       | Design system implementation (theme.dart, tokens) | Flutter-B    | 1-2     |
| S1-05       | S3 presigned upload service                       | Backend      | 2       |
| S1-06       | Celery + Redis setup, transcribe_voice task       | AI Eng       | 2       |
| S1-07       | DeepSeek intent extraction task                   | AI Eng       | 3       |
| S1-08       | FLUX image generation task (3 options)            | AI Eng       | 3-4     |
| S1-09       | WebSocket server + event push                     | Backend      | 3       |
| S1-10       | HomeScreen + BottomNav + CrewWidget (static)      | Flutter-A    | 3-4     |
| S1-11       | MagicModeScreen — mic recording + upload          | Flutter-B    | 3-4     |
| S1-12       | MagicModeScreen — WS listener + state machine     | Flutter-A    | 4-5     |
| S1-13       | Image result display + 3-card selection UI        | Flutter-B    | 5       |
| S1-14       | Poster export endpoint + basic template           | Backend + AI | 5-6     |
| S1-15       | PremiereScreen + Share button                     | Flutter-A    | 6       |
| S1-16       | Crew dialogue integration (static script)         | Flutter-B    | 6       |
| S1-17       | E2E integration test + bug fix                    | All          | 7       |
| S1-18       | TestFlight + Play Store internal deploy           | DevOps       | 7       |

## 13.3 Sprint 2 — Guided Mode + Crew Leveling (Days 8-14)

|**Task ID**|**Task**|**Owner**|
|---|---|---|
|S2-01|Guided Mode bottom sheet (3 sticker cards + 3D card widget)|Flutter-A|
|S2-02|POST /projects/{id}/refine endpoint + Celery task|Backend + AI|
|S2-03|Erase-and-redraw image transition animation|Flutter-B|
|S2-04|Crew XP system + level-up logic in backend|Backend|
|S2-05|Crew mood state machine in Flutter (CrewAnimationController)|Flutter-A|
|S2-06|Task Mission system (daily gen cron + API endpoints)|Backend + AI|
|S2-07|TaskCapsuleList UI (film reel design)|Flutter-B|
|S2-08|Analytics event logging (analytics_events table)|Backend|
|S2-09|Weekly report generation logic|Backend + AI|
|S2-10|ReportScreen UI (parent-facing)|Flutter-A|

## 13.4 Sprint 3 — Studio Mode + Subscription (Days 15-21)

|**Task ID**|**Task**|**Owner**|
|---|---|---|
|S3-01|DAG canvas widget (custom Flutter painter, node/edge drag)|Flutter-A|
|S3-02|Workflow validation rules (RULE-01 to RULE-05)|Flutter-B + Backend|
|S3-03|Studio execution: POST /studio/run + Celery orchestration|Backend + AI|
|S3-04|Payment integration (Stripe / WeChat Pay)|Backend|
|S3-05|Subscription tier enforcement middleware|Backend|
|S3-06|PaywallScreen + upgrade flow UI|Flutter-B|
|S3-07|Crew skill tree UI (CrewScreen)|Flutter-A|
|S3-08|GalleryScreen — project grid with filters|Flutter-B|
|S3-09|Push notifications (Firebase FCM)|DevOps + Backend|
|S3-10|Performance audit + image caching optimization|Flutter-A|

# 14. Testing Strategy
## 14.1 Backend Tests

|**Test Type**|**Tool**|**Coverage Target**|**What to Test**|
|---|---|---|---|
|Unit|pytest|80%+|Service functions, prompt parsers, XP logic|
|Integration|pytest + TestClient|Key paths|API endpoints with real DB (test schema)|
|Task Tests|pytest + Celery eager mode|All tasks|Pipeline steps in isolation|
|Load Test|Locust|P95 < 2s at 100 concurrent|Voice commit → WS response time|

## 14.2 Flutter Tests

|**Test Type**|**Tool**|**What to Test**|
|---|---|---|
|Unit|flutter_test|Providers, state machines, utility functions|
|Widget|flutter_test + WidgetTester|Individual screens with mocked providers|
|Integration|integration_test package|Full user flows on emulator (voice → result)|
|Golden|golden_toolkit|Screenshot comparison for critical UI screens|

## 14.3 AI Pipeline Tests
- Mock FLUX and DeepSeek in CI — use snapshot fixtures for deterministic tests.
- Clarity scorer: regression test set of 20 sample transcripts with expected score ranges.
- Content safety: test set of edge-case prompts that should trigger moderation.

# 15. Open Questions & Risks

|**#**|**Risk / Question**|**Impact**|**Mitigation**|
|---|---|---|---|
|R-01|FLUX image gen latency > 15s on free tier|High|Show animated crew 'drawing' state; use schnell model; consider local SDXL fallback|
|R-02|DeepSeek NLU misinterprets young children's speech|High|Collect failure cases; fine-tune with child speech dataset; add fallback template|
|R-03|App Store rejection (child safety)|Critical|Implement COPPA flow, age gate, parental consent screen before launch|
|R-04|FLUX content policy violations|High|Strict negative prompts + post-gen moderation + human review queue|
|R-05|Voice STT accuracy for non-standard child speech|Medium|Evaluate Whisper large-v3 vs Azure STT; may need language model fine-tuning|
|R-06|Celery queue overload on viral growth|Medium|Auto-scale workers; implement user queue position display ('排队第3位')|
|R-07|WeChat Pay integration complexity (China market)|Medium|Use Ping++ or XPay SDK to abstract; plan 2 extra days buffer|

Document Sign-Off

|**Role**|**Name**|**Sign**|**Date**|
|---|---|---|---|
|Engineering Lead||||
|Product Owner||||
|AI Engineer||||
|DevOps Lead||||

END OF DOCUMENT — ImagiLab Low Level Design v1.0