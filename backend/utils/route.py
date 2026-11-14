import logging

from flask import Blueprint, request, send_file, jsonify
from utils.downloadFiles import get_model_path
from utils.uploadFiles import handle_upload_file
from services.model_catalog import get_model_catalog, get_catalog_from_db, MODEL_CATALOG_VERSION

utils_routes = Blueprint('utils_routes', __name__)
log = logging.getLogger(__name__)

from auth.auth_middleware import token_required
from extensions import limiter
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
@token_required
def download_model(current_user):
    import os
    try:
        model_path = get_model_path(request, current_user)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not os.path.exists(model_path):
        return jsonify({"error": "Trained model file not found on server. Please train a new model."}), 404

    download_name = os.path.basename(model_path)
    return send_file(model_path, as_attachment=True, download_name=download_name)

@utils_routes.route('/download-model-predictions/<session_id>', methods=['GET'])
@token_required
def download_model_predictions_session(current_user, session_id):
    """Download a session's predictions CSV — owner-scoped, served from Drive.

    Replaces the old query-param route that read a GLOBAL predictions/<model>.csv
    with no ownership check (any user could fetch the last predictions for a
    model type). Predictions are now uploaded per session like the trained model.
    """
    try:
        session = get_session(session_id)
        if session['user_id'] != current_user['_id']:
            return jsonify({"error": "Unauthorized"}), 403

        drive_id = session.get('predictions_drive_id')
        if not drive_id:
            return jsonify({"error": "Predictions not available for this session."}), 404

        from services.google_drive_service import stream_file_from_drive
        fh, mime_type = stream_file_from_drive(drive_id)
        download_name = session.get('predictions_filename') or f"{session.get('session_label', 'model')}_predictions.csv"
        return send_file(fh, as_attachment=True, download_name=download_name, mimetype=mime_type)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@utils_routes.route('/upload', methods=['POST'])
@limiter.limit("30 per hour")
@token_required
def upload_file(current_user):
    from config import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB

    # Reject oversized uploads early (Content-Length is set by the browser for
    # multipart bodies). This is a cheap guard before we stream to Drive.
    try:
        if request.content_length and request.content_length > MAX_UPLOAD_SIZE_BYTES:
            return jsonify({
                "error": f"File too large. Max upload size is {MAX_UPLOAD_SIZE_MB} MB."
            }), 413
    except Exception:
        pass

    # Enforce per-plan storage cap (no-op unless SUBSCRIPTION_ENABLED).
    from services.subscription_service import check_storage_quota
    ok, info = check_storage_quota(current_user, additional=1)
    if not ok:
        return jsonify(info), 429

    body, status = handle_upload_file(request, current_user['_id'])
    return jsonify(body), status


_FEEDBACK_TYPES = {'general', 'bug', 'feature', 'model', 'billing', 'other'}


@utils_routes.route('/feedback', methods=['POST'])
@limiter.limit("10 per hour")
@token_required
def submit_feedback(current_user):
    from utils.validators import clean_str, ValidationError
    data = request.get_json(silent=True) or {}
    try:
        message = clean_str(data.get('message'), 'message', max_len=5000, required=True)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    ftype = data.get('type') if data.get('type') in _FEEDBACK_TYPES else 'general'

    from mongoDb.connection import get_db
    import datetime
    get_db().feedback.insert_one({
        "user_id": current_user['_id'],
        "email": current_user.get('email'),
        "message": message,
        "type": ftype,
        "resolved": False,
        "created_at": datetime.datetime.utcnow(),
    })
    return jsonify({"message": "Feedback submitted successfully"}), 201

@utils_routes.route('/models/info', methods=['GET'])
def get_models_info():
    """Rich model info for the in-app info drawer (ModelInfoPanel).

    Reads the structured catalog from the MongoDB `models` collection (the
    runtime source of truth, seeded by migration 004). Each document's
    `description` is an ARRAY of sections — which is what the drawer renders.
    get_catalog_from_db() transparently falls back to the in-code catalog if the
    DB is empty/unavailable; the flat registry is a last-resort fallback.
    """
    try:
        resp = jsonify(get_catalog_from_db())
        resp.headers['Cache-Control'] = 'public, max-age=600'
        return resp, 200
    except Exception:
        try:
            from services.model_registry import get_model_registry
            registry = get_model_registry()
            return jsonify(list(registry['models'].values())), 200
        except Exception:
            return jsonify({"error": "Failed to load model info"}), 500


