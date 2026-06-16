"""
Centralized configuration loader for ML-vlab backend.
All constants and settings are loaded from .env — no hardcoded values.
"""
import os

# Force the pure-Python protobuf implementation BEFORE anything imports TensorFlow
# or other protobuf-using libraries. Must stay at the top of this module since
# config.py is the first thing app.py imports.
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))


# --- MongoDB ---
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'aiml-lab')

# --- JWT ---
_JWT_DEFAULT = 'change-me-in-production'
JWT_SECRET = os.getenv('JWT_SECRET', _JWT_DEFAULT)
JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
JWT_ALGORITHM = 'HS256'

if JWT_SECRET == _JWT_DEFAULT:
    import warnings
    warnings.warn(
        "JWT_SECRET is using the public default value. "
        "Set JWT_SECRET in backend/.env to a long random string before running in any non-throwaway environment.",
        stacklevel=2,
    )

# --- File Storage ---
UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'static/uploads')
TRAINED_MODELS_DIR = os.getenv('TRAINED_MODELS_DIR', 'trainedModels')
IMAGES_DIR = os.getenv('IMAGES_DIR', 'static/images')
PREDICTIONS_DIR = os.getenv('PREDICTIONS_DIR', 'predictions')

# --- Google Drive ---
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
GOOGLE_TOKEN_JSON = os.getenv('GOOGLE_TOKEN_JSON')
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', os.path.join(BASE_DIR, 'credentials.json'))
GOOGLE_TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH', os.path.join(BASE_DIR, 'token.json'))

