"""
Auth routes — login, signup, password management, user profile and account
data management (export / storage summary / revoke sessions / delete).
"""
import io
import json
import logging
from datetime import datetime

from bson import ObjectId
from flask import Blueprint, request, jsonify, send_file
from gridfs import GridFS

from auth.authController import (
    login, signup, forgot_password, reset_password,
    verify_login_otp, verify_signup_otp, resend_otp, AuthError,
)
from auth.auth_middleware import token_required
from extensions import limiter
from mongoDb.connection import get_db
from services.user_service import (
    update_user_profile, change_password, delete_user, update_profile_photo,
    verify_user_password,
)
from utils.validators import ValidationError

log = logging.getLogger(__name__)
auth_routes = Blueprint('auth_routes', __name__)

# Machine error code -> HTTP status. Anything not listed is treated as an
# unexpected server error and its details are NOT sent to the client.
_STATUS = {
    'invalid_credentials': 401,
    'account_deactivated': 403,
    'user_already_exists': 409,
    'email_already_in_use': 409,
    'otp_cooldown': 429,
}


def _error(e):
    """Translate an exception into a JSON error response without leaking internals."""
    if isinstance(e, (AuthError, ValidationError)):
        code = str(e)
        if code.startswith('otp_cooldown:'):
            return jsonify({"error": "otp_cooldown", "retry_after": int(code.split(':', 1)[1])}), 429
        return jsonify({"error": code}), _STATUS.get(code, 400)
    log.exception("Unhandled auth error")
    return jsonify({"error": "internal_error"}), 500


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@auth_routes.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def handle_login():
    data = _json_body()
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    try:
        return jsonify(login(data['email'], data['password'])), 200
    except Exception as e:
        return _error(e)


@auth_routes.route('/signup', methods=['POST'])
@limiter.limit("5 per minute")
def handle_signup():
    data = _json_body()
    required = ['firstName', 'email', 'password', 'termsAccepted']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    try:
        result = signup(
            data.get('firstName'), data.get('lastName'), data.get('email'),
            data.get('password'), data.get('phone'), data.get('countryCode'),
            data.get('termsAccepted'),
        )
        return jsonify(result), 201
    except Exception as e:
        return _error(e)


# ── OTP email verification (signup / login) ─────────────────────────────────

@auth_routes.route('/verify-otp', methods=['POST'])
@limiter.limit("15 per minute")
def handle_verify_otp():
    """Verify an emailed OTP and complete signup/login.

    Body: {email, code, purpose: 'signup'|'login'}. On success returns the same
    {user, token} shape as login/signup so the client can store the JWT.
    """
    data = _json_body()
    email, code, purpose = data.get('email'), data.get('code'), data.get('purpose')
    if not email or not code or purpose not in ('signup', 'login'):
        return jsonify({"error": "email, code and purpose are required"}), 400
    try:
        fn = verify_signup_otp if purpose == 'signup' else verify_login_otp
        return jsonify(fn(email, code)), 200
    except Exception as e:
        return _error(e)


@auth_routes.route('/resend-otp', methods=['POST'])
@limiter.limit("5 per minute")
def handle_resend_otp():
    """Re-issue an OTP (subject to a per-account cooldown)."""
    data = _json_body()
    if not data.get('email') or data.get('purpose') not in ('signup', 'login'):
        return jsonify({"error": "email and purpose are required"}), 400
    try:
        return jsonify(resend_otp(data['email'], data['purpose'])), 200
    except Exception as e:
        return _error(e)


@auth_routes.route('/forgot-password', methods=['POST'])
@limiter.limit("5 per minute")
def handle_forgot_password():
    data = _json_body()
    if not data.get('email'):
        return jsonify({"error": "Email is required"}), 400
    try:
        return jsonify(forgot_password(data['email'])), 200
    except Exception as e:
        return _error(e)


@auth_routes.route('/reset-password', methods=['POST'])
@limiter.limit("5 per minute")
def handle_reset_password():
    data = _json_body()
    if not data.get('token') or not data.get('newPassword'):
        return jsonify({"error": "Token and new password are required"}), 400
    try:
        return jsonify(reset_password(data['token'], data['newPassword'])), 200
    except Exception as e:
        return _error(e)


# ── Current user ─────────────────────────────────────────────────────────────

@auth_routes.route('/me', methods=['GET'])
@token_required
def handle_get_me(current_user):
    """Get current logged-in user's profile."""
    return jsonify({"user": current_user}), 200


@auth_routes.route('/update-profile', methods=['PUT'])
@limiter.limit("30 per minute")
@token_required
def handle_update_profile(current_user):
    data = _json_body()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    try:
        updated_user = update_user_profile(current_user['_id'], data)
        return jsonify({"user": updated_user, "message": "Profile updated successfully"}), 200
    except Exception as e:
        return _error(e)


