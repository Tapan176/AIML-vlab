# Payments, Subscriptions, Pricing & Abuse-Prevention Guide

This document covers:

1. [What was implemented](#1-what-was-implemented)
2. [Step-by-step Stripe setup](#2-step-by-step-stripe-setup)
3. [Local testing with the Stripe CLI](#3-local-testing-with-the-stripe-cli)
4. [Going live (production)](#4-going-live-production)
5. [Pricing & feature recommendations](#5-pricing--feature-recommendations)
6. [Security & abuse review](#6-security--abuse-review)
7. [Rate limits & storage caps](#7-rate-limits--storage-caps)
8. [Operational runbook](#8-operational-runbook)

---

## 1. What was implemented

**Provider:** Stripe (Checkout + Billing Portal, hosted). Free to set up — Stripe
charges only per successful payment (~2.9% + $0.30 US; varies by region). Test
mode is free and unlimited. Stripe supports 195+ countries / 135+ currencies.

**Currency display:** Stripe **Adaptive Pricing** localizes the currency on the
hosted checkout page automatically. The pricing page also shows the price in the
visitor's local currency (via geo-IP + `Intl.NumberFormat`) — display only; the
canonical price is the same everywhere.

### Backend
| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/subscription/plans` | public | Plan catalog + `payments_enabled` + publishable key |
| `GET /api/subscription/me` | user | Current plan, limits, month-to-date usage |
| `GET /api/billing/locale` | public | Geo-IP country → display currency |
| `POST /api/billing/checkout` | user | Create Stripe Checkout Session → returns URL |
| `POST /api/billing/portal` | user | Open Stripe Billing Portal (manage/cancel) |
| `POST /api/billing/webhook` | Stripe sig | **Source of truth** — activates/cancels subs |

- `services/subscription_service.py` — plans, quotas, usage counters, storage
  caps, Stripe↔plan mapping, `set_user_subscription` (writes `user.subscription`).
- Webhook verifies the Stripe signature (`STRIPE_WEBHOOK_SECRET`) and is exempt
  from the rate limiter.
- Graceful degradation: with no `STRIPE_SECRET_KEY`, billing endpoints return
  `503 payments_not_configured` and the UI shows "Coming soon".

### Frontend
- `PricingPage.js` — localized prices, "Upgrade to Pro/Team" → redirects to
  Stripe Checkout, "Manage billing" → Billing Portal, marks the current plan.
- `SubscriptionContext` — real-time usage refresh (training/usage events +
  window focus/visibility).
- `UsageWidget` (on Profile) — shows classical / deep / finetune / Data Studio.

### Config (env)
All optional. See `backend/.env.example`. Key ones:
```
SUBSCRIPTION_ENABLED=true
STRIPE_SECRET_KEY=sk_test_…
STRIPE_PUBLISHABLE_KEY=pk_test_…
STRIPE_WEBHOOK_SECRET=whsec_…
STRIPE_PRICE_PRO=price_…
STRIPE_PRICE_TEAM=price_…
STRIPE_SUCCESS_URL=http://localhost:3000/profile
STRIPE_CANCEL_URL=http://localhost:3000/pricing
```

---

## 2. Step-by-step Stripe setup

1. **Create a Stripe account** at https://dashboard.stripe.com (keep it in
   **Test mode** while developing — toggle top-right).
2. **Get API keys:** Dashboard → Developers → API keys. Copy:
   - *Publishable key* → `STRIPE_PUBLISHABLE_KEY`
   - *Secret key* → `STRIPE_SECRET_KEY`
3. **Create Products + recurring Prices:**
   - Dashboard → Product catalog → **Add product**.
   - Product "ML Lab Pro" → add a **recurring** price, $9 / month → save → copy
     the Price ID (`price_…`) → `STRIPE_PRICE_PRO`.
   - Repeat for "ML Lab Team" → $29 / month → `STRIPE_PRICE_TEAM`.
4. **Enable Adaptive Pricing (optional, for local currencies):**
   Dashboard → Settings → Checkout and Payment Links → **Adaptive Pricing** → On.
5. **Enable the Billing Portal:** Dashboard → Settings → Billing → Customer
   portal → activate; allow plan switching + cancellation.
6. **Set env vars** in `backend/.env` (see block above) and
   `SUBSCRIPTION_ENABLED=true`.
7. **Install the dependency** (already in `requirements-base.txt`):
   `pip install "stripe>=9.0,<13"`.
8. **Restart the backend** (it reads env at import).

---

## 3. Local testing with the Stripe CLI

The webhook is how subscriptions actually activate, so you must forward events
to your local server.

```bash
# 1. Install the Stripe CLI: https://stripe.com/docs/stripe-cli
stripe login

# 2. Forward webhooks to your local backend
stripe listen --forward-to http://localhost:5050/api/billing/webhook
#   → prints a signing secret: whsec_…  → put it in STRIPE_WEBHOOK_SECRET, restart backend

# 3. In the app: open /pricing → "Upgrade to Pro" → you're sent to Stripe Checkout.
#    Use a test card: 4242 4242 4242 4242, any future expiry, any CVC, any ZIP.

# 4. After paying, Stripe fires checkout.session.completed → the CLI forwards it
#    → the webhook sets user.subscription = { plan: 'pro', status: 'active' }.
#    Refresh the Profile page: usage limits now reflect Pro.

# Optional: trigger events manually
stripe trigger checkout.session.completed
stripe trigger customer.subscription.deleted   # simulates a cancel → back to free
```

**Test cards:** `4242…` succeeds, `4000 0000 0000 9995` fails (insufficient
funds), `4000 0025 0000 3155` requires 3D-Secure. Full list:
https://stripe.com/docs/testing.

---

## 4. Going live (production)

1. Toggle the dashboard to **Live mode**, redo Products/Prices, copy **live**
   keys (`sk_live_…`, `pk_live_…`) into your prod env.
2. **Register the webhook endpoint:** Dashboard → Developers → Webhooks → Add
   endpoint → `https://YOUR_BACKEND/api/billing/webhook`. Subscribe to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   Copy the endpoint's **signing secret** → `STRIPE_WEBHOOK_SECRET` (prod).
3. Set `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` to your prod frontend URLs.
4. Complete Stripe **account activation** (business details, bank account) to
   receive payouts. India: enable international card acceptance if selling abroad.
5. Ensure the webhook route is reachable **without** auth and that any
   WAF/proxy forwards the raw body (signature verification needs it byte-exact).

---

## 5. Pricing & feature recommendations

### Recommended tiers (tuned to attract Pro upgrades)

| | **Free** | **Pro — $9/mo** | **Team — $29/mo** |
|---|---|---|---|
| Classical ML runs | 50/mo | **Unlimited** | Unlimited |
| Deep learning runs | 5/mo | 100/mo | 400/mo |
| Fine-tuning runs | **0** (locked) | 20/mo | 100/mo |
| Data Studio ops | 100/mo | Unlimited | Unlimited |
| Datasets stored | 20 | 200 | 1000 |
| Replay, profiling, versions | ✓ | ✓ | ✓ |
| Priority queue / GPU / all models | — | ✓ | ✓ |
| Shared workspace / API access | — | — | ✓ |

**Why this converts well:**
- **Fine-tuning locked on Free (0)** is the single biggest upgrade driver —
  it's the most expensive workload and the most desirable "pro" capability.
  Users hit the wall exactly where the value is highest.
- **Deep learning at 5/mo** lets people *taste* CNN/LSTM/ResNet, then run out —
  a classic "aha, I need more" trigger without feeling cheated.
- **Classical unlimited on Pro** removes nagging friction for the bread-and-butter
  workflow, making $9 feel generous.
- **$9** is an impulse-level price (below the ~$10 psychological threshold);
  **$29 Team** is anchored 3x higher so Pro looks like the obvious value pick.
- Keep **profiling/replay/versions free** — they're cheap and increase
  engagement/retention, which feeds conversions.

**Optional levers to test later:** annual billing (2 months free), a 7-day Pro
trial, student discount, and usage-based add-on packs (e.g. +50 deep runs).

> To change limits, edit `PLANS` in `services/subscription_service.py` and the
> `FREE_TIER_*` env vars. To change prices, update the Stripe Price objects AND
> the `price` field in `PLANS` (display only).

---

## 6. Security & abuse review

### Fixed / implemented
- ✅ **Quota enforcement server-side** at session creation (`check_quota` +
  `record_usage`) — can't be bypassed from the client.
- ✅ **Webhook signature verification** — only genuine Stripe events mutate
  subscriptions; the client redirect is never trusted to grant a plan.
- ✅ **Upload size guard** — `Content-Length` check (413) + global
  `MAX_CONTENT_LENGTH` backstop so huge bodies can't exhaust memory/disk.
- ✅ **Per-account dataset storage caps** (`check_storage_quota`) on upload and
  preprocessing output.
- ✅ **Data Studio metering** — preprocessing runs count against `datastudio`
  quota (profiling/diff stay free, read-only).
- ✅ **Rate limiter** global default (`2000/day, 500/hour` per IP); webhook
  exempted (verified by signature instead).
- ✅ **JWT auth** on all mutating endpoints; deactivated accounts rejected.

### Remaining risks & recommendations
| Risk | Severity | Recommendation |
|---|---|---|
| **Free-account farming** (many signups to dodge quotas) | Med | Add email verification before training; consider per-IP signup throttle. |
| **No quota on raw model training rate** beyond monthly count | Med | Add a per-route `@limiter.limit("10/minute")` on training endpoints to stop burst abuse within quota. |
| **Profiling endpoint unmetered** (CPU on big CSVs) | Low | Already cheap; cap dataset rows profiled, or meter if abused. |
| **Drive storage cost** (datasets + result zips accumulate) | Med | Storage caps added; also add a retention/cleanup job for old sessions. |
| **Webhook replay** | Low | Stripe signatures include a timestamp; optionally store processed `event.id`s to dedupe. |
| **In-memory rate limiter** resets on restart / not shared across workers | Med | Use Redis (`storage_uri="redis://…"`) in production. |
| **Secrets in `.env`** committed risk | High | `.env` is gitignored — keep it so; never commit live keys. Rotate the JWT secret + any leaked keys. |
| **Quota check race** (two concurrent runs slip past the cap) | Low | Acceptable; for strictness, use an atomic `find_one_and_update` guard. |

---

## 7. Rate limits & storage caps

**Do you need more limits?** Yes — recommended additions:

1. **Per-route burst limits** on expensive endpoints (training, preprocess,
   upload). The monthly quota stops *volume*; a per-minute limit stops *bursts*:
   ```python
   # in models/route.py, with the shared limiter
   @limiter.limit("10 per minute")
   ```
2. **Dataset version creation** — preprocessing already creates versioned
   datasets and is now metered (`datastudio`) + storage-capped. Good.
3. **Upload size** — enforced (413 + `MAX_CONTENT_LENGTH`). Tune
   `MAX_UPLOAD_SIZE_MB` per your hosting limits.
4. **Storage caps** — `FREE_TIER_MAX_DATASETS=20`, Pro 200, Team 1000 (env-tunable).
5. **Production rate limiter** — switch `storage_uri` to Redis so limits are
   shared across gunicorn workers and survive restarts.

---

## 8. Operational runbook

- **A user paid but is still on Free:** check the webhook was received
  (`stripe listen` output / Dashboard → Webhooks → event log). Verify
  `STRIPE_WEBHOOK_SECRET` matches. The `user.subscription` doc is the source of
  truth; `set_user_subscription` busts the auth cache so it applies immediately.
- **Refund / cancel:** handled by `customer.subscription.deleted` → user drops to
  Free at period end (Stripe portal handles proration).
- **Change a plan's limits:** edit `PLANS` + restart. Existing subscribers keep
  their Stripe price; only the in-app caps change.
- **Disable payments quickly:** unset `STRIPE_SECRET_KEY` (endpoints → 503,
  UI → "Coming soon") or `SUBSCRIPTION_ENABLED=false` (hide all subscription UI).
