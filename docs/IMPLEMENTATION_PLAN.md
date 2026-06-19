# AIML-vlab — Phased Implementation Plan

**Branch:** `backend/flask-improvements`
**Scope:** Incrementally improve the existing **Flask + React (CRA) + MongoDB** project.
No framework rewrite. Each phase is independently shippable and ordered by dependency
and value. Nothing here is blocking; sequence by appetite.

---

## Decisions on record

- **Stay on Flask.** FastAPI was evaluated and rejected: the dominant workload is
  CPU-bound ML training, where async yields ~no gain (handlers would run in a threadpool
  and behave like Flask anyway), while the migration cost is a rewrite of ~96 endpoints +
  SSE + the raw-body webhook + CORS + rate limiting + the Vercel WSGI→ASGI switch. The
  surviving benefits (OpenAPI, Pydantic, DI) are obtainable on Flask incrementally
  (Phase 3). If I/O-bound features ever dominate, **Quart** (async Flask, near-drop-in)
  is the cheap escape hatch — not FastAPI.
- **The real backend weakness is architecture, not framework:** training runs
  synchronously inside the HTTP request under a 300s gunicorn timeout. Phase 2 fixes it.
- **The real frontend weakness is the build tool:** CRA (`react-scripts`) is
  unmaintained. Phase 5 migrates to Vite — low risk, high value.

### Leave as-is (don't churn)
Service layer, blueprint split, migrations + runner, requirements split, multi-stage
Dockerfile, context-based state (no Redux), centralized `api.js` / `config.js`
boundaries, the `models/` naming (domain-appropriate — just documented).

---

## Phase overview

| # | Phase | Side | Effort | Value | Risk | Depends on |
|---|---|---|---|---|---|---|
| 1 | App factory + test harness | BE | S–M | High (unblocks all) | Low | — |
| 2 | Background job queue + Redis rate-limit | BE | M–L | **Highest** | Med | 1 |
| 3 | Pydantic validation (collapse 3-way sync) | BE | M | High | Med | 1 |
| 4 | Route reorg (split `utils/route.py`) | BE | S | Med | Low | 1 |
| 5 | CRA → Vite | FE | M | High | Low | — |
| 6 | Generic `<ModelPage>` (dedup 23 components) | FE | M–L | High | Med | 5 (nice-to-have) |
| 7 | Frontend polish + config hardening | FE/BE | S–M | Med | Low | 5,6 |

Backend track (1→2→3→4) and frontend track (5→6→7) are independent and can run in
parallel. **Phase 1 must precede 2/3/4.**

---

## Phase 1 — App factory + test harness *(foundation)* — ✅ DONE

**Status:** Implemented on `backend/flask-improvements`. `create_app()` factory in
`backend/app.py` (no import-time side effects); `gunicorn "app:create_app()"` in the
Dockerfile; `mongoDb.connection.init_db(client_factory=...)` injection hook; `pytest` +
`mongomock` harness under `backend/tests/` with `conftest.py` — **29 tests passing**
covering auth (`token_required`/`admin_required` incl. expired/optional/deactivated/admin
paths), hyperparam validation, and subscription quota. Run with `python -m pytest` from
`backend/`.

**Goal:** make the app testable and free of import-time side effects, so every later
phase can be verified.

**Why:** `app.py` runs `init_db()` + `run_migrations()` at module import — that fires on
every import (tests, the future RQ worker). Convention is a `create_app()` factory.

**Changes:**
- Extract `create_app()`; move `init_db`, migration run, blueprint registration, CORS,
  and limiter binding inside it. `app.py` becomes a thin entrypoint (`app = create_app()`).
- Add `backend/tests/` with `pytest` + `mongomock` (or a disposable test Mongo) and a
  `conftest.py` app fixture.
- Seed tests for the logic most likely to regress silently: auth (`token_required`,
  optional/expired/deactivated paths), hyperparam validation, and quota
  (`check_quota`/`record_usage`).

