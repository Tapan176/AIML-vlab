from flask import Blueprint, request, send_file, jsonify
from utils.downloadFiles import get_model_path
from services.model_catalog import get_model_catalog, get_catalog_from_db, MODEL_CATALOG_VERSION

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

@utils_routes.route('/training-sessions/<session_id>/result-images', methods=['GET'])
@token_required
def get_result_images(current_user, session_id):
    """Return a completed session's output plots as base64 data URIs.

    The trainer's local PNGs are deleted right after a run (they only survive
    inside the Drive results.zip), so on a Dashboard "Replay" the model page has
    no images to show. This streams the results.zip back from Drive, extracts
    the image files, and returns them base64-encoded — the SAME plots the user
    saw live — without bloating the session document in MongoDB.
    """
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403

        drive_id = session.get('results_zip_drive_id')
        if not drive_id:
            return jsonify({"images": []}), 200

        # Immutable per results.zip — serve a cached extract to skip the Drive
        # download + unzip on repeat replay loads (incl. after a page reload).
        from utils.result_image_cache import get as _img_cache_get, put as _img_cache_put
        cached = _img_cache_get(drive_id)
        if cached is not None:
            return jsonify({"images": cached}), 200

        import os
        import zipfile
        import base64
        from services.google_drive_service import stream_file_from_drive

        IMG_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        MAX_IMAGES = 20
        images = []
        fh, _ = stream_file_from_drive(drive_id)
        with zipfile.ZipFile(fh) as zf:
            for name in zf.namelist():
                ext = os.path.splitext(name)[1].lower()
                if ext not in IMG_EXTS:
                    continue
                raw = zf.read(name)
                mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else f"image/{ext.lstrip('.')}"
                images.append(f"data:{mime};base64,{base64.b64encode(raw).decode('utf-8')}")
                if len(images) >= MAX_IMAGES:
                    break
        _img_cache_put(drive_id, images)
        return jsonify({"images": images}), 200
    except Exception as e:
        return jsonify({"error": str(e), "images": []}), 200


@utils_routes.route('/download-trained-model', methods=['GET'])
@token_required
def download_model(current_user):
    import os
    try:
        model_path = get_model_path(request, current_user)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not os.path.exists(model_path):
        return jsonify({"error": "Trained model file not found on server. Please train a new model."}), 404

    download_name = os.path.basename(model_path)
    return send_file(model_path, as_attachment=True, download_name=download_name)

@utils_routes.route('/download-model-predictions/<session_id>', methods=['GET'])
@token_required
def download_model_predictions_session(current_user, session_id):
    """Download a session's predictions CSV — owner-scoped, served from Drive.

    Replaces the old query-param route that read a GLOBAL predictions/<model>.csv
    with no ownership check (any user could fetch the last predictions for a
    model type). Predictions are now uploaded per session like the trained model.
    """
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403

        drive_id = session.get('predictions_drive_id')
        if not drive_id:
            return jsonify({"error": "Predictions not available for this session."}), 404

        from services.google_drive_service import stream_file_from_drive
        fh, mime_type = stream_file_from_drive(drive_id)
        download_name = session.get('predictions_filename') or f"{session.get('session_label', 'model')}_predictions.csv"
        return send_file(fh, as_attachment=True, download_name=download_name, mimetype=mime_type)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

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
    """Rich model info for the in-app info drawer (ModelInfoPanel).

    Reads the structured catalog from the MongoDB `models` collection (the
    runtime source of truth, seeded by migration 004). Each document's
    `description` is an ARRAY of sections — which is what the drawer renders.
    get_catalog_from_db() transparently falls back to the in-code catalog if the
    DB is empty/unavailable; the flat registry is a last-resort fallback.
    """
    try:
        return jsonify(get_catalog_from_db()), 200
    except Exception:
        try:
            from services.model_registry import get_model_registry
            registry = get_model_registry()
            return jsonify(list(registry['models'].values())), 200
        except Exception:
            return jsonify({"error": "Failed to load model info"}), 500


@utils_routes.route('/config', methods=['GET'])
def public_config():
    """Public runtime config the SPA reads on startup (no auth).

    Exposes feature flags that must be toggleable without rebuilding the
    frontend bundle (CRA bakes process.env at build time, so flags can't ride
    in there). Currently just the subscription master switch.
    """
    from config import SUBSCRIPTION_ENABLED
    return jsonify({"subscription_enabled": SUBSCRIPTION_ENABLED}), 200


@utils_routes.route('/models/registry', methods=['GET'])
def get_model_registry_route():
    """
    Dynamic model registry endpoint.
    Returns complete metadata for all models including categories,
    endpoints, streaming info, file extensions, and component import paths.
    This is the single source of truth for the frontend — add a model to
    services/model_registry.py and it automatically appears everywhere.
    """
    try:
        from services.model_registry import get_model_registry
        return jsonify(get_model_registry()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
