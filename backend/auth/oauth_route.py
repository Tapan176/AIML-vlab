"""
OAuth routes for third-party authentication (Google, GitHub).
Creates/links user accounts and returns JWT tokens.
"""
from flask import Blueprint, request, jsonify, redirect, url_for, session as flask_session
import requests
import json
from datetime import datetime

oauth_routes = Blueprint('oauth_routes', __name__)

from urllib.parse import urlencode
from config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET,
    ALLOWED_ORIGINS, BASE_DIR,
    OAUTH_REDIRECT_BASE, FRONTEND_URL,
)
from auth.authController import generate_token


def _get_redirect_uri(provider):
    """Build the OAuth callback URL for `provider`.

    This URL must be IDENTICAL in the auth request and the token exchange, and
    must match what's registered with the provider. The callback is a top-level
    redirect from the provider (no Origin header), so we cannot derive it from
    the frontend origin. Order of truth:
      1. OAUTH_REDIRECT_BASE — explicit public backend URL (required in prod).
      2. request.host_url — this backend's own base; consistent between the
         /login and /callback requests since both hit the backend (dev fallback).
    """
    base = OAUTH_REDIRECT_BASE or request.host_url
    return f"{base.rstrip('/')}/api/auth/{provider}/callback"


def _allowed_origins():
    return [o.strip().rstrip('/') for o in (ALLOWED_ORIGINS or []) if o and o.strip()]


def _frontend_origin():
    """Where the popup should post the token back to."""
    return (
        request.headers.get('Origin')
        or FRONTEND_URL
        or (ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else 'http://localhost:3000')
    )


def _resolve_frontend_origin(candidate):
    """Return a SAFE frontend origin for delivering the minted JWT.

    `candidate` is the `state` echoed back by the provider — fully attacker-
    controllable (anyone can craft a provider auth URL with an arbitrary state),
    so it is honored ONLY if it is in ALLOWED_ORIGINS. Otherwise we fall back to
    the configured frontend. This prevents redirecting the token to an attacker
    origin (token exfiltration / open redirect).
    """
    allowed = _allowed_origins()
    if candidate:
        c = candidate.replace('/api', '').rstrip('/')
        if c in allowed:
            return c
    if FRONTEND_URL:
        return FRONTEND_URL.rstrip('/')
    return allowed[0] if allowed else 'http://localhost:3000'


