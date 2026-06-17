from config import TRAINED_MODELS_DIR
import os
from utils.path_safety import safe_join, validate_extension, ALLOWED_MODEL_EXTENSIONS


def get_model_path(request, current_user):
    model_name = request.args.get('model_name')
    extension = request.args.get('extension', '.pkl')
    version = request.args.get('version')

    if not model_name:
        raise ValueError("Missing model_name")

    extension = validate_extension(extension, ALLOWED_MODEL_EXTENSIONS)

    filename_base = model_name
    if version:
        filename_base = f"{model_name}_v{version}"

    # Always scope to the authenticated user. Previously a request-supplied
    # `user_id` selected the directory, so anyone could download another user's
    # model by guessing their id + model name (IDOR).
    root = os.path.join(TRAINED_MODELS_DIR, str(current_user['_id']))

    return safe_join(root, filename_base + extension)
