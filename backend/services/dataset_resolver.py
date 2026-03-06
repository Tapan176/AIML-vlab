"""
Dataset path resolver for image-based deep learning models.
Resolves dataset paths from filesystem, database, or Google Drive.
For CSV datasets, use dataset_service.get_dataset_df() instead.
"""
import os
import zipfile
import shutil
from config import UPLOAD_DIR, ensure_dir


def resolve_image_dataset_path(user_id, filename=None, file_path=None):
    """
    Resolve the actual filesystem path for an image dataset (zip-based).
    
    Priority:
    1. If file_path is a valid directory on disk, use it directly.
    2. Lookup dataset in DB by user_id + filename.
       a. If extracted_path exists on disk, use it.
       b. If drive_id exists, download zip from Drive, extract, cache locally.
       c. If filepath (original upload path) exists, extract from there.
    3. Check common local fallback paths.
    
    Returns the absolute path to the extracted dataset directory.
    Raises FileNotFoundError if the dataset cannot be resolved.
    """
    # 1. Try the provided file_path directly
    if file_path and os.path.isdir(file_path):
        return os.path.abspath(file_path)
    
    # Also try as absolute path
    if file_path and os.path.isdir(os.path.abspath(file_path)):
        return os.path.abspath(file_path)
    
    # 2. Lookup in database
    if filename or file_path:
        from mongoDb.connection import get_db
        db = get_db()
        
        lookup_filename = filename or (os.path.basename(file_path) if file_path else None)
        
        if lookup_filename:
            # Search user's datasets first
            dataset = db.datasets.find_one({
                'user_id': str(user_id),
                'filename': lookup_filename
            })
            
            # Fallback to default datasets
            if not dataset:
                dataset = db.datasets.find_one({
                    'is_default': True,
                    'filename': lookup_filename
                })
            
            if dataset:
                # 2a. Check if extracted_path from DB is valid
                extracted_path = dataset.get('extracted_path')
                if extracted_path and os.path.isdir(extracted_path):
                    return os.path.abspath(extracted_path)
                
                # Build a cached extraction directory for this user
                cache_dir = os.path.join(UPLOAD_DIR, 'extracted', str(user_id))
                base_name = os.path.splitext(lookup_filename)[0]
                cached_extracted_path = os.path.join(cache_dir, base_name)
                
                # Check if we already have it cached
                if os.path.isdir(cached_extracted_path):
                    return os.path.abspath(cached_extracted_path)
                
                # 2b. Try downloading from Google Drive
                drive_id = dataset.get('drive_id')
                if drive_id:
                    try:
                        zip_path = _download_and_extract_from_drive(
                            drive_id, lookup_filename, cache_dir, base_name
                        )
                        if zip_path and os.path.isdir(zip_path):
                            return os.path.abspath(zip_path)
                    except Exception as e:
                        print(f"Warning: Drive download failed for {lookup_filename}: {e}")
                
                # 2c. Try the original filepath from DB
                db_filepath = dataset.get('filepath')
                if db_filepath and os.path.exists(db_filepath):
                    if db_filepath.endswith('.zip'):
                        return _extract_zip(db_filepath, cache_dir, base_name)
                    elif os.path.isdir(db_filepath):
                        return os.path.abspath(db_filepath)
    
    # 3. Local fallback paths
    if filename:
        base_name = os.path.splitext(filename)[0]
        fallback_paths = [
            os.path.join(UPLOAD_DIR, 'extracted', base_name),
            os.path.join(UPLOAD_DIR, base_name),
        ]
        if user_id:
            fallback_paths.insert(0, os.path.join(UPLOAD_DIR, 'extracted', str(user_id), base_name))
            fallback_paths.append(os.path.join(UPLOAD_DIR, str(user_id), base_name))
        
        for p in fallback_paths:
            if os.path.isdir(p):
                return os.path.abspath(p)
    
    raise FileNotFoundError(
        f"Dataset could not be resolved. Please upload a dataset or select one from the library. "
        f"(filename={filename}, file_path={file_path})"
    )


def _download_and_extract_from_drive(drive_id, filename, cache_dir, base_name):
    """Download a zip file from Google Drive and extract it."""
    from services.google_drive_service import stream_file_from_drive
    
    ensure_dir(cache_dir)
    zip_path = os.path.join(cache_dir, filename)
    
    # Download zip
    fh, _ = stream_file_from_drive(drive_id)
    with open(zip_path, 'wb') as f:
        f.write(fh.read())
    
    # Extract
    extracted_path = _extract_zip(zip_path, cache_dir, base_name)
    
    # Clean up zip
    try:
        os.remove(zip_path)
    except Exception:
        pass
    
    return extracted_path


def _extract_zip(zip_path, cache_dir, base_name):
    """Extract a zip file and return the path to the extracted contents.
    
    Handles cases where the zip's internal root folder name differs from
    the expected base_name. Also handles flat zips (no root folder).
    """
    import tempfile
    ensure_dir(cache_dir)
    target_path = os.path.join(cache_dir, base_name)
    
    # Clean up old extraction if present
    if os.path.isdir(target_path):
        shutil.rmtree(target_path, ignore_errors=True)
    
    # Extract to a temp dir first to inspect structure
    temp_extract = os.path.join(cache_dir, f'_temp_extract_{base_name}')
    if os.path.isdir(temp_extract):
        shutil.rmtree(temp_extract, ignore_errors=True)
    
    os.makedirs(temp_extract, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)
    
    # Determine the actual root contents
    extracted_items = [f for f in os.listdir(temp_extract) if not f.startswith('.') and f != '__MACOSX']
    
    if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract, extracted_items[0])):
        # ZIP had a single root folder — move it to the target path
        actual_root = os.path.join(temp_extract, extracted_items[0])
        shutil.move(actual_root, target_path)
    else:
        # ZIP had flat files or multiple roots — move the entire temp dir
        shutil.move(temp_extract, target_path)
    
    # Clean up temp dir if it still exists
    if os.path.isdir(temp_extract):
        shutil.rmtree(temp_extract, ignore_errors=True)
    
    return os.path.abspath(target_path)

