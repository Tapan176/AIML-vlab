# AIML-vlab — Roadmap & Next-Session Plan

> Working doc to carry context across sessions. Branch: `refactor/security-perf-dedup-hardening`.
> Last updated end of the security/UX session (commits up to `86cb589`).

---

## 1. What's DONE (this session)

- **UI theme overhaul** — unified teal/cyan light+dark theme, token-driven, readability + mobile fixes (hamburger nav, responsive tables). No purple.
- **Native dialogs replaced** — global `UIDialog` provider (`frontend/src/context/UIDialog.js`): `notify()` toasts + Promise-based `confirm()`. All 36 `alert`/`window.confirm` calls migrated.
- **Data Studio fixes** — pagination on Data Manager; storage-quota error now shows the friendly UpgradeModal; preprocessing no longer resets the selected dataset/pipeline or redirects after a run; fixed the `'SF' object has no attribute 'seek'` 500 (predictions upload).
- **Payments** — Lemon Squeezy provider completed (India/global, no invite), provider-agnostic billing; setup steps in `docs/PAYMENT_SETUP.md`.
- **Security pass (all Critical + High + several Medium):**
  - C1/C2 NoSQL-injection auth bypass; C3 reset-token leak + user-enum (auth now generic + token never returned).
  - C4 webhook replay protection (`mark_webhook_event`).
  - H1 JWT default-secret startup guard; `FLASK_DEBUG` default → false.
  - H2/H3 zip-slip + zip-bomb guard (`utils/path_safety.safe_extract_zip`).
  - H4/H5/H6 OAuth: state→origin allowlist, frontend `postMessage` origin check, verified-email linking, dropped `postMessage('*')`.
  - H7 photo/Drive proxy bound to registered photo ids.
  - M2 upload extension allowlist; M3 per-route auth rate limits (limiter extracted to `extensions.py`); M5 trained-model download IDOR; M6 plan allowlist.
  - **Predictions now owner-scoped** — per-session, uploaded to Drive, downloaded via `/download-model-predictions/<session_id>` with ownership check (old global-by-model-name route removed).

**Ownership principle now enforced:** every per-user artifact (datasets, sessions, models, results, predictions, photos) is accessible only to its owner. See the sweep table in §3-A for the one remaining gap.

---

## 2. Current constraints / decisions

- **Free services only for now.** No paid object storage, no managed Redis, no worker fleet yet. 1M-user architecture is parked (see git history / prior session for the full design if needed).
- **⚠️ Large-dataset vs free-storage tension.** Goal mentions 5–10 GB datasets, but:
  - `MAX_UPLOAD_SIZE_MB` is currently **50 MB**.
  - Google Drive free = 15 GB **total, shared across all users** via one OAuth token — cannot hold multiple large datasets, and is rate-limited.
  - Free S3-likes: Cloudflare R2 (10 GB total, no egress), Backblaze B2 (10 GB) — still can't hold many 5–10 GB files.
  - **Plan:** keep a small free-tier dataset cap (e.g. 50–200 MB) that fits free storage; gate large datasets behind a paid tier later, OR process-and-discard (keep only derived/sampled data + metadata, never persist the raw 10 GB), OR "bring-your-own-storage" (user supplies their own Drive/S3 creds). Decide before raising the cap.

---

## 3. REMAINING WORK (prioritized backlog)

### A. Security — deferred items
| ID | Item | Severity | File(s) |
|----|------|----------|---------|
| `/api/uploads` | Unauthenticated static serving of `static/uploads/<path>` (transient preview images, not user-namespaced) | Med | `backend/app.py:102` — best fixed by serving previews as base64/signed URLs |
| M1 | No CSRF nonce in OAuth `state` (needs server-side session store) | Med | `backend/auth/oauth_route.py` |
| M4 | Verbose `str(e)` errors returned to clients (pervasive) | Med | auth/models/subscription/utils/admin routes — do as one error-handler pass |
| L2 | LS signature compare is type-fragile | Low | `backend/subscription/lemonsqueezy.py:86` |
| L3 | Login user-enumeration (distinct user_not_found/incorrect_password) | Low | `backend/auth/authController.py` |
| L4 | Admin `$regex` injection/ReDoS (admin-only) | Low | `backend/admin/admin_route.py:111,324` |
| L5 | JWT in `localStorage` → httpOnly Secure cookie + refresh token (strategic) | Low | `AuthContext.js`, `api.js`, `OAuthSection.js` |

