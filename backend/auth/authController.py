"""
Authentication controller — handles login, signup, password management.
Generates JWT tokens for session management.
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from mongoDb.connection import get_db
from bson import ObjectId
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS, FLASK_DEBUG


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


def login(email, password):
    # Reject non-string credentials BEFORE they reach the Mongo query. A JSON
    # body like {"email": {"$gt": ""}} would otherwise be a NoSQL operator that
    # matches an arbitrary user (authentication bypass).
    if not isinstance(email, str) or not isinstance(password, str):
        raise Exception("user_not_found")

    db = get_db()
    user = db.users.find_one({"email": email})

    if not user:
        raise Exception("user_not_found")

    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        raise Exception("incorrect_password")

    # Generate JWT token
    token = _generate_token(user['_id'], user['email'], user.get('role', 'user'))

    return {
        'user': _sanitize_user(user),
        'token': token
    }


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
        
        result = db.users.insert_one(update_payload)
        user_id = result.inserted_id
        role = "user"
        
        update_payload["_id"] = user_id
        user_data = update_payload

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
            # TODO: deliver the reset link by email. Until an email backend is
            # wired up, surface the token only in the server log in dev so it is
            # never exposed over the API.
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
