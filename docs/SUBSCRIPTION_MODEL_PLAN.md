# Subscription Model — Architecture Plan (Future Version)

> Status: **PLAN ONLY.** Nothing here is implemented yet. This documents how
> we would introduce tiered usage (a limited Free tier + paid plans) into
> AIML-vlab without rewriting the training/storage core.

## 1. Goals & principles

- **Free tier stays genuinely useful** for learning & light experimentation.
- **Meter the things that actually cost us** (compute + storage), not vanity
  counts. The expensive operations here are deep-learning / fine-tuning runs
  (GPU/CPU minutes) and Google Drive storage of datasets + model artifacts.
- **Fail soft & transparent**: when a user hits a limit, tell them exactly
  which limit, the reset time, and the upgrade path — never a silent 500.
- **Entitlements are server-enforced.** The frontend only *reflects* limits;
  every limit is also checked in the backend before work is done.
- **Plans are data, not code.** A `plans` collection defines limits so we can
  tune them without a deploy.

## 2. Cost drivers in this app (what we meter)

Derived from the current architecture (`backend/models/route.py`,
`finetune_routes.py`, `services/google_drive_service.py`, `training_sessions`):

| Driver | Where it happens | Why it costs |
|---|---|---|
| **Classical ML run** (regression, trees, SVM, KMeans, …) | `_train_model()` sync | Cheap CPU, seconds |
| **Deep-learning run** (CNN, ANN, ResNet, LSTM, YOLO, StyleGAN) | SSE routes | Minutes of CPU/GPU |
| **Fine-tuning run** (BERT, DistilBERT, ViT) | `finetune_routes.py` | Most expensive; downloads base model + trains |
| **Dataset storage** | Drive upload on dataset create | GB stored |
| **Model-artifact storage** | `update_session_results()` zips → Drive | GB stored, grows per run |
| **Retention** | sessions/artifacts never auto-expire today | unbounded storage growth |
| **Concurrency** | multiple SSE streams | server memory/CPU |

So the metered units are: **runs/month (split by class), stored GB, retained
sessions, concurrent jobs.** Everything else (model variety, previews,
profiling, replay) is a *feature flag*, not a counter.

## 3. Proposed tiers

Three launch tiers + an Enterprise conversation. Prices are placeholders for
an education-oriented product (USD/month, annual ≈ 2 months free).

| | **Free** | **Pro** ($9/mo) | **Team** ($29/seat/mo) | **Enterprise** |
|---|---|---|---|---|
| Price | $0 | $9 | $29/seat | Custom |
| Classical ML runs / mo | 50 | Unlimited* | Unlimited* | Unlimited |
| Deep-learning runs / mo | 5 | 100 | 400/seat | Custom |
| Fine-tuning runs / mo | 0 (preview only) | 20 | 100/seat | Custom |
| Concurrent training jobs | 1 | 2 | 4/seat | Custom |
| Dataset storage | 500 MB | 10 GB | 50 GB pooled | Custom |
| Max single dataset | 50 MB | 1 GB | 5 GB | Custom |
| Trained-model retention | 7 days | 90 days | 1 year | Configurable |
| Session history kept | 20 | Unlimited | Unlimited | Unlimited |
| Dataset versions / pipelines | basic | full | full | full |
| Data profiling & diff | ✓ | ✓ | ✓ | ✓ |
| Replay sessions | ✓ | ✓ | ✓ | ✓ |
| Priority queue (skip ahead) | – | ✓ | ✓ | ✓ |
| GPU-backed training (when available) | – | ✓ | ✓ | dedicated |
| Team workspace / shared datasets | – | – | ✓ | ✓ |
| API / programmatic access (future) | – | limited | ✓ | ✓ |
| Support | community | email | priority | SLA |

\* "Unlimited" classical runs are still **rate-limited** (e.g. 60/hour) via the
existing `flask_limiter` to stop abuse — that's a guardrail, not a quota.

**Why fine-tuning = 0 on Free:** it's our heaviest operation. Free users still
get to *see* the fine-tuning UI and a sample/demo result (preview), which is a
natural upgrade prompt.

## 4. Data model changes

### `users` (add fields)
```jsonc
{
  "subscription": {
    "plan": "free",              // free | pro | team | enterprise
    "status": "active",          // active | past_due | canceled | trialing
    "seats": 1,
    "team_id": null,             // set when part of a Team workspace
    "stripe_customer_id": null,
    "stripe_subscription_id": null,
    "current_period_end": null,  // datetime; entitlements valid until here
    "trial_end": null
  }
}
```

### `plans` (new collection — limits as data)
```jsonc
{
  "_id": "pro",
  "display_name": "Pro",
  "price_cents": 900,
  "limits": {
    "classical_runs_month": null,        // null = unlimited (still rate-limited)
    "deep_runs_month": 100,
    "finetune_runs_month": 20,
    "concurrent_jobs": 2,
    "storage_bytes": 10737418240,
    "max_dataset_bytes": 1073741824,
    "model_retention_days": 90,
    "session_history": null
  },
  "features": ["priority_queue", "gpu", "api_limited"]
}
```

### `usage_counters` (new collection — fast, resettable)
One doc per `(user_id, period)` where period = `YYYY-MM`:
```jsonc
{
  "user_id": "…",
  "period": "2026-06",
  "classical_runs": 12,
  "deep_runs": 3,
  "finetune_runs": 1,
  "storage_bytes": 734003200,   // maintained on upload/delete
  "updated_at": "…"
}
```
- Counters increment with an atomic `$inc` at run start.
- Monthly counters reset implicitly by keying on `period` (new month → new doc).
- `storage_bytes` is a running total adjusted on dataset/artifact create+delete,
  reconciled by a nightly job against Drive.

