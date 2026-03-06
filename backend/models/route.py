"""
Model routes — endpoints for training all 11 ML models.
Supports hyperparameter tuning, user-scoped storage, and training sessions.
"""
from flask import Blueprint, request, jsonify
import math
from auth.auth_middleware import token_required
from services.hyperparam_validator import validate_hyperparams, get_model_schema
from services.training_session_service import create_session, update_session_results, update_session_error, get_user_sessions, get_session, delete_session
from services.dataset_service import get_user_datasets

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

# Map model codes to route paths
MODEL_ROUTES = {
    'simple_linear_regression': '/linear-regression',
    'multivariable_linear_regression': '/multivariable-linear-regression',
    'logistic_regression': '/logistic-regression',
    'decision_tree': '/decision-tree',
    'random_forest': '/random-forest',
    'knn': '/knn',
    'svm': '/support-vector-machine',
    'naive_bayes': '/naive-bayes',
    'k_means': '/k-means',
    'dbscan': '/dbscan',
    'cnn': '/cnn',
    'ann': '/ann',
    'gradient_boosting': '/gradient-boosting',
    'xgboost': '/xgboost',
    'sentiment_analysis': '/sentiment-analysis',
    'text_classification': '/text-classification',
    'resnet': '/resnet',
    'lstm': '/lstm',
    'yolo': '/yolo',
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
        dataset_id = data.get('dataset_id')
        session = create_session(user_id, model_code, validated_params, dataset_id)
        session_id = session['_id']
        data['user_id'] = user_id
        data['session_id'] = session_id
        data['session_version'] = session['version']

    try:
        # Call the model's training function
        train_fn = MODEL_FUNCTIONS[model_code]
        results = train_fn(request_obj, validated_params=validated_params, user_id=user_id, session_version=session.get('version') if user_id else None)

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

        return jsonify(results), 200

    except Exception as e:
        if session_id:
            update_session_error(session_id, str(e))
        return jsonify({"error": str(e)}), 500


# --- Model Training Endpoints ---

@model_routes.route('/linear-regression', methods=['POST'])
@token_required(optional=True)
def linear_regression(current_user):
    return _train_model('simple_linear_regression', request, current_user)


@model_routes.route('/multivariable-linear-regression', methods=['POST'])
@token_required(optional=True)
def multivariate_linear_regression(current_user):
    return _train_model('multivariable_linear_regression', request, current_user)


@model_routes.route('/logistic-regression', methods=['POST'])
@token_required(optional=True)
def logistic_regression_route(current_user):
    return _train_model('logistic_regression', request, current_user)


@model_routes.route('/decision-tree', methods=['POST'])
@token_required(optional=True)
def decision_tree(current_user):
    return _train_model('decision_tree', request, current_user)


@model_routes.route('/random-forest', methods=['POST'])
@token_required(optional=True)
def random_forest(current_user):
    return _train_model('random_forest', request, current_user)


@model_routes.route('/knn', methods=['POST'])
@token_required(optional=True)
def k_nearest_neighbors(current_user):
    return _train_model('knn', request, current_user)


@model_routes.route('/k-means', methods=['POST'])
@token_required(optional=True)
def k_means(current_user):
    return _train_model('k_means', request, current_user)


@model_routes.route('/support-vector-machine', methods=['POST'])
@token_required(optional=True)
def support_vector_machine(current_user):
    return _train_model('svm', request, current_user)


@model_routes.route('/naive-bayes', methods=['POST'])
@token_required(optional=True)
def naive_bayes(current_user):
    return _train_model('naive_bayes', request, current_user)


@model_routes.route('/dbscan', methods=['POST'])
@token_required(optional=True)
def db_scan(current_user):
    return _train_model('dbscan', request, current_user)


@model_routes.route('/cnn', methods=['POST'])
@token_required
def cnn(current_user):
    """CNN training — lazy-loads TensorFlow to avoid startup protobuf conflicts."""
    try:
        from models.cnn.cnn import train_cnn as _train_cnn
    except ImportError as e:
        return jsonify({"error": f"CNN requires TensorFlow: {e}"}), 500
        
    data = request.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    try:
        validated_params = validate_hyperparams('cnn', user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
    user_id = current_user['_id']
    dataset_id = data.get('dataset_id')
    
    session = create_session(user_id, 'cnn', validated_params, dataset_id)
    session_id = session['_id']
    
    def generate():
        import json
        try:
            results_data = {}
            for chunk in _train_cnn(request, validated_params=validated_params, user_id=user_id, session_version=session['version']):
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
                    except: pass
                yield chunk
            
            # Final update with all metadata captured from the inner function
            db_results = update_session_results(
                session_id, 
                results_data, 
                [], 
                results_data.get('trained_model_path', ''), 
                ''
            )
            db_results['status'] = 'completed'
            db_results['session_id'] = session_id
            yield f"data: {json.dumps(db_results)}\n\n"
        except Exception as e:
            update_session_error(session_id, str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response, stream_with_context
    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


@model_routes.route('/ann', methods=['POST'])
@token_required
def ann(current_user):
    """ANN training — lazy-loads TensorFlow to avoid startup protobuf conflicts."""
    try:
        from models.ann.ann import train_ann as _train_ann
    except ImportError as e:
        return jsonify({"error": f"ANN requires TensorFlow: {e}"}), 500
    data = request.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    try:
        validated_params = validate_hyperparams('ann', user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    user_id = current_user['_id']
    dataset_id = data.get('dataset_id')
    session = create_session(user_id, 'ann', validated_params, dataset_id)
    session_id = session['_id']
    
    def generate():
        import json
        try:
            results_data = {}
            for chunk in _train_ann(request, validated_params=validated_params, user_id=user_id, session_version=session['version']):
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
                    except: pass
                yield chunk
            
            # Update session with results
            db_results = update_session_results(
                session_id, 
                results_data, 
                [], 
                results_data.get('trained_model_path', ''), 
                ''
            )
            db_results['status'] = 'completed'
            db_results['session_id'] = session_id
            yield f"data: {json.dumps(db_results)}\n\n"
        except Exception as e:
            update_session_error(session_id, str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response, stream_with_context
    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


@model_routes.route('/xgboost', methods=['POST'])
@token_required(optional=True)
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
    return jsonify(_train_xgboost(request, validated_params=validated_params, user_id=user_id)), 200

@model_routes.route('/resnet', methods=['POST'])
@token_required
def resnet(current_user):
    """ResNet training execution."""
    try:
        from models.resnet.resnet_model import train_resnet as _train_resnet
    except ImportError as e:
        return jsonify({"error": f"ResNet requires TensorFlow: {e}"}), 500
    
    data = request.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    hidden_layer_array = data.get('hiddenLayerArray', [])
    class_mode = data.get('classMode', 'categorical')
    is_base_frozen = data.get('isBaseFrozen', True)
    
    try:
        validated_params = validate_hyperparams('resnet', user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
    user_id = current_user['_id']
    dataset_id = data.get('dataset_id')
    
    session = create_session(user_id, 'resnet', validated_params, dataset_id)
    session_id = session['_id']
    
    def generate():
        import json
        try:
            results_data = {}
            for chunk in _train_resnet(request, validated_params=validated_params, hidden_layer_array=hidden_layer_array, class_mode=class_mode, is_base_frozen=is_base_frozen, user_id=user_id, session_version=session['version']):
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
                    except: pass
                yield chunk
            
            yield f"data: {json.dumps({'log': 'Finalizing session results...'})}\n\n"
            
            # Final update with captures from inner function
            db_results = update_session_results(
                session_id, 
                results_data or {"message": "Training complete."}, 
                [], 
                results_data.get('trained_model_path', ''), 
                ''
            )
            db_results['status'] = 'completed'
            db_results['session_id'] = session_id
            yield f"data: {json.dumps(db_results)}\n\n"
        except Exception as e:
            update_session_error(session_id, str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response, stream_with_context
    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

@model_routes.route('/lstm', methods=['POST'])
@token_required
def lstm(current_user):
    """LSTM execution processing sequence data and dense matrices."""
    try:
        from models.lstm.lstm_model import train_lstm as _train_lstm
    except ImportError as e:
        return jsonify({"error": f"LSTM requires TensorFlow: {e}"}), 500
        
    data = request.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    hidden_layer_array = data.get('hiddenLayerArray', [])
    class_mode = data.get('classMode', 'categorical')
    
    try:
        validated_params = validate_hyperparams('lstm', user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
    user_id = current_user['_id']
    dataset_id = data.get('dataset_id')
    
    session = create_session(user_id, 'lstm', validated_params, dataset_id)
    session_id = session['_id']
    
    def generate():
        import json
        try:
            results_data = {}
            for chunk in _train_lstm(request, validated_params=validated_params, hidden_layer_array=hidden_layer_array, class_mode=class_mode, user_id=user_id, session_version=session['version']):
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
                    except: pass
                yield chunk
            
            yield f"data: {json.dumps({'log': 'Finalizing LSTM session results...'})}\n\n"
            
            # Final update with captures from inner function
            db_results = update_session_results(
                session_id, 
                results_data or {"message": "Training complete."}, 
                [], 
                results_data.get('trained_model_path', ''), 
                ''
            )
            db_results['status'] = 'completed'
            db_results['session_id'] = session_id
            yield f"data: {json.dumps(db_results)}\n\n"
        except Exception as e:
            update_session_error(session_id, str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response, stream_with_context
    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

@model_routes.route('/yolo', methods=['POST'])
@token_required
def yolo(current_user):
    """YOLOv8 training execution."""
    try:
        from models.yolo.yolo_model import train_yolo as _train_yolo
    except ImportError as e:
        return jsonify({"error": f"YOLO requires Ultralytics: {e}"}), 500
        
    data = request.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    
    try:
        validated_params = validate_hyperparams('yolo', user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
    user_id = current_user['_id']
    dataset_id = data.get('dataset_id')
    
    session = create_session(user_id, 'yolo', validated_params, dataset_id)
    session_id = session['_id']
    
    def generate():
        import json
        try:
            results_data = {}
            for chunk in _train_yolo(request, validated_params=validated_params, user_id=user_id, session_version=session['version']):
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
                    except: pass
                yield chunk
            
            # Final update with captures from inner function
            db_results = update_session_results(
                session_id, 
                results_data or {"message": "Training complete."}, 
                [], 
                results_data.get('trained_model_path', ''), 
                ''
            )
            db_results['status'] = 'completed'
            db_results['session_id'] = session_id
            yield f"data: {json.dumps(db_results)}\n\n"
        except Exception as e:
            update_session_error(session_id, str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response, stream_with_context
    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

@model_routes.route('/stylegan', methods=['POST'])
@token_required
def stylegan(current_user):
    """StyleGAN generation instance handler."""
    try:
        from models.stylegan.stylegan_model import train_stylegan as _train_stylegan
    except ImportError as e:
        return jsonify({"error": f"StyleGAN requires PyTorch: {e}"}), 500
        
    data = request.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    
    try:
        validated_params = validate_hyperparams('stylegan', user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
    user_id = current_user['_id']
    dataset_id = data.get('dataset_id')
    
    session = create_session(user_id, 'stylegan', validated_params, dataset_id)
    session_id = session['_id']
    
    def generate():
        import json
        try:
            results_data = {}
            for chunk in _train_stylegan(data, validated_params=validated_params, user_id=user_id, session_version=session['version']):
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
                    except: pass
                yield chunk
            
            yield f"data: {json.dumps({'log': 'Finalizing StyleGAN session results...'})}\n\n"
            
            # Final update with captures from inner function
            db_results = update_session_results(
                session_id, 
                results_data or {"message": "Training complete."}, 
                [], 
                results_data.get('trained_model_path', ''), 
                ''
            )
            db_results['status'] = 'completed'
            db_results['session_id'] = session_id
            yield f"data: {json.dumps(db_results)}\n\n"
        except Exception as e:
            update_session_error(session_id, str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    from flask import Response, stream_with_context
    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

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
