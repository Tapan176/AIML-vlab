# config import must come first — it sets PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION
# before any TensorFlow/protobuf imports happen elsewhere.
from config import FLASK_PORT, FLASK_DEBUG, UPLOAD_DIR, ALLOWED_ORIGINS

# Pin matplotlib to the non-interactive Agg backend ONCE, before any model
# module imports pyplot. After pyplot is imported, matplotlib.use() is a no-op
# with a warning — so this must precede the route imports below.
import matplotlib
matplotlib.use('Agg')

from flask import Flask, send_from_directory
from flask_cors import CORS

from extensions import limiter
from mongoDb.connection import init_db

# import routes
from models.route import model_routes
from utils.route import utils_routes
from auth.auth_route import auth_routes
from auth.oauth_route import oauth_routes
from admin.admin_route import admin_routes
from models.finetune_routes import finetune_routes
from subscription.subscription_route import subscription_routes


# Exempt OPTIONS preflight requests from rate limiting at the limiter level.
# Registered once on the shared limiter singleton (not per-app) so repeated
# create_app() calls in tests don't stack duplicate filters.
@limiter.request_filter
def _skip_options():
    from flask import request as req
    return req.method == 'OPTIONS'


def create_app(*, testing=False, init_database=True, run_migrations_on_start=True):
    """Application factory.

    Building the app inside a function — rather than at import time — keeps
    ``import app`` free of side effects (no DB connection, no migrations). That
    lets the test-suite construct an isolated app with a mock DB, and lets the
    future background-job worker import app code without booting the web stack.

    Args:
        testing: set Flask TESTING and disable the rate limiter so repeated
            calls to the same endpoint in a test don't trip per-minute limits.
        init_database: connect to the real MongoDB via ``init_db()``. Tests pass
            ``False`` and inject a mongomock DB themselves via
            ``mongoDb.connection.init_db(client_factory=...)``.
        run_migrations_on_start: apply pending migrations once the DB is up.
    """
    app = Flask(__name__)

    if testing:
        app.config['TESTING'] = True
        # Disable rate limiting in tests so repeated hits to the same endpoint
        # don't cause flaky 429s. Must be set before limiter.init_app(app).
        app.config['RATELIMIT_ENABLED'] = False

    # Preserve dict insertion order in JSON responses. Flask sorts keys
    # alphabetically by default, which scrambled the model registry's category
    # and model ordering (the Sidebar relies on the backend's intentional
    # Regression → … → Fine-Tuning order). Disable sorting so jsonify keeps
    # insertion order.
    app.config['JSON_SORT_KEYS'] = False  # Flask < 2.2
    try:
        app.json.sort_keys = False         # Flask >= 2.2 (provider-based)
    except Exception:
        pass

    # Hard backstop on request body size so a malicious client can't exhaust
    # memory/disk by streaming a huge upload. Slightly above MAX_UPLOAD_SIZE_BYTES
    # to leave room for multipart overhead; the upload route also checks the
    # per-plan storage cap and returns a friendly 413/429.
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

    # Bind the shared rate limiter (defined in extensions.py so blueprints can
    # apply per-route limits). In-memory storage for now — use Redis in
    # production (see docs/IMPLEMENTATION_PLAN.md, Phase 2).
    limiter.init_app(app)

    # Handle preflight early to send a proper 200 response.
    @app.before_request
    def handle_preflight():
        from flask import request, make_response
        if request.method == 'OPTIONS':
            response = make_response()
            response.status_code = 200
            return response

    if init_database:
        init_db()
    if run_migrations_on_start:
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
    # retries — exempt it from the per-IP rate limit so legitimate billing
    # events are never dropped. (The endpoint still verifies the provider
    # signature.)
    try:
        limiter.exempt(app.view_functions['subscription_routes.billing_webhook'])
    except Exception as e:
        print(f"Could not exempt billing webhook from rate limit: {e}")

    @app.route('/api')
    def health_check():
        return {"status": "ok", "message": "ML-vlab API is running on Vercel Context Region"}

    @app.route('/api/uploads/<path:filename>')
    def serve_public_files(filename):
        return send_from_directory(UPLOAD_DIR, filename)

    return app


# Entry point. gunicorn invokes the factory directly via "app:create_app()"
# (see Dockerfile); `python app.py` builds it here for the dev server. Importing
# this module does NOT create an app, so test imports stay side-effect free.
if __name__ == '__main__':
    create_app().run(debug=FLASK_DEBUG, port=FLASK_PORT)
