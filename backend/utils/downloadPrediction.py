from config import PREDICTIONS_DIR
from utils.path_safety import safe_join, validate_extension, ALLOWED_PREDICTION_EXTENSIONS


def get_model_predictions(request):
    model_name = request.args.get('model_name')
    extension = request.args.get('extension', '.csv')

    if not model_name:
        raise ValueError("Missing model_name")

    extension = validate_extension(extension, ALLOWED_PREDICTION_EXTENSIONS)
    return safe_join(PREDICTIONS_DIR, model_name + extension)
