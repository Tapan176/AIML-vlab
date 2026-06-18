"""Tests for auth/auth_middleware.py — the JWT gate on every protected route.

Two layers:
  * end-to-end through a real protected endpoint (/api/user-datasets) for the
    common missing / invalid / valid token paths;
  * direct decorator calls inside a request context for the nuanced paths
    (expired token, optional pass-through, deactivated account, admin gate)
    that don't have a dedicated simple endpoint.
"""
import time

import jwt
import pytest
from bson import ObjectId

from config import JWT_SECRET, JWT_ALGORITHM
from auth.auth_middleware import token_required, admin_required


def _make_token(user_id, *, expired=False, secret=JWT_SECRET):
    payload = {
        'user_id': str(user_id),
        'exp': int(time.time()) + (-10 if expired else 3600),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def _insert_user(db, **overrides):
    doc = {'_id': ObjectId(), 'email': 'u@example.com', 'name': 'U', 'active': True}
    doc.update(overrides)
    db.users.insert_one(doc)
    return doc


# ---- end-to-end via a real protected endpoint -----------------------------

def test_missing_token_returns_401(client):
    assert client.get('/api/user-datasets').status_code == 401


def test_malformed_token_returns_401(client):
    resp = client.get('/api/user-datasets',
                      headers={'Authorization': 'Bearer not.a.jwt'})
    assert resp.status_code == 401


def test_valid_token_allows_access(client, db):
    user = _insert_user(db)
    tok = _make_token(user['_id'])
    resp = client.get('/api/user-datasets',
                      headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 200
    assert 'datasets' in resp.get_json()


def test_token_signed_with_wrong_secret_is_rejected(client, db):
    user = _insert_user(db)
    tok = _make_token(user['_id'], secret='a-totally-different-secret')
    resp = client.get('/api/user-datasets',
                      headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 401


def test_valid_token_for_unknown_user_returns_401(client, db):
    # Token is well-formed and correctly signed, but no such user exists.
    tok = _make_token(ObjectId())
    resp = client.get('/api/user-datasets',
                      headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 401


# ---- decorator-level tests for the nuanced paths --------------------------

def test_expired_token_is_rejected(app, db):
    user = _insert_user(db)
    tok = _make_token(user['_id'], expired=True)

    @token_required
    def protected(current_user):
        return 'ok'

    with app.test_request_context(headers={'Authorization': f'Bearer {tok}'}):
        result = protected()
    assert result[1] == 401  # (json, status) tuple on failure


def test_optional_passes_through_without_token(app):
    @token_required(optional=True)
    def maybe(current_user):
        return 'anon' if current_user is None else 'user'

    with app.test_request_context():
        assert maybe() == 'anon'


def test_deactivated_account_is_forbidden(app, db):
    user = _insert_user(db, active=False)
    tok = _make_token(user['_id'])

    @token_required
    def protected(current_user):
        return 'ok'

    with app.test_request_context(headers={'Authorization': f'Bearer {tok}'}):
        result = protected()
    assert result[1] == 403


def test_admin_required_blocks_non_admin(app, db):
    user = _insert_user(db, role='user')
    tok = _make_token(user['_id'])

    @admin_required
    def admin_only(current_user):
        return 'secret'

    with app.test_request_context(headers={'Authorization': f'Bearer {tok}'}):
        result = admin_only()
    assert result[1] == 403


def test_admin_required_allows_admin(app, db):
    user = _insert_user(db, role='admin')
    tok = _make_token(user['_id'])

    @admin_required
    def admin_only(current_user):
        return 'secret'

    with app.test_request_context(headers={'Authorization': f'Bearer {tok}'}):
        assert admin_only() == 'secret'
