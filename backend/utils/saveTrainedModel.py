"""
Save trained models to user-scoped directories with versioning.
"""
import os
from config import TRAINED_MODELS_DIR, ensure_dir


def saveTrainedModel(model, filename, model_type, user_id=None, version=None):
    """Saves a trained model to a file with a suitable extension.

    Args:
        model: The trained model object.
        filename: The base model name (e.g., 'knn').
        model_type: The type of model (e.g., 'scikit-learn', 'Keras', 'PyTorch').
        user_id: Optional user ID for user-scoped storage.
        version: Optional version number for versioned storage.
    """
    # Build directory path
    if user_id:
        save_dir = os.path.join(TRAINED_MODELS_DIR, str(user_id))
    else:
        save_dir = TRAINED_MODELS_DIR

    ensure_dir(save_dir)

    # Build filename with optional version
    if version:
        save_filename = f"{filename}_v{version}"
    else:
        save_filename = filename

    if model_type in ("scikit-learn", "nlp-learn"):
        import joblib
        extension = ".pkl"
        save_path = os.path.join(save_dir, save_filename + extension)
        joblib.dump(model, save_path)
    elif model_type in ("Keras", "TensorFlow"):
        extension = ".h5"
        save_path = os.path.join(save_dir, save_filename + extension)
        model.save(save_path)
    elif model_type == "PyTorch":
        import torch
        extension = ".pt"
        save_path = os.path.join(save_dir, save_filename + extension)
        torch.save(model.state_dict(), save_path)
    else:
        raise NotImplementedError(f"Saving logic not implemented for {model_type} models yet.")

    return save_path
