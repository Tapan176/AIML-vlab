"""
Admin API — system stats, user management, sessions, feedback, datasets.

Every route is @admin_required. Search terms are regex-escaped (they used to
be passed to $regex raw, which allowed ReDoS / regex injection), per-row owner
lookups are batched with $in (they were one query per row), and per-user
counts are computed only for the users on the current page.
"""
import logging
from datetime import datetime

from bson import ObjectId
from flask import Blueprint, jsonify, request

from auth.auth_middleware import admin_required, invalidate_user_cache
from mongoDb.connection import get_db
from utils.validators import safe_regex

log = logging.getLogger(__name__)
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


def _emails_for(user_ids):
    """{user_id_str: email} for a set of user id strings, in ONE query."""
    oids = [o for o in (_to_oid(u) for u in user_ids if u) if o]
    if not oids:
        return {}
    return {str(u['_id']): u.get('email') for u in get_db().users.find({'_id': {'$in': oids}}, {'email': 1})}


def _counts_by_user(collection, user_ids):
    if not user_ids:
        return {}
    return {d['_id']: d['count'] for d in collection.aggregate([
        {'$match': {'user_id': {'$in': list(user_ids)}}},
        {'$group': {'_id': '$user_id', 'count': {'$sum': 1}}},
    ])}


def _public_user(u):
    u = dict(u)
    u['_id'] = str(u['_id'])
    for secret in ('password', 'token_version'):
        u.pop(secret, None)
    for k, v in list(u.items()):
        if isinstance(v, datetime):
            u[k] = v.isoformat()
    return u


@admin_routes.route('/stats', methods=['GET'])
@admin_required
def get_system_stats(current_user):
    """Aggregate system statistics for the admin dashboard."""
    db = get_db()
    since = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    sessions_by_model = list(db.training_sessions.aggregate([
        {"$group": {"_id": "$model_code", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]))
    sessions_by_status = {d['_id'] or 'unknown': d['count'] for d in db.training_sessions.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ])}
    return jsonify({
        "total_users": db.users.count_documents({}),
        "active_users_7d": db.users.count_documents({"last_login": {"$gte": week_ago}}),
        "new_users_today": db.users.count_documents({"created_at": {"$gte": since}}),
        "deactivated_users": db.users.count_documents({"active": False}),
        "admins": db.users.count_documents({"role": "admin"}),
        "total_sessions": db.training_sessions.count_documents({}),
        "running_sessions": sessions_by_status.get('running', 0),
        "sessions_by_status": sessions_by_status,
        "total_datasets": db.datasets.count_documents({}),
        "open_feedback": db.feedback.count_documents({"resolved": {"$ne": True}}),
        "sessions_by_model": sessions_by_model,
    }), 200


@admin_routes.route('/datasets/default', methods=['GET'])
@admin_required
def list_default_datasets(current_user):
    """List all official platform datasets available to users."""
    db = get_db()
    datasets = list(db.datasets.find({"is_default": True}, {"csv_data": 0, "image_links": 0}))
    for d in datasets:
        d['_id'] = str(d['_id'])
    return jsonify({"datasets": datasets}), 200


@admin_routes.route('/datasets/default/<dataset_id>', methods=['DELETE'])
@admin_required
def delete_default_dataset(current_user, dataset_id):
    """Remove an official dataset from the cloud library."""
    oid = _to_oid(dataset_id)
    if not oid:
        return jsonify({"error": "Invalid dataset id"}), 400
    res = get_db().datasets.delete_one({"_id": oid, "is_default": True})
    if res.deleted_count == 0:
        return jsonify({"error": "Dataset not found"}), 404
    return jsonify({"message": "Dataset removed successfully"}), 200


