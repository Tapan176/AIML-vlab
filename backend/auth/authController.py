"""
Authentication controller — handles login, signup, password management.
Generates JWT tokens for session management.

Session revocation
------------------
Every user document carries an integer ``token_version`` (missing = 0) and
every JWT carries it as the ``tv`` claim. ``token_required`` rejects tokens
whose ``tv`` no longer matches, so bumping the counter (password change /
reset, "log out everywhere", admin force-logout, account deletion) instantly
invalidates every token issued before it.
"""
import hashlib
import re
from datetime import datetime, timedelta

import bcrypt
import jwt

from mongoDb.connection import get_db
from config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS, FLASK_DEBUG, OTP_ENABLED,
    PASSWORD_RESET_TTL_MINUTES,
)
from utils.validators import normalize_email, validate_password, clean_str, ValidationError


class AuthError(Exception):
    """Auth failure carrying a machine-readable code (str(e) == code)."""


# A precomputed hash so a login for an unknown email still spends the same
# bcrypt time as a real one (prevents user enumeration by timing).
_DUMMY_HASH = bcrypt.hashpw(b"timing-equaliser", bcrypt.gensalt()).decode("utf-8")


def _hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password, hashed):
    if not isinstance(password, str) or not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _password_fingerprint(user):
    """Short digest of the stored password hash. Embedded in reset tokens so a
    token stops working as soon as the password changes (single-use)."""
    return hashlib.sha256((user.get("password") or "").encode("utf-8")).hexdigest()[:16]


def find_user_by_email(email):
    """Look up a user by (already normalised) email.

    Emails are stored lower-cased since migration 007; the case-insensitive
    fallback only exists for legacy rows that could not be normalised (e.g. a
    case-variant duplicate).
    """
    db = get_db()
    user = db.users.find_one({"email": email})
    if user:
        return user
    return db.users.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}})


def _generate_token(user_id, email, role="user", token_version=0):
    now = datetime.utcnow()
    payload = {
        "user_id": str(user_id),
        "email": email,
        "role": role,
        "tv": int(token_version or 0),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_token(user):
    """Public helper: issue a JWT for a user dict (used by OAuth routes)."""
    return _generate_token(
        user.get("_id") or user.get("id"),
        user.get("email"),
        user.get("role", "user"),
        user.get("token_version", 0),
    )


def sanitize_user(user):
    """Remove sensitive fields and convert ObjectId for JSON serialization."""
    user = dict(user)
    user["_id"] = str(user["_id"])
    for field in ("password", "token_version"):
        user.pop(field, None)
    return user


def _issue_token_for(user):
    return {"user": sanitize_user(user), "token": generate_token(user)}


def _verify_credentials(email, password):
    """Shared credential check used by login. Returns the user doc.

    Always raises the SAME 'invalid_credentials' code for unknown email and
    wrong password, and spends bcrypt time in both cases, so the endpoint can't
    be used to discover which emails have accounts.
    """
    try:
        email = normalize_email(email)
    except ValidationError:
        raise AuthError("invalid_credentials")
    if not isinstance(password, str) or not password:
        raise AuthError("invalid_credentials")

    user = find_user_by_email(email)
    if not user or not user.get("password"):
        _check_password(password, _DUMMY_HASH)
        raise AuthError("invalid_credentials")
    if not _check_password(password, user["password"]):
        raise AuthError("invalid_credentials")
    if user.get("active", True) is False:
        raise AuthError("account_deactivated")
    return user


def login(email, password):
    user = _verify_credentials(email, password)

    # OTP gate: don't issue a JWT yet — email a code and signal the client to
    # collect it via /verify-otp. Credentials are confirmed valid at this point.
    if OTP_ENABLED:
        _send_otp(user["email"], "login", "sign in to your account")
        return {"otp_required": True, "purpose": "login", "email": user["email"]}

    get_db().users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
    return _issue_token_for(user)


def _send_otp(email, purpose, human_purpose):
    """Generate + email an OTP. Swallows email errors (logged) so a flaky mail
    server can't break the auth flow. Returns (ok, info)."""
    from services.otp_service import request_otp
    from services.email_service import send_otp_email
    ok, info = request_otp(email, purpose)
    if ok and info.get("code"):
        send_otp_email(email, info["code"], human_purpose)
    return ok, info


def _complete_otp(email, code, purpose):
    from services.otp_service import verify_otp
    try:
        email = normalize_email(email)
    except ValidationError:
        raise AuthError("invalid_otp")
    ok, err = verify_otp(email, purpose, code if isinstance(code, str) else "")
    if not ok:
        raise AuthError(err or "otp_incorrect")
    user = find_user_by_email(email)
    if not user:
        raise AuthError("invalid_otp")
    get_db().users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email_verified": True, "last_login": datetime.utcnow()}},
    )
    user["email_verified"] = True
    return _issue_token_for(user)


def verify_login_otp(email, code):
    """Complete an OTP login: verify the code, then issue the JWT."""
    return _complete_otp(email, code, "login")


def verify_signup_otp(email, code):
    """Complete an OTP signup: verify the code, mark verified, issue the JWT."""
    return _complete_otp(email, code, "signup")


