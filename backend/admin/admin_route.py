from flask import Blueprint, jsonify, request
from auth.auth_middleware import admin_required, invalidate_user_cache
from mongoDb.connection import get_db
from bson import ObjectId

admin_routes = Blueprint('admin_routes', __name__)


def _to_oid(value):
    """Parse an ObjectId or return None (so routes can 400 on bad ids)."""
    try:
        return ObjectId(value)
    except Exception:
        return None


def _paging():
    """Read page/limit query params with sane bounds. Returns (page, limit, skip)."""
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        limit = min(100, max(1, int(request.args.get('limit', 20))))
    except (TypeError, ValueError):
        limit = 20
    return page, limit, (page - 1) * limit

@admin_routes.route('/stats', methods=['GET'])
@admin_required
def get_system_stats(current_user):
    """Aggregate system statistics for the admin dashboard."""
    try:
        db = get_db()
        
        # Total Users
        total_users = db.users.count_documents({})
        
        # Total Training Sessions
        total_sessions = db.training_sessions.count_documents({})
        
        # Total Datasets Uploaded
        total_datasets = db.datasets.count_documents({})
        
        # Sessions by Model
        pipeline = [
            {"$group": {"_id": "$model_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        sessions_by_model = list(db.training_sessions.aggregate(pipeline))
        
        return jsonify({
            "total_users": total_users,
            "total_sessions": total_sessions,
            "total_datasets": total_datasets,
            "sessions_by_model": sessions_by_model
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/datasets/default', methods=['GET'])
@admin_required
def list_default_datasets(current_user):
    """List all official platform datasets available to users."""
    try:
        db = get_db()
        datasets = list(db.datasets.find({"is_default": True}))
        for d in datasets:
            d['_id'] = str(d['_id'])
        return jsonify({"datasets": datasets}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/datasets/default/<dataset_id>', methods=['DELETE'])
@admin_required
def delete_default_dataset(current_user, dataset_id):
    """Remove an official dataset from the cloud library."""
    try:
        oid = _to_oid(dataset_id)
        if not oid:
            return jsonify({"error": "Invalid dataset id"}), 400
        db = get_db()
        res = db.datasets.delete_one({"_id": oid, "is_default": True})
        if res.deleted_count == 0:
            return jsonify({"error": "Dataset not found"}), 404
        return jsonify({"message": "Dataset removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────
# User management
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/users', methods=['GET'])
@admin_required
def list_users(current_user):
    """Paginated user list with per-user session & dataset counts.

    Supports ?search= (regex on email/first_name/last_name), ?page=, ?limit=.
    """
    try:
        db = get_db()
        page, limit, skip = _paging()
        search = (request.args.get('search') or '').strip()

        query = {}
        if search:
            rx = {"$regex": search, "$options": "i"}
            query = {"$or": [{"email": rx}, {"first_name": rx}, {"last_name": rx}]}

        total = db.users.count_documents(query)
        users = list(db.users.find(query, {"password": 0}).sort("created_at", -1).skip(skip).limit(limit))

        # Per-user counts via aggregation (two grouped queries, then map).
        session_counts = {d["_id"]: d["count"] for d in db.training_sessions.aggregate(
            [{"$group": {"_id": "$user_id", "count": {"$sum": 1}}}]
        )}
        dataset_counts = {d["_id"]: d["count"] for d in db.datasets.aggregate(
            [{"$group": {"_id": "$user_id", "count": {"$sum": 1}}}]
        )}

        for u in users:
            uid = str(u["_id"])
            u["_id"] = uid
            u["session_count"] = session_counts.get(uid, 0)
            u["dataset_count"] = dataset_counts.get(uid, 0)
            sub = u.get("subscription") or {}
            u["plan"] = sub.get("plan", "free")

        return jsonify({"users": users, "total": total, "page": page, "limit": limit}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/users/<user_id>/role', methods=['PATCH'])
@admin_required
def set_user_role(current_user, user_id):
    """Promote/demote a user. Blocks self-demotion to avoid admin lockout."""
    try:
        oid = _to_oid(user_id)
        if not oid:
            return jsonify({"error": "Invalid user id"}), 400
        role = (request.get_json() or {}).get('role')
        if role not in ('admin', 'user'):
            return jsonify({"error": "role must be 'admin' or 'user'"}), 400
        if str(current_user['_id']) == str(user_id) and role != 'admin':
            return jsonify({"error": "You cannot remove your own admin role"}), 400

        db = get_db()
        res = db.users.update_one({"_id": oid}, {"$set": {"role": role}})
        if res.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
        invalidate_user_cache(user_id)  # so the 30s auth cache reflects it now
        return jsonify({"message": "Role updated", "role": role}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/users/<user_id>/status', methods=['PATCH'])
@admin_required
def set_user_status(current_user, user_id):
    """Activate/deactivate a user account (soft). Blocks self-deactivation."""
    try:
        oid = _to_oid(user_id)
        if not oid:
            return jsonify({"error": "Invalid user id"}), 400
        active = bool((request.get_json() or {}).get('active', True))
        if str(current_user['_id']) == str(user_id) and not active:
            return jsonify({"error": "You cannot deactivate your own account"}), 400

        db = get_db()
        res = db.users.update_one({"_id": oid}, {"$set": {"active": active}})
        if res.matched_count == 0:
            return jsonify({"error": "User not found"}), 404
        invalidate_user_cache(user_id)
        return jsonify({"message": "Status updated", "active": active}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────
# All training sessions
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/sessions', methods=['GET'])
@admin_required
def list_all_sessions(current_user):
    """Paginated view of every user's training sessions, with owner email.

    Filters: ?model_code= ?status= ?user_id= plus ?page= ?limit=.
    """
    try:
        db = get_db()
        page, limit, skip = _paging()
        query = {}
        for field in ('model_code', 'status', 'user_id'):
            val = request.args.get(field)
            if val:
                query[field] = val

        total = db.training_sessions.count_documents(query)
        sessions = list(db.training_sessions.find(query).sort("created_at", -1).skip(skip).limit(limit))

        # Resolve owner emails in one pass.
        owner_ids = {s.get('user_id') for s in sessions if s.get('user_id')}
        emails = {}
        for uid in owner_ids:
            oid = _to_oid(uid)
            if oid:
                u = db.users.find_one({"_id": oid}, {"email": 1})
                if u:
                    emails[uid] = u.get('email')

        for s in sessions:
            s['_id'] = str(s['_id'])
            s['user_email'] = emails.get(s.get('user_id'))

        return jsonify({"sessions": sessions, "total": total, "page": page, "limit": limit}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/sessions/<session_id>', methods=['DELETE'])
@admin_required
def admin_delete_session(current_user, session_id):
    """Delete any user's session (reuses the owner-scoped cleanup incl. Drive)."""
    try:
        oid = _to_oid(session_id)
        if not oid:
            return jsonify({"error": "Invalid session id"}), 400
        db = get_db()
        session = db.training_sessions.find_one({"_id": oid})
        if not session:
            return jsonify({"error": "Session not found"}), 404
        from services.training_session_service import delete_session
        # Pass the session's own owner so the ownership check inside passes.
        delete_session(session_id, session.get('user_id'))
        return jsonify({"message": "Session deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────
# Feedback inbox
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/feedback', methods=['GET'])
@admin_required
def list_feedback(current_user):
    """Paginated feedback inbox. Filter with ?type= and ?resolved=true|false."""
    try:
        db = get_db()
        page, limit, skip = _paging()
        query = {}
        ftype = request.args.get('type')
        if ftype:
            query['type'] = ftype
        resolved = request.args.get('resolved')
        if resolved in ('true', 'false'):
            query['resolved'] = (resolved == 'true')

        total = db.feedback.count_documents(query)
        items = list(db.feedback.find(query).sort("created_at", -1).skip(skip).limit(limit))
        for f in items:
            f['_id'] = str(f['_id'])
            f['resolved'] = bool(f.get('resolved', False))
        return jsonify({"feedback": items, "total": total, "page": page, "limit": limit}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/feedback/<feedback_id>', methods=['PATCH'])
@admin_required
def update_feedback(current_user, feedback_id):
    """Mark a feedback item resolved/unresolved."""
    try:
        oid = _to_oid(feedback_id)
        if not oid:
            return jsonify({"error": "Invalid feedback id"}), 400
        resolved = bool((request.get_json() or {}).get('resolved', True))
        db = get_db()
        res = db.feedback.update_one({"_id": oid}, {"$set": {"resolved": resolved}})
        if res.matched_count == 0:
            return jsonify({"error": "Feedback not found"}), 404
        return jsonify({"message": "Feedback updated", "resolved": resolved}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/feedback/<feedback_id>', methods=['DELETE'])
@admin_required
def delete_feedback(current_user, feedback_id):
    try:
        oid = _to_oid(feedback_id)
        if not oid:
            return jsonify({"error": "Invalid feedback id"}), 400
        db = get_db()
        res = db.feedback.delete_one({"_id": oid})
        if res.deleted_count == 0:
            return jsonify({"error": "Feedback not found"}), 404
        return jsonify({"message": "Feedback deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────
# Dataset library management (all datasets, not just defaults)
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/datasets', methods=['GET'])
@admin_required
def list_all_datasets(current_user):
    """Paginated view of ALL datasets with owner email. Filters: ?search=
    (filename), ?is_default=true|false."""
    try:
        db = get_db()
        page, limit, skip = _paging()
        query = {}
        search = (request.args.get('search') or '').strip()
        if search:
            query['filename'] = {"$regex": search, "$options": "i"}
        is_default = request.args.get('is_default')
        if is_default in ('true', 'false'):
            query['is_default'] = (is_default == 'true')

        total = db.datasets.count_documents(query)
        datasets = list(db.datasets.find(query).sort("uploaded_at", -1).skip(skip).limit(limit))

        owner_ids = {d.get('user_id') for d in datasets if d.get('user_id')}
        emails = {}
        for uid in owner_ids:
            oid = _to_oid(uid)
            if oid:
                u = db.users.find_one({"_id": oid}, {"email": 1})
                if u:
                    emails[uid] = u.get('email')

        for d in datasets:
            d['_id'] = str(d['_id'])
            d['owner_email'] = emails.get(d.get('user_id'))
            d['is_default'] = bool(d.get('is_default', False))
        return jsonify({"datasets": datasets, "total": total, "page": page, "limit": limit}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/datasets/<dataset_id>/default', methods=['PATCH'])
@admin_required
def set_dataset_default(current_user, dataset_id):
    """Promote/demote a dataset into/out of the curated default library."""
    try:
        oid = _to_oid(dataset_id)
        if not oid:
            return jsonify({"error": "Invalid dataset id"}), 400
        is_default = bool((request.get_json() or {}).get('is_default', True))
        db = get_db()
        res = db.datasets.update_one({"_id": oid}, {"$set": {"is_default": is_default}})
        if res.matched_count == 0:
            return jsonify({"error": "Dataset not found"}), 404
        return jsonify({"message": "Dataset updated", "is_default": is_default}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_routes.route('/datasets/<dataset_id>', methods=['DELETE'])
@admin_required
def admin_delete_dataset(current_user, dataset_id):
    """Delete any dataset record and best-effort remove its Drive blob."""
    try:
        oid = _to_oid(dataset_id)
        if not oid:
            return jsonify({"error": "Invalid dataset id"}), 400
        db = get_db()
        ds = db.datasets.find_one({"_id": oid})
        if not ds:
            return jsonify({"error": "Dataset not found"}), 404
        if ds.get('drive_id'):
            try:
                from services.google_drive_service import delete_file_from_drive
                delete_file_from_drive(ds['drive_id'])
            except Exception as e:
                print(f"Warning: could not delete dataset Drive blob: {e}")
        db.datasets.delete_one({"_id": oid})
        return jsonify({"message": "Dataset deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
