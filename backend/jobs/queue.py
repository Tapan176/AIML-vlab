"""RQ queue access with graceful degradation.

`get_redis()` / `get_queue()` return None whenever Redis isn't configured or
isn't reachable, so every caller can fall back to synchronous execution rather
than failing. `redis` and `rq` are imported lazily so the package only needs to
be importable, not connectable, on the sync path.
"""
import logging

from config import REDIS_URL

log = logging.getLogger(__name__)

TRAINING_QUEUE = "training"

# Cache the redis client so we don't reconnect per enqueue. The queue object is
# cheap, so it's rebuilt per call (keeps tests that swap the connection simple).
_redis = None


def get_redis():
    """Return a shared redis client, or None when REDIS_URL is unset/unreachable."""
    global _redis
    if not REDIS_URL:
        return None
    if _redis is None:
        try:
            import redis
            client = redis.from_url(REDIS_URL, socket_connect_timeout=0.5)
            client.ping()
            _redis = client
        except Exception as e:
            log.warning("Redis unavailable (%s); training will run synchronously.", e)
            return None
    return _redis


def get_queue():
    """Return the RQ training queue, or None when Redis isn't available."""
    conn = get_redis()
    if conn is None:
        return None
    try:
        from rq import Queue
        return Queue(TRAINING_QUEUE, connection=conn)
    except Exception as e:
        log.warning("Could not build RQ queue (%s); training will run synchronously.", e)
        return None


def enqueue_training(payload, *, job_timeout=3600):
    """Enqueue a training job. Returns the RQ job, or None if no queue (caller
    should then run training synchronously). `job_timeout` is generous so long
    deep-learning runs aren't killed mid-flight."""
    q = get_queue()
    if q is None:
        return None
    # Import the task by string so the worker resolves it without importing the
    # Flask app, and to avoid a circular import at module load.
    from jobs.tasks import run_training_job
    return q.enqueue(run_training_job, payload, job_timeout=job_timeout)
