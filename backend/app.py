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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
# Apply CORS — allow credentials so Authorization header passes preflight
CORS(app, resources={r"/*": {
    "origins": ALLOWED_ORIGINS,
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "expose_headers": ["Content-Type", "Authorization", "Content-Disposition"],
    "supports_credentials": True,
}})

# Set up global rate limiting (in-memory for now, use Redis in production)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://"
)

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

@app.route('/api')
def health_check():
    return {"status": "ok", "message": "ML-vlab API is running on Vercel Context Region"}

@app.route('/api/uploads/<path:filename>')
def serve_public_files(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
