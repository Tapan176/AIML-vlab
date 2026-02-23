import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from mongoDb.connection import init_db, get_db
from config import FLASK_PORT, FLASK_DEBUG, UPLOAD_DIR, ALLOWED_ORIGINS

# import routes
from models.route import model_routes
from utils.route import utils_routes
from auth.auth_route import auth_routes
from admin.admin_route import admin_routes

app = Flask(__name__)
# Apply strict CORS according to ALLOWED_ORIGINS
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}})

# Set up global rate limiting (in-memory for now, use Redis in production)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

init_db()

# Run database migrations on startup
try:
    from migrations.migration_runner import run_migrations
    run_migrations()
except Exception as e:
    print(f"Migration warning: {e}")

# Register blueprints
app.register_blueprint(model_routes)
app.register_blueprint(utils_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(admin_routes, url_prefix='/admin')


@app.route('/uploads/<path:filename>')
def serve_public_files(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
