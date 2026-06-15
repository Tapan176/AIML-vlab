# AIML-vLab Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Production Deploy                     │
├──────────────┬──────────────────┬───────────────────────┤
│   Frontend   │     Backend      │     Database          │
│  (React SPA) │  (Flask + TF)    │   (MongoDB Atlas)     │
│              │                  │                       │
│  Cloud Run   │  Cloud Run       │   Atlas M0 (Free)     │
│  or Vercel   │  or GCP VM       │   512MB RAM           │
│  (80MB)      │  (4-8GB RAM)     │                       │
└──────────────┴──────────────────┴───────────────────────┘
                              │
                    Google Drive API
                 (Models + Datasets)
```

## Option 1: GCP (Recommended for occasional use)

### Prerequisites
1. GCP account with billing enabled (free trial: $300 credit / 90 days)
2. `gcloud` CLI installed and authenticated
3. MongoDB Atlas free tier cluster

### Step 1: Deploy Backend to Cloud Run

The repo's existing `backend/Dockerfile` is already Cloud Run-ready: it binds
`$PORT` (Cloud Run injects `8080`), runs gunicorn as a non-root user, and is the
same image used for Railway/Render — so there is **one** Dockerfile to maintain.
`gcloud run deploy --source` auto-detects it (any file literally named
`Dockerfile`). Secrets stay out of the build context because `.env`,
`credentials.json`, and `token.json` are gitignored (and also in
`.dockerignore`), and `--source` respects `.gitignore`.

```bash
cd backend

# Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# Build (Cloud Build) + deploy in one step, straight from the Dockerfile.
gcloud run deploy aiml-backend \
  --source . \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600 \
  --concurrency 2 \
  --max-instances 1 \
  --set-env-vars "WEB_CONCURRENCY=1" \
  --set-env-vars "GUNICORN_TIMEOUT=600" \
  --set-env-vars "MONGO_URI=mongodb+srv://..." \
  --set-env-vars "JWT_SECRET=your-secret" \
  --set-env-vars "ALLOWED_ORIGINS=https://your-frontend-url.web.app" \
  --set-env-vars "GOOGLE_CREDENTIALS_JSON=...,GOOGLE_TOKEN_JSON=..." \
  --allow-unauthenticated
```

> **Why `WEB_CONCURRENCY=1`?** The image's gunicorn CMD defaults to 2 workers
> (good for the ~512 MB Railway free tier). On Cloud Run with TensorFlow **and**
> PyTorch loaded, each worker holds its own copy of the frameworks — 2 workers
> will OOM a 4 GiB instance. Run a single worker and scale with instances/CPU,
> not workers. `--timeout 600` (deploy) and `GUNICORN_TIMEOUT=600` must agree so
> Cloud Run doesn't cut a request the worker is still serving.

> **Long secrets:** for `GOOGLE_CREDENTIALS_JSON` / `GOOGLE_TOKEN_JSON` (multi-line
> JSON) and `JWT_SECRET`, prefer Secret Manager over `--set-env-vars`:
> `gcloud run deploy ... --set-secrets "GOOGLE_TOKEN_JSON=drive-token:latest"`.

### Step 2: Deploy Frontend to Firebase Hosting (free)

```bash
cd frontend

# Build with the backend URL
REACT_APP_API_URL=https://aiml-backend-xxxxx-uc.a.run.app/api npm run build

# Deploy to Firebase
firebase init hosting
firebase deploy --only hosting
```

### Cost Estimate (Cloud Run, occasional use)
- Idle (no requests): $0/month (scales to zero)
- 100 training sessions/month: ~$5-10/month
- Free tier covers: first 2M requests, 360K vCPU-seconds, 180K GiB-seconds

### Cloud Run gotchas for this app
- **Ephemeral, in-memory filesystem.** Cloud Run's `/app` writes (uploads,
  `trainedModels/`, predictions) live in RAM and count against `--memory`. This
  app already treats local files as scratch and persists artifacts to Google
  Drive, so size `--memory` for *model + framework + the largest temp file*, not
  long-term storage. Files vanish when the instance scales to zero — by design.
- **Cold starts are slow.** First request after idle pays for the container boot
  plus the lazy TF/PyTorch/Ultralytics import on the first DL route. Expect tens
  of seconds. Set `--min-instances 1` to keep one warm (you lose scale-to-zero
  and pay ~always-on for that instance).
- **Request timeout caps the training job.** A synchronous train must finish
  within `--timeout` (max **3600s / 60 min** on Cloud Run). Long DL runs that
  exceed this need the split/async approach in Option 3, or a GPU VM (Option 2).
- **SSE streaming works** (CNN/ANN/ResNet/LSTM/YOLO/StyleGAN + fine-tuning) as
  long as the whole stream completes inside `--timeout`. Keep `--concurrency`
  low (1–2) so one instance isn't juggling multiple heavy trainings.
- **No GPU on the standard service.** Cloud Run GPU is a separate (preview)
  product; the default image is CPU-only (`requirements.txt`). Heavy ViT/StyleGAN
  training will be slow — fine for demos, not for large datasets.

## Option 2: Single GCP VM (simpler, always-on)

```bash
# Create e2-standard-2 (2 vCPU, 8GB RAM) — ~$50/month
gcloud compute instances create aiml-vlab \
  --zone us-central1-a \
  --machine-type e2-standard-2 \
  --boot-disk-size 50GB \
  --image-family ubuntu-2204-lts \
  --image-project ubuntu-os-cloud

