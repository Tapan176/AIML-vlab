from flask import Blueprint, request, jsonify

pipelines_routes = Blueprint('pipelines_routes', __name__)

from auth.auth_middleware import token_required


@pipelines_routes.route('/pipelines/templates', methods=['GET'])
def get_pipeline_templates_route():
    """Get built-in pipeline templates."""
    try:
        from services.preprocessing_service import get_pipeline_templates
        return jsonify(get_pipeline_templates()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@pipelines_routes.route('/pipelines', methods=['GET'])
@token_required
def list_pipelines_route(current_user):
    """List all saved pipelines for the current user."""
    try:
        from services.preprocessing_service import list_pipelines
        return jsonify(list_pipelines(current_user['_id'])), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@pipelines_routes.route('/pipelines', methods=['POST'])
@token_required
def save_pipeline_route(current_user):
    """Save a named preprocessing pipeline."""
    try:
        data = request.get_json()
        name = data.get('name')
        operations = data.get('operations', [])
        if not name:
            return jsonify({"error": "Pipeline name is required"}), 400
        from services.preprocessing_service import save_pipeline
        pid = save_pipeline(current_user['_id'], name, operations)
        return jsonify({"message": "Pipeline saved", "pipeline_id": pid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@pipelines_routes.route('/pipelines/<pipeline_name>', methods=['GET'])
@token_required
def load_pipeline_route(current_user, pipeline_name):
    """Load a saved pipeline by name."""
    try:
        from services.preprocessing_service import load_pipeline
        ops = load_pipeline(current_user['_id'], pipeline_name)
        return jsonify({"name": pipeline_name, "operations": ops}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@pipelines_routes.route('/pipelines/<pipeline_name>', methods=['DELETE'])
@token_required
def delete_pipeline_route(current_user, pipeline_name):
    """Delete a saved pipeline."""
    try:
        from services.preprocessing_service import delete_pipeline
        delete_pipeline(current_user['_id'], pipeline_name)
        return jsonify({"message": f"Pipeline '{pipeline_name}' deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404
