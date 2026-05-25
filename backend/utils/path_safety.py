"""
Path-traversal defenses for routes that build filesystem paths from user input.
"""
import os
from werkzeug.utils import secure_filename


ALLOWED_MODEL_EXTENSIONS = {'.pkl', '.h5', '.pt', '.zip'}
ALLOWED_PREDICTION_EXTENSIONS = {'.csv'}


def safe_join(root, *parts):
    """Join `parts` onto `root` and verify the resolved path stays inside `root`.

    Any user-supplied path component is run through secure_filename first.
    Raises ValueError if the result would escape `root`.
    """
    root_real = os.path.realpath(root)
    cleaned = [secure_filename(str(p)) for p in parts if p is not None and str(p) != '']
    candidate = os.path.realpath(os.path.join(root_real, *cleaned))
    if candidate != root_real and not candidate.startswith(root_real + os.sep):
        raise ValueError("Path escapes allowed root")
    return candidate


def validate_extension(extension, allowed):
    """Return `extension` (normalized to lowercase with leading dot) if it is in `allowed`.

    Raises ValueError otherwise.
    """
    if not extension:
        raise ValueError("Missing extension")
    ext = extension.lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    if ext not in allowed:
        raise ValueError(f"Extension {ext} not allowed")
    return ext
