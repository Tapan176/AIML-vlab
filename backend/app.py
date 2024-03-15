from flask import Flask, send_from_directory
from flask_cors import CORS

# import routes
from models.route import model_routes
from utils.route import utils_routes

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(model_routes)
app.register_blueprint(utils_routes)


@app.route('/uploads/<path:filename>')
def serve_public_files(filename):
    return send_from_directory('static/uploads', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
