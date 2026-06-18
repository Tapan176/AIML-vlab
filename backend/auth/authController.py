"""
Authentication controller — handles login, signup, password management.
Generates JWT tokens for session management.
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from mongoDb.connection import get_db
from bson import ObjectId
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS, FLASK_DEBUG, OTP_ENABLED


def _generate_token(user_id, email, role="user"):
    """Generate a JWT access token."""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_token(user):
    """Public helper: issue a JWT for a user dict (used by OAuth routes).

    Accepts a user document with `_id` (or `id`), `email`, and optional `role`,
    and delegates to _generate_token so OAuth and password flows mint identical
    tokens that token_required can validate the same way.
    """
    return _generate_token(
        user.get('_id') or user.get('id'),
        user.get('email'),
        user.get('role', 'user'),
    )


def _sanitize_user(user):
    """Remove sensitive fields and convert ObjectId for JSON serialization."""
    user['_id'] = str(user['_id'])
    user.pop('password', None)
    return user


def _verify_credentials(email, password):
    """Shared credential check used by login + OTP login. Returns the user doc.

    Rejects non-string credentials BEFORE they reach the Mongo query. A JSON
    body like {"email": {"$gt": ""}} would otherwise be a NoSQL operator that
    matches an arbitrary user (authentication bypass).
    """
    if not isinstance(email, str) or not isinstance(password, str):
        raise Exception("user_not_found")
    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        raise Exception("user_not_found")
    if not user.get('password'):
        # OAuth-only account with no local password set.
        raise Exception("incorrect_password")
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        raise Exception("incorrect_password")
    return user


def _issue_token_for(user):
    token = _generate_token(user['_id'], user['email'], user.get('role', 'user'))
    return {'user': _sanitize_user(dict(user)), 'token': token}


def login(email, password):
    user = _verify_credentials(email, password)

    # OTP gate: don't issue a JWT yet — email a code and signal the client to
    # collect it via /verify-otp. Credentials are confirmed valid at this point.
    if OTP_ENABLED:
        _send_otp(user['email'], "login", "sign in to your account")
        return {"otp_required": True, "purpose": "login", "email": user['email']}

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


def verify_login_otp(email, code):
    """Complete an OTP login: verify the code, then issue the JWT."""
    from services.otp_service import verify_otp
    if not isinstance(email, str):
        raise Exception("user_not_found")
    ok, err = verify_otp(email, "login", code if isinstance(code, str) else "")
    if not ok:
        raise Exception(err or "otp_incorrect")
    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        raise Exception("user_not_found")
    db.users.update_one({"_id": user["_id"]}, {"$set": {"email_verified": True}})
    user["email_verified"] = True
    return _issue_token_for(user)


def verify_signup_otp(email, code):
    """Complete an OTP signup: verify the code, mark verified, issue the JWT."""
    from services.otp_service import verify_otp
    if not isinstance(email, str):
        raise Exception("user_not_found")
    ok, err = verify_otp(email, "signup", code if isinstance(code, str) else "")
    if not ok:
        raise Exception(err or "otp_incorrect")
    db = get_db()
    user = db.users.find_one({"email": email})
    if not user:
        raise Exception("user_not_found")
    db.users.update_one({"_id": user["_id"]}, {"$set": {"email_verified": True}})
    user["email_verified"] = True
    return _issue_token_for(user)


def resend_otp(email, purpose):
    """Re-issue an OTP (subject to the service-level cooldown)."""
    if purpose not in ("login", "signup"):
        raise Exception("invalid_purpose")
    human = "sign in to your account" if purpose == "login" else "verify your email"
    ok, info = _send_otp(email, purpose, human)
    if not ok and info.get("error") == "otp_cooldown":
        raise Exception(f"otp_cooldown:{info.get('retry_after', 60)}")
    return {"message": "A new code has been sent if the account is eligible."}


def signup(first_name, last_name, email, password, phone, country_code, terms_accepted):
    db = get_db()
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    update_payload = {
        "first_name": first_name,
        "last_name": last_name,
        "password": hashed_password,
        "phone": phone,
        "countryCode": country_code,
        "termsAccepted": terms_accepted,
    }

    existing_user = db.users.find_one({"email": email})

    if existing_user:
        # Perform logical UPSERT to maintain single email index constraint
        db.users.update_one(
            {"_id": existing_user["_id"]},
            {"$set": update_payload}
        )
        user_id = existing_user["_id"]
        role = existing_user.get("role", "user")
        
        # Pull merged data for returning
        updated_user = db.users.find_one({"_id": user_id})
        user_data = updated_user
    else:
        # Create fresh user
        update_payload["email"] = email
        update_payload["role"] = "user"
        update_payload["created_at"] = datetime.utcnow()
        update_payload["email_verified"] = False

        result = db.users.insert_one(update_payload)
        user_id = result.inserted_id
        role = "user"

        update_payload["_id"] = user_id
        user_data = update_payload

    # OTP gate: require email verification before issuing a JWT. The account row
    # exists (so the email is reserved) but stays email_verified=False until the
    # code is confirmed via /verify-otp.
    if OTP_ENABLED:
        _send_otp(email, "signup", "verify your email")
        return {"otp_required": True, "purpose": "signup", "email": email}

    # Auto-login: generate token
    token = _generate_token(user_id, email, role)

    return {
        'user': _sanitize_user(user_data),
        'token': token
    }


def forgot_password(email):
    # Behave identically whether or not the account exists (prevents user
    # enumeration) and NEVER return the token to the caller. Returning it let
    # anyone mint a working reset token for any email = unauthenticated takeover.
    if isinstance(email, str):
        db = get_db()
        user = db.users.find_one({"email": email})
        if user:
            reset_token = jwt.encode(
                {
                    "email": email,
                    "type": "password_reset",
                    "exp": datetime.utcnow() + timedelta(hours=1),
                },
                JWT_SECRET,
                algorithm=JWT_ALGORITHM,
            )
            # Deliver the reset link by email (console fallback in dev when SMTP
            # isn't configured). The token is NEVER returned over the API.
            try:
                from config import APP_PUBLIC_URL
                from services.email_service import send_password_reset_email
                reset_url = f"{APP_PUBLIC_URL.rstrip('/')}/reset-password?token={reset_token}"
                send_password_reset_email(email, reset_url)
            except Exception as e:
                print(f"[forgot_password] email step failed: {e}", flush=True)
            if FLASK_DEBUG:
                print(f"[forgot_password] DEV ONLY reset token for {email}: {reset_token}", flush=True)

    return {"message": "If an account exists for that email, a password reset link has been sent."}


def reset_password(token, new_password):
    if not isinstance(token, str) or not isinstance(new_password, str):
        raise Exception("invalid_reset_token")

    db = get_db()

    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise Exception("reset_token_expired")
    except jwt.InvalidTokenError:
        raise Exception("invalid_reset_token")

    if decoded.get('type') != 'password_reset':
        raise Exception("invalid_reset_token")

    user = db.users.find_one({"email": decoded['email']})

    if not user:
        raise Exception("user_not_found")

    if bcrypt.checkpw(new_password.encode('utf-8'), user['password'].encode('utf-8')):
        raise Exception("new_password_same_as_old_password")

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    db.users.update_one(
        {"email": decoded['email']},
        {"$set": {"password": hashed_password}}
    )

    return {"message": "Password reset successfully"}