def _find_or_create_user(email, first_name='', last_name='', oauth_provider='', oauth_id='', avatar_url='', email_verified=False):
    """Find existing user by email or create a new one. Returns user dict.

    `email_verified` MUST reflect whether the provider asserted the email as
    verified. We only auto-link an OAuth identity to a pre-existing (e.g.
    password) account when the email is verified — otherwise an attacker could
    register a provider account with a victim's (unverified) email and take over
    the victim's account. Raises ValueError('oauth_email_unverified') if linking
    is attempted with an unverified email.
    """
    from mongoDb.connection import get_db
    from bson import ObjectId
    import bcrypt
    import secrets

    db = get_db()

    # Try finding by OAuth ID first
    if oauth_id:
        existing = db.users.find_one({'oauth_id': oauth_id, 'oauth_provider': oauth_provider})
        if existing:
            existing['_id'] = str(existing['_id'])
            # Update last login
            db.users.update_one(
                {'_id': ObjectId(existing['_id'])},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            return existing

    # Try finding by email
    if email:
        existing = db.users.find_one({'email': email.lower().strip()})
        if existing:
            existing['_id'] = str(existing['_id'])
            # Linking a brand-new OAuth identity to an existing account requires
            # a provider-verified email (anti-takeover).
            if oauth_id and existing.get('oauth_id') != oauth_id and not email_verified:
                raise ValueError("oauth_email_unverified")
            # Link OAuth to existing account
            if oauth_id:
                db.users.update_one(
                    {'_id': ObjectId(existing['_id'])},
                    {'$set': {
                        'oauth_id': oauth_id,
                        'oauth_provider': oauth_provider,
                        'avatar_url': avatar_url or existing.get('avatar_url'),
                        'last_login': datetime.utcnow(),
                    }}
                )
                existing['oauth_id'] = oauth_id
                existing['oauth_provider'] = oauth_provider
            return existing

    # Create new user. Field names MUST match the password-signup schema in
    # authController.signup (password / countryCode / termsAccepted) so the
    # rest of the app — login, _sanitize_user, profile — treats OAuth users
    # identically to password users.
    names = first_name.split(' ', 1) if first_name else ['User', '']
    new_user = {
        'email': email.lower().strip() if email else f'{oauth_provider}_{oauth_id[:8]}@placeholder.local',
        'first_name': names[0] or first_name or 'User',
        'last_name': names[1] if len(names) > 1 else last_name or '',
        'password': bcrypt.hashpw(secrets.token_hex(32).encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'role': 'user',
        'phone': '',
        'countryCode': '',
        'oauth_provider': oauth_provider,
        'oauth_id': oauth_id,
        'avatar_url': avatar_url,
        'termsAccepted': True,
        'email_verified': True,
        'created_at': datetime.utcnow(),
        'last_login': datetime.utcnow(),
    }
    result = db.users.insert_one(new_user)
    new_user['_id'] = str(result.inserted_id)
    return new_user


# ── Google OAuth ──────────────────────────────────────────────────────────

@oauth_routes.route('/auth/google/login', methods=['GET'])
def google_login():
    """Initiate Google OAuth flow."""
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"}), 501

    redirect_uri = _get_redirect_uri('google')
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': _frontend_origin(),  # echoed back to the callback for postMessage targeting
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return jsonify({"url": auth_url}), 200


@oauth_routes.route('/auth/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback."""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Authorization code not provided"}), 400

    redirect_uri = _get_redirect_uri('google')

    # Exchange code for tokens
    token_resp = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    })
    if not token_resp.ok:
        return jsonify({"error": "Failed to exchange code", "detail": token_resp.text}), 400

    tokens = token_resp.json()
    access_token = tokens.get('access_token')

    # Get user info
    user_resp = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers={
        'Authorization': f'Bearer {access_token}'
    })
    if not user_resp.ok:
        return jsonify({"error": "Failed to get user info"}), 400

    google_user = user_resp.json()

    try:
        user = _find_or_create_user(
            email=google_user.get('email'),
            first_name=google_user.get('given_name', ''),
            last_name=google_user.get('family_name', ''),
            oauth_provider='google',
            oauth_id=google_user.get('id'),
            avatar_url=google_user.get('picture'),
            email_verified=bool(google_user.get('verified_email') or google_user.get('email_verified')),
        )
    except ValueError as e:
        return _oauth_error_response(str(e))

    jwt_token = generate_token(user)
    return _oauth_callback_response(jwt_token, user)


# ── GitHub OAuth ──────────────────────────────────────────────────────────

@oauth_routes.route('/auth/github/login', methods=['GET'])
def github_login():
    """Initiate GitHub OAuth flow."""
    if not GITHUB_CLIENT_ID:
        return jsonify({"error": "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env"}), 501

    redirect_uri = _get_redirect_uri('github')
    params = {
        'client_id': GITHUB_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'user:email',
        'state': _frontend_origin(),  # echoed back to the callback for postMessage targeting
    }
    auth_url = 'https://github.com/login/oauth/authorize?' + urlencode(params)
    return jsonify({"url": auth_url}), 200


@oauth_routes.route('/auth/github/callback', methods=['GET'])
def github_callback():
    """Handle GitHub OAuth callback."""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Authorization code not provided"}), 400

    # Exchange code for access token
    token_resp = requests.post('https://github.com/login/oauth/access_token', data={
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code,
    }, headers={'Accept': 'application/json'})

    if not token_resp.ok:
        return jsonify({"error": "Failed to exchange code"}), 400

    tokens = token_resp.json()
    access_token = tokens.get('access_token')
    if not access_token:
        return jsonify({"error": "No access token received"}), 400

    # Get user info
    user_resp = requests.get('https://api.github.com/user', headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    })
    if not user_resp.ok:
        return jsonify({"error": "Failed to get GitHub user info"}), 400

    gh_user = user_resp.json()

    # Resolve the email AND whether GitHub considers it verified. The public
    # `gh_user.email` carries no verified flag, so always consult /user/emails
    # to get the verified status of the primary email.
    email = None
    email_verified = False
    email_resp = requests.get('https://api.github.com/user/emails', headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    })
    if email_resp.ok:
        emails = email_resp.json()
        primary = [e for e in emails if e.get('primary')]
        chosen = (primary or emails or [None])[0]
        if chosen:
            email = chosen.get('email')
            email_verified = bool(chosen.get('verified'))
    if not email:
        email = gh_user.get('email')  # last resort; treated as unverified

    name_parts = (gh_user.get('name') or gh_user.get('login', 'User')).split(' ', 1)

    try:
        user = _find_or_create_user(
            email=email,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else '',
            oauth_provider='github',
            oauth_id=str(gh_user.get('id')),
            avatar_url=gh_user.get('avatar_url'),
            email_verified=email_verified,
        )
    except ValueError as e:
        return _oauth_error_response(str(e))

    jwt_token = generate_token(user)
    return _oauth_callback_response(jwt_token, user)


