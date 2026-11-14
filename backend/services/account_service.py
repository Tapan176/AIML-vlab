"""
Account-level data management: full export, storage summary, cascade delete,
and session revocation.

Before this module existed, deleting an account removed only the `users`
document. Every dataset, trained model, results zip and prediction file stayed
in Google Drive (and in MongoDB) forever with no owner, which is both a
storage leak and a privacy problem. `purge_user_data` removes everything the
user owns; billing records (`invoices`) are retained for accounting but
detached from the deleted identity.
"""
import os
import shutil
from datetime import datetime

from bson import ObjectId

from mongoDb.connection import get_db
from auth.auth_middleware import invalidate_user_cache


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _jsonable(doc, drop=()):
    out = {}
    for k, v in doc.items():
        if k in drop:
            continue
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = _jsonable(v)
        elif isinstance(v, list):
            out[k] = [_jsonable(i) if isinstance(i, dict) else (str(i) if isinstance(i, ObjectId) else _iso(i)) for i in v]
        else:
            out[k] = v
    return out


def revoke_all_sessions(user_id):
    """Invalidate every JWT issued to this user (bumps token_version)."""
    db = get_db()
    db.users.update_one({"_id": ObjectId(str(user_id))}, {"$inc": {"token_version": 1}})
    invalidate_user_cache(user_id)


def current_token_version(user_id):
    doc = get_db().users.find_one({"_id": ObjectId(str(user_id))}, {"token_version": 1})
    return int((doc or {}).get("token_version", 0) or 0)


def storage_summary(user_id):
    """Counts of what the user is storing — powers the account / data page."""
    db = get_db()
    uid = str(user_id)
    by_status = {
        d["_id"] or "unknown": d["count"]
        for d in db.training_sessions.aggregate([
            {"$match": {"user_id": uid}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ])
    }
    by_type = {
        d["_id"] or "other": d["count"]
        for d in db.datasets.aggregate([
            {"$match": {"user_id": uid}},
            {"$group": {"_id": "$file_type", "count": {"$sum": 1}}},
        ])
    }
    return {
        "datasets": sum(by_type.values()),
        "datasets_by_type": by_type,
        "training_sessions": sum(by_status.values()),
        "sessions_by_status": by_status,
        "pipelines": db.pipelines.count_documents({"user_id": uid}),
        "feedback": db.feedback.count_documents({"user_id": uid}),
    }


def export_user_data(user_id):
    """Everything we hold about the user as one JSON-serialisable dict.

    Files themselves (datasets, models) stay on Drive and are downloadable from
    the app; this export carries their metadata and ids. Large/internal fields
    (password hash, token_version, inline CSV samples, progress logs) are left
    out.
    """
    db = get_db()
    uid = str(user_id)
    user = db.users.find_one({"_id": ObjectId(uid)}) or {}
    return {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "profile": _jsonable(user, drop=("password", "token_version")),
        "datasets": [
            _jsonable(d, drop=("csv_data", "image_links"))
            for d in db.datasets.find({"user_id": uid}).sort("uploaded_at", -1)
        ],
        "training_sessions": [
            _jsonable(s, drop=("progress_logs",))
            for s in db.training_sessions.find({"user_id": uid}).sort("created_at", -1)
        ],
        "pipelines": [_jsonable(p) for p in db.pipelines.find({"user_id": uid})],
        "usage": [_jsonable(u) for u in db.usage_counters.find({"user_id": uid})],
        "invoices": [_jsonable(i) for i in db.invoices.find({"user_id": uid})],
        "feedback": [_jsonable(f) for f in db.feedback.find({"user_id": uid})],
    }


def _safe_drive_delete(file_id):
    if not file_id:
        return
    try:
        from services.google_drive_service import delete_file_from_drive
        delete_file_from_drive(file_id)
    except Exception as e:
        print(f"[account] Drive delete failed for {file_id}: {e}")


def _remove_local_dirs(user_id):
    from config import (
        get_user_upload_dir, get_user_models_dir, get_user_images_dir,
        get_user_predictions_dir, get_user_extract_cache_dir, get_user_tmp_upload_dir,
    )
    for fn in (get_user_upload_dir, get_user_models_dir, get_user_images_dir,
               get_user_predictions_dir, get_user_extract_cache_dir, get_user_tmp_upload_dir):
        path = fn(user_id)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)


def purge_user_data(user_id):
    """Delete a user and EVERYTHING they own. Returns a small report.

    Order matters: revoke sessions first so the account can't be used while
    the (slow, Drive-bound) cleanup is running.
    """
    db = get_db()
    uid = str(user_id)
    oid = ObjectId(uid)
    user = db.users.find_one({"_id": oid})
    if not user:
        raise LookupError("user_not_found")

    revoke_all_sessions(uid)
    db.users.update_one({"_id": oid}, {"$set": {"active": False, "deletion_started_at": datetime.utcnow()}})

    report = {"sessions": 0, "datasets": 0}

    # Training sessions: reuse the per-session cleanup (Drive folder + files).
    from services.training_session_service import delete_session
    for s in db.training_sessions.find({"user_id": uid}, {"_id": 1}):
        try:
            delete_session(str(s["_id"]), uid)
            report["sessions"] += 1
        except Exception as e:
            print(f"[account] session cleanup failed for {s['_id']}: {e}")
    db.training_sessions.delete_many({"user_id": uid})  # anything the loop missed

    # Datasets (never touch curated defaults even if this user uploaded them).
    for d in db.datasets.find({"user_id": uid, "is_default": {"$ne": True}}, {"drive_id": 1}):
        _safe_drive_delete(d.get("drive_id"))
        report["datasets"] += 1
    db.datasets.delete_many({"user_id": uid, "is_default": {"$ne": True}})
    db.datasets.update_many({"user_id": uid, "is_default": True}, {"$unset": {"user_id": ""}})

    db.pipelines.delete_many({"user_id": uid})
    db.usage_counters.delete_many({"user_id": uid})
    db.otp_codes.delete_many({"email": user.get("email")})
    # Keep feedback text for the product team but drop the identity.
    db.feedback.update_many({"user_id": uid}, {"$set": {"user_id": None, "email": None, "anonymized": True}})
    # Invoices are legal/accounting records — retain, but detach the email.
    db.invoices.update_many({"user_id": uid}, {"$set": {"email": None, "user_deleted": True}})

    photo_id = user.get("profile_photo_id")
    if photo_id and len(str(photo_id)) > 24:
        _safe_drive_delete(photo_id)
    elif photo_id:
        try:
            from gridfs import GridFS
            GridFS(db).delete(ObjectId(photo_id))
        except Exception:
            pass

    _remove_local_dirs(uid)
    db.users.delete_one({"_id": oid})
    invalidate_user_cache(uid)
    return report
