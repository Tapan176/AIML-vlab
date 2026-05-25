from config import TRAINED_MODELS_DIR
import os
from utils.path_safety import safe_join, validate_extension, ALLOWED_MODEL_EXTENSIONS


def get_model_path(request):
    model_name = request.args.get('model_name')
    extension = request.args.get('extension', '.pkl')
    user_id = request.args.get('user_id')
    version = request.args.get('version')

    if not model_name:
        raise ValueError("Missing model_name")

    extension = validate_extension(extension, ALLOWED_MODEL_EXTENSIONS)

    filename_base = model_name
    if version:
        filename_base = f"{model_name}_v{version}"

    root = TRAINED_MODELS_DIR
    if user_id:
        root = os.path.join(TRAINED_MODELS_DIR, str(user_id))

    return safe_join(root, filename_base + extension)