**Acceptance:** `pytest` boots an isolated app with no real DB/migration side effects;
auth + validation + quota covered; app still serves under gunicorn unchanged.

**Touch points:** `app.py`, new `backend/tests/`, `requirements-dev.txt`
(`pytest`, `mongomock`).

---

## Phase 2 — Background job queue + Redis rate-limit *(highest impact)* — 🟡 INFRA DONE, ROLLOUT PENDING

**Status — landed & tested on `backend/flask-improvements` (38 tests passing):**
- ✅ `REDIS_URL` + `TRAINING_ASYNC` config; `redis`+`rq` deps (base), `fakeredis` (dev).
- ✅ Redis-backed `flask-limiter` with graceful fallback to `memory://` (`extensions.py`).
- ✅ `backend/jobs/` — `queue.py` (`get_queue`/`enqueue_training`, return `None` when no
  Redis) + `tasks.py` (`run_training_job` + `JobRequest` shim).
- ✅ Flag-gated async path in `_train_model` (returns `202 {session_id}`), falls back to
  sync when the queue is down.
- ✅ `redis` + `rq worker` services in `docker-compose.yml`.

**Remaining to actually turn it on (the rollout):**
1. Frontend: make the classical model pages poll `/training-sessions/<id>/progress`
   instead of awaiting a synchronous result (the replay hook already polls — reuse it).
2. Verify enqueue→worker→poll end-to-end against a **real** Redis + `rq worker` (couldn't
   run locally — Windows dev has no Redis; RQ workers need `fork`, so use Linux/Docker or
   `SimpleWorker`).
3. Extend beyond classical: XGBoost route, then the SSE deep-learning models (these read
   `request.files`/stream, so they need more than the `JobRequest` shim).
4. Flip `TRAINING_ASYNC=true` once 1–3 are done; retire in-request execution.

**Goal:** training returns instantly and runs out-of-process; rate limits work across
workers.

**Why:** today training blocks the request (300s timeout ceiling, a worker tied up per
run, a dropped connection loses the run). And `extensions.py` uses `memory://` storage —
with `WEB_CONCURRENCY>1` each worker has separate counters.

**Why it's lower-risk than it sounds:** the persistence + progress plumbing already
exists — `training_sessions`, `mark_session_running`, `append_session_progress`,
`append_session_metric`, `is_cancel_requested`, and `/training-sessions/<id>/progress`
polling. We mostly relocate *where* the trainer runs.

**Changes:**
1. Add `redis` + `rq` to `requirements-base.txt`; add `REDIS_URL` to `config.py`.
2. New `backend/jobs/`: `queue.py` (RQ queue from `REDIS_URL`) + `tasks.py` with
   `run_training(model_code, session_id, user_id, params, …)` calling existing model fns.
3. Training routes: **enqueue + return `session_id` (HTTP 202)** instead of run+stream.
4. Frontend model pages poll `/training-sessions/<id>/progress` (the replay path already
   exists) for logs/metrics/results. **Start with polling — it removes worker-blocking
   with zero SSE changes.** (Optional later: Redis pub/sub → thin SSE relay for push.)
5. Worker process: `rq worker` in `docker-compose.yml` + Dockerfile/Railway second
   process.
6. Cancellation: worker checks `is_cancel_requested(session_id)` between epochs (reuse
   the existing `sse_helpers` logic).
7. Point `flask-limiter` `storage_uri` at the same `REDIS_URL`; graceful fallback to
   `memory://` if Redis is down (so local dev still boots). No route-decorator changes.

**Migration order:** one classical model end-to-end first (e.g.
`simple_linear_regression`) to validate enqueue→poll→results, then the SSE deep-learning
models, then retire in-request execution.

**Acceptance:** training returns <1s with a `session_id`; model page shows live progress
via polling; killing the web worker mid-run doesn't lose the job; cancel still works;
rate limits hold across >1 worker.

**Touch points:** `models/route.py`, `utils/sse_helpers.py`,
`services/training_session_service.py`, `extensions.py`, `config.py`, new
`backend/jobs/`, `docker-compose.yml`, Dockerfile; frontend model pages + `api.js`.