# ──────────────────────────────────────────────────────────────────────────
# User management
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/users', methods=['GET'])
@admin_required
def list_users(current_user):
    """Paginated user list with per-user session & dataset counts.

    Filters: ?search= (email / first / last name), ?role=admin|user,
    ?status=active|inactive, ?plan=free|pro|team, ?page=, ?limit=.
    """
    db = get_db()
    page, limit, skip = _paging()
    query = {}
    term = safe_regex(request.args.get('search') or '')
    if term:
        rx = {"$regex": term, "$options": "i"}
        query["$or"] = [{"email": rx}, {"first_name": rx}, {"last_name": rx}]
    role = request.args.get('role')
    if role in ('admin', 'user'):
        query['role'] = role
    status = request.args.get('status')
    if status == 'inactive':
        query['active'] = False
    elif status == 'active':
        query['active'] = {'$ne': False}
    plan = request.args.get('plan')
    if plan == 'free':
        query['$and'] = [{'$or': [{'subscription.plan': {'$exists': False}}, {'subscription.plan': 'free'}]}]
    elif plan in ('pro', 'team'):
        query['subscription.plan'] = plan

    total = db.users.count_documents(query)
    users = list(db.users.find(query, {"password": 0, "token_version": 0})
                 .sort("created_at", -1).skip(skip).limit(limit))
    ids = [str(u['_id']) for u in users]
    session_counts = _counts_by_user(db.training_sessions, ids)
    dataset_counts = _counts_by_user(db.datasets, ids)

    out = []
    for u in users:
        pu = _public_user(u)
        pu["session_count"] = session_counts.get(pu['_id'], 0)
        pu["dataset_count"] = dataset_counts.get(pu['_id'], 0)
        pu["plan"] = (u.get("subscription") or {}).get("plan", "free")
        out.append(pu)
    return jsonify({"users": out, "total": total, "page": page, "limit": limit}), 200


