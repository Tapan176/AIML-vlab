"""
Dataset path resolver for image-based deep learning models.
Resolves dataset paths from filesystem, database, or Google Drive.
For CSV datasets, use dataset_service.get_dataset_df() instead.

Security model: `filename` / `file_path` come straight from the request body,
so they are only ever used as a LOOKUP KEY. The old resolver returned
`file_path` as-is whenever it named an existing directory, which let a client
train on (and preview) any directory on the server — including other users'
extracted datasets. Now the only directories ever returned live inside the
caller's own extraction cache, and they are produced from datasets the caller
is allowed to read.
"""
import os
import shutil
import zipfile
import threading

from werkzeug.utils import secure_filename

from config import ensure_dir, get_user_extract_cache_dir
from utils.path_safety import safe_extract_zip, safe_join

# One lock per cache target so two concurrent runs on the same dataset don't
# extract into the same directory at the same time.
_locks = {}
_locks_guard = threading.Lock()


def _lock_for(key):
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def _lookup_name(filename, file_path):
    name = filename or (os.path.basename(str(file_path).rstrip('/\\')) if file_path else None)
    if not name:
        return None
    return os.path.basename(str(name))


def resolve_image_dataset_path(user_id, filename=None, file_path=None, dataset=None):
    """Return the absolute path of the extracted image dataset.

    `dataset` may be passed directly by callers that already loaded (and
    access-checked) the dataset document. Otherwise it is looked up by name
    among the user's datasets, then the curated defaults.

    Raises FileNotFoundError if the dataset cannot be resolved.
    """
    if dataset is None:
        name = _lookup_name(filename, file_path)
        if not name:
            raise FileNotFoundError("No dataset selected. Upload a ZIP dataset or pick one from the library.")
        from services.dataset_service import find_dataset_for_user
        dataset = find_dataset_for_user(user_id, name)
        if dataset is None and not name.lower().endswith('.zip'):
            dataset = find_dataset_for_user(user_id, name + '.zip')
        if dataset is None:
            raise FileNotFoundError(
                "Dataset could not be found. Please upload a dataset or select one from the library."
            )

    lookup = dataset.get('filename') or 'dataset.zip'
    base_name = secure_filename(os.path.splitext(lookup)[0]) or 'dataset'
    # Defaults are shared, so cache them once under a common key instead of
    # re-downloading per user.
    owner_key = '_defaults' if dataset.get('is_default') else str(user_id)
    cache_dir = get_user_extract_cache_dir(owner_key)
    version = dataset.get('version', 1)
    target = safe_join(cache_dir, f"{base_name}_v{version}")

    with _lock_for(target):
        if os.path.isdir(target) and os.listdir(target):
            return os.path.abspath(target)

        drive_id = dataset.get('drive_id')
        if drive_id:
            return _download_and_extract_from_drive(drive_id, cache_dir, target)

        db_filepath = dataset.get('filepath')
        if db_filepath and os.path.isfile(db_filepath) and db_filepath.lower().endswith('.zip'):
            return _extract_zip(db_filepath, cache_dir, target)

    raise FileNotFoundError("Dataset files are no longer available. Please re-upload the dataset.")


def _download_and_extract_from_drive(drive_id, cache_dir, target):
    """Download a zip file from Google Drive and extract it into `target`."""
    from services.google_drive_service import stream_file_from_drive
    import tempfile

    ensure_dir(cache_dir)
    fh, _ = stream_file_from_drive(drive_id)
    fd, zip_path = tempfile.mkstemp(suffix='.zip', dir=cache_dir)
    try:
        with os.fdopen(fd, 'wb') as f:
            fh.seek(0)
            shutil.copyfileobj(fh, f, length=1024 * 1024)
        return _extract_zip(zip_path, cache_dir, target)
    finally:
        try:
            os.remove(zip_path)
        except OSError:
            pass


def _extract_zip(zip_path, cache_dir, target):
    """Extract a zip into `target`, flattening a single top-level folder.

    Extraction happens in a temp dir and is moved into place at the end, so a
    crash mid-extract never leaves a half-populated `target` that later runs
    would mistake for a complete cache.
    """
    import tempfile
    ensure_dir(cache_dir)
    temp_extract = tempfile.mkdtemp(prefix='_extract_', dir=cache_dir)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            safe_extract_zip(zip_ref, temp_extract)

        items = [f for f in os.listdir(temp_extract) if not f.startswith('.') and f != '__MACOSX']
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
        if len(items) == 1 and os.path.isdir(os.path.join(temp_extract, items[0])):
            shutil.move(os.path.join(temp_extract, items[0]), target)
        else:
            shutil.move(temp_extract, target)
    finally:
        if os.path.isdir(temp_extract):
            shutil.rmtree(temp_extract, ignore_errors=True)
    return os.path.abspath(target)
