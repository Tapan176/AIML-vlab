"""Tests for the incremental /progress snapshot (get_session_progress + route).

Covers the bandwidth optimisation: ?since=<n> returns only the log/metric tail
and omits the heavy results/images payload until the run completes, while the
no-args call stays byte-compatible with the original full snapshot.
"""
import time

import jwt
from bson import ObjectId

from config import JWT_SECRET, JWT_ALGORITHM
from services.training_session_service import (
    create_session,
    append_session_progress,
    append_session_metric,
    get_session_progress,
)


def _seed_session(db, user_id='owner-1', n_logs=5, n_metrics=3, status='running'):
    session = create_session(user_id, 'cnn', {'epochs': 3})
    sid = session['_id']
    for i in range(n_logs):
        append_session_progress(sid, f'log line {i}')
    for i in range(n_metrics):
        append_session_metric(sid, {'epoch': i, 'total_epochs': n_metrics, 'loss': 1.0 / (i + 1)})
    db.training_sessions.update_one({'_id': ObjectId(sid)}, {'$set': {'status': status}})
    return sid


# ---- service layer ---------------------------------------------------------

def test_legacy_mode_returns_full_snapshot_with_counts(app, db):
    sid = _seed_session(db, n_logs=5, n_metrics=3)
    snap = get_session_progress(sid)
    assert len(snap['logs']) == 5
    assert len(snap['metrics']) == 3
    assert snap['logs_count'] == 5
    assert snap['metrics_count'] == 3
    # Heavy fields present (back-compat) even though not completed.
    assert 'results' in snap and 'output_images' in snap


def test_incremental_returns_only_the_tail(app, db):
    sid = _seed_session(db, n_logs=5, n_metrics=3)
    snap = get_session_progress(sid, since_logs=3, since_metrics=2)
    assert snap['logs'] == ['log line 3', 'log line 4']
    assert len(snap['metrics']) == 1
    # Counts still report the server-side totals so the client knows its offset.
    assert snap['logs_count'] == 5
    assert snap['metrics_count'] == 3


def test_incremental_omits_results_until_completed(app, db):
    sid = _seed_session(db, status='running')
    snap = get_session_progress(sid, since_logs=0)
    assert 'results' not in snap
    assert 'output_images' not in snap
    assert 'trained_model_drive_id' not in snap


def test_incremental_includes_results_once_completed(app, db):
    sid = _seed_session(db, status='running')
    db.training_sessions.update_one(
        {'_id': ObjectId(sid)},
        {'$set': {'status': 'completed', 'results': {'accuracy': 0.9}}},
    )
    snap = get_session_progress(sid, since_logs=5)
    assert snap['status'] == 'completed'
    assert snap['results'] == {'accuracy': 0.9}


def test_offset_beyond_end_yields_empty_slice(app, db):
    sid = _seed_session(db, n_logs=2)
    snap = get_session_progress(sid, since_logs=99)
    assert snap['logs'] == []
    assert snap['logs_count'] == 2  # client sees 2 < 99 and can resync


def test_unknown_session_returns_none(app, db):
    assert get_session_progress(str(ObjectId())) is None


# ---- route layer -----------------------------------------------------------

def _make_token(user_id):
    return jwt.encode(
        {'user_id': str(user_id), 'exp': int(time.time()) + 3600},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


def test_progress_route_incremental_query_params(client, db):
    user = {'_id': ObjectId(), 'email': 'p@example.com', 'name': 'P', 'active': True}
    db.users.insert_one(user)
    sid = _seed_session(db, user_id=str(user['_id']), n_logs=4, n_metrics=0)
    tok = _make_token(user['_id'])

    resp = client.get(
        f'/api/training-sessions/{sid}/progress?since=2',
        headers={'Authorization': f'Bearer {tok}'},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['logs'] == ['log line 2', 'log line 3']
    assert body['logs_count'] == 4


def test_progress_route_rejects_non_owner(client, db):
    owner = {'_id': ObjectId(), 'email': 'o@example.com', 'name': 'O', 'active': True}
    other = {'_id': ObjectId(), 'email': 'x@example.com', 'name': 'X', 'active': True}
    db.users.insert_many([owner, other])
    sid = _seed_session(db, user_id=str(owner['_id']))
    tok = _make_token(other['_id'])

    resp = client.get(
        f'/api/training-sessions/{sid}/progress',
        headers={'Authorization': f'Bearer {tok}'},
    )
    assert resp.status_code == 403
