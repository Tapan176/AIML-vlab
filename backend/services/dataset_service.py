"""
Dataset service — manages per-user dataset uploads and persistence.
Datasets persist across page refreshes (stored server-side, linked to user).
Supports versioning: uploading the same filename increments the version number.
"""
import os
from datetime import datetime
from mongoDb.connection import get_db
from bson import ObjectId
from config import get_user_upload_dir, ensure_dir


def _get_next_version(user_id, filename):
    """Get the next version number for a given user+filename combination."""
    db = get_db()
    latest = db.datasets.find_one(
        {'user_id': str(user_id), 'filename': filename},
        sort=[('version', -1)]
    )
    if latest and 'version' in latest:
        return latest['version'] + 1
    return 1


def save_dataset(user_id, filename, filepath, file_type, csv_data=None, image_links=None, extracted_path=None, drive_id=None):
    """Record a dataset upload in the database with auto-incrementing version."""
    db = get_db()

    version = _get_next_version(user_id, filename)

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
        'version': version
    }

    result = db.datasets.insert_one(dataset)
    dataset['_id'] = str(result.inserted_id)
    return dataset


def get_user_datasets(user_id):
    """Get all datasets uploaded by a user (all versions)."""
    db = get_db()
    datasets = list(db.datasets.find(
        {'user_id': str(user_id)},
        {'csv_data': 0}  # Exclude large csv_data from listing
    ).sort([('filename', 1), ('version', -1)]))

    for d in datasets:
        d['_id'] = str(d['_id'])
        if 'uploaded_at' in d and hasattr(d['uploaded_at'], 'isoformat'):
            d['uploaded_at'] = d['uploaded_at'].isoformat()
        if 'version' not in d:
            d['version'] = 1

    return datasets


def get_dataset(dataset_id):
    """Get a single dataset by ID."""
    db = get_db()
    dataset = db.datasets.find_one({'_id': ObjectId(dataset_id)})

    if not dataset:
        raise Exception("dataset_not_found")

    dataset['_id'] = str(dataset['_id'])
    return dataset


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
    datasets = list(db.datasets.find(
        {'user_id': str(user_id), 'filename': filename},
        {'csv_data': 0}
    ).sort('version', -1))

    for d in datasets:
        d['_id'] = str(d['_id'])
        if 'uploaded_at' in d and hasattr(d['uploaded_at'], 'isoformat'):
            d['uploaded_at'] = d['uploaded_at'].isoformat()
        if 'version' not in d:
            d['version'] = 1

    return datasets


def get_dataset_df(user_id, filename):
    """
    Universally retrieves a pandas DataFrame from Google Drive if possible, 
    falling back to local storage otherwise.
    Searches current user's datasets first, then default system datasets.
    """
    import pandas as pd
    from config import UPLOAD_DIR
    import os
    
    db = get_db()
    
    # 1. Search User DB (latest version)
    dataset = db.datasets.find_one(
        {'user_id': str(user_id), 'filename': filename},
        sort=[('version', -1)]
    )
    
    # 2. Search Default Admin DB
    if not dataset:
        dataset = db.datasets.find_one({'is_default': True, 'filename': filename})
        
    # 3. Direct drive retrieval
    if dataset and dataset.get('drive_id'):
        try:
            from services.google_drive_service import stream_file_from_drive
            fh, _ = stream_file_from_drive(dataset['drive_id'])
            return pd.read_csv(fh)
        except Exception as e:
            print(f"Warning: Failed to load dataset {filename} directly from Google Drive ({e}). Attempting local fallback.")

    # 4. Fallback Filepath retrieval
    fallback_paths = []
    if dataset and dataset.get('filepath'):
        fallback_paths.append(dataset['filepath'])
    
    # Generic unlogged fallbacks for development servers
    fallback_paths.append(os.path.join(UPLOAD_DIR, filename))
    if user_id:
        fallback_paths.append(os.path.join(UPLOAD_DIR, str(user_id), filename))
        
    for p in fallback_paths:
        if p and os.path.exists(p):
            return pd.read_csv(p)
            
    raise FileNotFoundError(f"Dataset {filename} could not be retrieved from Google Drive or local Disk Storage.")

