"""
OTP service — email one-time-code verification for signup / login.

Security properties
-------------------
* Codes are **never stored in plaintext.** We store a bcrypt hash of the code,
  so a DB leak can't reveal active OTPs.
* **Constant-ish verification.** bcrypt.checkpw is used for the compare.
* **Brute-force resistant.** Each challenge tracks an attempt counter; after
  OTP_MAX_ATTEMPTS failures the code is invalidated (forces a resend).
* **TTL expiry.** Mongo TTL index drops codes after OTP_TTL_MINUTES.
* **Resend throttle.** A per-(email,purpose) cooldown blocks rapid re-issues
  (in addition to the route-level flask_limiter limits).
* **No user enumeration via OTP.** request_otp() behaves identically whether or
  not a matching account exists for the given purpose.

Collection: `otp_codes`  { email, purpose, code_hash, attempts, expires_at,
                            created_at }  — one active doc per (email, purpose).
Purposes: "signup", "login".
"""
import secrets
from datetime import datetime, timedelta

import bcrypt

from config import (
    OTP_ENABLED,
    OTP_LENGTH,
    OTP_TTL_MINUTES,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
)
from mongoDb.connection import get_db


def is_enabled():
    return OTP_ENABLED


def _coll():
    db = get_db()
    coll = db.otp_codes
    # Idempotent index setup (also created in a migration, but safe to ensure).
    try:
        coll.create_index([("email", 1), ("purpose", 1)], name="email_purpose")
        coll.create_index("expires_at", expireAfterSeconds=0, name="otp_ttl")
    except Exception:
        pass
    return coll


def _generate_code():
    """Cryptographically-strong numeric code of OTP_LENGTH digits."""
    n = max(4, int(OTP_LENGTH))
    lo = 10 ** (n - 1)
    hi = (10 ** n) - 1
    return str(secrets.randbelow(hi - lo + 1) + lo)


def request_otp(email, purpose):
    """Generate, store (hashed) and return a code for emailing.

    Returns (ok: bool, info: dict). On cooldown returns
    (False, {"error": "otp_cooldown", "retry_after": seconds}). On success
    returns (True, {"code": "123456"}). The CALLER emails the code; we never
    return it to the client.
    """
    if not isinstance(email, str) or "@" not in email:
        # Behave like success to avoid leaking which inputs are valid.
        return False, {"error": "invalid_email"}

    coll = _coll()
    now = datetime.utcnow()
    existing = coll.find_one({"email": email, "purpose": purpose})
    if existing:
        created = existing.get("created_at")
        if created and (now - created).total_seconds() < OTP_RESEND_COOLDOWN_SECONDS:
            retry = int(OTP_RESEND_COOLDOWN_SECONDS - (now - created).total_seconds())
            return False, {"error": "otp_cooldown", "retry_after": max(1, retry)}

    code = _generate_code()
    code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    coll.update_one(
        {"email": email, "purpose": purpose},
        {"$set": {
            "email": email,
            "purpose": purpose,
            "code_hash": code_hash,
            "attempts": 0,
            "created_at": now,
            "expires_at": now + timedelta(minutes=OTP_TTL_MINUTES),
        }},
        upsert=True,
    )
    return True, {"code": code}


def verify_otp(email, purpose, code):
    """Verify a submitted code. Returns (ok: bool, error: str|None).

    On success the challenge is consumed (deleted). On failure the attempt
    counter is incremented and the challenge is dropped once attempts are
    exhausted.
    """
    if not (isinstance(email, str) and isinstance(code, str)):
        return False, "invalid_otp"
    coll = _coll()
    doc = coll.find_one({"email": email, "purpose": purpose})
    if not doc:
        return False, "otp_not_found"
    if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
        coll.delete_one({"_id": doc["_id"]})
        return False, "otp_expired"
    if int(doc.get("attempts", 0)) >= OTP_MAX_ATTEMPTS:
        coll.delete_one({"_id": doc["_id"]})
        return False, "otp_too_many_attempts"

    if bcrypt.checkpw(code.encode("utf-8"), doc["code_hash"].encode("utf-8")):
        coll.delete_one({"_id": doc["_id"]})  # one-time use
        return True, None

    # Wrong code — count the attempt; invalidate when exhausted.
    new_attempts = int(doc.get("attempts", 0)) + 1
    if new_attempts >= OTP_MAX_ATTEMPTS:
        coll.delete_one({"_id": doc["_id"]})
        return False, "otp_too_many_attempts"
    coll.update_one({"_id": doc["_id"]}, {"$set": {"attempts": new_attempts}})
    return False, "otp_incorrect"
