"""
Lemon Squeezy payment provider.

Lemon Squeezy is a Merchant of Record — it's the legal seller, handles global
sales tax/VAT/GST, and works from India without an invite (unlike Stripe IN).

This module wraps the LS REST API (https://docs.lemonsqueezy.com/api):
  - create_checkout(plan, user) → hosted checkout URL
  - verify_webhook(payload, signature) → bool (HMAC-SHA256 with the signing secret)
  - parse_event(body) → normalized dict the route maps to set_user_subscription

LS uses Products → Variants. Each paid plan maps to one subscription *variant*.
"""
import hashlib
import hmac
import json

import requests

from config import (
    LEMONSQUEEZY_API_KEY,
    LEMONSQUEEZY_STORE_ID,
    LEMONSQUEEZY_WEBHOOK_SECRET,
    LEMONSQUEEZY_REDIRECT_URL,
)

API_BASE = "https://api.lemonsqueezy.com/v1"


def is_configured():
    return bool(LEMONSQUEEZY_API_KEY and LEMONSQUEEZY_STORE_ID)


def _headers():
    return {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
    }


def create_checkout(variant_id, user, plan_id):
    """Create a hosted LS checkout and return its URL.

    We pass our internal user id in `custom` so the webhook can attribute the
    purchase back to the user, and prefill the buyer's email.
    """
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user.get("email"),
                    "custom": {
                        "user_id": str(user["_id"]),
                        "plan": plan_id,
                    },
                },
                "product_options": {
                    "redirect_url": LEMONSQUEEZY_REDIRECT_URL or None,
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": str(LEMONSQUEEZY_STORE_ID)}},
                "variant": {"data": {"type": "variants", "id": str(variant_id)}},
            },
        }
    }
    resp = requests.post(f"{API_BASE}/checkouts", headers=_headers(),
                         data=json.dumps(payload), timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["attributes"]["url"]


def verify_webhook(raw_body, signature):
    """Verify the X-Signature header (HMAC-SHA256 of the raw body)."""
    if not (LEMONSQUEEZY_WEBHOOK_SECRET and signature):
        return False
    digest = hmac.new(
        LEMONSQUEEZY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    # Constant-time compare against the hex signature LS sends.
    return hmac.compare_digest(digest, signature)


def parse_event(body):
    """Normalize an LS webhook into a provider-agnostic dict.

    Returns: {
        event, user_id, plan_id (via variant), status, customer_id,
        subscription_id, portal_url
    }
    LS subscription statuses: on_trial, active, paused, past_due, unpaid,
    cancelled, expired.
    """
    meta = body.get("meta", {})
    event = meta.get("event_name")
    custom = (meta.get("custom_data") or {})
    data = body.get("data", {})
    attrs = data.get("attributes", {}) or {}

    variant_id = attrs.get("variant_id")
    status = attrs.get("status")
    customer_id = attrs.get("customer_id")
    subscription_id = data.get("id")
    urls = attrs.get("urls") or {}
    portal_url = urls.get("customer_portal")

    return {
        "event": event,
        "user_id": custom.get("user_id"),
        "variant_id": variant_id,
        "status": status,
        "customer_id": str(customer_id) if customer_id is not None else None,
        "subscription_id": str(subscription_id) if subscription_id is not None else None,
        "portal_url": portal_url,
    }
