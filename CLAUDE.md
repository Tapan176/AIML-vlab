# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIML-vlab is a web-based AI/ML virtual lab where users can train and experiment with ~20 ML models (regression, classification, clustering, neural networks, NLP, generative) through an interactive UI. Stack: **React (CRA) frontend + Flask backend + MongoDB**, with Google Drive used as the primary cloud store for datasets and trained models.

## Common Commands

### Backend (Python / Flask)
```bash
cd backend
pip install -r requirements-dev.txt     # local dev — GPU-capable tensorflow + torch + ultralytics
# OR
pip install -r requirements.txt         # production/CPU — tensorflow-cpu + torch+cpu (matches Docker)

python app.py                           # dev server at http://127.0.0.1:5050
python -m migrations.migration_runner   # apply pending DB migrations explicitly (app.py also runs them on startup)
```

**Requirements file layout** (see `backend/requirements-*.txt`):
- `requirements-base.txt` — shared deps (flask, pymongo, numpy/pandas/sklearn, xgboost, opencv-headless). Included by the others via `-r`; don't install directly.
- `requirements-dev.txt` — local dev: base + `tensorflow` + `torch` + `torchvision` + `ultralytics` (GPU defaults; falls back to CPU on machines without CUDA).
- `requirements.txt` — production: base + `tensorflow-cpu` + `torch==X+cpu` (uses `--extra-index-url https://download.pytorch.org/whl/cpu`). Default for Docker.
- `requirements.railway.txt` — free-tier minimal: no DL stack at all; standalone (does NOT include base).

The Dockerfile defaults to `requirements.txt`. Switch via `docker build --build-arg REQUIREMENTS_FILE=requirements-dev.txt .` (rarely needed) or `--build-arg REQUIREMENTS_FILE=requirements.railway.txt .` for RAM-constrained platforms.

### Frontend (React)
```bash
cd frontend
npm install
npm start          # dev server at http://localhost:3000
npm run build      # production build to frontend/build/
npm test           # react-scripts test (CRA)
```

### One-shot dev launch (Windows)
```cmd
server.bat         # opens frontend + backend in separate cmd windows
```

### Docker
```bash
docker compose up --build              # backend on :5050, frontend (nginx) on :3000
```
The `REACT_APP_API_URL` is **baked into the React bundle at build time** via Docker build args — changing it requires a rebuild.

## Architecture

### Request flow for model training
1. Frontend model component (e.g. `frontend/src/components/Models/SimpleLinearRegression.js`) gathers a CSV dataset + `hyperparams` from `HyperparamPanel`, POSTs to a model route.
2. `backend/models/route.py` is the **single dispatch point** for every model. The generic handler `_train_model()` (lines 93–167) validates hyperparams, creates a `training_sessions` MongoDB record, calls the model's training function, then updates the session with results — including zipping artifacts and uploading to Google Drive.
3. Per-model training code lives in `backend/models/<modelName>/<modelName>.py`. Each accepts `(request, validated_params, user_id, session_version)` and returns a dict with keys: `outputImageUrls`, `evaluation_metrics`, `trained_model_path`, `predictions_output_file`, `hyperparams_used`.
4. After response, output images and local model files are **deleted** — they live only in Google Drive. The frontend gets base64-encoded images in the response so it can render them without a follow-up fetch.

### Two execution patterns coexist in `models/route.py`
- **Synchronous (classical ML):** routes use `_train_model()`. Models registered in `MODEL_FUNCTIONS`.
- **SSE-streaming (deep learning):** CNN, ANN, ResNet, LSTM, YOLO, StyleGAN each have their own route that yields `text/event-stream` chunks. These **lazy-import TensorFlow/PyTorch/Ultralytics inside the route function** to keep startup time low and avoid protobuf conflicts (see `os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'` at the top of `app.py`). When adding a new deep-learning model, follow this lazy-import pattern.