@utils_routes.route('/config', methods=['GET'])
def public_config():
    """Public runtime config the SPA reads on startup (no auth).

    Exposes feature flags that must be toggleable without rebuilding the
    frontend bundle (CRA bakes process.env at build time, so flags can't ride
    in there). Currently just the subscription master switch.
    """
    from config import SUBSCRIPTION_ENABLED
    return jsonify({"subscription_enabled": SUBSCRIPTION_ENABLED}), 200


@utils_routes.route('/models/registry', methods=['GET'])
def get_model_registry_route():
    """
    Dynamic model registry endpoint.
    Returns complete metadata for all models including categories,
    endpoints, streaming info, file extensions, and component import paths.
    This is the single source of truth for the frontend — add a model to
    services/model_registry.py and it automatically appears everywhere.
    """
    try:
        from services.model_registry import get_model_registry
        resp = jsonify(get_model_registry())
        resp.headers['Cache-Control'] = 'public, max-age=600'
        return resp, 200
    except Exception:
        log.exception("Model registry failed")
        return jsonify({"error": "Failed to load model registry"}), 500

@utils_routes.route('/datasets/default', methods=['GET'])
def list_default_datasets_public():
    try:
        from mongoDb.connection import get_db
        db = get_db()
        # Public endpoint: never expose inline samples, local paths or owner ids.
        datasets = list(db.datasets.find(
            {"is_default": True},
            {"csv_data": 0, "image_links": 0, "filepath": 0, "extracted_path": 0, "user_id": 0},
        ))
        for d in datasets:
            d['_id'] = str(d['_id'])
        resp = jsonify({"datasets": datasets})
        resp.headers['Cache-Control'] = 'public, max-age=300'
        return resp, 200
    except Exception:
        return jsonify({"error": "Failed to load default datasets"}), 500


@utils_routes.route('/datasets/<dataset_id>', methods=['DELETE'])
@token_required
def delete_user_dataset(current_user, dataset_id):
    import os
    import shutil
    from mongoDb.connection import get_db
    from bson import ObjectId
    from utils.validators import is_object_id
    from config import get_user_extract_cache_dir

    if not is_object_id(dataset_id):
        return jsonify({"error": "Dataset not found"}), 404
    db = get_db()
    dataset = db.datasets.find_one({'_id': ObjectId(dataset_id), 'user_id': current_user['_id']})
    if not dataset:
        return jsonify({"error": "Dataset not found or unauthorized"}), 404
    if dataset.get('is_default'):
        return jsonify({"error": "This dataset is part of the public library; ask an admin to remove it."}), 409

    if dataset.get('drive_id'):
        try:
            from services.google_drive_service import delete_file_from_drive
            delete_file_from_drive(dataset['drive_id'])
        except Exception as e:
            log.warning("Drive delete failed for dataset %s: %s", dataset_id, e)

    # Drop the extracted image cache for this version, if any.
    if dataset.get('file_type') == 'zip':
        from werkzeug.utils import secure_filename
        base = secure_filename(os.path.splitext(dataset.get('filename', ''))[0])
        cache = os.path.join(get_user_extract_cache_dir(current_user['_id']), f"{base}_v{dataset.get('version', 1)}")
        if base and os.path.isdir(cache):
            shutil.rmtree(cache, ignore_errors=True)

    db.datasets.delete_one({'_id': ObjectId(dataset_id)})
    return jsonify({"message": "Dataset deleted successfully"}), 200

