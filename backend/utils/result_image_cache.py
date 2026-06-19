"""Tiny in-process LRU cache for extracted result images.

GET /result-images streams a run's results.zip from Google Drive and unzips +
base64-encodes it on every call. The extracted images are immutable, keyed by
the results.zip Drive id, so caching the most-recent N keeps repeat replay loads
— even after a page reload — off the Drive API and the unzip path.

Bounded by entry count to cap memory; per-worker (not shared across gunicorn
processes), which is fine for a best-effort accelerator. Thread-safe so it's
correct under threaded workers.
"""
import threading
from collections import OrderedDict

_MAX_ENTRIES = 32
_cache = OrderedDict()   # drive_id -> list[str] (base64 data URLs)
_lock = threading.Lock()


def get(drive_id):
    """Return cached images for a Drive id (most-recent-use bump), or None."""
    if not drive_id:
        return None
    with _lock:
        if drive_id in _cache:
            _cache.move_to_end(drive_id)
            return _cache[drive_id]
    return None


def put(drive_id, images):
    """Cache a non-empty image list, evicting the least-recently-used over cap."""
    if not drive_id or not images:
        return
    with _lock:
        _cache[drive_id] = images
        _cache.move_to_end(drive_id)
        while len(_cache) > _MAX_ENTRIES:
            _cache.popitem(last=False)


def clear():
    with _lock:
        _cache.clear()
