"""
Auth routes — login, signup, password management, user profile.
"""
from flask import Blueprint, request, jsonify
from auth.authController import login, signup, forgot_password, reset_password
from auth.authMiddleware import token_required
from services.userService import get_user_by_id, update_user_profile, change_password

auth_routes = Blueprint('auth_routes', __name__)


@auth_routes.route('/login', methods=['POST'])
def handle_login():
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email and password are required"}), 400

        result = login(data['email'], data['password'])
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        status = 401 if error_message in ('user_not_found', 'incorrect_password') else 500
        return jsonify({"error": error_message}), status


@auth_routes.route('/signup', methods=['POST'])
def handle_signup():
    try:
        data = request.get_json()
        required_fields = ['firstName', 'lastName', 'email', 'password', 'phone', 'countryCode', 'termsAccepted']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        result = signup(
            data['firstName'], data['lastName'], data['email'],
            data['password'], data['phone'], data['countryCode'],
            data['termsAccepted']
        )
        return jsonify(result), 201
    except Exception as e:
        error_message = str(e)
        status = 409 if error_message == 'user_already_exists' else 500
        return jsonify({"error": error_message}), status


@auth_routes.route('/forgot-password', methods=['POST'])
def handle_forgot_password():
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({"error": "Email is required"}), 400

        result = forgot_password(data['email'])
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        status = 404 if error_message == 'user_not_found' else 500
        return jsonify({"error": error_message}), status


@auth_routes.route('/reset-password', methods=['POST'])
def handle_reset_password():
    try:
        data = request.get_json()
        if not data or 'token' not in data or 'newPassword' not in data:
            return jsonify({"error": "Token and new password are required"}), 400

        result = reset_password(data['token'], data['newPassword'])
        return jsonify(result), 200
    except Exception as e:
        error_message = str(e)
        return jsonify({"error": error_message}), 400


@auth_routes.route('/me', methods=['GET'])
@token_required
def handle_get_me(current_user):
    """Get current logged-in user's profile."""
    return jsonify({"user": current_user}), 200


@auth_routes.route('/update-profile', methods=['PUT'])
@token_required
def handle_update_profile(current_user):
    """Update current user's profile."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        updated_user = update_user_profile(current_user['_id'], data)
        return jsonify({"user": updated_user, "message": "Profile updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_routes.route('/change-password', methods=['PUT'])
@token_required
def handle_change_password(current_user):
    """Change current user's password."""
    try:
        data = request.get_json()
        if not data or 'oldPassword' not in data or 'newPassword' not in data:
            return jsonify({"error": "Old and new passwords are required"}), 400

        change_password(current_user['_id'], data['oldPassword'], data['newPassword'])
        return jsonify({"message": "Password changed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_routes.route('/logout', methods=['POST'])
@token_required
def handle_logout(current_user):
    """Logout — client-side token clearing. Server acknowledges."""
    return jsonify({"message": "Logged out successfully"}), 200
