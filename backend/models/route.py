"""
Model routes — endpoints for training all 11 ML models.
Supports hyperparameter tuning, user-scoped storage, and training sessions.
"""
from flask import Blueprint, request, jsonify
import math
from auth.auth_middleware import token_required
from services.hyperparam_validator import validate_hyperparams, get_model_schema
from services.training_session_service import create_session, update_session_results, update_session_error, get_user_sessions, get_session, delete_session, get_session_progress
from services.dataset_service import get_user_datasets
from utils.sse_helpers import run_sse_training

from models.linearRegression.linearRegression import simpleLinearRegression
# CNN/ANN are lazy-loaded at call time to avoid TensorFlow protobuf import errors at startup
from models.multivariableLinearRegression.multivariableLinearRegression import multivariateLinearRegression
from models.logisticRegression.logisticRegression import logisticRegression
from models.decisionTree.decisionTree import decisionTree
from models.randomForest.randomForest import randomForest
from models.knn.knn import knn
from models.supportVectorMachine.supportVectorMachine import supportVectorMachine
from models.naiveBayes.naiveBayes import naiveBayes
from models.kMeans.kMeans import kMeans
from models.dbscan.dbscan import dbscan
from models.gradientBoosting.gradientBoosting import train_gradient_boosting
from models.sentimentAnalysis.sentimentAnalysis import train_sentiment_analysis
from models.textClassification.textClassification import train_text_classification

model_routes = Blueprint('model_routes', __name__)


def _sanitize_for_json(value):
    """Recursively replace NaN/Infinity with None so JSON is valid."""
    try:
        import numpy as np
        if isinstance(value, np.generic):
            return _sanitize_for_json(value.item())
        if isinstance(value, np.ndarray):
            return [_sanitize_for_json(v) for v in value.tolist()]
    except Exception:
        pass
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    return value

# Map model codes to training functions
MODEL_FUNCTIONS = {
    'simple_linear_regression': simpleLinearRegression,
    'multivariable_linear_regression': multivariateLinearRegression,
    'logistic_regression': logisticRegression,
    'decision_tree': decisionTree,
    'random_forest': randomForest,
    'knn': knn,
    'svm': supportVectorMachine,
    'naive_bayes': naiveBayes,
    'k_means': kMeans,
    'dbscan': dbscan,
    'gradient_boosting': train_gradient_boosting,
    'sentiment_analysis': train_sentiment_analysis,
    'text_classification': train_text_classification,
    # CNN/ANN omitted — handled via lazy import
    # XGBoost omitted — handled via lazy import
}