---

## Phase 3 — Pydantic validation (collapse the 3-way sync) — ✅ DONE

**Status:** Implemented on `backend/flask-improvements`. `backend/services/hyperparam_models.py`
is now the single Pydantic v2 source of truth (one `BaseModel` per model_code,
registry `HYPERPARAM_MODELS`); `config.DEFAULT_HYPERPARAMS`,
`hyperparam_validator.VALIDATION_SCHEMAS`, and `model_catalog.PARAM_LABELS`/`PARAM_NOTES`
are all **derived** from it. `validate_hyperparams()`/`get_model_schema()` keep their exact
return shapes (frontend unchanged); a golden-snapshot diff confirmed byte-for-byte parity.
**127 tests passing** (38 → +84 new model tests, +5 from Phase 4).

**Goal:** one source of truth per model for hyperparams.

**Why:** `config.DEFAULT_HYPERPARAMS`, `services/hyperparam_validator.VALIDATION_SCHEMAS`,
and `services/model_catalog.PARAM_LABELS/PARAM_NOTES` are three hand-kept dicts that must
stay in sync (CLAUDE.md flags this footgun).

**Changes:**
- Pin `pydantic>=2`. Define one `BaseModel` per model_code holding type, range
  (`Field(ge=, le=)`), enum, default, **and** label/note (`Field(title=, description=)`).
- `validate_hyperparams()` → `Model.model_validate(...)`; `get_model_schema()` →
  `Model.model_json_schema()`. Adapt the `/model-schema/<code>` shape once; verify
  `HyperparamPanel` renders from it (add a thin adapter if needed).
- Migrate model-by-model; keep the old validator as fallback until all are moved.

**Acceptance:** each migrated model validates via Pydantic; the frontend panel renders
unchanged; the three dicts collapse to one definition per model.

**Touch points:** `services/hyperparam_validator.py`, `config.py`,
`services/model_catalog.py`, possibly `HyperparamPanel.js`.

---

## Phase 4 — Backend route reorganization — ✅ DONE

**Status:** Implemented on `backend/flask-improvements`. Dataset endpoints (upload, preview,
profile, diff, versions, folder-images, preprocess, save-annotations, delete, default) moved
to `backend/datasets/route.py`; pipeline CRUD to `backend/pipelines/route.py`; both registered
under `/api` in `create_app()` so **every path is unchanged** (frontend unaffected). `utils/route.py`
keeps only misc endpoints (downloads, feedback, model catalog/registry, public config). Route
count unchanged (99); `tests/test_route_layout.py` asserts the moved paths still resolve.

**Goal:** routes grouped by domain, not misfiled under "utils".

**Why:** `utils/route.py` holds ~900 LOC of real domain endpoints (dataset upload,
preview, profile, diff, pipelines, annotations). "utils" should be helpers.

**Changes:** split into a `datasets/` blueprint (+ `pipelines/` if it stays large);
register under `/api`. Pure move + blueprint rename — no behavior change. Add a one-line
note in CLAUDE.md clarifying `models/` = ML training code (not DB models).

**Acceptance:** all endpoints respond at the same paths; no behavior change; `utils/`
holds only helpers.

**Touch points:** `utils/route.py` → `datasets/route.py` (+ `pipelines/route.py`),
`app.py`/`create_app()`, CLAUDE.md.

---

## Phase 5 — CRA → Vite — ✅ DONE

