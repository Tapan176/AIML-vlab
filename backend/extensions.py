"""
Shared Flask extensions.

Instantiated WITHOUT an app so blueprints can import them (e.g. to apply
per-route rate limits) without importing app.py and creating a circular import.
app.py binds them with `limiter.init_app(app)` at startup.
"""
import logging

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import REDIS_URL

log = logging.getLogger(__name__)


def _resolve_storage_uri(redis_url):
    """Pick the rate-limiter storage backend.

    With REDIS_URL set and reachable, limits are shared across all gunicorn
    workers and survive restarts. Otherwise we fall back to in-memory storage
    (per-process, lost on restart) — fine for single-worker / local dev, and it
    means a missing or briefly-unreachable Redis never blocks startup. The
    connectivity probe uses a short timeout so boot isn't delayed if Redis is
    down.
    """
    if not redis_url:
        return "memory://"
    try:
        import redis
        redis.from_url(redis_url, socket_connect_timeout=0.5).ping()
        return redis_url
    except Exception as e:
        log.warning(
            "Redis unavailable (%s); rate limiter falling back to in-memory "
            "storage. Set a reachable REDIS_URL in production for shared limits.",
            e,
        )
        return "memory://"


# Global default limits apply to every route; sensitive routes (e.g. auth) add
# stricter per-route limits via @limiter.limit(...).
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri=_resolve_storage_uri(REDIS_URL),
)
