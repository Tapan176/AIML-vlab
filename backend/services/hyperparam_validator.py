"""
Hyperparameter validation schemas for all ML models.
Validates user-provided hyperparams against allowed types, ranges, and enums.
"""
from config import DEFAULT_HYPERPARAMS


# Validation schema: {param_name: {type, min, max, options, nullable}}
VALIDATION_SCHEMAS = {
    'simple_linear_regression': {
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'multivariable_linear_regression': {
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'logistic_regression': {
        'C': {'type': float, 'min': 0.01, 'max': 1000.0},
        'solver': {'type': str, 'options': ['lbfgs', 'liblinear', 'newton-cg', 'sag', 'saga']},
        'max_iter': {'type': int, 'min': 50, 'max': 10000},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'knn': {
        'n_neighbors': {'type': int, 'min': 1, 'max': 50},
        'metric': {'type': str, 'options': ['euclidean', 'manhattan', 'minkowski', 'chebyshev']},
        'p': {'type': int, 'min': 1, 'max': 5},
        'weights': {'type': str, 'options': ['uniform', 'distance']},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'decision_tree': {
        'criterion': {'type': str, 'options': ['gini', 'entropy', 'log_loss']},
        'max_depth': {'type': int, 'min': 1, 'max': 100, 'nullable': True},
        'min_samples_split': {'type': int, 'min': 2, 'max': 50},
        'min_samples_leaf': {'type': int, 'min': 1, 'max': 50},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'random_forest': {
        'n_estimators': {'type': int, 'min': 1, 'max': 500},
        'criterion': {'type': str, 'options': ['gini', 'entropy', 'log_loss']},
        'max_depth': {'type': int, 'min': 1, 'max': 100, 'nullable': True},
        'min_samples_split': {'type': int, 'min': 2, 'max': 50},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'svm': {
        'kernel': {'type': str, 'options': ['linear', 'rbf', 'poly', 'sigmoid']},
        'C': {'type': float, 'min': 0.01, 'max': 1000.0},
        'gamma': {'type': str, 'options': ['scale', 'auto']},
        'degree': {'type': int, 'min': 1, 'max': 10},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'naive_bayes': {
        'var_smoothing': {'type': float, 'min': 1e-12, 'max': 1.0},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'k_means': {
        'n_clusters': {'type': int, 'min': 2, 'max': 20},
        'init': {'type': str, 'options': ['k-means++', 'random']},
        'max_iter': {'type': int, 'min': 100, 'max': 1000},
        'n_init': {'type': int, 'min': 1, 'max': 50},
        'random_state': {'type': int, 'min': 0, 'max': 9999, 'nullable': True},
    },
    'dbscan': {
        'eps': {'type': float, 'min': 0.01, 'max': 10.0},
        'min_samples': {'type': int, 'min': 1, 'max': 50},
        'metric': {'type': str, 'options': ['euclidean', 'manhattan', 'cosine']},
    },
    'ann': {
        'epochs': {'type': int, 'min': 1, 'max': 500},
        'batch_size': {'type': int, 'min': 1, 'max': 512},
        'optimizer': {'type': str, 'options': ['adam', 'sgd', 'rmsprop', 'adagrad']},
        'loss': {'type': str, 'options': ['binary_crossentropy', 'categorical_crossentropy', 'sparse_categorical_crossentropy', 'mse']},
        'validation_split': {'type': float, 'min': 0.05, 'max': 0.5},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
    },
    'gradient_boosting': {
        'n_estimators': {'type': int, 'min': 10, 'max': 1000},
        'learning_rate': {'type': float, 'min': 0.001, 'max': 1.0},
        'max_depth': {'type': int, 'min': 1, 'max': 20},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
    },
    'xgboost': {
        'n_estimators': {'type': int, 'min': 10, 'max': 1000},
        'learning_rate': {'type': float, 'min': 0.001, 'max': 1.0},
        'max_depth': {'type': int, 'min': 1, 'max': 20},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
    },
    'sentiment_analysis': {
        'max_features': {'type': int, 'min': 100, 'max': 50000},
        'max_iter': {'type': int, 'min': 100, 'max': 5000},
        'C': {'type': float, 'min': 0.01, 'max': 100.0},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
    },
    'text_classification': {
        'max_features': {'type': int, 'min': 100, 'max': 50000},
        'alpha': {'type': float, 'min': 0.001, 'max': 10.0},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
    },
    'cnn': {
        'epochs': {'type': int, 'min': 1, 'max': 500},
        'batch_size': {'type': int, 'min': 1, 'max': 512},
        'optimizer': {'type': str, 'options': ['adam', 'sgd', 'rmsprop', 'adagrad', 'adadelta']},
        'loss': {'type': str, 'options': ['binary_crossentropy', 'categorical_crossentropy', 'sparse_categorical_crossentropy', 'mse']},
        'validation_split': {'type': float, 'min': 0.05, 'max': 0.5},
        'test_size': {'type': float, 'min': 0.05, 'max': 0.5},
    },
}


def validate_hyperparams(model_code, user_params):
    """
    Validate user-provided hyperparameters against the schema.
    Returns merged dict with defaults + validated user params.
    Raises Exception with friendly error message if validation fails.
    """
    if model_code not in VALIDATION_SCHEMAS:
        raise Exception(f"Unknown model code: {model_code}")

    schema = VALIDATION_SCHEMAS[model_code]
    defaults = DEFAULT_HYPERPARAMS.get(model_code, {})

    # Start with defaults
    validated = dict(defaults)

    if not user_params:
        return validated

    errors = []

    for param_name, value in user_params.items():
        if param_name not in schema:
            continue  # Ignore unknown params silently

        rules = schema[param_name]
        is_nullable = rules.get('nullable', False)

        # Handle None/null values
        if value is None:
            if is_nullable:
                validated[param_name] = None
                continue
            else:
                errors.append(f"'{param_name}' cannot be null")
                continue

        # Type validation
        expected_type = rules['type']
        try:
            if expected_type == float:
                value = float(value)
            elif expected_type == int:
                value = int(value)
            elif expected_type == str:
                value = str(value)
        except (ValueError, TypeError):
            errors.append(f"'{param_name}' must be {expected_type.__name__}, got '{value}'")
            continue

        # Enum validation
        if 'options' in rules and value not in rules['options']:
            errors.append(f"'{param_name}' must be one of {rules['options']}, got '{value}'")
            continue

        # Range validation
        if 'min' in rules and value < rules['min']:
            errors.append(f"'{param_name}' must be >= {rules['min']}, got {value}")
            continue
        if 'max' in rules and value > rules['max']:
            errors.append(f"'{param_name}' must be <= {rules['max']}, got {value}")
            continue

        validated[param_name] = value

    if errors:
        raise Exception("Hyperparameter validation failed: " + "; ".join(errors))

    return validated


def get_model_schema(model_code):
    """Get the validation schema for a model (used by frontend for UI generation)."""
    if model_code not in VALIDATION_SCHEMAS:
        return None

    schema = VALIDATION_SCHEMAS[model_code]
    defaults = DEFAULT_HYPERPARAMS.get(model_code, {})

    result = {}
    for param_name, rules in schema.items():
        result[param_name] = {
            'type': rules['type'].__name__,
            'default': defaults.get(param_name),
            **{k: v for k, v in rules.items() if k != 'type'}
        }

    return result