### B. Dead code cleanup (verified safe to delete — do LAST so new code is swept too)
- Frontend dead files: `components/ContactUs/`, `components/ModelDescription/` (+css), `Profile/ProfileDropdown.js`+`.css`, `Auth/login.css`, `Auth/signup.css`.
- Redundant `React` imports: `OAuthSection.js`, `FinetuneBERT/DistilBERT/ViT.js`, `shared/ColumnSelect.js`.
- Backend dead: `services/model_registry.py:get_model_import_path`, `services/preprocessing_service.py:ensure_unique_filename` wrapper, `models/route.py:MODEL_ROUTES` dict, commented blocks in `utils/uploadFiles.py:18-38`.
- **Now-dead from this session:** `backend/utils/downloadPrediction.py` (whole file — `get_model_predictions` no longer imported after predictions route change).
- Debug noise: `console.log` in `Dashboard.js:36,60,61` + `Navbar.js:75`; `print("DEBUG DIR...")` in `google_drive_service.py:211-218`.

### C. Hardcoded values & smells
- **Inline hyperparameter defaults that contradict `config.DEFAULT_HYPERPARAMS`** (latent bug): `knn`, `decisionTree`, `randomForest` (`n_estimators 10` vs `100`), `logisticRegression` (`C=1.0` vs `10.0`), `naiveBayes`, linear regressions. Reconcile, then drop inline fallbacks.
- `http://localhost:3000` fallbacks → derive from `FRONTEND_URL` (`subscription_route.py:174-221`, `oauth_route.py`).
- `'static/uploads'` hardcoded → use `UPLOAD_DIR`/`get_user_upload_dir` (`uploadFiles.py`); also make uploads user-scoped on disk.
- `'aiml_token'` in 12 files → export a `TOKEN_KEY` constant. `api.js:86` `'/login'` → `ROUTES.LOGIN`.
- `random_state=42` repeated inline → `RANDOM_SEED` constant. Duplicated Drive `SCOPES` → shared constant.
- ~40 `print()` → a configured `logging` logger. 10 bare `except:` → `except Exception:`. Log the swallowed provenance write at `preprocessing_service.py:270`.

### D. Features (from usability analysis — highest user value)
| Priority | Feature | Effort | Notes |
|---|---|---|---|
| 1 | **Live training charts** (loss/accuracy curves) | M | SSE already streams text; emit structured `{epoch, loss, val_acc}` events + chart. Needs a chart lib. |
| 2 | **Run comparison UI** (multi-select sessions → table + overlaid curves) | M | Pure frontend over `training_sessions` data. |
| 3 | **Predict-on-new-data** (`/predict/<session_id>`) | M | Models persist on Drive but are download-only today. |
| 4 | **Onboarding / sample projects** | S | No tour/starter flow today. High activation. |
| 5 | **Per-dataset leaderboard** | S | Cheap aggregation over session metrics. |
| 6 | **Surface dataset diff in UI** | S | `POST /datasets/diff` exists with no frontend entry point — nearly free. |
| 7 | **DataStudio → "Train on this output" handoff** | S | Versioned datasets exist; just wire a button. |
| 8 | **One-click "Apply pipeline to dataset"** | S | Pipelines are reusable; add an "Apply to…" dropdown on saved pipelines. |
| 9 | Cancel a running training job | M | SSE runs to completion; wastes quota on misconfig. |
| 10 | Hyperparameter sweep (lite), notebook/code export, dataset sharing/gallery, annotation polygons | L | Larger; later. |

