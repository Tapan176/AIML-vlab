from flask import Blueprint, request, jsonify
from auth.authController import login, signup, forgot_password, reset_password

auth_routes = Blueprint('auth_routes', __name__)
@auth_routes.route('/login', methods=['POST'])
def handle_login():
    try:
        data = request.get_json()
        user = login(data['email'], data['password'])
        return jsonify(user), 200
    except Exception as e:
        error_message = str(e)
        # Log the error message for debugging purposes
        print(f"Login Error: {error_message}")
        return str(e), 401

@auth_routes.route('/signup', methods=['POST'])
def handle_signup():
    try:
        data = request.get_json()
        user = signup(data['firstName'], data['lastName'], data['email'], data['password'], data['phone'], data['countryCode'], data['termsAccepted'],)
        return jsonify(user), 201
    except Exception as e:
        error_message = str(e)
        # Log the error message for debugging purposes
        print(f"Signup Error: {error_message}")
        return jsonify({"error": error_message}), 409

@auth_routes.route('/forgot-password', methods=['POST'])
def handle_forgot_password():
    try:
        data = request.get_json()
        user = forgot_password(data['email'])
        return jsonify(user), 200
    except Exception as e:
        return str(e), 404

@auth_routes.route('/reset-password', methods=['POST'])
def handle_reset_password():
    try:
        data = request.get_json()
        user = reset_password(data['token'], data['newPassword'])
        return jsonify(user), 200
    except Exception as e:
        return str(e), 400
