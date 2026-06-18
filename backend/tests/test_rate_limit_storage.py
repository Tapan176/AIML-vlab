"""Tests for the rate-limiter storage selection in extensions.py.

The limiter must use Redis when REDIS_URL is set and reachable, but degrade to
in-memory storage (never crash) when Redis is absent or unreachable — so local
dev and first boot work without Redis.
"""
from extensions import _resolve_storage_uri


def test_no_redis_url_uses_memory():
    assert _resolve_storage_uri(None) == "memory://"
    assert _resolve_storage_uri("") == "memory://"


def test_unreachable_redis_falls_back_to_memory():
    # Port 1 refuses connections; the short connect timeout means this returns
    # quickly rather than hanging startup.
    assert _resolve_storage_uri("redis://127.0.0.1:1/0") == "memory://"