def resend_otp(email, purpose):
    """Re-issue an OTP (subject to the service-level cooldown).

    Only sends when a matching account exists, but always answers the same way
    so the endpoint can't be used to enumerate accounts or spam arbitrary
    addresses.
    """
    if purpose not in ("login", "signup"):
        raise AuthError("invalid_purpose")
    try:
        email = normalize_email(email)
    except ValidationError:
        raise AuthError("invalid_email")
    if find_user_by_email(email):
        human = "sign in to your account" if purpose == "login" else "verify your email"
        ok, info = _send_otp(email, purpose, human)
        if not ok and info.get("error") == "otp_cooldown":
            raise AuthError(f"otp_cooldown:{info.get('retry_after', 60)}")
    return {"message": "A new code has been sent if the account is eligible."}


def signup(first_name, last_name, email, password, phone, country_code, terms_accepted):
    """Create a password account.

    An existing email is NEVER overwritten for a verified account — the old
    "logical upsert" replaced the existing user's password and returned a token
    for it, i.e. anyone could take over any account by signing up with its
    email. The one exception is an UNVERIFIED account while OTP is on: the
    new registrant still has to prove they own the mailbox before a token is
    issued, which lets the real owner reclaim an address someone squatted.
    """
    email = normalize_email(email)
    validate_password(password)
    if terms_accepted is not True:
        raise ValidationError("terms_not_accepted")
    profile = {
        "first_name": clean_str(first_name, "first_name", 80, required=True),
        "last_name": clean_str(last_name, "last_name", 80) or "",
        "phone": clean_str(phone, "phone", 32) or "",
        "countryCode": clean_str(country_code, "country_code", 8) or "",
        "termsAccepted": True,
    }

    db = get_db()
    existing = find_user_by_email(email)
    if existing:
        reclaimable = (
            OTP_ENABLED
            and not existing.get("email_verified")
            and not existing.get("oauth_id")
        )
        if not reclaimable:
            raise AuthError("user_already_exists")
        db.users.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {**profile, "password": _hash_password(password)},
                "$inc": {"token_version": 1},
            },
        )
        _send_otp(email, "signup", "verify your email")
        return {"otp_required": True, "purpose": "signup", "email": email}

    now = datetime.utcnow()
    new_user = {
        **profile,
        "email": email,
        "password": _hash_password(password),
        "role": "user",
        "active": True,
        "email_verified": False,
        "token_version": 0,
        "created_at": now,
    }
    try:
        result = db.users.insert_one(new_user)
    except Exception as e:  # unique index race (two signups for the same email)
        if "duplicate key" in str(e).lower():
            raise AuthError("user_already_exists")
        raise
    new_user["_id"] = result.inserted_id

    if OTP_ENABLED:
        _send_otp(email, "signup", "verify your email")
        return {"otp_required": True, "purpose": "signup", "email": email}

    return _issue_token_for(new_user)


def forgot_password(email):
    # Behave identically whether or not the account exists (prevents user
    # enumeration) and NEVER return the token to the caller.
    try:
        email = normalize_email(email)
    except ValidationError:
        email = None
    user = find_user_by_email(email) if email else None
    if user:
        reset_token = jwt.encode(
            {
                "uid": str(user["_id"]),
                "type": "password_reset",
                "fp": _password_fingerprint(user),
                "exp": datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        try:
            from config import APP_PUBLIC_URL
            from services.email_service import send_password_reset_email
            reset_url = f"{APP_PUBLIC_URL.rstrip('/')}/reset-password?token={reset_token}"
            send_password_reset_email(user["email"], reset_url)
        except Exception as e:
            print(f"[forgot_password] email step failed: {e}", flush=True)
        if FLASK_DEBUG:
            print(f"[forgot_password] DEV ONLY reset token for {user['email']}: {reset_token}", flush=True)

    return {"message": "If an account exists for that email, a password reset link has been sent."}


def reset_password(token, new_password):
    """Set a new password from an emailed reset token.

    The token is bound to the password hash at issue time (``fp``), so it is
    single-use: once the password changes, any outstanding reset link dies.
    All existing sessions are revoked.
    """
    if not isinstance(token, str):
        raise AuthError("invalid_reset_token")
    validate_password(new_password)

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("reset_token_expired")
    except jwt.InvalidTokenError:
        raise AuthError("invalid_reset_token")

    if decoded.get("type") != "password_reset" or not decoded.get("uid"):
        raise AuthError("invalid_reset_token")

    from bson import ObjectId
    db = get_db()
    try:
        user = db.users.find_one({"_id": ObjectId(decoded["uid"])})
    except Exception:
        user = None
    if not user or decoded.get("fp") != _password_fingerprint(user):
        raise AuthError("invalid_reset_token")
    if _check_password(new_password, user.get("password")):
        raise AuthError("new_password_same_as_old_password")

    db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password": _hash_password(new_password), "password_changed_at": datetime.utcnow()},
            "$inc": {"token_version": 1},
        },
    )
    from auth.auth_middleware import invalidate_user_cache
    invalidate_user_cache(user["_id"])
    return {"message": "Password reset successfully"}
