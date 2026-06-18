"""
Razorpay payment provider — the DOMESTIC (India) behaviour.

Razorpay is India's leading gateway, has a free Test Mode (no fees, fake cards/
UPI), and supports UPI / RuPay / netbanking that Indian buyers expect. It is the
"domestic" side of the one-interface, two-behaviours billing design: buyers
detected in India are routed here; everyone else to the international provider
(Lemon Squeezy / Stripe).

This module wraps the Razorpay Subscriptions API with the SAME provider contract
as subscription/lemonsqueezy.py so subscription_route.py can treat them
identically:

    is_configured() -> bool
    create_checkout(plan_id, user) -> {"url": short_url, "subscription_id": ...}
    verify_webhook(raw_body, signature) -> bool   (HMAC-SHA256, constant-time)
    parse_event(body) -> normalized dict the route maps to set_user_subscription

We call the REST API directly with HTTP Basic auth (key_id:key_secret) so we
don't add the `razorpay` SDK as a hard dependency — `requests` is already
present. The SDK is used only (optionally) for nothing here.
"""
import hashlib
import hmac
import json

import requests

from config import (
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET,
    RAZORPAY_WEBHOOK_SECRET,
    RAZORPAY_PLAN_PRO,
    RAZORPAY_PLAN_TEAM,
)

API_BASE = "https://api.razorpay.com/v1"

# Razorpay subscription statuses → keep paid vs drop to free.
_ACTIVE_STATUSES = {"active", "authenticated", "created", "pending"}
_TERMINAL_STATUSES = {"cancelled", "completed", "expired", "halted"}


def is_configured():
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def _auth():
    return (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)


def plan_id_for_plan(plan_id):
    """Internal plan id → Razorpay plan id (from config)."""
    return {"pro": RAZORPAY_PLAN_PRO, "team": RAZORPAY_PLAN_TEAM}.get(plan_id)


def plan_for_plan_id(rzp_plan_id):
    """Reverse map a Razorpay plan id → internal plan id (for webhooks)."""
    if rzp_plan_id and rzp_plan_id == RAZORPAY_PLAN_PRO:
        return "pro"
    if rzp_plan_id and rzp_plan_id == RAZORPAY_PLAN_TEAM:
        return "team"
    return None


def create_checkout(plan_id, user):
    """Create a Razorpay Subscription and return its hosted-checkout short URL.

    We stash our internal user id + plan in `notes` so the webhook can attribute
    the purchase. `total_count` is the number of billing cycles to charge; we use
    a large value for an effectively open-ended monthly subscription.
    """
    rzp_plan = plan_id_for_plan(plan_id)
    if not rzp_plan:
        raise ValueError("invalid_or_unconfigured_plan")

    payload = {
        "plan_id": rzp_plan,
        "total_count": 120,           # up to 10 years of monthly cycles
        "quantity": 1,
        "customer_notify": 1,
        "notes": {
            "user_id": str(user["_id"]),
            "plan": plan_id,
            "email": user.get("email", ""),
        },
    }
    resp = requests.post(f"{API_BASE}/subscriptions", auth=_auth(),
                         headers={"Content-Type": "application/json"},
                         data=json.dumps(payload), timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return {
        "url": data.get("short_url"),
        "subscription_id": data.get("id"),
    }


def cancel_subscription(subscription_id):
    """Cancel a Razorpay subscription at cycle end (used by the manage flow)."""
    if not subscription_id:
        return False
    try:
        resp = requests.post(
            f"{API_BASE}/subscriptions/{subscription_id}/cancel",
            auth=_auth(), headers={"Content-Type": "application/json"},
            data=json.dumps({"cancel_at_cycle_end": 1}), timeout=20,
        )
        return resp.ok
    except Exception as e:
        print(f"[razorpay] cancel failed: {e}", flush=True)
        return False


def verify_webhook(raw_body, signature):
    """Verify the X-Razorpay-Signature header (HMAC-SHA256 of the raw body)."""
    if not (RAZORPAY_WEBHOOK_SECRET and signature):
        return False
    digest = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


def parse_event(body):
    """Normalize a Razorpay webhook into the provider-agnostic dict.

    Razorpay events of interest:
      subscription.activated / .charged / .updated / .pending  → paid
      subscription.cancelled / .completed / .halted / .expired → free

    Returns: {event, user_id, plan_id, status, customer_id, subscription_id,
              event_id, currency, amount, paid (bool)}
    """
    event = body.get("event")
    payload = body.get("payload", {}) or {}
    sub_entity = ((payload.get("subscription") or {}).get("entity")) or {}
    pay_entity = ((payload.get("payment") or {}).get("entity")) or {}

    notes = sub_entity.get("notes") or {}
    rzp_plan_id = sub_entity.get("plan_id")
    plan_id = plan_for_plan_id(rzp_plan_id) or notes.get("plan")
    status = sub_entity.get("status")
    subscription_id = sub_entity.get("id")
    customer_id = sub_entity.get("customer_id")

    # Amount/currency for the invoice come from the payment entity when present.
    amount = pay_entity.get("amount")  # in paise
    currency = pay_entity.get("currency", "INR")

    is_charged = event == "subscription.charged"

    return {
        "provider": "razorpay",
        "event": event,
        "user_id": notes.get("user_id"),
        "plan_id": plan_id,
        "status": status,
        "customer_id": str(customer_id) if customer_id else None,
        "subscription_id": str(subscription_id) if subscription_id else None,
        "event_id": body.get("id") or f"{event}:{subscription_id}",
        "currency": currency,
        "amount": (amount / 100.0) if isinstance(amount, (int, float)) else None,
        "paid": is_charged,
        "terminal": (status in _TERMINAL_STATUSES) or event in (
            "subscription.cancelled", "subscription.completed",
            "subscription.expired", "subscription.halted",
        ),
    }