@utils_routes.route('/datasets/preprocess', methods=['POST'])
@token_required
def preprocess_cloud_dataset(current_user):
    try:
        data = request.get_json()
        dataset_id = data.get('dataset_id')
        operations = data.get('operations')
        
        if not dataset_id or not operations or not isinstance(operations, list):
            return jsonify({"error": "dataset_id and an array of operations are required"}), 400

        # Enforce Data Studio quota (no-op unless SUBSCRIPTION_ENABLED). Data
        # Studio runs are metered under the 'datastudio' class.
        from services.subscription_service import check_quota, record_usage, check_storage_quota
        ok, info = check_quota(current_user, 'datastudio')
        if not ok:
            return jsonify(info), 429
        # Preprocessing creates a NEW dataset — make sure there's room.
        ok_store, store_info = check_storage_quota(current_user, additional=1)
        if not ok_store:
            return jsonify(store_info), 429

        from services.preprocessing_service import perform_preprocessing
        new_dataset = perform_preprocessing(current_user, dataset_id, operations)
        record_usage(current_user['_id'], 'datastudio')
        
        # ensure _id is stringified for JSON compatibility
        new_dataset['_id'] = str(new_dataset['_id'])
        
        return jsonify({"message": "Preprocessing complete", "dataset": new_dataset}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── Data Profiling ──────────────────────────────────────────────────────

@utils_routes.route('/datasets/<dataset_id>/profile', methods=['GET'])
@token_required
def profile_dataset_route(current_user, dataset_id):
    """Generate a comprehensive data quality profile for a CSV dataset."""
    try:
        from services.preprocessing_service import profile_dataset
        profile = profile_dataset(current_user['_id'], dataset_id)
        return jsonify(profile), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@utils_routes.route('/datasets/diff', methods=['POST'])
@token_required
def diff_datasets_route(current_user):
    """Compare two datasets side-by-side."""
    try:
        data = request.get_json()
        id_a = data.get('dataset_id_a')
        id_b = data.get('dataset_id_b')
        if not id_a or not id_b:
            return jsonify({"error": "Both dataset_id_a and dataset_id_b are required"}), 400
        from services.preprocessing_service import diff_datasets
        result = diff_datasets(current_user['_id'], id_a, id_b)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Pipeline Management ─────────────────────────────────────────────────

@utils_routes.route('/pipelines/templates', methods=['GET'])
def get_pipeline_templates_route():
    """Get built-in pipeline templates."""
    try:
        from services.preprocessing_service import get_pipeline_templates
        return jsonify(get_pipeline_templates()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@utils_routes.route('/pipelines', methods=['GET'])
@token_required
def list_pipelines_route(current_user):
    """List all saved pipelines for the current user."""
    try:
        from services.preprocessing_service import list_pipelines
        return jsonify(list_pipelines(current_user['_id'])), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@utils_routes.route('/pipelines', methods=['POST'])
@token_required
def save_pipeline_route(current_user):
    """Save a named preprocessing pipeline."""
    try:
        data = request.get_json()
        name = data.get('name')
        operations = data.get('operations', [])
        if not name:
            return jsonify({"error": "Pipeline name is required"}), 400
        from services.preprocessing_service import save_pipeline
        pid = save_pipeline(current_user['_id'], name, operations)
        return jsonify({"message": "Pipeline saved", "pipeline_id": pid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@utils_routes.route('/pipelines/<pipeline_name>', methods=['GET'])
@token_required
def load_pipeline_route(current_user, pipeline_name):
    """Load a saved pipeline by name."""
    try:
        from services.preprocessing_service import load_pipeline
        ops = load_pipeline(current_user['_id'], pipeline_name)
        return jsonify({"name": pipeline_name, "operations": ops}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@utils_routes.route('/pipelines/<pipeline_name>', methods=['DELETE'])
@token_required
def delete_pipeline_route(current_user, pipeline_name):
    """Delete a saved pipeline."""
    try:
        from services.preprocessing_service import delete_pipeline
        delete_pipeline(current_user['_id'], pipeline_name)
        return jsonify({"message": f"Pipeline '{pipeline_name}' deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@utils_routes.route('/datasets/<dataset_id>/preview', methods=['GET'])
@token_required
def preview_dataset(current_user, dataset_id):
    """Preview a dataset the user can access.

    CSV: a page of rows (?offset=&limit=, capped at CSV_PREVIEW_MAX_ROWS) plus
    the total row count. The old version returned EVERY row of the file, which
    froze the browser on large datasets.
    ZIP: folder structure and up to MAX_PREVIEW_THUMBNAILS thumbnails; more are
    loaded per folder via /folder-images.
    """
    from services.dataset_service import get_accessible_dataset
    dataset = get_accessible_dataset(current_user['_id'], dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    file_type = dataset.get('file_type', 'other')
    try:
        if file_type == 'csv':
            return _preview_csv(dataset)
        if file_type == 'zip':
            return _preview_zip(current_user['_id'], dataset)
    except FileNotFoundError as e:
        return jsonify({"preview_type": file_type, "error": str(e)}), 200
    except Exception:
        log.exception("Preview failed for dataset %s", dataset_id)
        return jsonify({"preview_type": file_type, "error": "Could not load preview data"}), 200
    return jsonify({"preview_type": "unsupported",
                    "message": f"Preview not available for file type: {file_type}"}), 200


def _int_arg(name, default, lo, hi):
    try:
        return max(lo, min(hi, int(request.args.get(name, default))))
    except (TypeError, ValueError):
        return default


def _preview_csv(dataset):
    """Return one page of a CSV dataset's rows."""
    import pandas as pd
    from config import CSV_PREVIEW_MAX_ROWS
    from services.dataset_service import load_dataset_df

    limit = _int_arg('limit', CSV_PREVIEW_MAX_ROWS, 1, CSV_PREVIEW_MAX_ROWS)
    offset = _int_arg('offset', 0, 0, 10**9)
    try:
        df = load_dataset_df(dataset)
    except FileNotFoundError:
        sample = dataset.get('csv_data') or []
        return jsonify({
            "preview_type": "csv",
            "columns": list(sample[0].keys()) if sample else [],
            "rows": sample[:limit],
            "total_rows_shown": min(len(sample), limit),
            "total_rows": dataset.get('row_count', len(sample)),
            "offset": 0, "limit": limit, "partial": True,
        }), 200

    page = df.iloc[offset:offset + limit]
    page = page.astype(object).where(pd.notnull(page), None)
    rows = page.to_dict(orient='records')
    return jsonify({
        "preview_type": "csv",
        "columns": [str(c) for c in df.columns],
        "rows": rows,
        "total_rows_shown": len(rows),
        "total_rows": int(len(df)),
        "offset": offset,
        "limit": limit,
    }), 200


_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}


def _thumbnail(abs_path, rel_path):
    """150px JPEG thumbnail as a data URL, or None if the image can't be read."""
    import io
    import base64
    from PIL import Image
    try:
        with Image.open(abs_path) as img:
            img.thumbnail((150, 150))
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=70)
        return {"path": rel_path, "data": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('ascii')}
    except Exception:
        return None


def _preview_zip(user_id, dataset):
    """Folder tree + a capped set of thumbnails from the extracted dataset."""
    import os
    from config import MAX_PREVIEW_THUMBNAILS
    from services.dataset_resolver import resolve_image_dataset_path

    root = resolve_image_dataset_path(user_id, dataset=dataset)
    folders, files_by_folder, images = set(), {}, []
    for cur, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(('.', '__')))
        rel_root = os.path.relpath(cur, root).replace('\\', '/')
        key = '' if rel_root == '.' else rel_root + '/'
        if key:
            parts = rel_root.split('/')
            for depth in range(1, len(parts) + 1):
                folders.add('/'.join(parts[:depth]) + '/')
        visible = sorted(f for f in files if not f.startswith(('.', '__')))
        if visible:
            files_by_folder[key] = visible
        for f in visible:
            if os.path.splitext(f)[1].lower() in _IMAGE_EXTS:
                images.append((key + f, os.path.join(cur, f)))

    # Spread the thumbnail budget across folders (classes) so every class is
    # represented instead of the first folder eating the whole budget.
    per_folder = {}
    for rel, abs_path in images:
        per_folder.setdefault(os.path.dirname(rel), []).append((rel, abs_path))
    quota = max(1, MAX_PREVIEW_THUMBNAILS // max(1, len(per_folder)))
    thumbs = []
    for folder in sorted(per_folder):
        for rel, abs_path in per_folder[folder][:quota]:
            t = _thumbnail(abs_path, rel)
            if t:
                thumbs.append(t)
            if len(thumbs) >= MAX_PREVIEW_THUMBNAILS:
                break

    return jsonify({
        "preview_type": "zip",
        "folder_tree": sorted(folders),
        "files_by_folder": files_by_folder,
        "total_files": sum(len(v) for v in files_by_folder.values()),
        "total_images": len(images),
        "csv_previews": [],
        "image_thumbnails": thumbs,
        "thumbnails_truncated": len(thumbs) < len(images),
    }), 200


@utils_routes.route('/datasets/versions/<filename>', methods=['GET'])
@token_required
def get_versions(current_user, filename):
    """Get all versions of a dataset by filename."""
    from services.dataset_service import get_dataset_versions
    return jsonify({"versions": get_dataset_versions(current_user['_id'], filename)}), 200


@utils_routes.route('/datasets/<dataset_id>/folder-images', methods=['GET'])
@token_required
def get_folder_images(current_user, dataset_id):
    """Thumbnails for one folder of a ZIP dataset, paginated.

    Query: folder (e.g. 'train/cats/'), offset, limit (max 200).
    The folder is confined to the dataset root — it used to be joined
    unchecked, so '../..' listed images anywhere on the server.
    """
    import os
    from services.dataset_service import get_accessible_dataset
    from services.dataset_resolver import resolve_image_dataset_path

    dataset = get_accessible_dataset(current_user['_id'], dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    try:
        root = os.path.realpath(resolve_image_dataset_path(current_user['_id'], dataset=dataset))
    except FileNotFoundError as e:
        return jsonify({"thumbnails": [], "error": str(e)}), 200

    folder = (request.args.get('folder') or '').strip().lstrip('/\\')
    target = os.path.realpath(os.path.join(root, folder))
    if target != root and not target.startswith(root + os.sep):
        return jsonify({"error": "Invalid folder"}), 400
    if not os.path.isdir(target):
        return jsonify({"thumbnails": [], "error": "Folder not found"}), 200

    offset = _int_arg('offset', 0, 0, 10**9)
    limit = _int_arg('limit', 60, 1, 200)
    names = sorted(
        f for f in os.listdir(target)
        if os.path.splitext(f)[1].lower() in _IMAGE_EXTS and not f.startswith(('.', '__'))
    )
    prefix = folder if (not folder or folder.endswith('/')) else folder + '/'
    thumbs = [t for t in (_thumbnail(os.path.join(target, n), prefix + n)
                          for n in names[offset:offset + limit]) if t]
    return jsonify({
        "thumbnails": thumbs,
        "total": len(names),
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < len(names),
    }), 200


@utils_routes.route('/datasets/save-annotations', methods=['POST'])
@token_required
def save_annotations(current_user):
    """Save annotated dataset to Google Drive with proper versioning and provenance.
    
    Uses a stable base name derived from `dataset_name` form field so repeated
    saves to the same project create versioned records (v1, v2, v3...) instead
    of scattergun timestamp-based filenames.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        # NOTE: `datetime` must be imported before first use — it used to be
        # imported below the else-branch that needs it, so saving without a
        # dataset name always crashed with UnboundLocalError.
        from datetime import datetime
        from werkzeug.utils import secure_filename
        from services.google_drive_service import upload_file_to_drive
        from services.dataset_service import save_dataset, get_accessible_dataset

        file = request.files['file']
        label_classes = request.form.get('label_classes', '[]')[:10000]
        try:
            image_count = max(0, int(request.form.get('image_count', '0')))
        except (TypeError, ValueError):
            image_count = 0
        dataset_name = request.form.get('dataset_name', '').strip()[:120]
        source_dataset_id = request.form.get('source_dataset_id', '').strip()
        if source_dataset_id and not get_accessible_dataset(current_user['_id'], source_dataset_id, {'_id': 1}):
            source_dataset_id = ''

        # Build a stable, human-readable base filename for version grouping
        base = secure_filename(
            dataset_name.replace(' ', '_').replace('.zip', '').replace('.csv', '')
        ) if dataset_name else ''
        if base:
            filename = f"{base}_annotated.json"
        else:
            filename = f"annotations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Upload to Drive under annotations subfolder (per-user isolated)
        drive_res = upload_file_to_drive(
            file, filename,
            folder_type='datasets',
            user_id=current_user['_id'],
            subfolder='annotations'
        )

        # save_dataset auto-increments version for this (user_id, filename) pair
        dataset = save_dataset(
            current_user['_id'], filename, '',
            file_type='annotated_json',
            drive_id=drive_res.get('id')
        )

        # Attach annotation metadata + provenance
        from mongoDb.connection import get_db
        from bson import ObjectId
        db = get_db()

        update_doc = {
            'annotation_meta': {
                'label_classes': label_classes,
                'image_count': int(image_count),
            },
            'dataset_name': dataset_name if dataset_name else None,
        }
        if source_dataset_id:
            update_doc['source_dataset_id'] = source_dataset_id
            try:
                src = db.datasets.find_one({'_id': ObjectId(source_dataset_id)}, {'filename': 1})
                if src:
                    update_doc['source_filename'] = src.get('filename')
            except Exception:
                pass

        db.datasets.update_one(
            {'_id': ObjectId(dataset['_id'])},
            {'$set': update_doc}
        )

        return jsonify({
            "message": "Annotations saved successfully",
            "dataset_id": dataset['_id'],
            "filename": filename,
            "version": dataset.get('version', 1),
            "drive_id": drive_res.get('id'),
            "provenance": {
                "source_dataset_id": source_dataset_id or None,
                "source_filename": update_doc.get('source_filename'),
            }
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