### `usage_events` (optional, append-only audit/billing)
One row per metered action (`run`, `upload`, `delete`) for analytics, dispute
resolution, and future usage-based billing.

## 5. Enforcement architecture

A single **entitlement service** is the only thing that knows the rules.

```
backend/services/entitlement_service.py
  get_plan(user)                  -> resolved plan doc (cached, 60s TTL)
  get_usage(user, period)         -> usage_counters doc (create if missing)
  check_quota(user, action)       -> Ok | QuotaExceeded(limit, used, reset_at, upgrade_to)
  record_usage(user, action, n=1) -> atomic $inc
  check_storage(user, add_bytes)  -> Ok | QuotaExceeded
  adjust_storage(user, delta)     -> $inc storage_bytes
```

### Decorator + hook points

```python
@require_quota('deep_run')          # raises 402/429 with structured body
```

Hook it at the **single dispatch points** that already exist, so we touch few
files:

- **Classical / sync** → inside `_train_model()` (`models/route.py`,
  ~line 93) before creating the session: `check_quota(user, 'classical_run')`,
  then `record_usage` after a successful start.
- **Deep learning + fine-tuning** → inside `run_sse_training()`
  (`utils/sse_helpers.py`) before `create_session()` — one place covers CNN,
  ANN, ResNet, LSTM, YOLO, StyleGAN, BERT, DistilBERT, ViT. Map `model_code`
  → run-class (`deep_run` vs `finetune_run`) via the model registry.
- **Concurrency** → count `training_sessions` with `status in (pending,
  running)` for the user before allowing a new run.
- **Storage** → in the dataset upload route and in
  `update_session_results()` (artifact upload): `check_storage` before, then
  `adjust_storage` after; `adjust_storage(-size)` on delete.
- **Retention** → a scheduled job (cron/Celery/APScheduler) deletes Drive
  artifacts + flips sessions to `expired` past `model_retention_days`. Reuses
  the existing `delete_session_folder_from_drive` path.

### Error contract (frontend-friendly)
```jsonc
HTTP 402 Payment Required
{
  "error": "quota_exceeded",
  "limit": "finetune_runs_month",
  "used": 20, "allowed": 20,
  "reset_at": "2026-07-01T00:00:00Z",
  "upgrade_to": "team",
  "message": "You've used all 20 fine-tuning runs this month."
}
```
`frontend/src/services/api.js` already centralizes responses — add a 402
handler that opens an upgrade modal (mirrors the existing 401→/login pattern).

## 6. Billing integration (Stripe)

- **Stripe Checkout** for purchase/upgrade; **Customer Portal** for
  manage/cancel — avoids handling card data ourselves.
- **Webhook** (`/api/billing/webhook`) is the source of truth: on
  `checkout.session.completed`, `customer.subscription.updated/deleted`,
  update `users.subscription` (plan, status, `current_period_end`).
- Entitlements key off `subscription.status == active/trialing` AND
  `current_period_end > now`. On `past_due`, soft-grace for N days then drop to
  Free limits (don't delete data).
- **Downgrade handling:** if new plan's storage < current usage, block new
  uploads (read-only) until under limit; never auto-delete user data — warn and
  let them prune.

## 7. Frontend surface

- **Pricing page** (public) rendered from the `plans` collection.
- **Usage widget** on the Dashboard: "Deep-learning runs: 3 / 5 this month",
  storage bar, reset date. (Replaces nicely the stat-card real estate.)
- **Upgrade modal** triggered by 402s and by locked features (e.g. Free user
  opening fine-tuning sees a "Preview — upgrade to run" state).
- **Billing settings** page → Stripe Customer Portal link.
- Gate UI affordances by entitlements fetched once (`GET /api/me/entitlements`)
  — but remember the server re-checks everything.

## 8. Rollout phasing

1. **Phase 0 — Meter, don't enforce.** Add counters + `usage_events`, show the
   usage widget. Learn real usage distributions; set limits from data.
2. **Phase 1 — Soft enforce.** Warn at thresholds; allow overflow. Validate the
   402 UX and messaging.
3. **Phase 2 — Hard enforce Free limits + launch Pro.** Stripe Checkout,
   webhooks, retention job.
4. **Phase 3 — Team workspaces** (shared `team_id`, pooled storage, seats).
5. **Phase 4 — API access & usage-based add-ons** (per-GPU-minute overage).

## 9. Open questions / decisions to make later

- Real GPU backend? Today training runs in-process; "GPU tier" needs a worker
  queue (Celery/RQ + GPU workers) before it's a sellable feature.
- Run-cost weighting: flat per-run, or weight by epochs/dataset size/wall-clock?
  (Start flat; move to weighted once `usage_events` shows the spread.)
- Education/student discount & academic site licenses.
- Region/currency, taxes (Stripe Tax).
- Data-retention legal/communication when artifacts expire on Free.

## 10. Smallest viable first step

Ship **Phase 0** behind everything else: `entitlement_service` with
`record_usage` wired into `_train_model` and `run_sse_training`, plus the
Dashboard usage widget. Zero enforcement, zero billing — just truth about usage
to price the tiers correctly.
