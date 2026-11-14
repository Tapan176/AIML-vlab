"""
Dataset upload pipeline (CSV + image ZIP).

Fixes over the previous version:
  * Uploads are staged in a per-user, per-request temp dir. They used to go to
    a shared `static/uploads/<filename>`, so two users uploading `data.csv`
    at the same time clobbered (and deleted) each other's file.
  * After a ZIP upload the old code `rmtree`'d the whole shared
    `static/uploads/extracted` directory — wiping every user's extracted
    dataset cache. Validation now happens in the request's own temp dir.
  * CSVs are parsed with pandas (the hand-rolled `split(',')` broke on quoted
    fields) and only a small sample is stored inline in MongoDB; the whole
    file used to be embedded, which fails past the 16 MB document limit.
"""
import os
import shutil
import tempfile
import zipfile
import logging

from werkzeug.utils import secure_filename

from config import ensure_dir, get_user_tmp_upload_dir, CSV_INLINE_SAMPLE_ROWS
from utils.path_safety import safe_extract_zip

log = logging.getLogger(__name__)
IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')


def csv_sample(filepath, n_rows=CSV_INLINE_SAMPLE_ROWS):
    """Return (sample_records, columns, total_rows) for a CSV file."""
    import pandas as pd
    df = pd.read_csv(filepath, low_memory=False)
    sample = df.head(n_rows)
    sample = sample.astype(object).where(pd.notnull(sample), None)
    return sample.to_dict(orient='records'), [str(c) for c in df.columns], int(len(df))


def _zip_summary(filepath, work_dir):
    """Validate a ZIP (zip-slip / bomb checks) and count its images."""
    extract_dir = os.path.join(work_dir, 'extract')
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(filepath, 'r') as zf:
        safe_extract_zip(zf, extract_dir)
    total = 0
    classes = set()
    for root, _dirs, files in os.walk(extract_dir):
        imgs = [f for f in files if f.lower().endswith(IMAGE_EXTS)]
        if imgs:
            total += len(imgs)
            classes.add(os.path.basename(root))
    return {'image_count': total, 'class_count': len(classes)}


def handle_upload_file(request, user_id):
    """Store an uploaded dataset on Drive and record it. Returns (body, status)."""
    file = request.files.get('file')
    if file is None:
        return {'error': 'No file part'}, 400
    if not file.filename:
        return {'error': 'No selected file'}, 400

    filename = secure_filename(file.filename)
    lower = filename.lower()
    if not lower.endswith(('.csv', '.zip')):
        return {'error': 'Unsupported file type. Upload a .csv or a .zip of images.'}, 400

    from services.google_drive_service import upload_file_to_drive
    from services.dataset_service import save_dataset

    work_dir = tempfile.mkdtemp(dir=ensure_dir(get_user_tmp_upload_dir(user_id)))
    filepath = os.path.join(work_dir, filename)
    try:
        file.save(filepath)

        def _drive_upload():
            try:
                return upload_file_to_drive(filepath, filename, folder_type='datasets', user_id=user_id)
            except Exception as e:
                log.warning("Google Drive upload failed for %s: %s", filename, e)
                return {}

        if lower.endswith('.csv'):
            try:
                sample, columns, total_rows = csv_sample(filepath)
            except Exception:
                return {'error': 'Could not parse the CSV file. Check that it is a valid comma-separated file.'}, 400
            drive_res = _drive_upload()
            if not drive_res.get('id'):
                return {'error': 'Upload to cloud storage failed. Please try again.'}, 502
            ds = save_dataset(
                user_id, filename, '', file_type='csv', csv_data=sample,
                drive_id=drive_res['id'],
                extra={'columns': columns, 'row_count': total_rows},
            )
            return {
                'csv_data': sample, 'columns': columns, 'row_count': total_rows,
                'filename': filename, 'dataset_id': ds['_id'], 'version': ds['version'],
                'drive_id': drive_res['id'],
            }, 200

        # ZIP of images
        try:
            summary = _zip_summary(filepath, work_dir)
        except (zipfile.BadZipFile, ValueError) as e:
            return {'error': f'Invalid ZIP archive: {e}'}, 400
        drive_res = _drive_upload()
        if not drive_res.get('id'):
            return {'error': 'Upload to cloud storage failed. Please try again.'}, 502
        ds = save_dataset(
            user_id, filename, '', file_type='zip', drive_id=drive_res['id'], extra=summary,
        )
        return {
            'filename': filename, 'dataset_id': ds['_id'], 'version': ds['version'],
            'drive_id': drive_res['id'], 'image_links': [], **summary,
        }, 200
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
