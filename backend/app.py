from flask import Flask, send_from_directory
from flask_cors import CORS

from mongoDb.connection import init_db, get_db
from config import FLASK_PORT, FLASK_DEBUG, UPLOAD_DIR

# import routes
from models.route import model_routes
from utils.route import utils_routes
from auth.authRoute import auth_routes

app = Flask(__name__)
CORS(app)

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


@app.route('/uploads/<path:filename>')
def serve_public_files(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