### Hyperparameter system (3 sources of truth, all must stay in sync)
- `backend/config.py` → `DEFAULT_HYPERPARAMS[model_code]` — the default values.
- `backend/services/hyperparam_validator.py` → `VALIDATION_SCHEMAS[model_code]` — type/range/enum validation.
- `backend/services/model_catalog.py` → `PARAM_LABELS`, `PARAM_NOTES` — UI labels and help text.

The frontend fetches the schema from `GET /api/model-schema/<model_code>` and renders inputs dynamically via `frontend/src/components/shared/HyperparamPanel.js`. Adding/changing a hyperparam means updating all three places.

### Storage strategy
- **Datasets and trained models live in Google Drive** (`backend/services/google_drive_service.py`), keyed by `drive_id` in MongoDB. Local filesystem is fallback only.
- `backend/services/dataset_resolver.py::resolve_image_dataset_path()` resolves image (ZIP) datasets. Client-supplied `filename`/`filePath` are **lookup keys only** — the resolver finds a dataset the user owns (or a curated default) and extracts it into that owner's cache (`get_user_extract_cache_dir`). Never return or join a client path directly.
- `backend/services/dataset_service.py::get_dataset_df()` is the canonical way to load a CSV dataset by name; `get_accessible_dataset(user_id, dataset_id)` is the owner-or-default access check for anything taking a `dataset_id`.
- Uploaded CSVs store only a small inline sample (`csv_data`, `CSV_INLINE_SAMPLE_ROWS`) plus `columns`/`row_count`; the full file lives on Drive.
- Per-user directories come from the helpers in `config.py` (`get_user_upload_dir`, `get_user_models_dir`, `get_user_extract_cache_dir`, `get_user_tmp_upload_dir`, `ensure_dir`). Classical models must write plots to `new_run_images_dir(user_id)` (a unique dir per run) — never a fixed filename in a shared folder.

### Auth
- JWT-based. `backend/auth/auth_middleware.py::token_required` is a decorator that can be used as `@token_required` (required) or `@token_required(optional=True)` (sets `current_user=None` if no token). Admin routes use `@admin_required`.
- **Revocation:** each user has `token_version`; JWTs carry it as `tv` and are rejected on mismatch. Bump it (`account_service.revoke_all_sessions`) whenever sessions must die — password change/reset, logout-all, admin deactivate/force-logout, deletion. Password-reset tokens are single-use (bound to the password hash).
- **Input validation:** anything that reaches a Mongo filter goes through `backend/utils/validators.py` first (`normalize_email`, `validate_password`, `clean_str`, `safe_regex` for `$regex` search). Emails are stored lower-cased.
- Account data management lives in `backend/services/account_service.py` (export, storage summary, cascade `purge_user_data`). Deleting a user must go through it so Drive files/sessions/datasets aren't orphaned.
- Frontend stores the JWT in `localStorage` under the key `aiml_token`. `frontend/src/services/api.js` is the centralized API client and redirects to `/login?next=…` on 401.

### MongoDB
- Connection in `backend/mongoDb/connection.py`. Always call `get_db()`, never instantiate `MongoClient` elsewhere.
- Collections: `users`, `datasets`, `training_sessions`, `models` (catalog), `feedback`, `pipelines`, `usage_counters`, `invoices`, `otp_codes`, `webhook_events`, `_migrations`.
- **Migrations** in `backend/migrations/00X_*.py` — each exports an `up(db)` function. They run automatically on app startup via `migration_runner.run_migrations()`. Use the next sequential prefix (currently `008_*.py`) for new migrations.

