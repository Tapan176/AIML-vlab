"""result_image_cache LRU + the /result-images route serving from it.

The route streams + unzips a run's results.zip from Drive; since that extract is
immutable per Drive id, a repeat load must hit the cache instead of Drive again.
"""
import io
import time
import zipfile

import jwt
from bson import ObjectId

from config import JWT_SECRET, JWT_ALGORITHM
from services.training_session_service import create_session
from utils import result_image_cache as ric


def test_lru_get_put_and_eviction():
    ric.clear()
    ric.put('a', ['img'])
    assert ric.get('a') == ['img']
    assert ric.get('missing') is None
    ric.put('b', [])          # empty list is not cached
    assert ric.get('b') is None
    for i in range(ric._MAX_ENTRIES + 10):
        ric.put(f'k{i}', [f'v{i}'])
    assert len(ric._cache) <= ric._MAX_ENTRIES   # bounded
    ric.clear()


def _png_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('plot.png', b'\x89PNG\r\n\x1a\nfake-bytes')
    buf.seek(0)
    return buf


def _token(uid):
    return jwt.encode(
        {'user_id': str(uid), 'exp': int(time.time()) + 3600},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


def test_result_images_route_caches_drive_extract(client, db, monkeypatch):
    ric.clear()
    user = {'_id': ObjectId(), 'email': 'ri@example.com', 'name': 'R', 'active': True}
    db.users.insert_one(user)
    session = create_session(str(user['_id']), 'cnn', {})
    db.training_sessions.update_one(
        {'_id': ObjectId(session['_id'])},
        {'$set': {'status': 'completed', 'results_zip_drive_id': 'drive-xyz'}},
    )

    calls = {'n': 0}
    import services.google_drive_service as gds

    def fake_stream(drive_id):
        calls['n'] += 1
        return _png_zip(), 'application/zip'

    monkeypatch.setattr(gds, 'stream_file_from_drive', fake_stream)

    headers = {'Authorization': f'Bearer {_token(user["_id"])}'}
    url = f'/api/training-sessions/{session["_id"]}/result-images'
    r1 = client.get(url, headers=headers)
    r2 = client.get(url, headers=headers)

    assert r1.status_code == 200 and r2.status_code == 200
    imgs1 = r1.get_json()['images']
    assert len(imgs1) == 1 and imgs1[0].startswith('data:image/png;base64,')
    assert imgs1 == r2.get_json()['images']
    assert calls['n'] == 1   # second load served from cache — Drive hit once
    ric.clear()
