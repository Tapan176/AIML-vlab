"""
Dataset service — manages per-user dataset uploads and persistence.
Datasets persist across page refreshes (stored server-side, linked to user).
"""
import os
from datetime import datetime
from mongoDb.connection import get_db
from bson import ObjectId
from config import get_user_upload_dir, ensure_dir


def save_dataset(user_id, filename, filepath, file_type, csv_data=None, image_links=None, extracted_path=None):
    """Record a dataset upload in the database."""
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
    }

    result = db.datasets.insert_one(dataset)
    dataset['_id'] = str(result.inserted_id)
    return dataset


def get_user_datasets(user_id):
    """Get all datasets uploaded by a user."""
    db = get_db()
    datasets = list(db.datasets.find(
        {'user_id': str(user_id)},
        {'csv_data': 0}  # Exclude large csv_data from listing
    ).sort('uploaded_at', -1))

    for d in datasets:
        d['_id'] = str(d['_id'])

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
    """Get a dataset by user ID and filename."""
    db = get_db()
    dataset = db.datasets.find_one({
        'user_id': str(user_id),
        'filename': filename
    })

    if dataset:
        dataset['_id'] = str(dataset['_id'])

    return dataset
