"""
Subscription / usage endpoints.

All read-only and safe to expose even when SUBSCRIPTION_ENABLED is false (the
service reports an unlimited 'free' plan in that case, and the frontend simply
hides the UI when subscription_enabled is false).
"""
from flask import Blueprint, jsonify

from auth.auth_middleware import token_required
from services.subscription_service import get_entitlements, list_plans

subscription_routes = Blueprint('subscription_routes', __name__)


@subscription_routes.route('/subscription/me', methods=['GET'])
@token_required
def my_entitlements(current_user):
    """Current user's plan, limits, and month-to-date usage."""
    try:
        return jsonify(get_entitlements(current_user)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@subscription_routes.route('/subscription/plans', methods=['GET'])
def plans():
    """Public plan catalog for the pricing page."""
    try:
        return jsonify({"plans": list_plans()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
