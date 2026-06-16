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

from config import (
    SUBSCRIPTION_ENABLED,
    FREE_TIER_CLASSICAL_RUNS,
    FREE_TIER_DEEP_RUNS,
    FREE_TIER_FINETUNE_RUNS,
)
from mongoDb.connection import get_db

RUN_CLASSES = ("classical", "deep", "finetune")

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
        },
        "features": ["data_profiling", "dataset_versions", "replay"],
        "blurb": "For learning and light experimentation.",
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price": 9,
        "limits": {"classical": None, "deep": 100, "finetune": 20},
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
        "limits": {"classical": None, "deep": 400, "finetune": 100},
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
    """Classify a model_code as 'classical' | 'deep' | 'finetune' using the
    model registry as the single source of truth (category + streaming flag)."""
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
        pretty = {"classical": "classical ML", "deep": "deep-learning", "finetune": "fine-tuning"}[cls]
        return False, {
            "error": "quota_exceeded",
            "run_class": cls,
            "used": used,
            "limit": limit,
            "plan": plan["id"],
            "plan_name": plan["name"],
            "reset_at": _period_reset_iso(),
            "message": (
                f"You've used all {limit} {pretty} training runs on the "
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


def get_entitlements(user):
    """Full snapshot for the frontend: plan, limits, current usage, reset time."""
    plan = get_user_plan(user)
    usage = get_usage(user["_id"]) if user else {}
    return {
        "subscription_enabled": SUBSCRIPTION_ENABLED,
        "plan": plan["id"],
        "plan_name": plan["name"],
        "limits": plan["limits"],
        "features": plan.get("features", []),
        "usage": {c: int(usage.get(c, 0)) for c in RUN_CLASSES},
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
            "features": p.get("features", []),
            "blurb": p.get("blurb", ""),
        }
        for p in PLANS.values()
    ]
