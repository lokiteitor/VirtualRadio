# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

VirtualRadio generates satirical radio stations (WCTR-style) for simulation games
(Farming Simulator, ETS2). A user defines a "universe" (stations, news, commercials,
brands, characters, music) and triggers an async pipeline that writes a script and
compiles a mixed MP3 episode.

Monorepo with two deployable apps plus a spec/docs contract:

- `backend/` — Flask 3 REST API + Celery generation pipeline (Python 3.12)
- `frontend/` — Nuxt 4 SPA control panel (Bun + Vue 3 + Pinia, Feature-Sliced Design)
- `specs/openapi.yaml` — the API contract the backend implements
- `docs/backend/` & `docs/frontend/` — architecture, DB schema, RBAC, and implementation plans (in Spanish; the source of truth for design decisions)

**Conventions:** the project is Spanish-first — docs, commit messages, user-facing
strings, and API error messages are in Spanish; code identifiers and comments are in
English. Both apps have detailed READMEs (`backend/README.md`, `frontend/README.md`).

## Commands

### Full stack (Docker, recommended)
```bash
cd backend && cp .env.example .env   # set secrets / AI keys if you have them
docker compose up --build            # db(pg18) + redis + api + worker + frontend
# API → http://localhost:5000/api/v1   Frontend → http://localhost:3000
```
The `api` service runs `flask db upgrade && flask seed-roles` on boot. The `frontend`
service is built from `../frontend` with `NUXT_PUBLIC_API_BASE` baked to the host API.

### Backend (local, needs Postgres 18 + Redis)
```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export FLASK_APP=wsgi:app PYTHONPATH=$(pwd)
export DATABASE_URL="postgresql+psycopg://virtualradio:virtualradio@localhost:5432/virtualradio"
export REDIS_URL="redis://localhost:6379/0" MEDIA_ROOT=/tmp/vrmedia

.venv/bin/flask db upgrade          # apply migrations
.venv/bin/flask seed-roles          # RBAC role catalog (idempotent)
.venv/bin/flask seed-demo <email>   # create a demo user with a seeded universe
.venv/bin/flask --app wsgi:app run --port 5000
.venv/bin/celery -A celery_worker.celery_app worker --beat --loglevel=info  # other terminal
```

### Backend tests (smoke scripts, not pytest — run as plain Python with PG+Redis up)
```bash
.venv/bin/python tests/smoke_e2e.py     # 41 checks: auth, CRUD, suggest, gen, audio, isolation
.venv/bin/python tests/smoke_async.py   # exercises the real Redis→worker path (needs a running worker)
```

### Frontend (Bun)
```bash
cd frontend && bun install
NUXT_PUBLIC_API_BASE=http://localhost:5000/api/v1 bun run dev   # :3000
bun run typecheck                       # vue-tsc, expected 0 errors
bun run build                           # node .output/server/index.mjs to preview
node smoke.e2e.mjs                      # Playwright E2E vs a live stack (run `bunx playwright install chromium` once)
```

## Backend architecture

Layered, owner-scoped, contract-driven. Request flow:

```
routes/ (blueprints)  →  controllers/  →  services/ (+ agents/)  →  repositories/  →  models/
   ↑ check_permission      ↑ orchestrate, return plain data         ↑ scoped_query    ↑ SQLAlchemy 2.0
```

- **Auto-discovered routes** — `app/routes/__init__.py` registers any module exposing a
  `bp` Blueprint under `/api/v1`. Adding a REST resource = drop `routes/<resource>.py`
  with a `bp`; no shared-file edits. Each route decorates handlers with
  `@check_permission("<resource>", "<action>")` and wraps controller output in the envelope.
- **Response envelope** — success `{"data": ..., "meta": {...}}`, error
  `{"error": {"code", "message", "details"}}`. Helpers in `app/common/responses.py`;
  error handlers in `app/common/errors.py` translate raised `*Error` exceptions.
- **RBAC + data isolation** — single role `USER` with scope `own` (see
  `app/auth/permissions.py`, `docs/backend/rbac.md`). `BaseRepository`/`scoped_query`
  (`app/repositories/base.py`) filter every query by `current_user.id`, and `create()`
  takes `owner_id` from the JWT — never the request body. **Accessing another user's
  resource returns 404, not 403** (existence is hidden). All routes except `auth` and
  `health` require `Authorization: Bearer <token>`.