### E. Optimizations (free-tier friendly)
- **MongoDB indexes** (cheap, high value): `training_sessions(user_id, created_at)`, `datasets(user_id, filename)`, `usage_counters(user_id, period)` unique, `users(email)` unique, `webhook_events(provider, event_id)` unique. Add via a migration (`backend/migrations/005_*.py`).
- **Rate limiter / usage counters / cache → Redis** when available (Upstash free tier). `extensions.py` limiter already abstracted — one-line `storage_uri` change. Keep `memory://` fallback for pure-free/local.
- **Big-CSV handling**: consider `polars` or chunked `pandas` for profiling/preprocessing large files; cap rows profiled.
- **Frontend data fetching**: consider `@tanstack/react-query` to replace ad-hoc fetch + the custom cache in `api.js` (dedupe, background refresh, less boilerplate).
- **Retention/cleanup job** for old sessions/artifacts + transient `static/uploads` (cron or startup sweep).

### F. Realtime & packages to evaluate
- **Realtime:** SSE (already used) is sufficient for one-way training progress/charts — no new service needed. Only add WebSockets/Socket.IO if bidirectional/collab is required. Multi-instance later → Redis pub/sub bridge. Hosted free options if needed: Ably/Pusher free tiers, Supabase Realtime.
- **Frontend packages:** `framer-motion` (animations/transitions), a chart lib (`recharts` or `chart.js`) for training curves, `react-query` (data layer), maybe `react-window` for very long lists.
- **Backend packages:** `python-json-logger` (structured logs), `sentry-sdk` (free tier error tracking), `polars` (fast CSV). Job queue (`rq`/`celery` + Redis) only if/when training is decoupled — parked for now.

### G. UI polish & animations (next "Claude design" pass)
- Add micro-interactions/transitions with `framer-motion`: page/route transitions, card hover, modal/toast enter-exit, button press.
- Skeleton loaders for Dashboard/Datasets/Studio instead of plain "Loading…".
- Animate the live training charts (#D1) and run-comparison.
- Keep the teal/cyan token system (see memory `ui-theme-teal-cyan`); no purple; respect `prefers-reduced-motion`.
- Accessibility pass: keyboard nav, focus rings (partly done), ARIA on the new modal/toast.

---

## 4. Suggested order for upcoming sessions
1. **Quick wins:** Mongo indexes (E) + surface dataset diff (D6) + DataStudio→train handoff (D7) + one-click pipeline apply (D8).
2. **Live training charts (D1)** + structured SSE — flagship feature; pairs with the UI/animation pass (G).
3. **Run comparison (D2)** + **predict-on-new-data (D3)**.
4. **UI/animation pass (G)** with framer-motion + charts.
5. **Cleanup pass (B + C)** LAST, so it also tidies everything added above.
6. Security deferred items (A) folded in opportunistically (M4 error-handler pass, `/api/uploads`).

---

## 5. Key files (orientation for a fresh session)
- Training dispatch: `backend/models/route.py` (`_train_model`, SSE routes). SSE helper: `backend/utils/sse_helpers.py`.
- Sessions/metrics/uploads-to-Drive: `backend/services/training_session_service.py`.
- Preprocessing/pipelines/diff: `backend/services/preprocessing_service.py` + `frontend/src/components/Studio/DataStudio.js`.
- Storage: `backend/services/google_drive_service.py`, `dataset_resolver.py`, `dataset_service.py`.
- Hyperparams (3 sources of truth): `config.py` `DEFAULT_HYPERPARAMS`, `services/hyperparam_validator.py`, `services/model_catalog.py`.
- Frontend dashboard/replay: `Dashboard.js`, `hooks/useReplaySession.js`. Theme: `index.css` + `context/ThemeContext.js`. Dialogs: `context/UIDialog.js`.
- Limiter: `backend/extensions.py`. Auth: `auth/authController.py`, `auth/auth_middleware.py`, `auth/oauth_route.py`.