# --- Server ---
FLASK_PORT = int(os.getenv('FLASK_PORT', '5050'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5050,http://127.0.0.1:5050').split(',')

# --- Subscription / Quotas ---
# Master switch. When false (default) the app behaves exactly as before:
# no quotas are enforced and the subscription UI stays hidden. Flip to true
# (SUBSCRIPTION_ENABLED=true in .env) to turn on tiered usage limits.
SUBSCRIPTION_ENABLED = os.getenv('SUBSCRIPTION_ENABLED', 'false').lower() == 'true'
# Free-tier monthly run caps, only enforced when SUBSCRIPTION_ENABLED. Runs are
# classed as classical (scikit-learn/XGBoost), deep (CNN/ANN/ResNet/LSTM/YOLO/
# StyleGAN), or finetune (BERT/DistilBERT/ViT). A value of 0 blocks that class
# on the free tier (e.g. fine-tuning is the heaviest, so it's off by default).
FREE_TIER_CLASSICAL_RUNS = int(os.getenv('FREE_TIER_CLASSICAL_RUNS', '50'))
FREE_TIER_DEEP_RUNS = int(os.getenv('FREE_TIER_DEEP_RUNS', '5'))
FREE_TIER_FINETUNE_RUNS = int(os.getenv('FREE_TIER_FINETUNE_RUNS', '0'))
# Data Studio operations (profiling/preprocessing/diff) are cheap CPU work but
# still metered so the free tier can't be abused. 0 would disable Data Studio
# on free; default is a generous monthly allowance.
FREE_TIER_DATASTUDIO_OPS = int(os.getenv('FREE_TIER_DATASTUDIO_OPS', '100'))

# Per-account storage caps (number of datasets a user may keep). Enforced on
# upload + preprocessing output when SUBSCRIPTION_ENABLED. 0 = unlimited.
FREE_TIER_MAX_DATASETS = int(os.getenv('FREE_TIER_MAX_DATASETS', '20'))
PRO_TIER_MAX_DATASETS = int(os.getenv('PRO_TIER_MAX_DATASETS', '200'))
TEAM_TIER_MAX_DATASETS = int(os.getenv('TEAM_TIER_MAX_DATASETS', '1000'))

# --- Stripe (payments) ------------------------------------------------------
# All optional — when STRIPE_SECRET_KEY is unset, the payment endpoints report
# "not configured" and the app behaves as before (manual/free only).
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', None)            # sk_test_… / sk_live_…
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', None)  # pk_test_… / pk_live_…
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', None)    # whsec_… (from `stripe listen` / dashboard)
# Recurring Price IDs created in the Stripe dashboard (one per paid plan).
STRIPE_PRICE_PRO = os.getenv('STRIPE_PRICE_PRO', None)              # price_…
STRIPE_PRICE_TEAM = os.getenv('STRIPE_PRICE_TEAM', None)           # price_…
# Where Stripe Checkout returns the user after success/cancel (frontend URLs).
STRIPE_SUCCESS_URL = os.getenv('STRIPE_SUCCESS_URL', None)         # e.g. https://app/billing?status=success
STRIPE_CANCEL_URL = os.getenv('STRIPE_CANCEL_URL', None)           # e.g. https://app/pricing?status=cancel

# --- HuggingFace ---
HF_TOKEN = os.getenv('HF_TOKEN', None)  # Optional — needed for gated models
# Shared on-disk cache for base models pulled from the HF Hub, so a given base
# model is downloaded once and reused across users/sessions on the instance.
HF_CACHE_DIR = os.getenv('HF_CACHE_DIR', os.path.join(BASE_DIR, '.hf_cache'))

# --- OAuth Providers ---
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', None)
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', None)
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', None)
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', None)
# Public base URL of THIS backend, e.g. https://aiml-backend-xxx.run.app — used to
# build the OAuth redirect_uri. Must match the redirect URI registered with the
# provider. Required in production (split frontend/backend domains); in local dev
# the OAuth route falls back to request.host_url. No trailing /api.
OAUTH_REDIRECT_BASE = os.getenv('OAUTH_REDIRECT_BASE', None)
# Public URL of the frontend SPA, e.g. https://your-app.web.app — the popup posts
# the token back here. Falls back to the request Origin, then ALLOWED_ORIGINS[0].
FRONTEND_URL = os.getenv('FRONTEND_URL', None)

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
    'gradient_boosting',
    'xgboost',
    'sentiment_analysis',
    'text_classification',
    # 🆕 Fine-Tuning
    'bert_finetune',
    'vit_finetune',
    'distilbert_finetune',
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
        'learning_rate': 0.001,
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
        'learning_rate': 0.0001,
    },
    'lstm': {
        'epochs': 100,
        'batch_size': 32,
        'optimizer': 'adam',
        'loss': 'mse',
        'learning_rate': 0.001,
        'validation_split': 0.15,
        'sequence_length': 20,
    },
    'yolo': {
        'epochs': 50,
        'batch_size': 16,
        'imgsz': 640,
        'optimizer': 'auto',
        'lr0': 0.01,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3,
        'augment': True,
        'mosaic': 1.0,
    },
    'stylegan': {
        'epochs': 300,
        'batch_size': 8,
        'z_dim': 256,
        'w_dim': 256,
        'log_resolution': 7,
        'learning_rate': 0.0001,
        'optimizer': 'adam',
        'disc_lr': 0.0001,
        'r1_penalty': 10.0,
    },
    'cnn': {
        'epochs': 50,
        'batch_size': 32,
        'optimizer': 'adam',
        'loss': 'categorical_crossentropy',
        'learning_rate': 0.001,
        'momentum': 0.0,
    },
    # ── 🆕 Fine-Tuning Defaults ─────────────────────────────────
    'bert_finetune': {
        'model_name': 'bert-base-uncased',
        'epochs': 3,
        'batch_size': 16,
        'learning_rate': 2e-5,
        'max_length': 256,
        'warmup_steps': 0,
        'weight_decay': 0.01,
        'test_size': 0.2,
        'freeze_base': False,
    },
    'vit_finetune': {
        'model_name': 'google/vit-base-patch16-224',
        'epochs': 3,
        'batch_size': 16,
        'learning_rate': 2e-5,
        'weight_decay': 0.01,
        'test_size': 0.2,
        'freeze_base': False,
    },
    'distilbert_finetune': {
        'model_name': 'distilbert-base-uncased',
        'epochs': 3,
        'batch_size': 16,
        'learning_rate': 2e-5,
        'max_length': 256,
        'warmup_steps': 0,
        'weight_decay': 0.01,
        'test_size': 0.2,
        'freeze_base': False,
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
