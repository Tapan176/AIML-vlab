"""
Subscription / usage-quota service.

Entirely gated by config.SUBSCRIPTION_ENABLED. When the flag is false, every
public function here is a no-op that reports "unlimited / allowed", so the rest
of the app behaves exactly as it did before subscriptions existed.

What we meter (the real cost drivers in this app):
  - classical : scikit-learn / XGBoost runs (cheap, sync)
  - deep      : CNN / ANN / ResNet / LSTM / YOLO / StyleGAN (minutes of compute)
  - finetune  : BERT / DistilBERT / ViT fine-tuning (heaviest)

Usage is counted per calendar month in the `usage_counters` collection, keyed
by (user_id, period="YYYY-MM"). Plans are defined in code (PLANS); the free-tier
caps come from config so they can be tuned via .env without a deploy.
"""
from datetime import datetime

from bson import ObjectId

from config import (
    SUBSCRIPTION_ENABLED,
    FREE_TIER_CLASSICAL_RUNS,
    FREE_TIER_DEEP_RUNS,
    FREE_TIER_FINETUNE_RUNS,
    FREE_TIER_DATASTUDIO_OPS,
    FREE_TIER_MAX_DATASETS,
    PRO_TIER_MAX_DATASETS,
    TEAM_TIER_MAX_DATASETS,
    STRIPE_PRICE_PRO,
    STRIPE_PRICE_TEAM,
    LEMONSQUEEZY_VARIANT_PRO,
    LEMONSQUEEZY_VARIANT_TEAM,
)
from mongoDb.connection import get_db

# Metered classes. classical/deep/finetune are training runs; datastudio covers
# Data Studio operations (profiling / preprocessing / diff).
RUN_CLASSES = ("classical", "deep", "finetune", "datastudio")

# None means "unlimited" (still subject to the global flask_limiter rate limit).
PLANS = {
    "free": {
        "id": "free",
        "name": "Free",
        "price": 0,
        "limits": {
            "classical": FREE_TIER_CLASSICAL_RUNS,
            "deep": FREE_TIER_DEEP_RUNS,
            "finetune": FREE_TIER_FINETUNE_RUNS,
            "datastudio": FREE_TIER_DATASTUDIO_OPS,
        },
        "max_datasets": FREE_TIER_MAX_DATASETS,
        "features": ["data_profiling", "dataset_versions", "replay"],
        "blurb": "For learning and light experimentation.",
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price": 9,
        "limits": {"classical": None, "deep": 100, "finetune": 20, "datastudio": None},
        "max_datasets": PRO_TIER_MAX_DATASETS,
        "features": [
            "data_profiling", "dataset_versions", "replay",
            "priority_queue", "gpu", "all_models",
        ],
        "blurb": "For serious experimentation and research.",
    },
    "team": {
        "id": "team",
        "name": "Team",
        "price": 29,
        "limits": {"classical": None, "deep": 400, "finetune": 100, "datastudio": None},
        "max_datasets": TEAM_TIER_MAX_DATASETS,
        "features": [
            "data_profiling", "dataset_versions", "replay",
            "priority_queue", "gpu", "all_models",
            "shared_workspace", "api_access",
        ],
        "blurb": "For teams sharing datasets and compute.",
    },
}


def is_enabled():
    return SUBSCRIPTION_ENABLED


def run_class(model_code):
    """Classify a model_code as 'classical' | 'deep' | 'finetune' | 'datastudio'
    using the model registry as the single source of truth (category + streaming
    flag). The sentinel 'datastudio' maps to the Data Studio class directly."""
    if model_code == "datastudio":
        return "datastudio"
    from services.model_registry import get_model_meta
    meta = get_model_meta(model_code) or {}
    if meta.get("category") == "Fine-Tuning" or str(model_code).endswith("_finetune"):
        return "finetune"
    return "deep" if meta.get("streaming") else "classical"


def current_period():
    now = datetime.utcnow()
    return f"{now.year:04d}-{now.month:02d}"


def _period_reset_iso():
    """ISO timestamp for the start of next month (when monthly counters reset)."""
    now = datetime.utcnow()
    if now.month == 12:
        nxt = datetime(now.year + 1, 1, 1)
    else:
        nxt = datetime(now.year, now.month + 1, 1)
    return nxt.isoformat() + "Z"


