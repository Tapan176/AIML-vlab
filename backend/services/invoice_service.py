"""
Invoice service — builds + persists billing invoices and emails them.

Invoices are generated when a payment webhook confirms a successful charge
(SOURCE OF TRUTH). We store them in the `invoices` collection so the user can
list/download them from their profile, and email a copy via email_service.

An invoice dict has a stable, display-ready shape consumed by both the email
template and the frontend "Billing history" list:

    {
      invoice_number, date, user_id, email, plan_id, plan_name,
      provider, provider_label, currency, amount,         # numeric (major units)
      amount_display, total_display,                       # formatted strings
      line_items: [{description, amount, amount_display}],
      created_at,
    }
"""
from datetime import datetime

from mongoDb.connection import get_db


_PROVIDER_LABELS = {
    "razorpay": "Razorpay",
    "lemonsqueezy": "Lemon Squeezy",
    "stripe": "Stripe",
}

_CURRENCY_SYMBOLS = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}


def _fmt_money(amount, currency):
    sym = _CURRENCY_SYMBOLS.get((currency or "USD").upper(), "")
    try:
        # Whole-number display for INR (no decimals), 2dp otherwise.
        if (currency or "").upper() == "INR":
            return f"{sym}{int(round(amount)):,}"
        return f"{sym}{amount:,.2f}"
    except Exception:
        return f"{sym}{amount}"


def _next_invoice_number(db):
    """Human-friendly sequential-ish invoice number: AIML-YYYYMM-#####.

    Uses an atomic per-month counter in `counters` so numbers don't collide
    under concurrent webhooks.
    """
    period = datetime.utcnow().strftime("%Y%m")
    doc = db.counters.find_one_and_update(
        {"_id": f"invoice-{period}"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    seq = (doc or {}).get("seq", 1)
    return f"AIML-{period}-{seq:05d}"


def build_invoice(user_id, email, plan_id, plan_name, provider, currency, amount,
                  description=None):
    """Build a display-ready invoice dict (does not persist)."""
    currency = (currency or "USD").upper()
    desc = description or f"{plan_name} plan — monthly subscription"
    amount_display = _fmt_money(amount, currency)
    return {
        "invoice_number": None,  # filled in on persist
        "date": datetime.utcnow().strftime("%d %b %Y"),
        "user_id": str(user_id),
        "email": email,
        "plan_id": plan_id,
        "plan_name": plan_name,
        "provider": provider,
        "provider_label": _PROVIDER_LABELS.get(provider, provider or "card"),
        "currency": currency,
        "amount": amount,
        "amount_display": amount_display,
        "total_display": amount_display,
        "line_items": [
            {"description": desc, "amount": amount, "amount_display": amount_display},
        ],
        "created_at": datetime.utcnow(),
    }


def persist_invoice(invoice):
    """Assign an invoice number and store it. Returns the stored invoice."""
    db = get_db()
    invoice["invoice_number"] = _next_invoice_number(db)
    db.invoices.insert_one(dict(invoice))
    return invoice


def create_and_email_invoice(user_id, email, plan_id, plan_name, provider,
                             currency, amount, description=None):
    """Build + persist + email an invoice. Returns the invoice dict.

    Email send failures are swallowed by email_service (logged), so a flaky mail
    server never aborts a billing webhook.
    """
    invoice = build_invoice(user_id, email, plan_id, plan_name, provider,
                            currency, amount, description=description)
    invoice = persist_invoice(invoice)
    try:
        from services.email_service import send_invoice_email
        if email:
            send_invoice_email(email, invoice)
    except Exception as e:
        print(f"[invoice] email step failed: {e}", flush=True)
    return invoice


def list_invoices(user_id, limit=50):
    """Return the user's invoices, newest first (for the billing-history UI)."""
    db = get_db()
    cur = (db.invoices
           .find({"user_id": str(user_id)})
           .sort("created_at", -1)
           .limit(int(limit)))
    out = []
    for doc in cur:
        doc["id"] = str(doc.pop("_id"))
        doc.pop("created_at", None)  # not JSON-serializable as-is; date string covers it
        out.append(doc)
    return out