# SSH in and deploy with Docker Compose
gcloud compute ssh aiml-vlab
# Install Docker, clone repo, docker compose up
```

## Option 3: Split Deployment (Lightweight + On-Demand DL)

1. **Classical ML service**: Cloud Run with `requirements.railway.txt`
   (Flask + sklearn + xgboost + pandas; **no** TF/PyTorch — DL routes return errors here)
   - Image: ~500 MB, fits in 1 GB RAM, near-$0 for occasional use, always responsive
2. **Deep Learning service**: separate Cloud Run service with full `requirements.txt`
   - 4 GB+ RAM, scales to zero when idle; front the two with a path-based router/LB

The Dockerfile selects the profile via the `REQUIREMENTS_FILE` build arg, but
`gcloud run deploy --source` can't pass build args. For the lightweight image,
build explicitly then deploy by image:

```bash
# Build the no-DL image with Cloud Build, overriding the requirements profile
gcloud builds submit backend \
  --tag REGION-docker.pkg.dev/PROJECT/REPO/aiml-light \
  --substitutions _REQ=requirements.railway.txt \
  --config backend/cloudbuild.light.yaml      # a 1-step config that runs:
  #   docker build --build-arg REQUIREMENTS_FILE=$_REQ -t $_IMAGE backend

gcloud run deploy aiml-light \
  --image REGION-docker.pkg.dev/PROJECT/REPO/aiml-light \
  --region us-central1 --memory 1Gi --cpu 1 --allow-unauthenticated
```

(The default `--source .` flow in Option 1 already builds the full DL image, so
the DL service needs no special steps.)

## MongoDB Atlas Setup (Free)

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create M0 (free) cluster
3. Add database user + whitelist IP (0.0.0.0/0 for Cloud Run)
4. Get connection string: `mongodb+srv://user:pass@cluster.mongodb.net/aiml-lab`
5. Set as `MONGO_URI` env var

## Google Drive Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download credentials.json → place in `backend/`
4. Run `python generate_drive_token.py` locally to get token.json
5. Upload both as env vars:
   - `GOOGLE_CREDENTIALS_JSON` = contents of credentials.json
   - `GOOGLE_TOKEN_JSON` = contents of token.json

## HuggingFace Setup (for Fine-Tuning)

1. Create account at https://huggingface.co
2. Generate token at https://huggingface.co/settings/tokens
3. Set `HF_TOKEN` env var

## OAuth Setup (Google Login)

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add redirect URI: `https://YOUR_BACKEND_URL/api/auth/google/callback`
4. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` env vars

> ⚠️ **Known limitation (not yet production-verified):** `auth/oauth_route.py`
> currently derives the callback URL from the request `Origin` by swapping port
> `3000`→`5050` — a local-dev assumption. In a split prod deploy (Firebase
> frontend + Cloud Run backend on different domains) that produces the wrong
> `redirect_uri` and Google will reject it. Before enabling OAuth in prod, pin
> the callback to an explicit env var (e.g. `OAUTH_REDIRECT_BASE`) instead of
> rewriting the origin. Tracked as a separate task; OAuth can stay disabled
> (omit the client-id env vars) and password login works unaffected.

## Environment Variables Checklist

```
MONGO_URI=                    # MongoDB Atlas connection string
JWT_SECRET=                   # Random 64-char string
ALLOWED_ORIGINS=              # Comma-separated frontend URLs
GOOGLE_CREDENTIALS_JSON=      # credentials.json content (JSON string)
GOOGLE_TOKEN_JSON=            # token.json content (JSON string)
HF_TOKEN=                     # (optional) HuggingFace API token
GOOGLE_CLIENT_ID=             # (optional) Google OAuth client ID
GOOGLE_CLIENT_SECRET=         # (optional) Google OAuth secret
GITHUB_CLIENT_ID=             # (optional) GitHub OAuth client ID
GITHUB_CLIENT_SECRET=         # (optional) GitHub OAuth secret
```
