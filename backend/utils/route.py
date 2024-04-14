from flask import Blueprint, request, send_file, jsonify
from utils.downloadFiles import get_model_path
from utils.uploadFiles import handle_upload_file
from utils.downloadPrediction import get_model_predictions

utils_routes = Blueprint('utils_routes', __name__)

@utils_routes.route('/download-trained-model', methods=['GET'])
def download_model():
    model_path = get_model_path(request)
    return send_file(model_path, as_attachment=True)

@utils_routes.route('/download-model-predictions', methods=['GET'])
def download_model_predictions():
    model_path = get_model_predictions(request)
    return send_file(model_path, as_attachment=True)

@utils_routes.route('/upload', methods=['POST'])
def upload_file():
    results = handle_upload_file(request)

    return jsonify(results)
