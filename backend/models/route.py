"""
Model routes — endpoints for training all 11 ML models.
Supports hyperparameter tuning, user-scoped storage, and training sessions.
"""
from flask import Blueprint, request, jsonify
from auth.auth_middleware import token_required
from services.hyperparam_validator import validate_hyperparams, get_model_schema
from services.training_session_service import create_session, update_session_results, update_session_error, get_user_sessions, get_session
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

        # Update session with results
        if session_id:
            update_session_results(
                session_id,
                results.get('evaluation_metrics') or results.get('results') or results,
                results.get('outputImageUrls', []),
                results.get('trained_model_path', ''),
                results.get('predictions_output_file', '')
            )
            results['session_id'] = session_id

        return jsonify(results), 200

    except Exception as e:
        if session_id:
            update_session_error(session_id, str(e))
        return jsonify({"error": str(e)}), 500


# --- Model Training Endpoints ---

@model_routes.route('/linear-regression', methods=['POST'])
def linear_regression():
    return _train_model('simple_linear_regression', request)


@model_routes.route('/multivariable-linear-regression', methods=['POST'])
def multivariate_linear_regression():
    return _train_model('multivariable_linear_regression', request)


@model_routes.route('/logistic-regression', methods=['POST'])
def logistic_regression_route():
    return _train_model('logistic_regression', request)


@model_routes.route('/decision-tree', methods=['POST'])
def decision_tree():
    return _train_model('decision_tree', request)


@model_routes.route('/random-forest', methods=['POST'])
def random_forest():
    return _train_model('random_forest', request)


@model_routes.route('/knn', methods=['POST'])
def k_nearest_neighbors():
    return _train_model('knn', request)


@model_routes.route('/k-means', methods=['POST'])
def k_means():
    return _train_model('k_means', request)


@model_routes.route('/support-vector-machine', methods=['POST'])
def support_vector_machine():
    return _train_model('svm', request)


@model_routes.route('/naive-bayes', methods=['POST'])
def naive_bayes():
    return _train_model('naive_bayes', request)


@model_routes.route('/dbscan', methods=['POST'])
def db_scan():
    return _train_model('dbscan', request)


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
    
    try:
        results = _train_cnn(request, validated_params=validated_params, user_id=user_id, session_version=session['version'])
        update_session_results(
            session_id,
            results.get('evaluation_metrics') or results.get('results') or results,
            results.get('outputImageUrls', []),
            results.get('trained_model_path', ''),
            results.get('predictions_output_file', '')
        )
        results['session_id'] = str(session_id)
        return jsonify(results), 200
    except Exception as e:
        update_session_error(session_id, str(e))
        return jsonify({"error": str(e)}), 500


@model_routes.route('/ann', methods=['POST'])
def ann():
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
    user_id = None
    return jsonify(_train_ann(request, validated_params=validated_params, user_id=user_id)), 200


@model_routes.route('/xgboost', methods=['POST'])
def xgboost():
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
    user_id = None
    return jsonify(_train_xgboost(request, validated_params=validated_params, user_id=user_id)), 200


# --- Session & Schema Endpoints ---

@model_routes.route('/training-sessions', methods=['GET'])
@token_required
def get_sessions(current_user):
    """Get all training sessions for the current user."""
    model_code = request.args.get('model_code')
    sessions = get_user_sessions(current_user['_id'], model_code)
    return jsonify({"sessions": sessions}), 200


@model_routes.route('/training-sessions/<session_id>', methods=['GET'])
@token_required
def get_session_detail(current_user, session_id):
    """Get a specific training session."""
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403
        return jsonify({"session": session}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


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
