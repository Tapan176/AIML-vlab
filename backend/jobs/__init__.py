"""Background-job layer (Phase 2).

Offloads model training to an RQ worker so HTTP requests return immediately
instead of blocking for the duration of a run. All of it degrades gracefully:
when REDIS_URL is unset / unreachable, `get_queue()` returns None and callers
fall back to running training synchronously in-request.
"""
