from flask import Blueprint, jsonify, request
from auth.auth_middleware import admin_required
from mongoDb.connection import get_db
from bson import ObjectId

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/stats', methods=['GET'])
@admin_required
def get_system_stats(current_user):
    """Aggregate system statistics for the admin dashboard."""
    try:
        db = get_db()
        
        # Total Users
        total_users = db.users.count_documents({})
        
        # Total Training Sessions
        total_sessions = db.training_sessions.count_documents({})
        
        # Total Datasets Uploaded
        total_datasets = db.datasets.count_documents({})
        
        # Sessions by Model
        pipeline = [
            {"$group": {"_id": "$model_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        sessions_by_model = list(db.training_sessions.aggregate(pipeline))
        
        return jsonify({
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_datasets": total_datasets,
            "sessions_by_model": sessions_by_model
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/datasets/default', methods=['GET'])
@admin_required
def list_default_datasets(current_user):
    """List all official platform datasets available to users."""
    try:
        db = get_db()
        datasets = list(db.datasets.find({"is_default": True}))
        for d in datasets:
            d['_id'] = str(d['_id'])
        return jsonify({"datasets": datasets}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/datasets/default/<dataset_id>', methods=['DELETE'])
@admin_required
def delete_default_dataset(current_user, dataset_id):
    """Remove an official dataset from the cloud library."""
    try:
        db = get_db()
        db.datasets.delete_one({"_id": ObjectId(dataset_id), "is_default": True})
        return jsonify({"message": "Dataset removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
