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
python -m pytest                        # run the backend test-suite (needs requirements-dev.txt: pytest + mongomock)
```

The Flask app is built by an **application factory** — `create_app()` in `backend/app.py`. Importing `app` has no side effects (no DB connect, no migrations); those happen inside `create_app()`. Production runs `gunicorn "app:create_app()"` (see Dockerfile); `python app.py` calls the factory for the dev server. Tests call `create_app(testing=True, init_database=False, ...)` and inject an in-memory `mongomock` DB via `mongoDb.connection.init_db(client_factory=...)` — see `backend/tests/conftest.py`.

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
- `backend/services/dataset_resolver.py` resolves image (ZIP) datasets: tries local cache → DB `extracted_path` → downloads from Drive and extracts to a per-user cache dir.
- `backend/services/dataset_service.py::get_dataset_df()` is the canonical way to load a CSV dataset — it transparently pulls from Drive or local disk.
- Per-user directories are computed by `get_user_upload_dir / get_user_models_dir / ensure_dir` in `config.py`. Always use those helpers, never hardcode paths.

### Auth
- JWT-based. `backend/auth/auth_middleware.py::token_required` is a decorator that can be used as `@token_required` (required) or `@token_required(optional=True)` (sets `current_user=None` if no token). Admin routes use `@admin_required`.
- Frontend stores the JWT in `localStorage` under the key `aiml_token`. `frontend/src/services/api.js` is the centralized API client and auto-redirects to `/login` on 401.

### MongoDB
- Connection in `backend/mongoDb/connection.py`. Always call `get_db()`, never instantiate `MongoClient` elsewhere.
- Collections: `users`, `datasets`, `training_sessions`, `models` (catalog), `feedback`, `_migrations`.
- **Migrations** in `backend/migrations/00X_*.py` — each exports an `up(db)` function. They run automatically on app startup via `migration_runner.run_migrations()`. Use the next sequential prefix (`004_*.py`) for new migrations.

### Frontend conventions
- **Never use `process.env` outside `frontend/src/config.js`.** Everything else imports `API_URL` (and other constants) from `frontend/src/constants/index.js`. There is also a `constants` default export with `API_BASE_URL = API_URL` for legacy components.
- All routes wrapped in `<ProtectedRoute>` require an authenticated user (`frontend/src/components/Auth/ProtectedRoute.js`).
- `AuthContext` (`frontend/src/context/AuthContext.js`) hits `/me` on mount to rehydrate the user; it also listens to the `storage` event so login/logout sync across tabs.

### Backend conventions
- **Never use `os.getenv` or `os.environ` outside `backend/config.py`.** Import named constants from `config`.
- All Flask blueprints are registered with `/api` prefix (e.g. `/api/linear-regression`, `/api/login`) — this matches the Vercel serverless deployment pattern and the docker-compose `REACT_APP_API_URL=http://localhost:5050/api` setting.
- Rate limiting via `flask_limiter` is configured globally in `app.py`. OPTIONS preflight is exempted both at the limiter level and at `before_request` to keep CORS working.
- When returning JSON containing model metrics, run results through `_sanitize_for_json()` in `models/route.py` — sklearn often produces `NaN`/`Infinity` which break strict JSON parsers. The frontend `api.js` also has a fallback that sanitizes `NaN` → `null` on parse failure.

### Adding a new ML model — checklist
1. Add model code to `MODEL_CODES` and a default entry to `DEFAULT_HYPERPARAMS` in `backend/config.py`.
2. Add validation schema in `backend/services/hyperparam_validator.py`.
3. Add labels + per-param notes in `backend/services/model_catalog.py`.
4. Create `backend/models/<newModel>/<newModel>.py` with the standard signature returning the standard result dict.
5. Register in `MODEL_FUNCTIONS` and `MODEL_ROUTES` in `backend/models/route.py`, add a route handler (use `_train_model` for sync, or the SSE pattern for deep learning).
6. Add a React component in `frontend/src/components/Models/<NewModel>.js` and wire it into navigation/routes.
7. Add the model code to the appropriate category in `MODEL_CATEGORIES` (`frontend/src/constants/index.js`).

## Environment & secrets

- `backend/.env` (gitignored) — see `backend/.env.example` for keys. `MONGO_URI`, `JWT_SECRET`, `ALLOWED_ORIGINS`, and Google Drive credentials (`GOOGLE_CREDENTIALS_JSON`/`GOOGLE_TOKEN_JSON` as raw JSON for Vercel, or `_PATH` variants pointing to local files) are the critical ones.
- `frontend/.env` — only `REACT_APP_API_URL` (read once at build time by CRA).
- `backend/credentials.json` and `backend/token.json` are gitignored and required for Google Drive OAuth; `generate_drive_token.py` is the helper to bootstrap `token.json`.

## Deployment notes

- **Frontend** ships to Vercel (`frontend/vercel.json` uses `@vercel/static-build` with SPA fallback routing).
- **Backend** is built around Vercel serverless conventions — all blueprints under `/api`, Google credentials read from env-JSON, gunicorn entry in the Dockerfile for Railway/Render. CPU vs GPU is selected by which requirements file you install (see above), not by editing a single file.
