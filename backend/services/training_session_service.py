"""
Training session service — manages per-user model training sessions with versioning.
"""
from datetime import datetime
from mongoDb.connection import get_db
from bson import ObjectId


def create_session(user_id, model_code, hyperparams, dataset_id=None):
    """Create a new training session for a user. Auto-increments version number.
    
    Also looks up and stores dataset metadata (filename, type, drive_id) so
    the session record is self-contained.
    """
    db = get_db()

    # Get the latest version for this user + model combination
    latest = db.training_sessions.find_one(
        {'user_id': str(user_id), 'model_code': model_code},
        sort=[('version', -1)]
    )
    version = (latest['version'] + 1) if latest else 1

    # Look up dataset metadata if dataset_id provided
    dataset_info = None
    if dataset_id:
        try:
            ds = db.datasets.find_one({'_id': ObjectId(dataset_id)})
            if ds:
                dataset_info = {
                    'dataset_id': str(ds['_id']),
                    'filename': ds.get('filename'),
                    'file_type': ds.get('file_type'),
                    'drive_id': ds.get('drive_id'),
                }
        except Exception:
            pass

    session = {
        'user_id': str(user_id),
        'model_code': model_code,
        'version': version,
        'session_label': f"{model_code}_v{version}",
        'hyperparams': hyperparams,
        'dataset_id': str(dataset_id) if dataset_id else None,
        'dataset_info': dataset_info,
        'results': None,
        'output_images': [],
        'trained_model_path': None,
        'trained_model_drive_id': None,
        'predictions_path': None,
        'status': 'pending',
        'created_at': datetime.utcnow(),
        'completed_at': None,
    }

    result = db.training_sessions.insert_one(session)
    session['_id'] = str(result.inserted_id)
    return session


from services.google_drive_service import upload_file_to_drive
import os
import zipfile
import shutil
import tempfile


def _zip_model_path(model_path, additional_files=None):
    """
    If model_path is a directory or there are sibling files that belong to the
    same model (e.g. .h5 + .json), or if there are additional_files (like images),
    create a single .zip archive and return its path. 
    If it's already a single file and no additional_files, return as-is.
    """
    additional_files = additional_files or []
    
    # Check if we inherently need to zip
    is_dir = os.path.isdir(model_path)
    
    parent = os.path.dirname(model_path)
    base_name = os.path.splitext(os.path.basename(model_path))[0]
    
    siblings = []
    if not is_dir:
        siblings = [f for f in os.listdir(parent)
                    if f.startswith(base_name) and os.path.isfile(os.path.join(parent, f))]
        
    needs_zip = is_dir or len(siblings) > 1 or len(additional_files) > 0

    if not needs_zip:
        # Single file, no additional files — return as-is
        return model_path

    # We need to create a zip
    zip_path = os.path.join(parent, base_name + '_results.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. Add the model files
        if is_dir:
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    abs_file = os.path.join(root, file)
                    arc_name = os.path.relpath(abs_file, model_path)
                    zf.write(abs_file, os.path.join("model", arc_name))
        else:
            if len(siblings) > 1:
                for sib in siblings:
                    zf.write(os.path.join(parent, sib), os.path.join("model", sib))
            else:
                zf.write(model_path, os.path.join("model", os.path.basename(model_path)))
                
        # 2. Add the additional files (output images)
        for fpath in additional_files:
            if os.path.exists(fpath):
                zf.write(fpath, os.path.join("output_images", os.path.basename(fpath)))

    return zip_path


def _create_results_zip(output_images, session_label):
    if not output_images:
        return None
        
    parent_dir = os.path.dirname(output_images[0])
    zip_path = os.path.join(parent_dir, f"{session_label}_results.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for img_path in output_images:
            if os.path.exists(img_path):
                zf.write(img_path, os.path.basename(img_path))
                
    return zip_path

def update_session_results(session_id, results, output_images, model_path, predictions_path=None):
    """Update a training session with results after training completes.
    
    - Zips the trained model if it's a directory or multi-file output.
    - Zips output images into a separate results.zip
    - Uploads both to Google Drive under UserData/{user_id}/trained_models/{session_label}.
    - Stores the Drive download URLs in the session record.
    """
    db = get_db()
    
    session = db.training_sessions.find_one({'_id': ObjectId(session_id)})
    user_id = session.get('user_id') if session else None
    session_label = session.get('session_label', f'session_{session_id}') if session else f'session_{session_id}'
    
    trained_model_drive_url = None
    trained_model_drive_id = None
    results_zip_drive_url = None
    results_zip_drive_id = None

    import shutil

    # 1. Handle Model Upload
    if model_path and os.path.exists(model_path):
        upload_path = _zip_model_path(model_path)
        upload_filename = os.path.basename(upload_path)
        
        try:
            drive_res = upload_file_to_drive(
                upload_path, upload_filename,
                folder_type='trained_models',
                user_id=user_id,
                subfolder=session_label
            )
            trained_model_drive_url = drive_res.get('webContentLink')
            trained_model_drive_id = drive_res.get('id')
            
            # Delete local model files to save disk space
            if os.path.exists(upload_path):
                os.remove(upload_path)
            if os.path.exists(model_path):
                if os.path.isdir(model_path):
                    shutil.rmtree(model_path, ignore_errors=True)
                else:
                    os.remove(model_path)
        except Exception as e:
            print(f"Warning: Failed to upload trained model to Drive: {e}")

    # 2. Handle Results Zip Upload
    if output_images:
        results_zip_path = _create_results_zip(output_images, session_label)
        if results_zip_path:
            try:
                drive_res = upload_file_to_drive(
                    results_zip_path, os.path.basename(results_zip_path),
                    folder_type='trained_models',
                    user_id=user_id,
                    subfolder=session_label
                )
                results_zip_drive_url = drive_res.get('webContentLink')
                results_zip_drive_id = drive_res.get('id')
                
                # Delete local results zip
                if os.path.exists(results_zip_path):
                    os.remove(results_zip_path)
            except Exception as e:
                print(f"Warning: Failed to upload results zip to Drive: {e}")
                
            # Delete the local output images
            for img_path in output_images:
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except Exception:
                        pass

    # Resolve the linked dataset's drive_id for easy reference
    dataset_drive_id = None
    dataset_id = session.get('dataset_id') if session else None
    if dataset_id:
        try:
            ds = db.datasets.find_one({'_id': ObjectId(dataset_id)})
            if ds:
                dataset_drive_id = ds.get('drive_id')
        except Exception:
            pass

    # Add to results so frontend knows they are available
    results['trained_model_drive_id'] = trained_model_drive_id
    results['results_zip_drive_id'] = results_zip_drive_id

    db.training_sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {
            'results': results,
            'output_images': output_images,
            'trained_model_path': model_path,
            'trained_model_drive_url': trained_model_drive_url,
            'trained_model_drive_id': trained_model_drive_id,
            'trained_model_filename': upload_filename,
            'results_zip_drive_url': results_zip_drive_url,
            'results_zip_drive_id': results_zip_drive_id,
            'dataset_drive_id': dataset_drive_id,
            'predictions_path': predictions_path,
            'status': 'completed',
            'completed_at': datetime.utcnow(),
        }}
    )
    return results