**Status:** Migrated on `backend/flask-improvements`. `react-scripts` removed (−1313 packages);
added `vite` + `@vitejs/plugin-react` + `vitest` + `jsdom`. `frontend/vite.config.js` keeps the
output at `build/` (so `vercel.json` + the frontend Dockerfile are unchanged) and configures
esbuild to parse `src/**/*.js` as JSX (automatic runtime, since components don't `import React`).
`public/index.html` → root `index.html` (module script, `%PUBLIC_URL%` stripped); env var
`REACT_APP_API_URL` → `VITE_API_URL` (only `src/config.js` reads it); Docker/compose build args
renamed. Dead CRA `App.test.js` replaced by a Vitest smoke test. **Verified locally:** `npm run
build` green (1124 modules → `build/`), `npm test` green, `npm run dev` boots in ~345 ms on :3000.
Note: the main chunk is ~881 kB — bundle-splitting is deferred to Phase 7 (lazy routes).

**Goal:** replace the unmaintained `react-scripts` toolchain.

**Why:** CRA is no longer maintained / recommended. Vite gives much faster dev start,
HMR, and builds, with a smaller config surface. Code is already Vite-friendly (single
env boundary, no `eject`).

**Changes:** add Vite + `@vitejs/plugin-react`; move `index.html` to project root with
the `/src/index.js` module script; map `REACT_APP_*` → `import.meta.env.VITE_*` in the
**one** file that reads env (`src/config.js`); update `package.json` scripts and
`vercel.json` build command. Verify the Docker frontend build and SPA fallback routing.

**Acceptance:** `dev` and `build` run under Vite; the SPA serves identically; Vercel +
Docker builds succeed; `react-scripts` removed.

**Touch points:** `package.json`, new `vite.config.js`, `index.html`, `src/config.js`,
`vercel.json`, frontend Dockerfile/nginx.

---

## Phase 6 — Generic `<ModelPage>` (dedup 23 components)

**Goal:** replace ~23 near-identical model components (~3,300 LOC) with one
registry-driven page.

**Why:** each `Models/*.js` gathers a dataset + hyperparams, POSTs, and renders results —
near-duplicates. The pieces already exist: `useModelTrain`, `model_registry`,
`HyperparamPanel`.

**Changes:** build `<ModelPage modelCode=…>` driven by the registry; route model codes
to it. **First audit how much per-model bespoke UI exists** — keep genuinely custom ones
(e.g. ObjectDetection, StyleGAN, HiddenLayers/ANN/CNN layer builders) as overrides or
standalone. Migrate the simple regressors/classifiers first.

**Acceptance:** simple models render via `<ModelPage>` with no UX regression; bespoke
models still work; net LOC down significantly.

**Touch points:** `components/Models/*`, new `components/Models/ModelPage.js`, routing,
`hooks/useModelTrain.js`.

---

## Phase 7 — Frontend polish + config hardening

**Goal:** convention cleanup + fail-fast config.

**Changes (pick per appetite, all low-risk):**
- `pages/` vs `components/` split (move route screens into `src/pages/`).
- `React.lazy` + `Suspense` on protected routes to shrink the initial bundle (pairs with
  Vite).
- Frontend tests: smoke-test `services/api.js` (dedup/cache/401-redirect) and
  `AuthContext`.
- Backend: `pydantic-settings` `BaseSettings` in `config.py` — typed env parsing that
  fails fast on a missing `JWT_SECRET`/`REDIS_URL` at startup (keep the "all env in
  config.py" rule).
- Optional/later: path aliases (`jsconfig.json`), TypeScript (large, deferred).

**Acceptance:** route screens live in `pages/`; protected routes code-split; key FE units
tested; backend refuses to boot on missing critical env.

---

## Cumulative new dependencies

```
# backend/requirements-base.txt
redis>=5.0,<6
rq>=1.16,<2                  # Phase 2
pydantic>=2.6,<3             # Phase 3 (pin explicitly)
pydantic-settings>=2.2,<3    # Phase 7
# backend/requirements-dev.txt
pytest                       # Phase 1
mongomock                    # Phase 1

# frontend/package.json (Phase 5)
vite, @vitejs/plugin-react   # (and remove react-scripts)
```

---

## Suggested execution order

```
BE:  Phase 1 ─► Phase 2 ─► Phase 3 ─► Phase 4
FE:  Phase 5 ─► Phase 6 ─► Phase 7
```

Stand up Redis once at the start of Phase 2 (shared by the job queue and rate limiting).
Backend and frontend tracks are independent — run them in parallel if capacity allows.
