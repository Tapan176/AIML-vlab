"""
Dataset service — manages per-user dataset uploads and persistence.
Datasets persist across page refreshes (stored server-side, linked to user).
Supports versioning: uploading the same filename increments the version number.

Access rule (enforced by `get_accessible_dataset` / `find_dataset_for_user`):
a user may read a dataset they own, or a curated default (is_default=True).
"""
import os
import logging
from datetime import datetime

from bson import ObjectId
from werkzeug.utils import secure_filename

from mongoDb.connection import get_db
from config import get_user_upload_dir

log = logging.getLogger(__name__)

# Fields never needed in list views (can be large).
_LIST_PROJECTION = {'csv_data': 0, 'image_links': 0}


def _serialize(d):
    d['_id'] = str(d['_id'])
    if 'uploaded_at' in d and hasattr(d['uploaded_at'], 'isoformat'):
        d['uploaded_at'] = d['uploaded_at'].isoformat()
    d.setdefault('version', 1)
    return d


def _get_next_version(user_id, filename):
    """Get the next version number for a given user+filename combination."""
    db = get_db()
    latest = db.datasets.find_one(
        {'user_id': str(user_id), 'filename': filename},
        sort=[('version', -1)],
        projection={'version': 1},
    )
    if latest and 'version' in latest:
        return latest['version'] + 1
    return 1


def save_dataset(user_id, filename, filepath, file_type, csv_data=None, image_links=None,
                 extracted_path=None, drive_id=None, extra=None):
    """Record a dataset upload in the database with auto-incrementing version.

    `csv_data` should be a SMALL sample (see CSV_INLINE_SAMPLE_ROWS); the full
    file lives on Drive.
    """
    db = get_db()
    dataset = {
        'user_id': str(user_id),
        'filename': filename,
        'filepath': filepath,
        'file_type': file_type,
        'csv_data': csv_data,
        'image_links': image_links,
        'extracted_path': extracted_path,
        'uploaded_at': datetime.utcnow(),
        'drive_id': drive_id,
        'version': _get_next_version(user_id, filename),
    }
    if extra:
        dataset.update(extra)
    result = db.datasets.insert_one(dataset)
    dataset['_id'] = str(result.inserted_id)
    return dataset


def get_user_datasets(user_id):
    """Get all datasets uploaded by a user (all versions)."""
    db = get_db()
    cursor = db.datasets.find({'user_id': str(user_id)}, _LIST_PROJECTION) \
        .sort([('filename', 1), ('version', -1)])
    return [_serialize(d) for d in cursor]


def get_dataset(dataset_id):
    """Get a single dataset by ID (NO access check — prefer get_accessible_dataset)."""
    db = get_db()
    try:
        oid = ObjectId(dataset_id)
    except Exception:
        raise Exception("dataset_not_found")
    dataset = db.datasets.find_one({'_id': oid})
    if not dataset:
        raise Exception("dataset_not_found")
    dataset['_id'] = str(dataset['_id'])
    return dataset


def get_accessible_dataset(user_id, dataset_id, projection=None):
    """Return the dataset if `user_id` owns it or it is a curated default, else None."""
    if not dataset_id:
        return None
    try:
        oid = ObjectId(str(dataset_id))
    except Exception:
        return None
    db = get_db()
    ds = db.datasets.find_one(
        {'_id': oid, '$or': [{'user_id': str(user_id)}, {'is_default': True}]},
        projection,
    )
    if ds:
        ds['_id'] = str(ds['_id'])
    return ds


def find_dataset_for_user(user_id, filename):
    """Latest version of `filename` owned by the user, else a default with that name."""
    if not isinstance(filename, str) or not filename:
        return None
    db = get_db()
    ds = None
    if user_id:
        ds = db.datasets.find_one(
            {'user_id': str(user_id), 'filename': filename},
            sort=[('version', -1)],
        )
    if not ds:
        ds = db.datasets.find_one({'is_default': True, 'filename': filename})
    return ds


def get_dataset_by_filename(user_id, filename):
    """Get the latest version of a dataset by user ID and filename."""
    db = get_db()
    dataset = db.datasets.find_one(
        {'user_id': str(user_id), 'filename': filename},
        sort=[('version', -1)]
    )
    if dataset:
        dataset['_id'] = str(dataset['_id'])
    return dataset


def get_dataset_versions(user_id, filename):
    """Get all versions of a dataset for a given user and filename."""
    db = get_db()
    cursor = db.datasets.find(
        {'user_id': str(user_id), 'filename': filename}, _LIST_PROJECTION
    ).sort('version', -1)
    return [_serialize(d) for d in cursor]


def _read_csv(source):
    import pandas as pd
    return pd.read_csv(source, low_memory=False)


def load_dataset_df(dataset):
    """Load a dataset document's CSV into a DataFrame (Drive first, then local)."""
    if dataset.get('drive_id'):
        try:
            from services.google_drive_service import stream_file_from_drive
            fh, _ = stream_file_from_drive(dataset['drive_id'])
            return _read_csv(fh)
        except Exception as e:
            log.warning("Drive load failed for dataset %s: %s", dataset.get('_id'), e)
    path = dataset.get('filepath')
    if path and os.path.isfile(path):
        return _read_csv(path)
    raise FileNotFoundError(f"Dataset {dataset.get('filename')} could not be retrieved.")


def get_dataset_df(user_id, filename):
    """Load a CSV dataset the user can access, by filename.

    Resolution: the user's latest version → a curated default → the user's own
    upload directory (dev fallback). The filename is client-supplied, so the
    local fallback is sanitised and confined to the user's directory — the old
    code joined it onto UPLOAD_DIR verbatim, which let a request read another
    user's file ("<their_id>/data.csv") or escape the folder entirely.
    """
    dataset = find_dataset_for_user(user_id, filename)
    if dataset:
        return load_dataset_df(dataset)

    safe_name = secure_filename(filename or '')
    if user_id and safe_name:
        from utils.path_safety import safe_join
        try:
            path = safe_join(get_user_upload_dir(user_id), safe_name)
            if os.path.isfile(path):
                return _read_csv(path)
        except ValueError:
            pass

    raise FileNotFoundError(f"Dataset {safe_name or filename} could not be found.")
