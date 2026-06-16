"""
Subscription / usage + Stripe payment endpoints.

Read endpoints (/subscription/me, /subscription/plans) are safe even when
SUBSCRIPTION_ENABLED is false. The Stripe endpoints (/billing/*) require both
SUBSCRIPTION_ENABLED and STRIPE_SECRET_KEY; otherwise they return 503 so the
app degrades gracefully.

Flow:
  1. Frontend POST /billing/checkout {plan} → Stripe Checkout Session
     (mode=subscription); frontend redirects to the returned URL.
  2. User pays on Stripe's hosted page → redirected back to STRIPE_SUCCESS_URL.
  3. Stripe POSTs a webhook to /billing/webhook → we verify the signature and
     update the user's subscription in Mongo. THIS is the source of truth —
     never trust the client redirect alone.
  4. POST /billing/portal opens the Stripe Billing Portal for self-serve
     upgrade/downgrade/cancel.
"""
from flask import Blueprint, jsonify, request

from auth.auth_middleware import token_required
from config import (
    SUBSCRIPTION_ENABLED,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
    STRIPE_SUCCESS_URL,
    STRIPE_CANCEL_URL,
    STRIPE_PUBLISHABLE_KEY,
)
from services.subscription_service import (
    get_entitlements,
    list_plans,
    price_id_for_plan,
    plan_for_price_id,
    set_user_subscription,
    find_user_by_stripe_customer,
)

subscription_routes = Blueprint('subscription_routes', __name__)


def _stripe():
    """Return a configured stripe module, or None when payments are off."""
    if not (SUBSCRIPTION_ENABLED and STRIPE_SECRET_KEY):
        return None
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    return stripe


def _with_param(url, extra):
    """Append a query param, choosing ? or & correctly."""
    if not url:
        return url
    sep = '&' if '?' in url else '?'
    return f"{url}{sep}{extra}"


# ── Read-only entitlement / plan catalog ────────────────────────────────────

@subscription_routes.route('/subscription/me', methods=['GET'])
@token_required
def my_entitlements(current_user):
    """Current user's plan, limits, and month-to-date usage."""
    try:
        return jsonify(get_entitlements(current_user)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@subscription_routes.route('/subscription/plans', methods=['GET'])
def plans():
    """Public plan catalog for the pricing page."""
    try:
        return jsonify({
            "plans": list_plans(),
            "payments_enabled": bool(SUBSCRIPTION_ENABLED and STRIPE_SECRET_KEY),
            "publishable_key": STRIPE_PUBLISHABLE_KEY if SUBSCRIPTION_ENABLED else None,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Minimal country → ISO-4217 currency map for display localization. The CHARGE
# is always the canonical USD Price (Stripe Adaptive Pricing localizes at the
# hosted checkout); this only picks the symbol/format shown on the pricing page.
_COUNTRY_CURRENCY = {
    "US": "USD", "IN": "INR", "GB": "GBP", "CA": "CAD", "AU": "AUD",
    "JP": "JPY", "CN": "CNY", "SG": "SGD", "AE": "AED", "DE": "EUR",
    "FR": "EUR", "ES": "EUR", "IT": "EUR", "NL": "EUR", "IE": "EUR",
    "BR": "BRL", "MX": "MXN", "ZA": "ZAR", "NG": "NGN", "CH": "CHF",
}


@subscription_routes.route('/billing/locale', methods=['GET'])
def billing_locale():
    """Best-effort geo-IP country + suggested display currency for pricing.

    Reads the country from the platform/CDN header set in front of the app
    (Vercel: x-vercel-ip-country, Cloudflare: cf-ipcountry, generic:
    x-country-code). Falls back to US/USD when unknown. This is DISPLAY ONLY —
    prices are charged in the canonical currency regardless.
    """
    country = (
        request.headers.get('x-vercel-ip-country')
        or request.headers.get('cf-ipcountry')
        or request.headers.get('x-country-code')
        or 'US'
    ).upper()
    currency = _COUNTRY_CURRENCY.get(country, 'USD')
    return jsonify({"country": country, "currency": currency}), 200


# ── Stripe Checkout / Billing Portal ────────────────────────────────────────

@subscription_routes.route('/billing/checkout', methods=['POST'])
@token_required
def create_checkout(current_user):
    """Create a Stripe Checkout Session for the requested plan and return its URL.

    Stripe Adaptive Pricing (enabled in the Stripe dashboard) localizes the
    displayed currency for the buyer automatically — the underlying Price stays
    canonical, so the price is the same everywhere.
    """
    stripe = _stripe()
    if not stripe:
        return jsonify({"error": "payments_not_configured"}), 503

    data = request.get_json(silent=True) or {}
    plan_id = data.get('plan')
    price_id = price_id_for_plan(plan_id)
    if not price_id:
        return jsonify({"error": "invalid_or_unconfigured_plan"}), 400

    sub = current_user.get('subscription') or {}
    customer_id = sub.get('stripe_customer_id')

    try:
        session_kwargs = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": _with_param(
                STRIPE_SUCCESS_URL or "http://localhost:3000/profile",
                "status=success&session_id={CHECKOUT_SESSION_ID}",
            ),
            "cancel_url": _with_param(
                STRIPE_CANCEL_URL or "http://localhost:3000/pricing", "status=cancel"
            ),
            "client_reference_id": str(current_user['_id']),
            "metadata": {"user_id": str(current_user['_id']), "plan": plan_id},
            "subscription_data": {"metadata": {"user_id": str(current_user['_id']), "plan": plan_id}},
            "allow_promotion_codes": True,
        }
        if customer_id:
            session_kwargs["customer"] = customer_id
        else:
            session_kwargs["customer_email"] = current_user.get('email')

        session = stripe.checkout.Session.create(**session_kwargs)
        return jsonify({"url": session.url, "id": session.id}), 200
    except Exception as e:
        return jsonify({"error": f"stripe_error: {e}"}), 502


@subscription_routes.route('/billing/portal', methods=['POST'])
@token_required
def billing_portal(current_user):
    """Open the Stripe Billing Portal so the user can manage/cancel their plan."""
    stripe = _stripe()
    if not stripe:
        return jsonify({"error": "payments_not_configured"}), 503

    sub = current_user.get('subscription') or {}
    customer_id = sub.get('stripe_customer_id')
    if not customer_id:
        return jsonify({"error": "no_active_subscription"}), 400
    try:
        portal = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=STRIPE_CANCEL_URL or "http://localhost:3000/profile",
        )
        return jsonify({"url": portal.url}), 200
    except Exception as e:
        return jsonify({"error": f"stripe_error: {e}"}), 502