def _train_model(model_code, request_obj, current_user=None):
    """Generic model training handler with hyperparameter validation and session tracking."""
    data = request_obj.get_json() or {}

    # Extract hyperparams from request
    user_hyperparams = data.get('hyperparams', {})

    try:
        # Validate hyperparameters
        validated_params = validate_hyperparams(model_code, user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Inject validated hyperparams into the data
    data['validated_hyperparams'] = validated_params

    # Create a training session if user is logged in
    session_id = None
    user_id = current_user['_id'] if current_user else None

    if user_id:
        # Enforce subscription quota (no-op unless SUBSCRIPTION_ENABLED).
        from services.subscription_service import check_quota, record_usage
        ok, info = check_quota(current_user, model_code)
        if not ok:
            return jsonify(info), 429

        dataset_id = data.get('dataset_id')
        session = create_session(user_id, model_code, validated_params, dataset_id)
        session_id = session['_id']
        record_usage(user_id, model_code)
        data['user_id'] = user_id
        data['session_id'] = session_id
        data['session_version'] = session['version']

    try:
        # Call the model's training function
        train_fn = MODEL_FUNCTIONS[model_code]
        results = train_fn(request_obj, validated_params=validated_params, user_id=user_id, session_version=session.get('version') if user_id else None)

        if isinstance(results, dict) and results.get('error'):
            if session_id:
                update_session_error(session_id, results['error'])
            return jsonify({"error": results['error']}), 400

        output_image_urls = results.get('outputImageUrls', [])
        
        # Base64 encode images for frontend display before they get deleted
        import base64
        import os
        output_image_base64 = []
        for img_path in output_image_urls:
            if os.path.exists(img_path):
                with open(img_path, "rb") as image_file:
                    b64 = base64.b64encode(image_file.read()).decode('utf-8')
                    ext = os.path.splitext(img_path)[1].lower()
                    mime_type = "image/png"
                    if ext in ['.jpg', '.jpeg']:
                        mime_type = "image/jpeg"
                    output_image_base64.append(f"data:{mime_type};base64,{b64}")
                    
        results['outputImageBase64'] = output_image_base64

        # Update session with results
        if session_id:
            db_results = update_session_results(
                session_id,
                results.get('evaluation_metrics') or results.get('results') or results,
                output_image_urls,
                results.get('trained_model_path', ''),
                results.get('predictions_output_file', '')
            )
            # Merge DB results (with Drive IDs) back into the response results
            results.update(db_results)
            results['session_id'] = session_id

        return jsonify(_sanitize_for_json(results)), 200

    except Exception as e:
        if session_id:
            update_session_error(session_id, str(e))
        return jsonify({"error": str(e)}), 500


# --- Model Training Endpoints ---

@model_routes.route('/linear-regression', methods=['POST'])
@token_required
def linear_regression(current_user):
    return _train_model('simple_linear_regression', request, current_user)


@model_routes.route('/multivariable-linear-regression', methods=['POST'])
@token_required
def multivariate_linear_regression(current_user):
    return _train_model('multivariable_linear_regression', request, current_user)


@model_routes.route('/logistic-regression', methods=['POST'])
@token_required
def logistic_regression_route(current_user):
    return _train_model('logistic_regression', request, current_user)


@model_routes.route('/decision-tree', methods=['POST'])
@token_required
def decision_tree(current_user):
    return _train_model('decision_tree', request, current_user)


@model_routes.route('/random-forest', methods=['POST'])
@token_required
def random_forest(current_user):
    return _train_model('random_forest', request, current_user)


@model_routes.route('/knn', methods=['POST'])
@token_required
def k_nearest_neighbors(current_user):
    return _train_model('knn', request, current_user)


@model_routes.route('/k-means', methods=['POST'])
@token_required
def k_means(current_user):
    return _train_model('k_means', request, current_user)


@model_routes.route('/support-vector-machine', methods=['POST'])
@token_required
def support_vector_machine(current_user):
    return _train_model('svm', request, current_user)


@model_routes.route('/naive-bayes', methods=['POST'])
@token_required
def naive_bayes(current_user):
    return _train_model('naive_bayes', request, current_user)


@model_routes.route('/dbscan', methods=['POST'])
@token_required
def db_scan(current_user):
    return _train_model('dbscan', request, current_user)


@model_routes.route('/gradient-boosting', methods=['POST'])
@token_required
def gradient_boosting(current_user):
    return _train_model('gradient_boosting', request, current_user)


@model_routes.route('/sentiment-analysis', methods=['POST'])
@token_required
def sentiment_analysis(current_user):
    return _train_model('sentiment_analysis', request, current_user)


@model_routes.route('/text-classification', methods=['POST'])
@token_required
def text_classification(current_user):
    return _train_model('text_classification', request, current_user)


@model_routes.route('/cnn', methods=['POST'])
@token_required
def cnn(current_user):
    """CNN training — lazy-loads TensorFlow to avoid startup protobuf conflicts."""
    try:
        from models.cnn.cnn import train_cnn as _train_cnn
    except ImportError as e:
        return jsonify({"error": f"CNN requires TensorFlow: {e}"}), 500

    return run_sse_training(
        'cnn', current_user, request,
        lambda params, uid, v: _train_cnn(
            request, validated_params=params, user_id=uid, session_version=v),
    )


@model_routes.route('/ann', methods=['POST'])
@token_required
def ann(current_user):
    """ANN training — lazy-loads TensorFlow to avoid startup protobuf conflicts."""
    try:
        from models.ann.ann import train_ann as _train_ann
    except ImportError as e:
        return jsonify({"error": f"ANN requires TensorFlow: {e}"}), 500

    return run_sse_training(
        'ann', current_user, request,
        lambda params, uid, v: _train_ann(
            request, validated_params=params, user_id=uid, session_version=v),
    )


@model_routes.route('/xgboost', methods=['POST'])
@token_required
def xgboost(current_user):
    """XGBoost training — lazy-imports xgboost."""
    try:
        from models.xgboost.xgboost_model import train_xgboost as _train_xgboost
    except ImportError as e:
        return jsonify({"error": f"xgboost not installed: {e}"}), 500
    data = request.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    try:
        validated_params = validate_hyperparams('xgboost', user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    user_id = current_user['_id'] if current_user else None
    session_id = None

    if user_id:
        from services.subscription_service import check_quota, record_usage
        ok, info = check_quota(current_user, 'xgboost')
        if not ok:
            return jsonify(info), 429
        dataset_id = data.get('dataset_id')
        session = create_session(user_id, 'xgboost', validated_params, dataset_id)
        session_id = session['_id']
        record_usage(user_id, 'xgboost')

    try:
        results = _train_xgboost(request, validated_params=validated_params, user_id=user_id, session_version=session.get('version') if user_id else None)
        if isinstance(results, dict) and results.get('error'):
            if session_id:
                update_session_error(session_id, results['error'])
            return jsonify({"error": results['error']}), 400

        if session_id:
            db_results = update_session_results(
                session_id,
                results.get('evaluation_metrics') or results.get('results') or results,
                results.get('outputImageUrls', []),
                results.get('trained_model_path', ''),
                results.get('predictions_output_file', '')
            )
            results.update(db_results)
            results['session_id'] = session_id

        return jsonify(_sanitize_for_json(results)), 200
    except Exception as e:
        if session_id:
            update_session_error(session_id, str(e))
        return jsonify({"error": str(e)}), 500

@model_routes.route('/resnet', methods=['POST'])
@token_required
def resnet(current_user):
    """ResNet training execution."""
    try:
        from models.resnet.resnet_model import train_resnet as _train_resnet
    except ImportError as e:
        return jsonify({"error": f"ResNet requires TensorFlow: {e}"}), 500

    data = request.get_json() or {}
    hidden_layer_array = data.get('hiddenLayerArray', [])
    class_mode = data.get('classMode', 'categorical')
    is_base_frozen = data.get('isBaseFrozen', True)

    return run_sse_training(
        'resnet', current_user, request,
        lambda params, uid, v: _train_resnet(
            request, validated_params=params,
            hidden_layer_array=hidden_layer_array, class_mode=class_mode,
            is_base_frozen=is_base_frozen,
            user_id=uid, session_version=v),
        finalizing_log='Finalizing session results...',
    )


@model_routes.route('/lstm', methods=['POST'])
@token_required
def lstm(current_user):
    """LSTM execution processing sequence data and dense matrices."""
    try:
        from models.lstm.lstm_model import train_lstm as _train_lstm
    except ImportError as e:
        return jsonify({"error": f"LSTM requires TensorFlow: {e}"}), 500

    data = request.get_json() or {}
    hidden_layer_array = data.get('hiddenLayerArray', [])
    class_mode = data.get('classMode', 'categorical')

    return run_sse_training(
        'lstm', current_user, request,
        lambda params, uid, v: _train_lstm(
            request, validated_params=params,
            hidden_layer_array=hidden_layer_array, class_mode=class_mode,
            user_id=uid, session_version=v),
        finalizing_log='Finalizing LSTM session results...',
    )


@model_routes.route('/yolo', methods=['POST'])
@token_required
def yolo(current_user):
    """YOLOv8 training execution."""
    try:
        from models.yolo.yolo_model import train_yolo as _train_yolo
    except ImportError as e:
        return jsonify({"error": f"YOLO requires Ultralytics: {e}"}), 500

    return run_sse_training(
        'yolo', current_user, request,
        lambda params, uid, v: _train_yolo(
            request, validated_params=params, user_id=uid, session_version=v),
    )


@model_routes.route('/stylegan', methods=['POST'])
@token_required
def stylegan(current_user):
    """StyleGAN generation instance handler."""
    try:
        from models.stylegan.stylegan_model import train_stylegan as _train_stylegan
    except ImportError as e:
        return jsonify({"error": f"StyleGAN requires PyTorch: {e}"}), 500

    # StyleGAN's training function takes the already-extracted JSON dict
    # rather than the Flask request object, unlike the other SSE models.
    data = request.get_json() or {}

    return run_sse_training(
        'stylegan', current_user, request,
        lambda params, uid, v: _train_stylegan(
            data, validated_params=params, user_id=uid, session_version=v),
        finalizing_log='Finalizing StyleGAN session results...',
    )

# --- Session & Schema Endpoints ---

@model_routes.route('/training-sessions', methods=['GET'])
@token_required
def get_sessions(current_user):
    """Get all training sessions for the current user."""
    model_code = request.args.get('model_code')
    sessions = get_user_sessions(current_user['_id'], model_code)
    # Ensure there are no NaN/Infinity values that would break JSON parsing on the frontend
    safe_sessions = _sanitize_for_json(sessions)
    return jsonify({"sessions": safe_sessions}), 200


@model_routes.route('/training-sessions/<session_id>', methods=['GET'])
@token_required
def get_session_detail(current_user, session_id):
    """Get a specific training session."""
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403
        # Sanitize for JSON safety
        safe_session = _sanitize_for_json(session)
        return jsonify({"session": safe_session}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@model_routes.route('/training-sessions/<session_id>/progress', methods=['GET'])
@token_required
def get_session_progress_route(current_user, session_id):
    """Lightweight progress snapshot for replay/reconnect polling.

    Returns { status, logs, results, error, ... } so a model page re-opened
    from the Dashboard can show either the completed results or the live
    training progress accumulated so far.
    """
    progress = get_session_progress(session_id)
    if not progress:
        return jsonify({"error": "Session not found"}), 404
    if progress.get('user_id') != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify(_sanitize_for_json(progress)), 200


@model_routes.route('/training-sessions/<session_id>/result-images', methods=['GET'])
@token_required
def get_session_result_images(current_user, session_id):
    """Return a completed session's output images as base64 data URLs.

    On a fresh run the trainer's local PNGs are base64-encoded into the
    response (`outputImageBase64`) before being deleted — they live only inside
    the results.zip on Google Drive afterwards. On replay the stored
    `output_images` paths no longer exist locally, so this endpoint rebuilds the
    images by streaming the session's results.zip from Drive and extracting the
    PNG/JPG entries. The shape ({ images: [dataUrl, ...] }) lets the replay hook
    reuse the same <ImageCarousel> code path as a fresh run.
    """
    try:
        session = get_session(session_id)
    except Exception:
        return jsonify({"error": "Session not found"}), 404
    if session.get('user_id') != current_user['_id']:
        return jsonify({"error": "Unauthorized"}), 403

    # The zip drive id lives at the top level on newer sessions but only inside
    # `results` on some older ones — check both so replay works either way.
    drive_id = session.get('results_zip_drive_id') or (session.get('results') or {}).get('results_zip_drive_id')
    if not drive_id:
        return jsonify({"images": []}), 200

    import base64
    import io
    import os
    import zipfile

    images = []
    try:
        from services.google_drive_service import stream_file_from_drive
        fh, _ = stream_file_from_drive(drive_id)
        # stream_file_from_drive returns a SpooledTemporaryFile, which on
        # Python <3.11 doesn't implement seekable() — zipfile.ZipFile calls it
        # and raises AttributeError. Copy into a BytesIO (fully seekable) so the
        # zip can be read reliably across Python versions. Results zips are
        # small (a handful of plot images), so the in-memory copy is cheap.
        fh.seek(0)
        buf = io.BytesIO(fh.read())
        with zipfile.ZipFile(buf) as zf:
            # Sort entries so the carousel order is stable across reloads.
            for name in sorted(zf.namelist()):
                ext = os.path.splitext(name)[1].lower()
                if ext not in ('.png', '.jpg', '.jpeg'):
                    continue
                mime_type = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
                b64 = base64.b64encode(zf.read(name)).decode('utf-8')
                images.append(f"data:{mime_type};base64,{b64}")
    except Exception as e:
        return jsonify({"error": f"Failed to load result images: {e}"}), 502

    return jsonify({"images": images}), 200


@model_routes.route('/training-sessions/<session_id>', methods=['DELETE'])
@token_required
def delete_session_route(current_user, session_id):
    """Delete a training session and its associated files."""
    try:
        delete_session(session_id, current_user['_id'])
        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        error_msg = str(e)
        if error_msg == 'unauthorized':
            return jsonify({"error": "Unauthorized"}), 403
        if error_msg == 'session_not_found':
            return jsonify({"error": "Session not found"}), 404
        return jsonify({"error": error_msg}), 500


@model_routes.route('/training-sessions/<session_id>/cancel', methods=['POST'])
@token_required
def cancel_session_route(current_user, session_id):
    """Request cancellation of a running streaming-training session.

    Sets a flag the SSE loop checks between chunks; the run stops at the next
    boundary and is recorded as 'cancelled'. Owner-scoped.
    """
    from services.training_session_service import request_session_cancel
    try:
        request_session_cancel(session_id, current_user['_id'])
        return jsonify({"message": "Cancellation requested."}), 200
    except Exception as e:
        msg = str(e)
        if msg == 'unauthorized':
            return jsonify({"error": "Unauthorized"}), 403
        if msg == 'session_not_found':
            return jsonify({"error": "Session not found"}), 404
        return jsonify({"error": msg}), 500


@model_routes.route('/predict/<session_id>', methods=['POST'])
@token_required
def predict_on_new_data(current_user, session_id):
    """Run batch prediction on an uploaded CSV using a session's trained model.

    Classical scikit-learn models only (see services/prediction_service.py).
    Expects a multipart upload with a `file` field (CSV). Returns predictions
    (and class probabilities when available). Owner-scoped via the session.
    """
    from services.prediction_service import predict_with_session, read_uploaded_csv

    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No CSV file uploaded (expected form field 'file')."}), 400

    try:
        df = read_uploaded_csv(file)
        result = predict_with_session(session_id, current_user['_id'], df)
        return jsonify(_sanitize_for_json(result)), 200
    except PermissionError:
        return jsonify({"error": "Unauthorized"}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500


@model_routes.route('/model-schema/<model_code>', methods=['GET'])
def get_schema(model_code):
    """Get the hyperparameter schema for a model (for frontend UI generation)."""
    schema = get_model_schema(model_code)
    if not schema:
        return jsonify({"error": f"Unknown model: {model_code}"}), 404
    return jsonify({"schema": schema}), 200


@model_routes.route('/user-datasets', methods=['GET'])
@token_required
def list_user_datasets(current_user):
    """List all datasets uploaded by the current user."""
    datasets = get_user_datasets(current_user['_id'])
    return jsonify({"datasets": datasets}), 200