def _safe_user(user):
    """Return a JSON-serializable copy of a user dict: drop the password hash
    and coerce ObjectId/datetime values to strings so json.dumps won't crash."""
    safe = {}
    for k, v in user.items():
        if k == 'password':
            continue
        if isinstance(v, datetime):
            safe[k] = v.isoformat()
        else:
            safe[k] = str(v) if type(v).__name__ == 'ObjectId' else v
    return safe


def _oauth_callback_response(jwt_token, user):
    """Return an HTML page that posts the token back to the React app, then closes.

    The popup is opened from the frontend, so window.opener is the SPA. We post
    the token to the frontend origin (from the `state` we set at login) and, if
    that origin is unavailable, fall back to '*'. If there's no opener at all
    (popup blocked / opened as a full redirect), we navigate to the frontend
    with the token in the URL hash so the SPA can still recover it.
    """
    # Only ever deliver the token to an allow-listed origin (see
    # _resolve_frontend_origin). Note the explicit target on postMessage and the
    # removal of any '*' fallback — '*' would broadcast the JWT to any window.
    frontend_origin = _resolve_frontend_origin(request.args.get('state'))

    return f"""<!DOCTYPE html>
<html>
<head><title>Login Complete</title></head>
<body>
    <script>
        (function() {{
            var token = {json.dumps(jwt_token)};
            var user = {json.dumps(_safe_user(user))};
            var target = {json.dumps(frontend_origin)};
            var msg = {{ type: 'OAUTH_LOGIN', token: token, user: user }};
            try {{
                if (window.opener && window.opener !== window) {{
                    window.opener.postMessage(msg, target);
                    window.close();
                    return;
                }}
            }} catch (e) {{}}
            // No opener: hand the token to the SPA via the URL hash.
            window.location.href = target + '/login#oauth_token=' + encodeURIComponent(token);
        }})();
    </script>
    <p>Login successful! This window will close automatically.</p>
</body>
</html>"""


def _oauth_error_response(code):
    """Render a small popup page for a failed OAuth login (e.g. an unverified
    email that can't be auto-linked), then return the user to the login page."""
    target = _resolve_frontend_origin(request.args.get('state'))
    messages = {
        "oauth_email_unverified": (
            "Your provider account's email isn't verified, so we can't link it "
            "to an existing account. Verify your email with the provider, or log "
            "in with your password."
        ),
    }
    msg = messages.get(code, "OAuth login failed. Please try again.")
    return f"""<!DOCTYPE html>
<html>
<head><title>Login Failed</title></head>
<body>
    <script>
        (function() {{
            var target = {json.dumps(target)};
            setTimeout(function() {{ window.location.href = target + '/login'; }}, 4000);
        }})();
    </script>
    <p>{msg}</p>
    <p>Redirecting back to login…</p>
</body>
</html>""", 400


# ── OAuth Config Endpoint ─────────────────────────────────────────────────

@oauth_routes.route('/auth/providers', methods=['GET'])
def get_oauth_providers():
    """Return which OAuth providers are configured."""
    providers = []
    if GOOGLE_CLIENT_ID:
        providers.append({
            'id': 'google',
            'name': 'Google',
            'icon': '🔵',
            'login_url': '/api/auth/google/login',
        })
    if GITHUB_CLIENT_ID:
        providers.append({
            'id': 'github',
            'name': 'GitHub',
            'icon': '🐙',
            'login_url': '/api/auth/github/login',
        })
    return jsonify({"providers": providers}), 200
