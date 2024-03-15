from flask import Blueprint, request, send_file, jsonify
from utils.downloadFiles import get_model_path
from utils.uploadFiles import handle_upload_file

utils_routes = Blueprint('utils_routes', __name__)

@utils_routes.route('/download-trained-model', methods=['GET'])
def download_model():
    model_path = get_model_path(request)
    return send_file(model_path, as_attachment=True)

@utils_routes.route('/upload', methods=['POST'])
def upload_file():
    results = handle_upload_file(request)

    return jsonify(results)