@subscription_routes.route('/billing/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe webhook: the SOURCE OF TRUTH for subscription state.

    Verifies the signature with STRIPE_WEBHOOK_SECRET, then maps Stripe events
    to the user's subscription. Returns 200 quickly so Stripe doesn't retry on
    transient app errors we've already logged.
    """
    if not (SUBSCRIPTION_ENABLED and STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET):
        return jsonify({"error": "payments_not_configured"}), 503

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    payload = request.get_data()
    sig = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return jsonify({"error": f"invalid_signature: {e}"}), 400

    try:
        _handle_stripe_event(stripe, event)
    except Exception as e:
        print(f"[stripe webhook] handler error for {event.get('type')}: {e}")

    return jsonify({"received": True}), 200


def _handle_stripe_event(stripe, event):
    etype = event['type']
    obj = event['data']['object']

    if etype == 'checkout.session.completed':
        user_id = (obj.get('metadata') or {}).get('user_id') or obj.get('client_reference_id')
        plan_id = (obj.get('metadata') or {}).get('plan')
        customer_id = obj.get('customer')
        subscription_id = obj.get('subscription')
        if not plan_id and subscription_id:
            sub = stripe.Subscription.retrieve(subscription_id)
            price_id = sub['items']['data'][0]['price']['id']
            plan_id = plan_for_price_id(price_id)
        if user_id and plan_id:
            set_user_subscription(
                user_id, plan_id, status="active",
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
            )

    elif etype in ('customer.subscription.updated', 'customer.subscription.created'):
        customer_id = obj.get('customer')
        status = obj.get('status', 'active')
        price_id = (obj.get('items', {}).get('data') or [{}])[0].get('price', {}).get('id')
        plan_id = plan_for_price_id(price_id) or 'free'
        period_end = obj.get('current_period_end')
        user = find_user_by_stripe_customer(customer_id)
        uid = (obj.get('metadata') or {}).get('user_id') or (str(user['_id']) if user else None)
        if uid:
            set_user_subscription(
                uid, plan_id, status=status,
                stripe_customer_id=customer_id,
                stripe_subscription_id=obj.get('id'),
                current_period_end=period_end,
            )

    elif etype == 'customer.subscription.deleted':
        customer_id = obj.get('customer')
        user = find_user_by_stripe_customer(customer_id)
        uid = (obj.get('metadata') or {}).get('user_id') or (str(user['_id']) if user else None)
        if uid:
            set_user_subscription(uid, 'free', status='canceled', stripe_customer_id=customer_id)
