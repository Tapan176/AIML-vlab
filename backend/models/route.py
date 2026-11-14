"""
Model routes — training endpoints for every model, plus training-session
management (list / detail / progress / images / cancel / delete / predict).
"""
import logging
import math

from flask import Blueprint, request, jsonify
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
log = logging.getLogger(__name__)


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

# Map model codes to training functions. Heavy/optional dependencies are
# referenced as "module:function" strings and imported on first use (keeps
# startup fast and lets the app boot without e.g. xgboost installed).
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
    'xgboost': 'models.xgboost.xgboost_model:train_xgboost',
}


# matplotlib's pyplot keeps a process-global "current figure", so two
# classical runs plotting at the same time in one process (threaded dev
# server, or gunicorn --threads > 1) draw into each other's charts. Classical
# fits are short, so we serialise them per process; with the default of one
# thread per gunicorn worker this lock is never contended.
import threading
_PLOT_LOCK = threading.Lock()


def _resolve_train_fn(model_code):
    fn = MODEL_FUNCTIONS[model_code]
    if isinstance(fn, str):
        import importlib
        module_name, attr = fn.split(':')
        fn = getattr(importlib.import_module(module_name), attr)
        MODEL_FUNCTIONS[model_code] = fn
    return fn


def _images_to_base64(paths):
    """Inline the run's plot files as data URLs (the files are deleted after
    being zipped to Drive, so the client can't fetch them later)."""
    import base64
    import os
    out = []
    for img_path in paths or []:
        if img_path and os.path.isfile(img_path):
            ext = os.path.splitext(img_path)[1].lower()
            mime = "image/jpeg" if ext in ('.jpg', '.jpeg') else "image/png"
            with open(img_path, "rb") as fh:
                out.append(f"data:{mime};base64,{base64.b64encode(fh.read()).decode('ascii')}")
    return out


def _extract_metrics(results):
    """Metrics to persist on the session. Prefers `evaluation_metrics`, then a
    nested `results` dict; otherwise keeps top-level scalar numbers only (so
    big arrays like `predictions` never get written into the session doc)."""
    for key in ('evaluation_metrics', 'results'):
        if isinstance(results.get(key), dict) and results[key]:
            return dict(results[key])
    return {
        k: v for k, v in results.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }


def _cleanup_run_dirs(paths):
    """Remove the per-run image directories once their files are uploaded."""
    import os
    import shutil
    for d in {os.path.dirname(p) for p in paths or [] if p}:
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)


def _train_model(model_code, request_obj, current_user):
    """Generic synchronous training handler: validate → quota → session →
    train → upload artifacts → respond."""
    data = request_obj.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    try:
        validated_params = validate_hyperparams(model_code, data.get('hyperparams') or {})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    try:
        train_fn = _resolve_train_fn(model_code)
    except ImportError as e:
        return jsonify({"error": f"{model_code} is not available on this server: {e}"}), 501

    user_id = current_user['_id']

    # Enforce subscription quota (no-op unless SUBSCRIPTION_ENABLED).
    from services.subscription_service import check_quota, record_usage
    ok, info = check_quota(current_user, model_code)
    if not ok:
        return jsonify(info), 429

    session = create_session(user_id, model_code, validated_params, data.get('dataset_id'))
    session_id = session['_id']
    record_usage(user_id, model_code)

    output_image_urls = []
    try:
        with _PLOT_LOCK:
            results = train_fn(request_obj, validated_params=validated_params,
                               user_id=user_id, session_version=session['version'])

        if isinstance(results, dict) and results.get('error'):
            update_session_error(session_id, results['error'])
            return jsonify({"error": results['error'], "session_id": session_id}), 400

        output_image_urls = results.get('outputImageUrls', []) or []
        results['outputImageBase64'] = _images_to_base64(output_image_urls)

        db_results = update_session_results(
            session_id,
            _extract_metrics(results),
            output_image_urls,
            results.get('trained_model_path', ''),
            results.get('predictions_output_file', ''),
        )
        results.update(db_results)
        results['session_id'] = session_id
        # Local filesystem paths mean nothing to the client.
        results.pop('trained_model_path', None)
        results.pop('predictions_output_file', None)
        return jsonify(_sanitize_for_json(results)), 200

    except (ValueError, FileNotFoundError, KeyError) as e:
        # Data problems (bad columns, missing dataset, wrong target type…) are
        # the user's to fix — surface the message.
        update_session_error(session_id, str(e))
        return jsonify({"error": str(e), "session_id": session_id}), 400
    except Exception as e:
        log.exception("Training failed for %s (session %s)", model_code, session_id)
        update_session_error(session_id, str(e))
        return jsonify({"error": "Training failed due to a server error.", "session_id": session_id}), 500
    finally:
        _cleanup_run_dirs(output_image_urls)


