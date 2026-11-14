# config import must come first — it sets PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION
# before any TensorFlow/protobuf imports happen elsewhere.
from config import FLASK_PORT, FLASK_DEBUG, ALLOWED_ORIGINS

# Pin matplotlib to the non-interactive Agg backend ONCE, before any model
# module imports pyplot. After pyplot is imported, matplotlib.use() is a no-op
# with a warning — so this must precede the route imports below.
import matplotlib
matplotlib.use('Agg')

import logging

from flask import Flask, jsonify
from flask_cors import CORS

logging.basicConfig(
    level=logging.DEBUG if FLASK_DEBUG else logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
log = logging.getLogger('aiml')

from extensions import limiter
from mongoDb.connection import init_db, get_db

# import routes
from models.route import model_routes
from utils.route import utils_routes
from auth.auth_route import auth_routes
from auth.oauth_route import oauth_routes
from admin.admin_route import admin_routes
from models.finetune_routes import finetune_routes
from subscription.subscription_route import subscription_routes

app = Flask(__name__)
# Preserve dict insertion order in JSON responses. Flask sorts keys
# alphabetically by default, which scrambled the model registry's category and
# model ordering (the Sidebar relies on the backend's intentional Regression →
# … → Fine-Tuning order). Disable sorting so jsonify keeps insertion order.
app.config['JSON_SORT_KEYS'] = False  # Flask < 2.2
try:
    app.json.sort_keys = False         # Flask >= 2.2 (provider-based)
except Exception:
    pass

# Hard backstop on request body size so a malicious client can't exhaust memory
# /disk by streaming a huge upload. Slightly above MAX_UPLOAD_SIZE_BYTES to
# leave room for multipart overhead; the upload route also checks the per-plan
# storage cap and returns a friendly 413/429.
try:
    from config import MAX_UPLOAD_SIZE_BYTES
    app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE_BYTES + (5 * 1024 * 1024)
except Exception:
    pass
# Apply CORS — allow credentials so Authorization header passes preflight
CORS(app, resources={r"/*": {
    "origins": ALLOWED_ORIGINS,
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "expose_headers": ["Content-Type", "Authorization", "Content-Disposition"],
    "supports_credentials": True,
}})

# Bind the shared rate limiter (defined in extensions.py so blueprints can apply
# per-route limits). In-memory storage for now — use Redis in production.
limiter.init_app(app)

# Exempt OPTIONS preflight requests from rate limiting at the limiter level
@limiter.request_filter
def _skip_options():
    from flask import request as req
    return req.method == 'OPTIONS'

# Also handle preflight early to send proper 200 response
@app.before_request
def handle_preflight():
    from flask import request, make_response
    if request.method == 'OPTIONS':
        response = make_response()
        response.status_code = 200
        return response

init_db()
try:
    from migrations.migration_runner import run_migrations
    run_migrations()
except Exception as e:
    print(f"Migration warning: {e}")

# Register blueprints with /api prefix for Vercel serverless compatibility
app.register_blueprint(model_routes, url_prefix='/api')
app.register_blueprint(utils_routes, url_prefix='/api')
app.register_blueprint(auth_routes, url_prefix='/api')
app.register_blueprint(oauth_routes, url_prefix='/api')
app.register_blueprint(admin_routes, url_prefix='/api/admin')
app.register_blueprint(finetune_routes, url_prefix='/api')
app.register_blueprint(subscription_routes, url_prefix='/api')

# Payment providers call the webhook from their own IPs and can burst on
# retries — exempt it from the per-IP rate limit so legitimate billing events
# are never dropped. (The endpoint still verifies the provider signature.)
try:
    limiter.exempt(app.view_functions['subscription_routes.billing_webhook'])
except Exception as e:
    print(f"Could not exempt billing webhook from rate limit: {e}")

@app.route('/api')
def health_check():
    status = {"status": "ok"}
    try:
        get_db().command('ping')
        status["db"] = "ok"
    except Exception:
        status.update(status="degraded", db="unreachable")
    return status, (200 if status["status"] == "ok" else 503)

# NOTE: the old unauthenticated /api/uploads/<path> route was removed — it
# served UPLOAD_DIR verbatim, i.e. every user's raw datasets and extracted
# image caches to anyone who could guess a path. Datasets are served through
# the owner-checked /api/datasets/* endpoints instead.


@app.after_request
def _security_headers(response):
    """Baseline hardening headers for every API response."""
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
    # The OAuth callback page carries an inline script; every other response is JSON/files.
    if response.mimetype == 'application/json':
        response.headers.setdefault('Cache-Control', 'no-store')
    return response


@app.errorhandler(413)
def _too_large(_e):
    from config import MAX_UPLOAD_SIZE_MB
    return jsonify({"error": f"File too large. Max upload size is {MAX_UPLOAD_SIZE_MB} MB."}), 413


@app.errorhandler(429)
def _rate_limited(e):
    return jsonify({"error": "rate_limited", "message": "Too many requests. Please slow down and try again shortly."}), 429


@app.errorhandler(Exception)
def _unhandled(e):
    """Last-resort handler: keep HTTP errors as-is, hide internals of everything else."""
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return jsonify({"error": e.name, "message": e.description}), e.code
    log.exception("Unhandled server error")
    body = {"error": "internal_error"}
    if FLASK_DEBUG:
        body["detail"] = str(e)
    return jsonify(body), 500


if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