def get_user_plan(user):
    """Resolve a user's effective plan dict. Falls back to free for anonymous
    users, unknown plans, or non-active subscription status."""
    if not user:
        return PLANS["free"]
    sub = user.get("subscription") or {}
    plan_id = sub.get("plan", "free")
    status = sub.get("status", "active")
    if status not in ("active", "trialing"):
        plan_id = "free"
    return PLANS.get(plan_id, PLANS["free"])


def get_usage(user_id, period=None):
    period = period or current_period()
    db = get_db()
    doc = db.usage_counters.find_one({"user_id": str(user_id), "period": period})
    if not doc:
        return {"user_id": str(user_id), "period": period, "classical": 0, "deep": 0, "finetune": 0}
    return doc


def check_quota(user, model_code):
    """Return (ok, info). When subscriptions are disabled, always (True, None).

    On block, info is a JSON-serializable dict describing the exceeded quota,
    suitable for a 429/402 response body.
    """
    if not SUBSCRIPTION_ENABLED or not user:
        return True, None
    cls = run_class(model_code)
    plan = get_user_plan(user)
    limit = plan["limits"].get(cls)
    if limit is None:
        return True, None  # unlimited for this class on this plan
    used = int(get_usage(user["_id"]).get(cls, 0))
    if used >= limit:
        pretty = {
            "classical": "classical ML",
            "deep": "deep-learning",
            "finetune": "fine-tuning",
            "datastudio": "Data Studio",
        }[cls]
        return False, {
            "error": "quota_exceeded",
            "run_class": cls,
            "used": used,
            "limit": limit,
            "plan": plan["id"],
            "plan_name": plan["name"],
            "reset_at": _period_reset_iso(),
            "message": (
                f"You've used all {limit} {pretty} "
                f"{'operations' if cls == 'datastudio' else 'training runs'} on the "
                f"{plan['name']} plan this month. Upgrade for more, or wait for the monthly reset."
            ),
        }
    return True, None


def record_usage(user_id, model_code, n=1):
    """Atomically increment the user's run counter for this model's class.
    No-op when subscriptions are disabled."""
    if not SUBSCRIPTION_ENABLED or not user_id:
        return
    cls = run_class(model_code)
    period = current_period()
    db = get_db()
    db.usage_counters.update_one(
        {"user_id": str(user_id), "period": period},
        {
            "$inc": {cls: int(n)},
            "$setOnInsert": {"user_id": str(user_id), "period": period},
            "$set": {"updated_at": datetime.utcnow()},
        },
        upsert=True,
    )


def _dataset_count(user_id):
    """Total datasets owned by the user (Data Studio outputs land here too)."""
    try:
        return get_db().datasets.count_documents({"user_id": str(user_id)})
    except Exception:
        return 0


def get_entitlements(user):
    """Full snapshot for the frontend: plan, limits, current usage, reset time.

    `usage` carries the per-class monthly run counts plus an informational
    `datasets` total (not currently capped — it surfaces storage/Data-Studio
    activity so users can see it; enforcing a storage limit is a future step)."""
    plan = get_user_plan(user)
    usage = get_usage(user["_id"]) if user else {}
    out = {c: int(usage.get(c, 0)) for c in RUN_CLASSES}
    if user:
        out["datasets"] = _dataset_count(user["_id"])
    return {
        "subscription_enabled": SUBSCRIPTION_ENABLED,
        "plan": plan["id"],
        "plan_name": plan["name"],
        "limits": plan["limits"],
        "max_datasets": plan.get("max_datasets"),
        "features": plan.get("features", []),
        "usage": out,
        "period": current_period(),
        "reset_at": _period_reset_iso(),
    }


def list_plans():
    """Public plan catalog for a pricing page."""
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "limits": p["limits"],
            "max_datasets": p.get("max_datasets"),
            "features": p.get("features", []),
            "blurb": p.get("blurb", ""),
        }
        for p in PLANS.values()
    ]


# ── Storage (dataset count) quota ───────────────────────────────────────────