# --- Synchronous model endpoints (path -> model code) ---

_SYNC_ROUTES = {
    '/linear-regression': 'simple_linear_regression',
    '/multivariable-linear-regression': 'multivariable_linear_regression',
    '/logistic-regression': 'logistic_regression',
    '/decision-tree': 'decision_tree',
    '/random-forest': 'random_forest',
    '/knn': 'knn',
    '/k-means': 'k_means',
    '/support-vector-machine': 'svm',
    '/naive-bayes': 'naive_bayes',
    '/dbscan': 'dbscan',
    '/gradient-boosting': 'gradient_boosting',
    '/sentiment-analysis': 'sentiment_analysis',
    '/text-classification': 'text_classification',
    '/xgboost': 'xgboost',
}


def _make_sync_view(model_code):
    @token_required
    def view(current_user):
        return _train_model(model_code, request, current_user)
    view.__name__ = f"train_{model_code}"
    return view


for _path, _code in _SYNC_ROUTES.items():
    model_routes.add_url_rule(_path, endpoint=f"train_{_code}",
                              view_func=_make_sync_view(_code), methods=['POST'])


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
    """Training sessions for the current user, newest first.

    Optional filters: ?model_code=&status=. Optional pagination: ?limit=&page=
    (when `limit` is given the response also carries `total`, `page`, `limit`).
    Without `limit` every session is returned, as before.
    """
    from services.training_session_service import count_user_sessions
    model_code = request.args.get('model_code')
    status = request.args.get('status')
    limit = request.args.get('limit', type=int)
    if limit:
        limit = max(1, min(limit, 200))
        page = max(1, request.args.get('page', 1, type=int) or 1)
        sessions = get_user_sessions(current_user['_id'], model_code, status, limit=limit, skip=(page - 1) * limit)
        total = count_user_sessions(current_user['_id'], model_code, status)
        return jsonify({"sessions": _sanitize_for_json(sessions), "total": total,
                        "page": page, "limit": limit}), 200
    sessions = get_user_sessions(current_user['_id'], model_code, status)
    return jsonify({"sessions": _sanitize_for_json(sessions)}), 200


@model_routes.route('/training-sessions/<session_id>', methods=['GET'])
@token_required
def get_session_detail(current_user, session_id):
    """Get a specific training session (owner only)."""
    try:
        session = get_session(session_id)
    except Exception:
        return jsonify({"error": "Session not found"}), 404
    if session['user_id'] != current_user['_id']:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"session": _sanitize_for_json(session)}), 200


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
        return jsonify({"error": "Unknown model"}), 404
    resp = jsonify({"schema": schema})
    resp.headers['Cache-Control'] = 'public, max-age=600'
    return resp, 200


@model_routes.route('/user-datasets', methods=['GET'])
@token_required
def list_user_datasets(current_user):
    """List all datasets uploaded by the current user."""
    datasets = get_user_datasets(current_user['_id'])
    return jsonify({"datasets": datasets}), 200