@admin_routes.route('/users/<user_id>', methods=['GET'])
@admin_required
def get_user_detail(current_user, user_id):
    """One user's profile, storage summary, current-month usage and recent runs."""
    oid = _to_oid(user_id)
    if not oid:
        return jsonify({"error": "Invalid user id"}), 400
    db = get_db()
    user = db.users.find_one({"_id": oid}, {"password": 0, "token_version": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    from services.account_service import storage_summary
    from services.subscription_service import get_usage
    recent = list(db.training_sessions.find(
        {"user_id": user_id},
        {"model_code": 1, "version": 1, "status": 1, "created_at": 1, "completed_at": 1, "error": 1},
    ).sort("created_at", -1).limit(10))
    for s in recent:
        s['_id'] = str(s['_id'])
    usage = get_usage(user_id)
    usage.pop('_id', None)
    return jsonify({
        "user": _public_user(user),
        "storage": storage_summary(user_id),
        "usage": usage,
        "recent_sessions": recent,
    }), 200


@admin_routes.route('/users/<user_id>/role', methods=['PATCH'])
@admin_required
def set_user_role(current_user, user_id):
    """Promote/demote a user. Blocks self-demotion to avoid admin lockout."""
    oid = _to_oid(user_id)
    if not oid:
        return jsonify({"error": "Invalid user id"}), 400
    role = (request.get_json(silent=True) or {}).get('role')
    if role not in ('admin', 'user'):
        return jsonify({"error": "role must be 'admin' or 'user'"}), 400
    if str(current_user['_id']) == str(user_id) and role != 'admin':
        return jsonify({"error": "You cannot remove your own admin role"}), 400
    res = get_db().users.update_one({"_id": oid}, {"$set": {"role": role}})
    if res.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
    invalidate_user_cache(user_id)
    log.info("admin %s set role of %s to %s", current_user['_id'], user_id, role)
    return jsonify({"message": "Role updated", "role": role}), 200


@admin_routes.route('/users/<user_id>/status', methods=['PATCH'])
@admin_required
def set_user_status(current_user, user_id):
    """Activate/deactivate a user account (soft). Deactivation also revokes
    the user's sessions immediately. Blocks self-deactivation."""
    oid = _to_oid(user_id)
    if not oid:
        return jsonify({"error": "Invalid user id"}), 400
    active = bool((request.get_json(silent=True) or {}).get('active', True))
    if str(current_user['_id']) == str(user_id) and not active:
        return jsonify({"error": "You cannot deactivate your own account"}), 400
    update = {"$set": {"active": active}}
    if not active:
        update["$inc"] = {"token_version": 1}
    res = get_db().users.update_one({"_id": oid}, update)
    if res.matched_count == 0:
        return jsonify({"error": "User not found"}), 404
    invalidate_user_cache(user_id)
    log.info("admin %s set active=%s for %s", current_user['_id'], active, user_id)
    return jsonify({"message": "Status updated", "active": active}), 200


@admin_routes.route('/users/<user_id>/plan', methods=['PATCH'])
@admin_required
def set_user_plan(current_user, user_id):
    """Manually assign a plan (comp accounts, support fixes). Body: {plan}."""
    from services.subscription_service import PLANS, set_user_subscription
    oid = _to_oid(user_id)
    if not oid:
        return jsonify({"error": "Invalid user id"}), 400
    plan = (request.get_json(silent=True) or {}).get('plan')
    if plan not in PLANS:
        return jsonify({"error": f"plan must be one of: {', '.join(PLANS)}"}), 400
    if not get_db().users.find_one({"_id": oid}, {"_id": 1}):
        return jsonify({"error": "User not found"}), 404
    sub = set_user_subscription(user_id, plan, status="active", provider="manual")
    log.info("admin %s set plan of %s to %s", current_user['_id'], user_id, plan)
    return jsonify({"message": "Plan updated", "subscription": sub}), 200


@admin_routes.route('/users/<user_id>/revoke-sessions', methods=['POST'])
@admin_required
def revoke_user_sessions(current_user, user_id):
    """Force-logout a user on every device."""
    oid = _to_oid(user_id)
    if not oid:
        return jsonify({"error": "Invalid user id"}), 400
    if not get_db().users.find_one({"_id": oid}, {"_id": 1}):
        return jsonify({"error": "User not found"}), 404
    from services.account_service import revoke_all_sessions
    revoke_all_sessions(user_id)
    log.info("admin %s revoked sessions of %s", current_user['_id'], user_id)
    return jsonify({"message": "All sessions revoked"}), 200


@admin_routes.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(current_user, user_id):
    """Permanently delete a user and all of their data."""
    oid = _to_oid(user_id)
    if not oid:
        return jsonify({"error": "Invalid user id"}), 400
    if str(current_user['_id']) == str(user_id):
        return jsonify({"error": "Use Settings → Delete account to delete your own account"}), 400
    from services.account_service import purge_user_data
    try:
        report = purge_user_data(user_id)
    except LookupError:
        return jsonify({"error": "User not found"}), 404
    log.warning("admin %s deleted user %s (%s)", current_user['_id'], user_id, report)
    return jsonify({"message": "User deleted", "deleted": report}), 200


# ──────────────────────────────────────────────────────────────────────────
# All training sessions
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/sessions', methods=['GET'])
@admin_required
def list_all_sessions(current_user):
    """Paginated view of every user's training sessions, with owner email.

    Filters: ?model_code= ?status= ?user_id= plus ?page= ?limit=.
    """
    db = get_db()
    page, limit, skip = _paging()
    query = {}
    for field in ('model_code', 'status', 'user_id'):
        val = request.args.get(field)
        if val:
            query[field] = str(val)

    total = db.training_sessions.count_documents(query)
    sessions = list(db.training_sessions.find(query, {"progress_logs": 0, "progress_metrics": 0})
                    .sort("created_at", -1).skip(skip).limit(limit))
    emails = _emails_for({s.get('user_id') for s in sessions})
    for s in sessions:
        s['_id'] = str(s['_id'])
        s['user_email'] = emails.get(s.get('user_id'))
    return jsonify({"sessions": sessions, "total": total, "page": page, "limit": limit}), 200


@admin_routes.route('/sessions/<session_id>', methods=['DELETE'])
@admin_required
def admin_delete_session(current_user, session_id):
    """Delete any user's session (reuses the owner-scoped cleanup incl. Drive)."""
    oid = _to_oid(session_id)
    if not oid:
        return jsonify({"error": "Invalid session id"}), 400
    session = get_db().training_sessions.find_one({"_id": oid}, {"user_id": 1})
    if not session:
        return jsonify({"error": "Session not found"}), 404
    from services.training_session_service import delete_session
    delete_session(session_id, session.get('user_id'))
    return jsonify({"message": "Session deleted"}), 200


# ──────────────────────────────────────────────────────────────────────────
# Feedback inbox
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/feedback', methods=['GET'])
@admin_required
def list_feedback(current_user):
    """Paginated feedback inbox. Filter with ?type= and ?resolved=true|false."""
    db = get_db()
    page, limit, skip = _paging()
    query = {}
    ftype = request.args.get('type')
    if ftype:
        query['type'] = str(ftype)
    resolved = request.args.get('resolved')
    if resolved in ('true', 'false'):
        query['resolved'] = True if resolved == 'true' else {'$ne': True}

    total = db.feedback.count_documents(query)
    items = list(db.feedback.find(query).sort("created_at", -1).skip(skip).limit(limit))
    for f in items:
        f['_id'] = str(f['_id'])
        f['resolved'] = bool(f.get('resolved', False))
    return jsonify({"feedback": items, "total": total, "page": page, "limit": limit}), 200


@admin_routes.route('/feedback/<feedback_id>', methods=['PATCH'])
@admin_required
def update_feedback(current_user, feedback_id):
    """Mark a feedback item resolved/unresolved."""
    oid = _to_oid(feedback_id)
    if not oid:
        return jsonify({"error": "Invalid feedback id"}), 400
    resolved = bool((request.get_json(silent=True) or {}).get('resolved', True))
    res = get_db().feedback.update_one({"_id": oid}, {"$set": {"resolved": resolved}})
    if res.matched_count == 0:
        return jsonify({"error": "Feedback not found"}), 404
    return jsonify({"message": "Feedback updated", "resolved": resolved}), 200


@admin_routes.route('/feedback/<feedback_id>', methods=['DELETE'])
@admin_required
def delete_feedback(current_user, feedback_id):
    oid = _to_oid(feedback_id)
    if not oid:
        return jsonify({"error": "Invalid feedback id"}), 400
    res = get_db().feedback.delete_one({"_id": oid})
    if res.deleted_count == 0:
        return jsonify({"error": "Feedback not found"}), 404
    return jsonify({"message": "Feedback deleted"}), 200


# ──────────────────────────────────────────────────────────────────────────
# Dataset library management (all datasets, not just defaults)
# ──────────────────────────────────────────────────────────────────────────

@admin_routes.route('/datasets', methods=['GET'])
@admin_required
def list_all_datasets(current_user):
    """Paginated view of ALL datasets with owner email. Filters: ?search=
    (filename), ?is_default=true|false."""
    db = get_db()
    page, limit, skip = _paging()
    query = {}
    term = safe_regex(request.args.get('search') or '')
    if term:
        query['filename'] = {"$regex": term, "$options": "i"}
    is_default = request.args.get('is_default')
    if is_default in ('true', 'false'):
        query['is_default'] = True if is_default == 'true' else {'$ne': True}

    total = db.datasets.count_documents(query)
    datasets = list(db.datasets.find(query, {"csv_data": 0, "image_links": 0})
                    .sort("uploaded_at", -1).skip(skip).limit(limit))
    emails = _emails_for({d.get('user_id') for d in datasets})
    for d in datasets:
        d['_id'] = str(d['_id'])
        d['owner_email'] = emails.get(d.get('user_id'))
        d['is_default'] = bool(d.get('is_default', False))
    return jsonify({"datasets": datasets, "total": total, "page": page, "limit": limit}), 200


@admin_routes.route('/datasets/<dataset_id>/default', methods=['PATCH'])
@admin_required
def set_dataset_default(current_user, dataset_id):
    """Promote/demote a dataset into/out of the curated default library."""
    oid = _to_oid(dataset_id)
    if not oid:
        return jsonify({"error": "Invalid dataset id"}), 400
    is_default = bool((request.get_json(silent=True) or {}).get('is_default', True))
    res = get_db().datasets.update_one({"_id": oid}, {"$set": {"is_default": is_default}})
    if res.matched_count == 0:
        return jsonify({"error": "Dataset not found"}), 404
    return jsonify({"message": "Dataset updated", "is_default": is_default}), 200


@admin_routes.route('/datasets/<dataset_id>', methods=['DELETE'])
@admin_required
def admin_delete_dataset(current_user, dataset_id):
    """Delete any dataset record and best-effort remove its Drive blob."""
    oid = _to_oid(dataset_id)
    if not oid:
        return jsonify({"error": "Invalid dataset id"}), 400
    db = get_db()
    ds = db.datasets.find_one({"_id": oid}, {"drive_id": 1})
    if not ds:
        return jsonify({"error": "Dataset not found"}), 404
    if ds.get('drive_id'):
        try:
            from services.google_drive_service import delete_file_from_drive
            delete_file_from_drive(ds['drive_id'])
        except Exception as e:
            log.warning("could not delete dataset Drive blob: %s", e)
    db.datasets.delete_one({"_id": oid})
    return jsonify({"message": "Dataset deleted"}), 200
