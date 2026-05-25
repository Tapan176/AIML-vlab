"""
JWT authentication middleware for protecting routes.
"""
import jwt
import time
import threading
from functools import wraps
from flask import request, jsonify
from mongoDb.connection import get_db
from bson import ObjectId
from config import JWT_SECRET, JWT_ALGORITHM


# Short-lived per-process cache for user lookups. Every protected request
# would otherwise hit MongoDB once. 30s TTL trades a brief delay in
# observing user mutations (e.g. account deletion, role change) for one
# round-trip saved on every API call.
_USER_CACHE_TTL_S = 30
_USER_CACHE_MAX = 1000
_user_cache = {}
_user_cache_lock = threading.Lock()


def _cache_get(user_id):
    with _user_cache_lock:
        entry = _user_cache.get(user_id)
        if entry is None:
            return None
        ts, user = entry
        if time.monotonic() - ts > _USER_CACHE_TTL_S:
            _user_cache.pop(user_id, None)
            return None
        return user


def _cache_set(user_id, user):
    with _user_cache_lock:
        if len(_user_cache) >= _USER_CACHE_MAX:
            oldest = min(_user_cache, key=lambda k: _user_cache[k][0])
            _user_cache.pop(oldest, None)
        _user_cache[user_id] = (time.monotonic(), user)


def invalidate_user_cache(user_id):
    """Drop the cached copy of a specific user. Call after any update to that
    user's document so subsequent requests re-read fresh state instead of
    seeing the cached version for up to 30 seconds."""
    with _user_cache_lock:
        _user_cache.pop(str(user_id), None)


def token_required(f=None, optional=False):
    """Decorator to protect routes with JWT authentication.

    When optional=True, the route still works without a token but
    current_user will be None. When optional=False (default), a missing
    or invalid token returns 401.
    """
    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            token = None
            current_user = None

            # Get token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

            if not token:
                if optional:
                    return fn(None, *args, **kwargs)
                return jsonify({'error': 'Authentication token is missing'}), 401

            try:
                # Decode the token
                payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                user_id = payload.get('user_id')

                if not user_id:
                    if optional:
                        return fn(None, *args, **kwargs)
                    return jsonify({'error': 'Invalid token payload'}), 401

                current_user = _cache_get(user_id)
                if current_user is None:
                    db = get_db()
                    current_user = db.users.find_one({'_id': ObjectId(user_id)})
                    if not current_user:
                        if optional:
                            return fn(None, *args, **kwargs)
                        return jsonify({'error': 'User not found'}), 401
                    current_user['_id'] = str(current_user['_id'])
                    current_user.pop('password', None)
                    _cache_set(user_id, current_user)

            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                if optional:
                    return fn(None, *args, **kwargs)
                return jsonify({'error': 'Invalid or expired token'}), 401
            except Exception as e:
                if optional:
                    return fn(None, *args, **kwargs)
                return jsonify({'error': f'Authentication failed: {str(e)}'}), 401

            # Pass current_user to the route function
            return fn(current_user, *args, **kwargs)

        return decorated

    # Support both @token_required and @token_required(optional=True) syntax
    if f is not None:
        # Called as @token_required (without parentheses)
        return decorator(f)
    # Called as @token_required(optional=True)
    return decorator

def admin_required(f):
    """Decorator to protect routes requiring admin privileges."""
    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
            
        return f(current_user, *args, **kwargs)

    return decorated
