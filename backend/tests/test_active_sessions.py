"""get_active_sessions + the /training-sessions/active route (global indicator)."""
import time
from datetime import datetime, timedelta

import jwt
from bson import ObjectId

from config import JWT_SECRET, JWT_ALGORITHM
from services.training_session_service import create_session, get_active_sessions


def _token(uid):
    return jwt.encode(
        {'user_id': str(uid), 'exp': int(time.time()) + 3600},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


def _set(db, sid, **fields):
    db.training_sessions.update_one({'_id': ObjectId(sid)}, {'$set': fields})


def test_active_filters_by_status_and_recency(app, db):
    uid = 'u-active'
    running = create_session(uid, 'cnn', {})
    _set(db, running['_id'], status='running')
    done = create_session(uid, 'ann', {})
    _set(db, done['_id'], status='completed')
    stale = create_session(uid, 'lstm', {})
    _set(db, stale['_id'], status='pending', created_at=datetime.utcnow() - timedelta(hours=48))

    ids = {a['session_id'] for a in get_active_sessions(uid)}
    assert running['_id'] in ids          # running + recent → active
    assert done['_id'] not in ids         # completed → excluded
    assert stale['_id'] not in ids        # too old → excluded


def test_active_route_is_not_shadowed_by_session_id(client, db):
    user = {'_id': ObjectId(), 'email': 'a@example.com', 'name': 'A', 'active': True}
    db.users.insert_one(user)
    s = create_session(str(user['_id']), 'cnn', {})
    _set(db, s['_id'], status='running')

    resp = client.get(
        '/api/training-sessions/active',
        headers={'Authorization': f'Bearer {_token(user["_id"])}'},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['count'] >= 1
    assert any(a['model_code'] == 'cnn' for a in body['active'])
