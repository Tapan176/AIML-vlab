"""
Subscription / usage + payment endpoints.

ONE INTERFACE, TWO BEHAVIOURS
-----------------------------
Buyers detected in India are routed to the DOMESTIC provider
(config.PAYMENT_PROVIDER_DOMESTIC, default 'razorpay'); everyone else to the
INTERNATIONAL provider (config.PAYMENT_PROVIDER_INTL, default 'lemonsqueezy',
'stripe' also supported). All three implement the same provider contract so the
checkout/webhook code treats them uniformly. Country is detected server-side
from the CDN geo-IP header — the client may pass a hint for DISPLAY only.

Read endpoints (/subscription/me, /subscription/plans) are always safe. Billing
endpoints require SUBSCRIPTION_ENABLED + the chosen provider's keys; otherwise
they return 503 and the UI shows "Coming soon".

Flow (every provider):
  1. POST /billing/checkout {plan} → hosted checkout URL; frontend redirects.
  2. User pays on the provider's hosted page → redirected back to our app.
  3. Provider POSTs a signed webhook to /billing/webhook → we verify the
     signature, update user.subscription in Mongo (SOURCE OF TRUTH — never trust
     the client redirect), and on a successful charge generate + email an invoice.
  4. POST /billing/portal → self-serve manage/cancel.
  5. GET  /billing/invoices → the user's billing history.
"""
from flask import Blueprint, jsonify, request

from auth.auth_middleware import token_required
from config import (
    SUBSCRIPTION_ENABLED,
    PAYMENT_PROVIDER,
    PAYMENT_PROVIDER_DOMESTIC,
    PAYMENT_PROVIDER_INTL,
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
    variant_id_for_plan,
    plan_for_variant_id,
    set_user_subscription,
    find_user_by_stripe_customer,
    find_user_by_customer,
    find_user_by_subscription_id,
    mark_webhook_event,
    inr_price_for_plan,
    usd_price_for_plan,
)
from services.subscription_service import PLANS
from extensions import limiter

subscription_routes = Blueprint('subscription_routes', __name__)

# Countries served by the domestic (India) provider. Everyone else → intl.
_DOMESTIC_COUNTRIES = {"IN"}


def _detect_country():
    """Server-authoritative buyer country from the CDN geo-IP header.

    Reads Vercel/Cloudflare/generic country headers. The client can NOT spoof
    this for a real charge — we always re-derive it here when creating checkout.
    Falls back to '' (→ international) when unknown.
    """
    return (
        request.headers.get('x-vercel-ip-country')
        or request.headers.get('cf-ipcountry')
        or request.headers.get('x-country-code')
        or ''
    ).upper()


def _provider_for_country(country):
    """Pick the provider for a buyer country (the routing decision)."""
    if country in _DOMESTIC_COUNTRIES:
        return PAYMENT_PROVIDER_DOMESTIC
    return PAYMENT_PROVIDER_INTL


def _provider_configured(provider):
    """True when the named provider has its keys set."""
    if provider == 'razorpay':
        from subscription import razorpay_provider as rzp
        return rzp.is_configured()
    if provider == 'lemonsqueezy':
        from subscription import lemonsqueezy as ls
        return ls.is_configured()
    if provider == 'stripe':
        return bool(STRIPE_SECRET_KEY)
    return False


def _stripe():
    """Return a configured stripe module, or None when Stripe isn't available."""
    if not (SUBSCRIPTION_ENABLED and STRIPE_SECRET_KEY):
        return None
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    return stripe