### Frontend conventions
- **Never use `process.env` outside `frontend/src/config.js`.** Everything else imports `API_URL` (and other constants) from `frontend/src/constants/index.js`. There is also a `constants` default export with `API_BASE_URL = API_URL` for legacy components.
- Pages are **lazy-loaded** in `App.js` (`React.lazy` + `Suspense`). Styles a page needs from another component's stylesheet won't be present until that chunk loads — put shared styles in `src/styles/responsive.css` or `Auth.css` (both imported globally in `index.js`).
- All routes wrapped in `<ProtectedRoute>` require an authenticated user; `<ProtectedRoute adminOnly>` also requires the admin role (`frontend/src/components/Auth/ProtectedRoute.js`).
- Never call `fetch` directly for the backend: use `api.get/post/put/patch/delete/upload`, `streamTraining()` for SSE training endpoints (buffered parser, handles 401/quota), and `downloadFile()` for authenticated downloads. Backend error codes are translated in `src/utils/errorMessages.js`.
- `AuthContext` (`frontend/src/context/AuthContext.js`) hits `/me` on mount to rehydrate the user; it also listens to the `storage` event so login/logout sync across tabs.

### Backend conventions
- **Never use `os.getenv` or `os.environ` outside `backend/config.py`.** Import named constants from `config`.
- All Flask blueprints are registered with `/api` prefix (e.g. `/api/linear-regression`, `/api/login`) — this matches the Vercel serverless deployment pattern and the docker-compose `REACT_APP_API_URL=http://localhost:5050/api` setting.
- Rate limiting via `flask_limiter` is configured globally in `app.py` (storage from `RATELIMIT_STORAGE_URI`; use Redis in production). OPTIONS preflight is exempted both at the limiter level and at `before_request` to keep CORS working.
- Don't return `str(e)` for unexpected exceptions — log with `log.exception(...)` and return a generic message; the global handler in `app.py` does this for anything uncaught. User-fixable errors (bad data, validation) may surface their message.
- When returning JSON containing model metrics, run results through `_sanitize_for_json()` in `models/route.py` — sklearn often produces `NaN`/`Infinity` which break strict JSON parsers. The frontend `api.js` also has a fallback that sanitizes `NaN` → `null` on parse failure.

### Adding a new ML model — checklist
1. Add model code to `MODEL_CODES` and a default entry to `DEFAULT_HYPERPARAMS` in `backend/config.py`.
2. Add validation schema in `backend/services/hyperparam_validator.py`.
3. Add labels + per-param notes in `backend/services/model_catalog.py`.
4. Create `backend/models/<newModel>/<newModel>.py` with the standard signature returning the standard result dict.
5. Sync models: add to `MODEL_FUNCTIONS` (a `'module:function'` string lazy-imports optional deps) and `_SYNC_ROUTES` in `backend/models/route.py` — no handler needed. Streaming models: add a route that lazy-imports the trainer and calls `run_sse_training` (enforces quota + the per-user concurrency cap).
6. Add a React component in `frontend/src/components/Models/<NewModel>.js` and wire it into navigation/routes.
7. Add the model code to the appropriate category in `MODEL_CATEGORIES` (`frontend/src/constants/index.js`).

## Environment & secrets

- `backend/.env` (gitignored) — see `backend/.env.example` for keys. `MONGO_URI`, `JWT_SECRET`, `ALLOWED_ORIGINS`, and Google Drive credentials (`GOOGLE_CREDENTIALS_JSON`/`GOOGLE_TOKEN_JSON` as raw JSON for Vercel, or `_PATH` variants pointing to local files) are the critical ones.
- `frontend/.env` — only `REACT_APP_API_URL` (read once at build time by CRA).
- `backend/credentials.json` and `backend/token.json` are gitignored and required for Google Drive OAuth; `generate_drive_token.py` is the helper to bootstrap `token.json`.

## Deployment notes

- **Frontend** ships to Vercel (`frontend/vercel.json` uses `@vercel/static-build` with SPA fallback routing).
- **Backend** is built around Vercel serverless conventions — all blueprints under `/api`, Google credentials read from env-JSON, gunicorn entry in the Dockerfile for Railway/Render. CPU vs GPU is selected by which requirements file you install (see above), not by editing a single file.
