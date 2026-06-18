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
    # A known default secret lets anyone forge JWTs (including admin role).
    # In local dev (FLASK_DEBUG=true) warn but allow; otherwise hard-fail at
    # startup so this can never reach production.
    if os.getenv('FLASK_DEBUG', 'false').lower() == 'true':
        import warnings
        warnings.warn(
            "JWT_SECRET is the public default value. Set a long random JWT_SECRET in "
            "backend/.env — allowed here only because FLASK_DEBUG=true.",
            stacklevel=2,
        )
    else:
        raise RuntimeError(
            "JWT_SECRET is unset or equals the public default. Set a long random "
            "JWT_SECRET environment variable before starting the server."
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
# Default OFF — the Werkzeug debugger must never be exposed in production. Opt
# into it explicitly with FLASK_DEBUG=true for local dev.
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5050,http://127.0.0.1:5050').split(',')

# --- Background jobs / Redis (Phase 2) --------------------------------------
# REDIS_URL powers two things when set: the flask_limiter storage (so per-IP
# rate limits are shared across gunicorn workers instead of per-process) and
# the RQ training queue. When unset, both gracefully fall back — the limiter
# uses in-memory storage and training runs synchronously in-request — so local
# dev and the free tier work with no Redis at all.
REDIS_URL = os.getenv('REDIS_URL', None)
# Opt-in master switch for offloading model training to the RQ worker. Default
# OFF: training runs synchronously in the request exactly as before. When true
# AND a queue is reachable, classical training is enqueued and the route returns
# 202 + a session_id for the client to poll. Falls back to sync if the queue is
# unavailable. See docs/IMPLEMENTATION_PLAN.md, Phase 2.
TRAINING_ASYNC = os.getenv('TRAINING_ASYNC', 'false').lower() == 'true'

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

# --- Payments: provider selector --------------------------------------------
# 'lemonsqueezy' (default — works from India, no invite, merchant of record) or
# 'stripe'. The active provider's keys must be set for checkout to work.
PAYMENT_PROVIDER = os.getenv('PAYMENT_PROVIDER', 'lemonsqueezy').lower()

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

# --- Lemon Squeezy (payments) -----------------------------------------------
# Merchant of record — works from India, no invite, handles global tax. All
# optional; when LEMONSQUEEZY_API_KEY is unset the endpoints report "not
# configured". Get these from https://app.lemonsqueezy.com/settings/api and your
# store's Products → Variants.
LEMONSQUEEZY_API_KEY = os.getenv('LEMONSQUEEZY_API_KEY', None)         # API key (Bearer)
LEMONSQUEEZY_STORE_ID = os.getenv('LEMONSQUEEZY_STORE_ID', None)       # numeric store id
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv('LEMONSQUEEZY_WEBHOOK_SECRET', None)  # webhook signing secret
# Variant IDs (one per paid plan) — each plan = a subscription variant.
LEMONSQUEEZY_VARIANT_PRO = os.getenv('LEMONSQUEEZY_VARIANT_PRO', None)
LEMONSQUEEZY_VARIANT_TEAM = os.getenv('LEMONSQUEEZY_VARIANT_TEAM', None)
# Where LS Checkout returns the user after success (frontend URL).
LEMONSQUEEZY_REDIRECT_URL = os.getenv('LEMONSQUEEZY_REDIRECT_URL', None)  # e.g. https://app/profile?status=success

# --- Razorpay (payments — India) --------------------------------------------
# Razorpay is the domestic (India) provider. It has a free/test mode and accepts
# UPI / Indian cards / netbanking. We use it for buyers detected in India and
# fall back to the international provider (Lemon Squeezy / Stripe) elsewhere.
# All optional; when RAZORPAY_KEY_ID is unset the India branch reports "not
# configured" and the app routes everyone to the international provider.
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', None)            # rzp_test_… / rzp_live_…
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', None)
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', None)
# Razorpay Subscription Plan IDs (one per paid plan), created in the dashboard.
RAZORPAY_PLAN_PRO = os.getenv('RAZORPAY_PLAN_PRO', None)        # plan_…
RAZORPAY_PLAN_TEAM = os.getenv('RAZORPAY_PLAN_TEAM', None)      # plan_…
# Monthly price in paise (INR * 100) shown on the bill for each plan.
RAZORPAY_PRICE_PRO_INR = int(os.getenv('RAZORPAY_PRICE_PRO_INR', '799'))
RAZORPAY_PRICE_TEAM_INR = int(os.getenv('RAZORPAY_PRICE_TEAM_INR', '2499'))

# --- Payment routing (one interface, two behaviours) ------------------------
# A buyer in India is routed to PAYMENT_PROVIDER_DOMESTIC; everyone else to
# PAYMENT_PROVIDER_INTL. Country is detected from the CDN geo-IP header (see
# /billing/locale) and can be overridden by the client only for DISPLAY — the
# server re-derives it server-side when creating a real checkout.
PAYMENT_PROVIDER_DOMESTIC = os.getenv('PAYMENT_PROVIDER_DOMESTIC', 'razorpay').lower()
PAYMENT_PROVIDER_INTL = os.getenv('PAYMENT_PROVIDER_INTL', PAYMENT_PROVIDER).lower()

# --- Email (free SMTP — invoices, OTP, password reset) ----------------------
# Works with any SMTP provider that has a free tier: Gmail (App Password),
# Brevo/Sendinblue (300/day free), Mailtrap (testing), etc. When SMTP_HOST is
# unset, emails are logged to the console instead of sent (safe dev default) so
# the OTP/invoice flows still work end-to-end locally without a mail account.
SMTP_HOST = os.getenv('SMTP_HOST', None)
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', None)
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', None)
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
EMAIL_FROM = os.getenv('EMAIL_FROM', SMTP_USER or 'no-reply@aiml-vlab.local')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'AIML Lab')

# --- OTP (email verification on signup / login) -----------------------------
# When OTP_ENABLED=true, signup and login require a one-time code emailed to the
# user before a JWT is issued. Off by default so existing flows are unchanged
# until you flip it on in .env.
OTP_ENABLED = os.getenv('OTP_ENABLED', 'false').lower() == 'true'
OTP_LENGTH = int(os.getenv('OTP_LENGTH', '6'))
OTP_TTL_MINUTES = int(os.getenv('OTP_TTL_MINUTES', '10'))
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', '5'))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv('OTP_RESEND_COOLDOWN_SECONDS', '60'))
# App URL used in invoice/OTP email bodies (links + branding). Falls back to
# FRONTEND_URL (defined below) at use-time via the email service if unset here.
APP_PUBLIC_URL = os.getenv('APP_PUBLIC_URL', None) or os.getenv('FRONTEND_URL', None) or 'http://localhost:3000'

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

# Default hyperparameter values per model  (optimised for best out-of-the-box accuracy).
#
# DERIVED — do not hand-edit. The single source of truth for every model's
# hyperparameters (defaults + ranges + enums + nullability + UI labels/notes)
# is the Pydantic models in ``services/hyperparam_models.py``. These defaults
# are extracted from those models' field defaults so a value lives in exactly
# one place. (Imported here, low in the file, to avoid a circular import with
# the protobuf env line at the top — hyperparam_models depends only on pydantic
# + stdlib and never imports config.)
from services.hyperparam_models import build_defaults as _build_defaults

DEFAULT_HYPERPARAMS = _build_defaults()


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
