from flask import Blueprint, request, send_file, jsonify
from utils.downloadFiles import get_model_path
from utils.uploadFiles import handle_upload_file
from utils.downloadPrediction import get_model_predictions

utils_routes = Blueprint('utils_routes', __name__)

from auth.auth_middleware import token_required
from services.training_session_service import get_session

@utils_routes.route('/download-trained-model/<session_id>', methods=['GET'])
@token_required
def download_model_session(current_user, session_id):
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Try Drive download first
        drive_id = session.get('trained_model_drive_id')
        if drive_id:
            try:
                from services.google_drive_service import stream_file_from_drive
                fh, mime_type = stream_file_from_drive(drive_id)
                download_name = session.get('trained_model_filename', f"{session.get('session_label', 'model')}.zip")
                return send_file(fh, as_attachment=True, download_name=download_name, mimetype=mime_type)
            except Exception as e:
                print(f"Drive download failed, falling back to local: {e}")
        
        # Fallback to local path
        model_path = session.get('trained_model_path')
        if not model_path:
            return jsonify({"error": "Model not available"}), 404
        
        import os
        download_name = session.get('trained_model_filename', os.path.basename(model_path))
        return send_file(model_path, as_attachment=True, download_name=download_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@utils_routes.route('/download-results-zip/<session_id>', methods=['GET'])
@token_required
def download_results_zip_session(current_user, session_id):
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403
        
        drive_id = session.get('results_zip_drive_id')
        if not drive_id:
            return jsonify({"error": "Results zip not available in Google Drive."}), 404
            
        from services.google_drive_service import stream_file_from_drive
        fh, mime_type = stream_file_from_drive(drive_id)
        download_name = f"{session.get('session_label', 'session')}_results.zip"
        return send_file(fh, as_attachment=True, download_name=download_name, mimetype=mime_type)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@utils_routes.route('/download-trained-model', methods=['GET'])
@token_required(optional=True)
def download_model(current_user):
    model_path = get_model_path(request)
    import os
    if not os.path.exists(model_path):
        return jsonify({"error": "Trained model file not found on server. Please train a new model."}), 404
        
    download_name = os.path.basename(model_path)
    return send_file(model_path, as_attachment=True, download_name=download_name)

@utils_routes.route('/download-model-predictions', methods=['GET'])
@token_required(optional=True)
def download_model_predictions(current_user):
    model_path = get_model_predictions(request)
    return send_file(model_path, as_attachment=True)

@utils_routes.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    results = handle_upload_file(request, current_user['_id'])

    return jsonify(results)

@utils_routes.route('/feedback', methods=['POST'])
@token_required
def submit_feedback(current_user):
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
            
        from mongoDb.connection import get_db
        import datetime
        db = get_db()
        db.feedback.insert_one({
            "user_id": current_user['_id'],
            "email": current_user.get('email'),
            "message": data['message'],
            "type": data.get('type', 'general'),
            "created_at": datetime.datetime.utcnow()
        })
        return jsonify({"message": "Feedback submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@utils_routes.route('/models/info', methods=['GET'])
def get_models_info():
    try:
        from mongoDb.connection import get_db
        db = get_db()
        models = list(db.models.find({}, {'_id': 0}))
        # Sort or just return as is
        return jsonify(models), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@utils_routes.route('/datasets/default', methods=['GET'])
def list_default_datasets_public():
    try:
        from mongoDb.connection import get_db
        db = get_db()
        datasets = list(db.datasets.find({"is_default": True}))
        for d in datasets:
            d['_id'] = str(d['_id'])
        return jsonify({"datasets": datasets}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@utils_routes.route('/datasets/<dataset_id>', methods=['DELETE'])
@token_required
def delete_user_dataset(current_user, dataset_id):
    try:
        from mongoDb.connection import get_db
        from bson import ObjectId
        from services.google_drive_service import delete_file_from_drive
        db = get_db()
        
        # Verify ownership
        dataset = db.datasets.find_one({'_id': ObjectId(dataset_id), 'user_id': current_user['_id']})
        if not dataset:
            return jsonify({"error": "Dataset not found or unauthorized"}), 404
            
        # Delete from Google Drive if it exists there
        if dataset.get('drive_id'):
            delete_file_from_drive(dataset['drive_id'])
            
        # Remove DB record
        db.datasets.delete_one({'_id': ObjectId(dataset_id)})
        return jsonify({"message": "Dataset deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@utils_routes.route('/datasets/preprocess', methods=['POST'])
@token_required
def preprocess_cloud_dataset(current_user):
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        operations = data.get('operations')
        
        if not dataset_id or not operations or not isinstance(operations, list):
            return jsonify({"error": "dataset_id and an array of operations are required"}), 400
            
        from services.preprocessing_service import perform_preprocessing
        new_dataset = perform_preprocessing(current_user, dataset_id, operations)
        
        # ensure _id is stringified for JSON compatibility
        new_dataset['_id'] = str(new_dataset['_id'])
        
        return jsonify({"message": "Preprocessing complete", "dataset": new_dataset}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@utils_routes.route('/datasets/<dataset_id>/preview', methods=['GET'])
@token_required
def preview_dataset(current_user, dataset_id):
    """Preview a dataset — CSV returns first 50 rows, ZIP returns folder structure and image lists."""
    try:
        from services.dataset_service import get_dataset
        dataset = get_dataset(dataset_id)

        # Verify ownership (allow default datasets too)
        if dataset.get('user_id') and dataset['user_id'] != current_user['_id']:
            if not dataset.get('is_default'):
                return jsonify({"error": "Unauthorized"}), 403

        drive_id = dataset.get('drive_id')
        file_type = dataset.get('file_type', 'other')
        filename = dataset.get('filename', '')

        if file_type == 'csv':
            return _preview_csv(dataset, drive_id)
        elif file_type == 'zip':
            return _preview_zip(dataset, drive_id, filename)
        else:
            return jsonify({"preview_type": "unsupported", "message": f"Preview not available for file type: {file_type}"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def _preview_csv(dataset, drive_id):
    """Return all rows of a CSV dataset."""
    import pandas as pd
    import io
    
    df = None
    
    # Try Drive first
    if drive_id:
        try:
            from services.google_drive_service import stream_file_from_drive
            fh, _ = stream_file_from_drive(drive_id)
            df = pd.read_csv(fh)
        except Exception as e:
            print(f"Drive preview failed: {e}")
    
    # Fallback to csv_data stored in DB
    if df is None and dataset.get('csv_data'):
        csv_data = dataset['csv_data']
        return jsonify({
            "preview_type": "csv",
            "columns": list(csv_data[0].keys()) if csv_data else [],
            "rows": csv_data,
            "total_rows_shown": len(csv_data)
        }), 200
    
    # Fallback to local file
    if df is None:
        filepath = dataset.get('filepath')
        if filepath:
            import os
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
    
    if df is not None:
        # Replace NaN with None for JSON serialization
        df = df.where(pd.notnull(df), None)
        rows = df.to_dict(orient='records')
        return jsonify({
            "preview_type": "csv",
            "columns": list(df.columns),
            "rows": rows,
            "total_rows_shown": len(rows)
        }), 200
    
    return jsonify({"preview_type": "csv", "error": "Could not load preview data"}), 200


def _preview_zip(dataset, drive_id, filename):
    """Return folder structure and image thumbnails from a ZIP dataset.
    
    Uses resolve_image_dataset_path to download from Google Drive and extract
    locally (with caching), then reads from the extracted directory for reliable
    thumbnail generation.
    """
    import os
    
    user_id = dataset.get('user_id')
    
    # --- Strategy: resolve to a local extracted directory ---
    # This downloads from Drive if needed, extracts, and caches locally.
    try:
        from services.dataset_resolver import resolve_image_dataset_path
        extracted_path = resolve_image_dataset_path(
            user_id, filename=filename, file_path=dataset.get('filepath')
        )
        if extracted_path and os.path.isdir(extracted_path):
            return _preview_local_directory(extracted_path)
    except Exception as e:
        print(f"Dataset resolution failed for preview: {e}")
    
    # Fallback: try extracted_path from DB directly
    extracted_path = dataset.get('extracted_path')
    if extracted_path and os.path.isdir(extracted_path):
        return _preview_local_directory(extracted_path)
    
    # Fallback: try the original filepath
    filepath = dataset.get('filepath')
    if filepath and os.path.isdir(filepath):
        return _preview_local_directory(filepath)
    
    # Last resort: try in-memory ZIP processing from Drive
    if drive_id or (filepath and os.path.exists(filepath)):
        return _preview_zip_stream(dataset, drive_id, filename)
    
    return jsonify({"preview_type": "zip", "error": "Could not load dataset for preview. Try re-uploading."}), 200


def _preview_zip_stream(dataset, drive_id, filename):
    """Fallback: preview ZIP via in-memory streaming (used when extraction fails)."""
    import zipfile
    import io
    import os
    import base64
    from PIL import Image
    
    zip_stream = None
    
    if drive_id:
        try:
            from services.google_drive_service import stream_file_from_drive
            fh, _ = stream_file_from_drive(drive_id)
            zip_stream = fh
        except Exception as e:
            print(f"Drive ZIP stream failed: {e}")
    
    if zip_stream is None:
        filepath = dataset.get('filepath')
        if filepath and os.path.exists(filepath):
            zip_stream = open(filepath, 'rb')
    
    if zip_stream is None:
        return jsonify({"preview_type": "zip", "error": "Could not load ZIP for preview"}), 200
    
    try:
        with zipfile.ZipFile(zip_stream, 'r') as zf:
            all_entries = zf.namelist()
            
            # Detect common root folder to strip
            real_entries = [e for e in all_entries
                           if not e.startswith('__MACOSX') and not e.split('/')[-1].startswith('.')]
            common_prefix = ''
            if real_entries:
                parts_list = [e.split('/') for e in real_entries]
                if all(len(p) > 1 for p in parts_list):
                    first_part = parts_list[0][0]
                    if first_part and all(p[0] == first_part for p in parts_list):
                        common_prefix = first_part + '/'
            
            def strip_prefix(path):
                if common_prefix and path.startswith(common_prefix):
                    return path[len(common_prefix):]
                return path
            
            folders = set()
            files_by_folder = {}
            image_files = []
            IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
            
            for entry in all_entries:
                if '__MACOSX' in entry:
                    continue
                normalized = strip_prefix(entry)
                if not normalized:
                    continue
                if entry.endswith('/'):
                    if normalized.rstrip('/'):
                        folders.add(normalized)
                    continue
                basename = os.path.basename(normalized)
                if basename.startswith('.') or basename.startswith('__'):
                    continue
                parent = os.path.dirname(normalized)
                parent_key = parent + '/' if parent else ''
                if parent_key not in files_by_folder:
                    files_by_folder[parent_key] = []
                files_by_folder[parent_key].append(basename)
                parts = parent.split('/') if parent else []
                for depth in range(1, len(parts) + 1):
                    folders.add('/'.join(parts[:depth]) + '/')
                ext = os.path.splitext(entry)[1].lower()
                if ext in IMAGE_EXTS:
                    image_files.append((entry, normalized))
            
            # Generate ALL thumbnails (no limit)
            images_by_folder = {}
            for orig_path, norm_path in image_files:
                parent = os.path.dirname(norm_path)
                parent_key = parent + '/' if parent else ''
                if parent_key not in images_by_folder:
                    images_by_folder[parent_key] = []
                images_by_folder[parent_key].append((orig_path, norm_path))
            
            image_thumbnails = []
            for folder_key in sorted(images_by_folder.keys()):
                for orig_path, norm_path in images_by_folder[folder_key]:
                    try:
                        with zf.open(orig_path) as img_file:
                            img = Image.open(img_file)
                            img.thumbnail((150, 150))
                            buf = io.BytesIO()
                            img.save(buf, format='JPEG', quality=70)
                            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                            image_thumbnails.append({
                                "path": norm_path,
                                "data": f"data:image/jpeg;base64,{b64}"
                            })
                    except Exception as e:
                        print(f"Thumbnail generation failed for {orig_path}: {e}")
            
            return jsonify({
                "preview_type": "zip",
                "folder_tree": sorted(list(folders)),
                "files_by_folder": {k: sorted(v) for k, v in files_by_folder.items()},
                "total_files": sum(len(v) for v in files_by_folder.values()),
                "total_images": len(image_files),
                "csv_previews": [],
                "image_thumbnails": image_thumbnails
            }), 200
            
    except zipfile.BadZipFile:
        return jsonify({"preview_type": "zip", "error": "Invalid ZIP file"}), 200
    finally:
        if hasattr(zip_stream, 'close'):
            zip_stream.close()


def _preview_local_directory(dir_path):
    """Preview an extracted directory (cached image dataset).
    Generates thumbnails for ALL images (no limit) in every folder."""
    import os
    import io
    import base64
    from PIL import Image
    
    folders = set()
    files_by_folder = {}
    images_by_folder = {}  # folder_key -> [(rel_path, abs_path), ...]
    csv_files = []
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    
    for root, dirs, files in os.walk(dir_path):
        rel_root = os.path.relpath(root, dir_path).replace('\\', '/')
        if rel_root == '.':
            folder_key = ''
        else:
            folder_key = rel_root + '/'
            # Add this folder and all ancestors
            parts = rel_root.split('/')
            for depth in range(1, len(parts) + 1):
                folders.add('/'.join(parts[:depth]) + '/')
        
        file_list = []
        for f in files:
            if f.startswith('.') or f.startswith('__'):
                continue
            file_list.append(f)
            abs_path = os.path.join(root, f)
            rel_path = os.path.relpath(abs_path, dir_path).replace('\\', '/')
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTS:
                if folder_key not in images_by_folder:
                    images_by_folder[folder_key] = []
                images_by_folder[folder_key].append((rel_path, abs_path))
            elif ext == '.csv':
                csv_files.append(abs_path)
        
        if file_list:
            files_by_folder[folder_key] = sorted(file_list)
    
    # Generate thumbnails for ALL images (no limit)
    image_thumbnails = []
    for folder_key in sorted(images_by_folder.keys()):
        for rel_path, abs_path in images_by_folder[folder_key]:
            try:
                img = Image.open(abs_path)
                img.thumbnail((150, 150))
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=70)
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                image_thumbnails.append({
                    "path": rel_path,
                    "data": f"data:image/jpeg;base64,{b64}"
                })
            except Exception:
                pass
    total_images = sum(len(v) for v in images_by_folder.values())
    return jsonify({
        "preview_type": "zip",
        "folder_tree": sorted(list(folders)),
        "files_by_folder": {k: sorted(v) for k, v in files_by_folder.items()},
        "total_files": sum(len(v) for v in files_by_folder.values()),
        "total_images": total_images,
        "csv_previews": [],
        "image_thumbnails": image_thumbnails
    }), 200


@utils_routes.route('/datasets/versions/<filename>', methods=['GET'])
@token_required
def get_versions(current_user, filename):
    """Get all versions of a dataset by filename."""
    try:
        from services.dataset_service import get_dataset_versions
        versions = get_dataset_versions(current_user['_id'], filename)
        return jsonify({"versions": versions}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@utils_routes.route('/datasets/<dataset_id>/folder-images', methods=['GET'])
@token_required
def get_folder_images(current_user, dataset_id):
    """On-demand thumbnail loading for a specific folder within a ZIP dataset.
    
    Uses resolve_image_dataset_path to download from Drive and extract locally
    (with caching), then reads images from the filesystem for reliability.
    
    Query params:
        folder: the folder path to load images from (e.g. 'test/cats/')
    Returns ALL base64-encoded thumbnails for images in that folder.
    """
    try:
        import io
        import os
        import base64
        from PIL import Image
        from services.dataset_service import get_dataset
        
        dataset = get_dataset(dataset_id)
        
        # Verify ownership
        if dataset.get('user_id') and dataset['user_id'] != current_user['_id']:
            if not dataset.get('is_default'):
                return jsonify({"error": "Unauthorized"}), 403
        
        folder = request.args.get('folder', '')
        IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        
        # Resolve dataset to a local extracted directory
        # This downloads from Drive if needed, extracts, and caches.
        resolved_path = None
        try:
            from services.dataset_resolver import resolve_image_dataset_path
            resolved_path = resolve_image_dataset_path(
                dataset.get('user_id'),
                filename=dataset.get('filename'),
                file_path=dataset.get('filepath')
            )
        except Exception as e:
            print(f"Dataset resolution failed for folder-images: {e}")
        
        # Fallback to extracted_path from DB
        if not resolved_path or not os.path.isdir(resolved_path):
            extracted_path = dataset.get('extracted_path')
            if extracted_path and os.path.isdir(extracted_path):
                resolved_path = extracted_path
        
        if not resolved_path or not os.path.isdir(resolved_path):
            return jsonify({"thumbnails": [], "error": "Could not resolve dataset to local directory"}), 200
        
        # Read images from the specific folder
        target_dir = os.path.join(resolved_path, folder.rstrip('/')) if folder else resolved_path
        if not os.path.isdir(target_dir):
            return jsonify({"thumbnails": [], "error": f"Folder not found: {folder}"}), 200
        
        thumbnails = []
        files = [f for f in os.listdir(target_dir)
                 if os.path.splitext(f)[1].lower() in IMAGE_EXTS
                 and not f.startswith('.') and not f.startswith('__')]
        
        for fname in sorted(files):
            try:
                abs_path = os.path.join(target_dir, fname)
                img = Image.open(abs_path)
                img.thumbnail((150, 150))
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=70)
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                rel_path = (folder + fname) if folder else fname
                thumbnails.append({
                    "path": rel_path,
                    "data": f"data:image/jpeg;base64,{b64}"
                })
            except Exception:
                pass
        
        return jsonify({"thumbnails": thumbnails}), 200
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@utils_routes.route('/datasets/save-annotations', methods=['POST'])
@token_required
def save_annotations(current_user):
    """Save annotated dataset ZIP to Google Drive with versioning."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        filename = file.filename or 'annotations.zip'
        
        # Get annotation metadata
        label_classes = request.form.get('label_classes', '[]')
        image_count = request.form.get('image_count', '0')
        
        from services.google_drive_service import upload_file_to_drive
        from services.dataset_service import save_dataset
        
        # Upload to Drive under annotations subfolder
        drive_res = upload_file_to_drive(
            file, filename,
            folder_type='datasets',
            user_id=current_user['_id'],
            subfolder='annotations'
        )

        # Save to DB with annotation metadata
        dataset = save_dataset(
            current_user['_id'], filename, '',
            file_type='annotated_zip',
            drive_id=drive_res.get('id')
        )
        
        from mongoDb.connection import get_db
        db = get_db()
        from bson import ObjectId
        db.datasets.update_one(
            {'_id': ObjectId(dataset['_id'])},
            {'$set': {
                'annotation_meta': {
                    'label_classes': label_classes,
                    'image_count': int(image_count)
                }
            }}
        )

        return jsonify({
            "message": "Annotations saved successfully",
            "dataset_id": dataset['_id'],
            "version": dataset.get('version', 1),
            "drive_id": drive_res.get('id')
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