def check_storage_quota(user, additional=1):
    """Return (ok, info) for whether the user may keep `additional` more
    datasets. No-op (allowed) when subscriptions are disabled. `additional`
    lets callers pre-check before an upload."""
    if not SUBSCRIPTION_ENABLED or not user:
        return True, None
    plan = get_user_plan(user)
    cap = plan.get("max_datasets")
    if not cap:  # None or 0 → unlimited
        return True, None
    current = _dataset_count(user["_id"])
    if current + additional > cap:
        return False, {
            "error": "storage_quota_exceeded",
            "used": current,
            "limit": cap,
            "plan": plan["id"],
            "plan_name": plan["name"],
            "message": (
                f"You've reached the {cap}-dataset limit on the {plan['name']} plan. "
                f"Delete some datasets or upgrade for more storage."
            ),
        }
    return True, None


# ── Stripe ↔ plan mapping + subscription mutation ───────────────────────────

def price_id_for_plan(plan_id):
    """Map an internal plan id → the Stripe Price ID (from config)."""
    return {"pro": STRIPE_PRICE_PRO, "team": STRIPE_PRICE_TEAM}.get(plan_id)


def plan_for_price_id(price_id):
    """Reverse map a Stripe Price ID → internal plan id (for webhooks)."""
    if price_id and price_id == STRIPE_PRICE_PRO:
        return "pro"
    if price_id and price_id == STRIPE_PRICE_TEAM:
        return "team"
    return None


# ── Lemon Squeezy ↔ plan mapping ────────────────────────────────────────────

def variant_id_for_plan(plan_id):
    """Map an internal plan id → the Lemon Squeezy variant ID (from config)."""
    return {"pro": LEMONSQUEEZY_VARIANT_PRO, "team": LEMONSQUEEZY_VARIANT_TEAM}.get(plan_id)


def plan_for_variant_id(variant_id):
    """Reverse map a Lemon Squeezy variant ID → internal plan id (for webhooks).

    LS sends variant_id as an int in webhook payloads; compare as strings so a
    config value of "12345" matches a payload int 12345.
    """
    vid = str(variant_id) if variant_id is not None else None
    if vid and LEMONSQUEEZY_VARIANT_PRO and vid == str(LEMONSQUEEZY_VARIANT_PRO):
        return "pro"
    if vid and LEMONSQUEEZY_VARIANT_TEAM and vid == str(LEMONSQUEEZY_VARIANT_TEAM):
        return "team"
    return None


def set_user_subscription(user_id, plan_id, status="active", stripe_customer_id=None,
                          stripe_subscription_id=None, current_period_end=None,
                          provider=None, customer_id=None, subscription_id=None,
                          portal_url=None):
    """Persist a user's subscription state (called from payment webhooks).

    Provider-agnostic: pass `provider` ('stripe'|'lemonsqueezy') with generic
    `customer_id`/`subscription_id`, OR the legacy `stripe_*` kwargs. We also
    keep the Stripe-named fields for backward compatibility with existing code.
    `status` follows the provider's subscription statuses (active, on_trial,
    past_due, cancelled, expired, …)."""
    db = get_db()
    cust = customer_id or stripe_customer_id
    subid = subscription_id or stripe_subscription_id
    sub = {
        "plan": plan_id or "free",
        "status": status,
        "provider": provider or ("stripe" if stripe_customer_id else None),
    }
    # Generic ids (used by the provider-agnostic billing layer).
    if cust:
        sub["customer_id"] = cust
        sub["stripe_customer_id"] = cust  # back-compat
    if subid:
        sub["subscription_id"] = subid
        sub["stripe_subscription_id"] = subid  # back-compat
    if current_period_end is not None:
        sub["current_period_end"] = current_period_end
    if portal_url:
        sub["portal_url"] = portal_url  # LS gives a per-subscription portal URL
    db.users.update_one({"_id": ObjectId(str(user_id))}, {"$set": {"subscription": sub}})
    # Bust the auth middleware's user cache so the new plan takes effect at once.
    try:
        from auth.auth_middleware import invalidate_user_cache
        invalidate_user_cache(user_id)
    except Exception:
        pass
    return sub


def find_user_by_stripe_customer(customer_id):
    """Locate the local user for a Stripe customer id (webhook reconciliation)."""
    if not customer_id:
        return None
    return get_db().users.find_one({"subscription.stripe_customer_id": customer_id})


def find_user_by_customer(customer_id):
    """Locate the local user for a provider customer id (any provider)."""
    if not customer_id:
        return None
    cid = str(customer_id)
    return get_db().users.find_one({
        "$or": [
            {"subscription.customer_id": cid},
            {"subscription.stripe_customer_id": cid},
        ]
    })