def update_session_error(session_id, error_message):
    """Mark a training session as failed."""
    db = get_db()

    db.training_sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {
            'status': 'failed',
            'error': error_message,
            'completed_at': datetime.utcnow(),
        }}
    )


def get_user_sessions(user_id, model_code=None):
    """Get all training sessions for a user, optionally filtered by model."""
    db = get_db()
    query = {'user_id': str(user_id)}
    if model_code:
        query['model_code'] = model_code

    sessions = list(db.training_sessions.find(query).sort('created_at', -1))

    for s in sessions:
        s['_id'] = str(s['_id'])

    return sessions


def get_session(session_id):
    """Get a single training session by ID."""
    db = get_db()
    session = db.training_sessions.find_one({'_id': ObjectId(session_id)})

    if not session:
        raise Exception("session_not_found")

    session['_id'] = str(session['_id'])
    return session


def delete_session(session_id, user_id):
    """Delete a training session: remove from DB and delete trained model from Drive."""
    db = get_db()
    session = db.training_sessions.find_one({'_id': ObjectId(session_id)})

    if not session:
        raise Exception("session_not_found")
    if session.get('user_id') != str(user_id):
        raise Exception("unauthorized")

    # Delete files from Google Drive if present
    try:
        from services.google_drive_service import delete_session_folder_from_drive, delete_file_from_drive
        
        session_label = f"{session.get('model_code')}_v{session.get('version', 1)}"
        
        # Delete trained model folder (which should contain both)
        drive_id = session.get('trained_model_drive_id')
        results_zip_drive_id = session.get('results_zip_drive_id')
        
        deleted_folder = False
        if drive_id:
            res = delete_session_folder_from_drive(drive_id, session_label)
            if res == 'folder':
                deleted_folder = True
        elif results_zip_drive_id:
            res = delete_session_folder_from_drive(results_zip_drive_id, session_label)
            if res == 'folder':
                deleted_folder = True
                
        # Fallback if folder deletion failed or wasn't triggered
        if not deleted_folder:
            if drive_id:
                delete_file_from_drive(drive_id)
            if results_zip_drive_id:
                delete_file_from_drive(results_zip_drive_id)
            
    except Exception as e:
        print(f"Warning: could not delete files from Drive for session {session_id}: {e}")

    # Delete local model file if it exists
    local_path = session.get('trained_model_path')
    if local_path and os.path.exists(local_path):
        try:
            os.remove(local_path)
        except Exception:
            pass

    # Remove from database
    db.training_sessions.delete_one({'_id': ObjectId(session_id)})
    return True