def _payments_active():
    """True when AT LEAST ONE provider (domestic or intl) is fully set up.

    The pricing page shows "Upgrade" buttons when this is true; the actual
    provider is chosen per-buyer at checkout based on country.
    """
    if not SUBSCRIPTION_ENABLED:
        return False
    return (_provider_configured(PAYMENT_PROVIDER_DOMESTIC)
            or _provider_configured(PAYMENT_PROVIDER_INTL))


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
    """Public plan catalog for the pricing page.

    Reports which provider WOULD handle the current visitor (by geo-IP) so the
    pricing page can show the right label/currency before checkout.
    """
    try:
        country = _detect_country()
        provider = _provider_for_country(country) if SUBSCRIPTION_ENABLED else None
        return jsonify({
            "plans": list_plans(),
            "payments_enabled": _payments_active(),
            "provider": provider,
            "country": country or None,
            "publishable_key": (STRIPE_PUBLISHABLE_KEY
                                if (SUBSCRIPTION_ENABLED and provider == 'stripe')
                                else None),
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


# ── Checkout / Portal / Webhook (provider-agnostic) ─────────────────────────

@subscription_routes.route('/billing/order', methods=['POST'])
@limiter.limit("30 per minute")
@token_required
def billing_order(current_user):
    """Return a server-priced bill preview for the requested plan + buyer region.

    Used by the checkout/order page to show an itemized bill BEFORE redirecting
    to the provider. Country (hence currency + provider) is resolved server-side
    so the displayed total matches what the user will actually be charged.
    """
    data = request.get_json(silent=True) or {}
    plan_id = data.get('plan')
    plan = PLANS.get(plan_id)
    if not plan or plan_id == 'free':
        return jsonify({"error": "invalid_plan"}), 400

    country = _detect_country()
    provider = _provider_for_country(country)
    if provider == 'razorpay':
        currency = 'INR'
        amount = inr_price_for_plan(plan_id)
        symbol = '₹'
        total_display = f"{symbol}{int(amount):,}/mo"
    else:
        currency = 'USD'
        amount = usd_price_for_plan(plan_id)
        symbol = '$'
        total_display = f"{symbol}{amount}/mo"

    provider_label = {'razorpay': 'Razorpay', 'lemonsqueezy': 'Lemon Squeezy',
                      'stripe': 'Stripe'}.get(provider, provider)
    return jsonify({
        "plan": plan_id,
        "plan_name": plan["name"],
        "country": country or "INTL",
        "provider": provider,
        "provider_label": provider_label,
        "currency": currency,
        "amount": amount,
        "configured": _provider_configured(provider),
        "line_items": [
            {"description": f"{plan['name']} plan — monthly subscription",
             "amount_display": total_display},
        ],
        "total_display": total_display,
        "tax_note": ("Inclusive of applicable GST." if provider == 'razorpay'
                     else "Local taxes (VAT/GST) handled at checkout."),
    }), 200


@subscription_routes.route('/billing/checkout', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def create_checkout(current_user):
    """Create a hosted checkout for the requested plan and return its URL.

    Routes to the DOMESTIC provider for India and the INTERNATIONAL provider
    elsewhere (country resolved server-side). Each provider localizes currency
    on its hosted page.
    """
    if not _payments_active():
        return jsonify({"error": "payments_not_configured"}), 503

    data = request.get_json(silent=True) or {}
    plan_id = data.get('plan')
    if plan_id not in PLANS or plan_id == 'free':
        return jsonify({"error": "invalid_or_unconfigured_plan"}), 400

    country = _detect_country()
    provider = _provider_for_country(country)
    if not _provider_configured(provider):
        # Fall back to the other provider if the region's primary isn't set up.
        alt = (PAYMENT_PROVIDER_INTL if provider == PAYMENT_PROVIDER_DOMESTIC
               else PAYMENT_PROVIDER_DOMESTIC)
        if _provider_configured(alt):
            provider = alt
        else:
            return jsonify({"error": "payments_not_configured"}), 503

    # ── Razorpay (India / domestic) ──
    if provider == 'razorpay':
        try:
            from subscription import razorpay_provider as rzp
            result = rzp.create_checkout(plan_id, current_user)
            return jsonify({"url": result["url"], "provider": "razorpay"}), 200
        except ValueError:
            return jsonify({"error": "invalid_or_unconfigured_plan"}), 400
        except Exception as e:
            return jsonify({"error": f"razorpay_error: {e}"}), 502

    # ── Lemon Squeezy (intl) ──
    if provider == 'lemonsqueezy':
        variant_id = variant_id_for_plan(plan_id)
        if not variant_id:
            return jsonify({"error": "invalid_or_unconfigured_plan"}), 400
        try:
            from subscription import lemonsqueezy as ls
            url = ls.create_checkout(variant_id, current_user, plan_id)
            return jsonify({"url": url, "provider": "lemonsqueezy"}), 200
        except Exception as e:
            return jsonify({"error": f"lemonsqueezy_error: {e}"}), 502

    # ── Stripe (intl alt) ──
    stripe = _stripe()
    if not stripe:
        return jsonify({"error": "payments_not_configured"}), 503
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
        return jsonify({"url": session.url, "id": session.id, "provider": "stripe"}), 200
    except Exception as e:
        return jsonify({"error": f"stripe_error: {e}"}), 502


@subscription_routes.route('/billing/portal', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def billing_portal(current_user):
    """Open the provider's customer portal so the user can manage/cancel.

    Behaviour differs by the provider that owns the user's subscription:
      - Lemon Squeezy: redirect to the per-subscription portal URL it gave us.
      - Stripe: create a billing-portal session.
      - Razorpay: no hosted portal — we cancel via API and report success so the
        frontend's "Manage subscription" can offer a cancel action directly.
    """
    if not _payments_active():
        return jsonify({"error": "payments_not_configured"}), 503

    sub = current_user.get('subscription') or {}
    provider = sub.get('provider')

    # ── Razorpay: cancel at cycle end (no hosted portal) ──
    if provider == 'razorpay':
        from subscription import razorpay_provider as rzp
        subscription_id = sub.get('subscription_id')
        if not subscription_id:
            return jsonify({"error": "no_active_subscription"}), 400
        if rzp.cancel_subscription(subscription_id):
            return jsonify({"cancelled": True,
                            "message": "Your subscription will end at the current cycle."}), 200
        return jsonify({"error": "razorpay_cancel_failed"}), 502

    # ── Lemon Squeezy: per-subscription portal URL captured on the webhook ──
    if provider == 'lemonsqueezy' or sub.get('portal_url'):
        portal_url = sub.get('portal_url')
        if portal_url:
            return jsonify({"url": portal_url}), 200
        return jsonify({"error": "no_active_subscription"}), 400

    # ── Stripe ──
    stripe = _stripe()
    if not stripe:
        return jsonify({"error": "payments_not_configured"}), 503
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


@subscription_routes.route('/billing/invoices', methods=['GET'])
@token_required
def billing_invoices(current_user):
    """The current user's billing history (for the Profile → Billing section)."""
    try:
        from services.invoice_service import list_invoices
        return jsonify({"invoices": list_invoices(current_user['_id'])}), 200
    except Exception as e:
        return jsonify({"error": str(e), "invoices": []}), 200


@subscription_routes.route('/billing/webhook', methods=['POST'])
def billing_webhook():
    """Payment webhook: the SOURCE OF TRUTH for subscription state.

    Multiple providers can be active at once (domestic + intl), so we identify
    the sender by its signature header, verify the signature, dedup, map the
    event to user.subscription, and (on a successful charge) generate + email an
    invoice. Returns 200 quickly so the provider doesn't retry on transient errors.
    """
    if not SUBSCRIPTION_ENABLED:
        return jsonify({"error": "payments_not_configured"}), 503

    raw = request.get_data()

    # ── Razorpay (X-Razorpay-Signature) ──
    rzp_sig = request.headers.get('X-Razorpay-Signature')
    if rzp_sig:
        from subscription import razorpay_provider as rzp
        if not rzp.is_configured():
            return jsonify({"error": "payments_not_configured"}), 503
        if not rzp.verify_webhook(raw, rzp_sig):
            return jsonify({"error": "invalid_signature"}), 400
        body = request.get_json(silent=True) or {}
        evt = rzp.parse_event(body)
        if not mark_webhook_event('razorpay', evt.get('event_id') or rzp_sig):
            return jsonify({"received": True, "duplicate": True}), 200
        try:
            _handle_rzp_event(evt)
        except Exception as e:
            print(f"[razorpay webhook] handler error: {e}")
        return jsonify({"received": True}), 200

    # ── Lemon Squeezy (X-Signature) ──
    ls_sig = request.headers.get('X-Signature')
    if ls_sig:
        from subscription import lemonsqueezy as ls
        if not ls.is_configured():
            return jsonify({"error": "payments_not_configured"}), 503
        if not ls.verify_webhook(raw, ls_sig):
            return jsonify({"error": "invalid_signature"}), 400
        if not mark_webhook_event('lemonsqueezy', ls_sig):
            return jsonify({"received": True, "duplicate": True}), 200
        try:
            evt = ls.parse_event(request.get_json(silent=True) or {})
            _handle_ls_event(evt)
        except Exception as e:
            print(f"[ls webhook] handler error: {e}")
        return jsonify({"received": True}), 200

    # ── Stripe (Stripe-Signature) ──
    if request.headers.get('Stripe-Signature'):
        if not (STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET):
            return jsonify({"error": "payments_not_configured"}), 503
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        sig = request.headers.get('Stripe-Signature', '')
        try:
            event = stripe.Webhook.construct_event(raw, sig, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            return jsonify({"error": f"invalid_signature: {e}"}), 400
        if not mark_webhook_event('stripe', event.get('id')):
            return jsonify({"received": True, "duplicate": True}), 200
        try:
            _handle_stripe_event(stripe, event)
        except Exception as e:
            print(f"[stripe webhook] handler error for {event.get('type')}: {e}")
        return jsonify({"received": True}), 200

    return jsonify({"error": "unrecognized_webhook"}), 400


def _email_invoice_safe(user_id, plan_id, provider, currency, amount):
    """Best-effort invoice generation + email. Never raises into the webhook."""
    try:
        from mongoDb.connection import get_db
        from bson import ObjectId
        user = get_db().users.find_one({"_id": ObjectId(str(user_id))})
        if not user:
            return
        plan = PLANS.get(plan_id) or {}
        from services.invoice_service import create_and_email_invoice
        create_and_email_invoice(
            user_id=user_id,
            email=user.get('email'),
            plan_id=plan_id,
            plan_name=plan.get('name', plan_id),
            provider=provider,
            currency=currency,
            amount=amount,
        )
    except Exception as e:
        print(f"[invoice] generation failed: {e}", flush=True)


def _handle_rzp_event(evt):
    """Map a normalized Razorpay event → user.subscription (+ invoice on charge)."""
    user_id = evt.get("user_id")
    plan_id = evt.get("plan_id")
    status = evt.get("status")
    subscription_id = evt.get("subscription_id")
    customer_id = evt.get("customer_id")

    if not user_id and subscription_id:
        u = find_user_by_subscription_id(subscription_id)
        user_id = str(u["_id"]) if u else None
    if not user_id:
        return

    if evt.get("terminal"):
        set_user_subscription(user_id, "free", status=status or "cancelled",
                              provider="razorpay", customer_id=customer_id,
                              subscription_id=subscription_id)
        return

    if plan_id in PLANS:
        set_user_subscription(user_id, plan_id, status=status or "active",
                              provider="razorpay", customer_id=customer_id,
                              subscription_id=subscription_id)
        # Successful charge → invoice + email.
        if evt.get("paid"):
            amount = evt.get("amount")
            if amount is None:
                from services.subscription_service import inr_price_for_plan
                amount = inr_price_for_plan(plan_id)
            _email_invoice_safe(user_id, plan_id, "razorpay",
                                evt.get("currency", "INR"), amount)


def _handle_ls_event(evt):
    """Map a normalized Lemon Squeezy event → user.subscription.

    LS events: subscription_created, subscription_updated, subscription_cancelled,
    subscription_expired, subscription_resumed, subscription_paused, …
    """
    event = evt.get("event")
    user_id = evt.get("user_id")
    status = evt.get("status")
    plan_id = plan_for_variant_id(evt.get("variant_id"))
    customer_id = evt.get("customer_id")
    subscription_id = evt.get("subscription_id")
    portal_url = evt.get("portal_url")

    # Resolve the user from custom_data, else by customer id (later events).
    if not user_id and customer_id:
        u = find_user_by_customer(customer_id)
        user_id = str(u["_id"]) if u else None
    if not user_id:
        return

    # Active-ish statuses keep the paid plan; terminal ones drop to free.
    active_statuses = {"active", "on_trial", "paused", "past_due"}
    terminal = {"cancelled", "expired", "unpaid"}
    if event in ("subscription_cancelled", "subscription_expired") or status in terminal:
        set_user_subscription(user_id, "free", status=status or "cancelled",
                              provider="lemonsqueezy", customer_id=customer_id,
                              subscription_id=subscription_id, portal_url=portal_url)
    elif plan_id:
        set_user_subscription(user_id, plan_id, status=status or "active",
                              provider="lemonsqueezy", customer_id=customer_id,
                              subscription_id=subscription_id, portal_url=portal_url)
        # First activation / renewal → invoice + email (USD canonical price).
        if event in ("subscription_created", "subscription_payment_success"):
            _email_invoice_safe(user_id, plan_id, "lemonsqueezy", "USD",
                                usd_price_for_plan(plan_id))


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
            # Checkout completed → invoice + email (USD canonical price).
            _email_invoice_safe(user_id, plan_id, "stripe", "USD",
                                usd_price_for_plan(plan_id))

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
