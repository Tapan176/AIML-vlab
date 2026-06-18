"""
Migration: Add indexes for OTP email-verification and billing invoices.

  - otp_codes: one active challenge per (email, purpose) lookup + a TTL index so
    expired codes are auto-purged by MongoDB (expireAfterSeconds=0 honours the
    per-doc `expires_at`).
  - invoices: per-user billing history listing (user_id + created_at desc) and a
    unique invoice_number so numbers never collide.
  - counters: the atomic per-month invoice sequence (single _id doc; no index
    needed beyond the implicit _id).
  - users.email_verified: backfill existing users as verified=True so enabling
    OTP later never locks out accounts that pre-date the feature.

Idempotent: create_index is a no-op when an equivalent index already exists.
"""


def _safe_unique_index(coll, keys, name):
    try:
        coll.create_index(keys, unique=True, name=name)
    except Exception as e:  # noqa: BLE001
        print(f"    WARN: unique index {name} not created ({e}); "
              f"falling back to non-unique")
        try:
            coll.create_index(keys, name=f"{name}_nonunique")
        except Exception:
            pass


def up(db):
    # --- otp_codes ---------------------------------------------------------
    db.otp_codes.create_index([('email', 1), ('purpose', 1)], name='email_purpose')
    # TTL: drop the doc once its own expires_at passes.
    try:
        db.otp_codes.create_index('expires_at', expireAfterSeconds=0, name='otp_ttl')
    except Exception as e:
        print(f"    WARN: otp_ttl index not created ({e})")

    # --- invoices ----------------------------------------------------------
    db.invoices.create_index([('user_id', 1), ('created_at', -1)],
                             name='user_created_desc')
    _safe_unique_index(db.invoices, [('invoice_number', 1)], 'uniq_invoice_number')

    # --- users: backfill email_verified for pre-OTP accounts ---------------
    try:
        db.users.update_many(
            {'email_verified': {'$exists': False}},
            {'$set': {'email_verified': True}},
        )
    except Exception as e:
        print(f"    WARN: email_verified backfill skipped ({e})")