- **Models** — `app/models/base.py` mixins: UUIDv7 PKs generated natively by Postgres
  (`server_default text("uuidv7()")`), tz-aware timestamps, and `OwnerMixin` (FK to
  `users` with `ON DELETE CASCADE`, indexed). Validation via Marshmallow `schemas/`.

### Generation pipeline (the core feature)
1. `POST /episodes/generate {station_id}` → controller validates the station, creates a
   queued `GenerationJob`, enqueues `tasks.generate_episode`, returns **202** with the job.
   Enqueue is best-effort/fail-fast — a down broker is logged, not fatal (config caps
   broker retries at 0 with short socket timeouts).
2. The Celery task (`app/tasks/generation.py`) advances the job through
   `PLANNING → SYNTHESIZING → MIXING → COMPLETED` (or `FAILED` with the error), persisting
   status+progress at each step. **It runs in the Flask app context but NOT a request
   context** — so it must NOT use `current_user`/`scoped_query`; it filters explicitly on
   the job's `owner_id`/`station_id`. Follow this pattern in any new worker code.
3. `services/agents/episode_assembly.build_episode()` orchestrates: `episode_planner`
   picks owner-scoped content → tries `llm_client.complete_json()` for a full script →
   on `None`/invalid output, builds the script procedurally from the news/commercial/
   character/host agents. Either path returns the same pinned dict.
4. `integrations/audio_engine.compile_episode()` synthesizes voices (TTS) and mixes the
   MP3 with DSP effects (ducking, telephony filter, sweepers).
5. Client polls `GET /jobs/{id}`; audio served at `GET /episodes/{id}/audio`
   (`send_file(conditional=True)` → supports `Range`/206).

### AI integrations — graceful degradation (everything works with no keys)
`integrations/` clients always tolerate a `None` result and fall back to procedural
content / synthetic audio:
- `llm_client` order: Gemini (via `google-genai` SDK) → OpenRouter → `None`.
- `genai_client` selects Gemini transport: **Vertex AI with ADC**
  (`GEMINI_USE_VERTEX=true` + `GOOGLE_CLOUD_PROJECT`/`GOOGLE_CLOUD_LOCATION`, location
  `global` works) **or** Developer API key (`GEMINI_API_KEY`), else `None`. Docker mounts
  ADC via `${ADC_PATH}` → `/secrets/adc.json`.
- `tts_client` uses Gemini TTS when available, else synthetic voice. Real TTS is slow
  (~10–14 s/segment → a full episode is ~3–4 min).

Config is 12-factor (`app/config/__init__.py`, selected by `FLASK_ENV`); the `testing`
config uses `task_always_eager` so Celery runs inline.

## Frontend architecture

Nuxt 4 SPA (`ssr: false` to keep JWT handling simple), organized by **Feature-Sliced
Design**. Strict dependency direction — a layer may only import from layers to its right:

```
pages → widgets → features → entities → shared
```

- Each slice exposes its public API via `index.ts`; **never import another slice's
  internal files**. Slices live under `app/{pages,widgets,features,entities,shared}/`.
- `shared/api` is the single HTTP client: wraps `$fetch`, attaches the JWT, unwraps the
  `{data}`/`{error}` envelope, and exposes `getBlob` for authenticated audio (the audio
  endpoint needs the token, so it's fetched as a blob, not a plain `<audio src>`).
- **Auth** — JWT from `/login` lives in the `session` entity + `localStorage`;
  `middleware/auth.global.ts` guards routes; a `401` clears the session and redirects to
  `/login`. `plugins/session.client.ts` restores the session on load.
- **Config** — backend URL is always `runtimeConfig.public.apiBase`
  (`NUXT_PUBLIC_API_BASE`), never hardcoded (default `http://localhost:5000/api/v1`).
- **Styling** — SASS tokens/mixins in `shared/styles/{_variables,_mixins}.scss` are
  auto-injected into every component `<style lang="scss">` via `nuxt.config.ts` vite
  `additionalData`, so `$`-vars and mixins are available without importing.

## Gotchas

- **Postgres 18 specifics**: episode IDs rely on the native `uuidv7()` function (PG18+),
  and the PG18 image stores data in a major-version subdir — the compose volume is
  mounted at `/var/lib/postgresql`, **not** `.../data`.
- Tests are standalone smoke scripts requiring a live Postgres + Redis (and a worker for
  the async one); there is no pytest/vitest suite yet.
- The generation worker must use explicit `owner_id` filtering, never the request-scoped
  `current_user`/`scoped_query` helpers (see pipeline note above).
