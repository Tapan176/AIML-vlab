"""
Centralized configuration loader for ML-vlab backend.
All constants and settings are loaded from .env — no hardcoded values.
"""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))


# --- MongoDB ---
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'aiml-lab')

# --- JWT ---
JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-in-production')
JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
JWT_ALGORITHM = 'HS256'

# --- File Storage ---
UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'static/uploads')
TRAINED_MODELS_DIR = os.getenv('TRAINED_MODELS_DIR', 'trainedModels')
IMAGES_DIR = os.getenv('IMAGES_DIR', 'static/images')
PREDICTIONS_DIR = os.getenv('PREDICTIONS_DIR', 'predictions')

# --- Google Drive ---
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
GOOGLE_TOKEN_JSON = os.getenv('GOOGLE_TOKEN_JSON')

# --- Server ---
FLASK_PORT = int(os.getenv('FLASK_PORT', '5050'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5050,http://127.0.0.1:5050').split(',')

# --- Upload Limits ---
ALLOWED_CSV_EXTENSIONS = set(os.getenv('ALLOWED_CSV_EXTENSIONS', 'csv').split(','))
ALLOWED_IMAGE_EXTENSIONS = set(os.getenv('ALLOWED_IMAGE_EXTENSIONS', 'jpg,jpeg,png').split(','))
ALLOWED_ARCHIVE_EXTENSIONS = set(os.getenv('ALLOWED_ARCHIVE_EXTENSIONS', 'zip').split(','))
MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', '1024'))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# --- Model Constants ---
MODEL_CODES = [
    'simple_linear_regression',
    'multivariable_linear_regression',
    'logistic_regression',
    'knn',
    'k_means',
    'decision_tree',
    'random_forest',
    'svm',
    'naive_bayes',
    'dbscan',
    'ann',
    'cnn',
    'resnet',
    'lstm',
    'yolo',
    'stylegan',
]

# Default hyperparameter values per model  (optimised for best out-of-the-box accuracy)
DEFAULT_HYPERPARAMS = {
    'simple_linear_regression': {
        'test_size': 0.2,
        'random_state': 42,
    },
    'multivariable_linear_regression': {
        'test_size': 0.2,
        'random_state': 42,
    },
    'logistic_regression': {
        'C': 10.0,
        'solver': 'lbfgs',
        'max_iter': 1000,
        'test_size': 0.2,
        'random_state': 42,
    },
    'knn': {
        'n_neighbors': 5,
        'metric': 'minkowski',
        'p': 2,
        'weights': 'distance',
        'test_size': 0.2,
        'random_state': 42,
    },
    'decision_tree': {
        'criterion': 'gini',
        'max_depth': 10,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'test_size': 0.2,
        'random_state': 42,
    },
    'random_forest': {
        'n_estimators': 100,
        'criterion': 'gini',
        'max_depth': 15,
        'min_samples_split': 3,
        'test_size': 0.2,
        'random_state': 42,
    },
    'svm': {
        'kernel': 'rbf',
        'C': 10.0,
        'gamma': 'scale',
        'degree': 3,
        'test_size': 0.2,
        'random_state': 42,
    },
    'naive_bayes': {
        'var_smoothing': 1e-9,
        'test_size': 0.2,
        'random_state': 42,
    },
    'k_means': {
        'n_clusters': 3,
        'init': 'k-means++',
        'max_iter': 300,
        'n_init': 10,
        'random_state': 42,
    },
    'dbscan': {
        'eps': 0.5,
        'min_samples': 5,
        'metric': 'euclidean',
    },
    'ann': {
        'epochs': 100,
        'batch_size': 32,
        'optimizer': 'adam',
        'loss': 'binary_crossentropy',
        'validation_split': 0.15,
        'test_size': 0.2,
    },
    'gradient_boosting': {
        'n_estimators': 200,
        'learning_rate': 0.05,
        'max_depth': 5,
        'test_size': 0.2,
    },
    'xgboost': {
        'n_estimators': 200,
        'learning_rate': 0.05,
        'max_depth': 6,
        'test_size': 0.2,
    },
    'sentiment_analysis': {
        'max_features': 10000,
        'max_iter': 1000,
        'C': 5.0,
        'test_size': 0.2,
    },
    'text_classification': {
        'max_features': 10000,
        'alpha': 0.5,
        'test_size': 0.2,
    },
    'resnet': {
        'epochs': 25,
        'batch_size': 16,
        'optimizer': 'adam',
        'loss': 'categorical_crossentropy',
        'validation_split': 0.15,
        'learning_rate': 0.0001,
    },
    'lstm': {
        'epochs': 100,
        'batch_size': 32,
        'optimizer': 'adam',
        'loss': 'mse',
        'validation_split': 0.15,
        'sequence_length': 20,
    },
    'yolo': {
        'epochs': 50,
        'batch_size': 16,
        'imgsz': 640,
        'optimizer': 'auto',
    },
    'stylegan': {
        'epochs': 300,
        'batch_size': 8,
        'z_dim': 256,
        'w_dim': 256,
        'log_resolution': 7,
        'learning_rate': 0.0001,
    },
    'cnn': {
        'epochs': 50,
        'batch_size': 32,
        'optimizer': 'adam',
        'loss': 'categorical_crossentropy',
        'validation_split': 0.15,
        'test_size': 0.2,
    },
}


def get_user_upload_dir(user_id):
    """Get user-specific upload directory path."""
    return os.path.join(UPLOAD_DIR, str(user_id))


def get_user_models_dir(user_id):
    """Get user-specific trained models directory path."""
    return os.path.join(TRAINED_MODELS_DIR, str(user_id))


def get_user_images_dir(user_id):
    """Get user-specific output images directory path."""
    return os.path.join(IMAGES_DIR, str(user_id))


def get_user_predictions_dir(user_id):
    """Get user-specific predictions directory path."""
    return os.path.join(PREDICTIONS_DIR, str(user_id))


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path
