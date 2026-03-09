"""
JWT authentication middleware for protecting routes.
"""
import jwt
from functools import wraps
from flask import request, jsonify
from mongoDb.connection import get_db
from bson import ObjectId
from config import JWT_SECRET, JWT_ALGORITHM


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

                # Fetch user from database
                db = get_db()
                current_user = db.users.find_one({'_id': ObjectId(user_id)})

                if not current_user:
                    if optional:
                        return fn(None, *args, **kwargs)
                    return jsonify({'error': 'User not found'}), 401

                # Convert ObjectId to string
                current_user['_id'] = str(current_user['_id'])
                # Remove password from user object
                current_user.pop('password', None)

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
