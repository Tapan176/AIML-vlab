"""
OAuth routes for third-party authentication (Google, GitHub).
Creates/links user accounts and returns JWT tokens.
"""
from flask import Blueprint, request, jsonify, redirect, url_for, session as flask_session
import requests
import json
from datetime import datetime

oauth_routes = Blueprint('oauth_routes', __name__)

from config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET,
    ALLOWED_ORIGINS, BASE_DIR,
)
from auth.authController import generate_token


def _get_redirect_uri(provider):
    """Get the OAuth redirect URI based on the request origin."""
    # Use the first allowed origin as base, or the request's origin
    origin = request.headers.get('Origin', ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else 'http://localhost:3000')
    # For local dev, the API is on a different port
    api_base = origin.replace('3000', '5050')
    return f"{api_base}/api/auth/{provider}/callback"


def _find_or_create_user(email, first_name='', last_name='', oauth_provider='', oauth_id='', avatar_url=''):
    """Find existing user by email or create a new one. Returns user dict."""
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

    # Create new user
    names = first_name.split(' ', 1) if first_name else ['User', '']
    new_user = {
        'email': email.lower().strip() if email else f'{oauth_provider}_{oauth_id[:8]}@placeholder.local',
        'first_name': names[0] or first_name or 'User',
        'last_name': names[1] if len(names) > 1 else last_name or '',
        'password_hash': bcrypt.hashpw(secrets.token_hex(32).encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'role': 'user',
        'phone': '',
        'country_code': '',
        'oauth_provider': oauth_provider,
        'oauth_id': oauth_id,
        'avatar_url': avatar_url,
        'terms_accepted': True,
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
    auth_url = (
        'https://accounts.google.com/o/oauth2/v2/auth'
        f'?client_id={GOOGLE_CLIENT_ID}'
        f'&redirect_uri={redirect_uri}'
        '&response_type=code'
        '&scope=openid%20email%20profile'
        '&access_type=offline'
        '&prompt=consent'
    )
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

    user = _find_or_create_user(
        email=google_user.get('email'),
        first_name=google_user.get('given_name', ''),
        last_name=google_user.get('family_name', ''),
        oauth_provider='google',
        oauth_id=google_user.get('id'),
        avatar_url=google_user.get('picture'),
    )

    jwt_token = generate_token(user)
    return _oauth_callback_response(jwt_token, user)


# ── GitHub OAuth ──────────────────────────────────────────────────────────

@oauth_routes.route('/auth/github/login', methods=['GET'])
def github_login():
    """Initiate GitHub OAuth flow."""
    if not GITHUB_CLIENT_ID:
        return jsonify({"error": "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env"}), 501

    redirect_uri = _get_redirect_uri('github')
    auth_url = (
        'https://github.com/login/oauth/authorize'
        f'?client_id={GITHUB_CLIENT_ID}'
        f'&redirect_uri={redirect_uri}'
        '&scope=user:email'
    )
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

    # Get email (may need separate call)
    email = gh_user.get('email')
    if not email:
        email_resp = requests.get('https://api.github.com/user/emails', headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        })
        if email_resp.ok:
            emails = email_resp.json()
            primary = [e for e in emails if e.get('primary')]
            if primary:
                email = primary[0]['email']
            elif emails:
                email = emails[0]['email']

    name_parts = (gh_user.get('name') or gh_user.get('login', 'User')).split(' ', 1)

    user = _find_or_create_user(
        email=email,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else '',
        oauth_provider='github',
        oauth_id=str(gh_user.get('id')),
        avatar_url=gh_user.get('avatar_url'),
    )

    jwt_token = generate_token(user)
    return _oauth_callback_response(jwt_token, user)


def _oauth_callback_response(jwt_token, user):
    """Return an HTML page that posts the token back to the React app, then closes."""
    frontend_origin = request.args.get('state') or (ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else 'http://localhost:3000')
    # Strip /api from any state if accidentally included
    frontend_origin = frontend_origin.replace('/api', '')

    return f"""<!DOCTYPE html>
<html>
<head><title>Login Complete</title></head>
<body>
    <script>
        (function() {{
            var token = {json.dumps(jwt_token)};
            var user = {json.dumps({k: v for k, v in user.items() if k != 'password_hash'})};
            try {{
                if (window.opener && window.opener !== window) {{
                    window.opener.postMessage({{
                        type: 'OAUTH_LOGIN',
                        token: token,
                        user: user
                    }}, '*');
                }}
            }} catch(e) {{}}
            localStorage.setItem('aiml_token', token);
            window.close();
        }})();
    </script>
    <p>Login successful! This window will close automatically.</p>
</body>
</html>"""


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