@auth_routes.route('/change-password', methods=['PUT'])
@limiter.limit("10 per minute")
@token_required
def handle_change_password(current_user):
    """Change password. Signs out all OTHER sessions; returns a fresh token
    for this one (the client must store it)."""
    data = _json_body()
    if not data.get('oldPassword') or not data.get('newPassword'):
        return jsonify({"error": "Old and new passwords are required"}), 400
    try:
        token = change_password(current_user['_id'], data['oldPassword'], data['newPassword'])
        return jsonify({"message": "Password changed successfully", "token": token}), 200
    except Exception as e:
        return _error(e)


@auth_routes.route('/logout', methods=['POST'])
@token_required
def handle_logout(current_user):
    """Logout — client-side token clearing. Server acknowledges."""
    return jsonify({"message": "Logged out successfully"}), 200


@auth_routes.route('/logout-all', methods=['POST'])
@limiter.limit("10 per minute")
@token_required
def handle_logout_all(current_user):
    """Revoke every session for this account, on every device (incl. this one)."""
    from services.account_service import revoke_all_sessions
    revoke_all_sessions(current_user['_id'])
    return jsonify({"message": "Signed out of all devices"}), 200


@auth_routes.route('/me/storage', methods=['GET'])
@token_required
def handle_storage_summary(current_user):
    """Counts of the datasets / sessions / pipelines the user is storing."""
    from services.account_service import storage_summary
    return jsonify(storage_summary(current_user['_id'])), 200


@auth_routes.route('/me/export', methods=['GET'])
@limiter.limit("5 per hour")
@token_required
def handle_export(current_user):
    """Download everything we hold about the account as a JSON file."""
    from services.account_service import export_user_data
    payload = export_user_data(current_user['_id'])
    buf = io.BytesIO(json.dumps(payload, indent=2, default=str).encode('utf-8'))
    name = f"aiml-lab-export-{datetime.utcnow().strftime('%Y%m%d')}.json"
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name=name)


@auth_routes.route('/upload-profile-photo', methods=['PUT'])
@limiter.limit("10 per minute")
@token_required
def handle_upload_profile_photo(current_user):
    file = request.files.get('photo')
    if not file or not file.filename:
        return jsonify({"error": "No photo provided"}), 400
    try:
        updated_user = update_profile_photo(current_user['_id'], file)
        return jsonify({"user": updated_user, "message": "Profile photo updated successfully"}), 200
    except Exception as e:
        return _error(e)


@auth_routes.route('/profile-photo/<photo_id>', methods=['GET'])
def get_profile_photo(photo_id):
    """Retrieve a profile photo from GridFS or via the Google Drive proxy.

    Profile photos are display assets rendered in <img> tags (which can't send
    the auth header), so this stays unauthenticated — but only ids registered as
    some user's profile_photo_id are served. Otherwise this endpoint could be
    abused to download ANY Drive file (datasets, trained models) by id.
    """
    try:
        db = get_db()
        if not db.users.find_one({'profile_photo_id': photo_id}, {'_id': 1}):
            return jsonify({"error": "Photo not found"}), 404
        if len(photo_id) > 24:
            from services.google_drive_service import stream_file_from_drive
            fh, mimetype = stream_file_from_drive(photo_id)
            resp = send_file(fh, mimetype=mimetype)
        else:
            grid_out = GridFS(db).get(ObjectId(photo_id))
            resp = send_file(io.BytesIO(grid_out.read()), mimetype=grid_out.content_type)
        resp.headers['Cache-Control'] = 'private, max-age=3600'
        return resp
    except Exception:
        return jsonify({"error": "Photo not found"}), 404


@auth_routes.route('/delete-account', methods=['DELETE', 'POST'])
@limiter.limit("5 per hour")
@token_required
def handle_delete_account(current_user):
    """Permanently delete the account and all data it owns.

    Requires re-authentication so a stolen/left-open session can't wipe the
    account: password accounts send {password}; OAuth-only accounts (whose
    password is a random value they never knew) send {confirm: "DELETE"}.
    """
    data = _json_body()
    if current_user.get('oauth_provider') and not data.get('password'):
        if data.get('confirm') != 'DELETE':
            return jsonify({"error": "confirmation_required"}), 400
    elif not verify_user_password(current_user['_id'], data.get('password')):
        return jsonify({"error": "incorrect_password"}), 403
    try:
        report = delete_user(current_user['_id'])
        return jsonify({"message": "Account deleted successfully", "deleted": report}), 200
    except Exception as e:
        return _error(e)
