from flask import Blueprint, request, send_file, jsonify
from utils.downloadFiles import get_model_path
from utils.uploadFiles import handle_upload_file
from utils.downloadPrediction import get_model_predictions

utils_routes = Blueprint('utils_routes', __name__)

from auth.auth_middleware import token_required
from services.training_session_service import get_session

@utils_routes.route('/download-trained-model/<session_id>', methods=['GET'])
@token_required
def download_model_session(current_user, session_id):
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Try Drive download first
        drive_id = session.get('trained_model_drive_id')
        if drive_id:
            try:
                from services.google_drive_service import stream_file_from_drive
                fh, mime_type = stream_file_from_drive(drive_id)
                download_name = session.get('trained_model_filename', f"{session.get('session_label', 'model')}.zip")
                return send_file(fh, as_attachment=True, download_name=download_name, mimetype=mime_type)
            except Exception as e:
                print(f"Drive download failed, falling back to local: {e}")
        
        # Fallback to local path
        model_path = session.get('trained_model_path')
        if not model_path:
            return jsonify({"error": "Model not available"}), 404
        
        import os
        download_name = session.get('trained_model_filename', os.path.basename(model_path))
        return send_file(model_path, as_attachment=True, download_name=download_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@utils_routes.route('/download-results-zip/<session_id>', methods=['GET'])
@token_required
def download_results_zip_session(current_user, session_id):
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403
        
        drive_id = session.get('results_zip_drive_id')
        if not drive_id:
            return jsonify({"error": "Results zip not available in Google Drive."}), 404
            
        from services.google_drive_service import stream_file_from_drive
        fh, mime_type = stream_file_from_drive(drive_id)
        download_name = f"{session.get('session_label', 'session')}_results.zip"
        return send_file(fh, as_attachment=True, download_name=download_name, mimetype=mime_type)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@utils_routes.route('/download-trained-model', methods=['GET'])
def download_model():
    model_path = get_model_path(request)
    import os
    download_name = os.path.basename(model_path)
    return send_file(model_path, as_attachment=True, download_name=download_name)

@utils_routes.route('/download-model-predictions', methods=['GET'])
def download_model_predictions():
    model_path = get_model_predictions(request)
    return send_file(model_path, as_attachment=True)

@utils_routes.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    results = handle_upload_file(request, current_user['_id'])

    return jsonify(results)

@utils_routes.route('/feedback', methods=['POST'])
@token_required
def submit_feedback(current_user):
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
            
        from mongoDb.connection import get_db
        import datetime
        db = get_db()
        db.feedback.insert_one({
            "user_id": current_user['_id'],
            "email": current_user.get('email'),
            "message": data['message'],
            "type": data.get('type', 'general'),
            "created_at": datetime.datetime.utcnow()
        })
        return jsonify({"message": "Feedback submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@utils_routes.route('/models/info', methods=['GET'])
def get_models_info():
    try:
        from mongoDb.connection import get_db
        db = get_db()
        models = list(db.models.find({}, {'_id': 0}))
        # Sort or just return as is
        return jsonify(models), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@utils_routes.route('/datasets/default', methods=['GET'])
def list_default_datasets_public():
    try:
        from mongoDb.connection import get_db
        db = get_db()
        datasets = list(db.datasets.find({"is_default": True}))
        for d in datasets:
            d['_id'] = str(d['_id'])
        return jsonify({"datasets": datasets}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@utils_routes.route('/datasets/<dataset_id>', methods=['DELETE'])
@token_required
def delete_user_dataset(current_user, dataset_id):
    try:
        from mongoDb.connection import get_db
        from bson import ObjectId
        from services.google_drive_service import delete_file_from_drive
        db = get_db()
        
        # Verify ownership
        dataset = db.datasets.find_one({'_id': ObjectId(dataset_id), 'user_id': current_user['_id']})
        if not dataset:
            return jsonify({"error": "Dataset not found or unauthorized"}), 404
            
        # Delete from Google Drive if it exists there
        if dataset.get('drive_id'):
            delete_file_from_drive(dataset['drive_id'])
            
        # Remove DB record
        db.datasets.delete_one({'_id': ObjectId(dataset_id)})
        return jsonify({"message": "Dataset deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@utils_routes.route('/datasets/preprocess', methods=['POST'])
@token_required
def preprocess_cloud_dataset(current_user):
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        operations = data.get('operations')
        
        if not dataset_id or not operations or not isinstance(operations, list):
            return jsonify({"error": "dataset_id and an array of operations are required"}), 400
            
        from services.preprocessing_service import perform_preprocessing
        new_dataset = perform_preprocessing(current_user, dataset_id, operations)
        
        # ensure _id is stringified for JSON compatibility
        new_dataset['_id'] = str(new_dataset['_id'])
        
        return jsonify({"message": "Preprocessing complete", "dataset": new_dataset}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
