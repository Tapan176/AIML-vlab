"""Shared pytest fixtures for the backend test-suite.

Test env vars are set BEFORE importing config/app — `config` raises at import
time if JWT_SECRET is the public default and FLASK_DEBUG isn't true, so the
secret must exist in the environment first. `setdefault` means a real env/.env
value still wins when present.

Each test gets a fresh in-memory mongomock database and an isolated Flask app
built by the application factory with the real DB and migrations turned off.
"""
import os

os.environ.setdefault('JWT_SECRET', 'pytest-only-secret-not-for-production-use')
os.environ.setdefault('SUBSCRIPTION_ENABLED', 'false')

import mongomock
import pytest

from mongoDb import connection
from app import create_app


@pytest.fixture
def app():
    """A fresh app per test, backed by a fresh in-memory mongomock database.

    The factory is told NOT to touch real Mongo or run migrations; we inject the
    mock client ourselves so `get_db()` returns it everywhere in the app.
    """
    connection.init_db(client_factory=mongomock.MongoClient)
    application = create_app(
        testing=True, init_database=False, run_migrations_on_start=False,
    )
    yield application


@pytest.fixture
def client(app):
    """Flask test client for hitting real routes end-to-end."""
    return app.test_client()


@pytest.fixture
def db(app):
    """The active mongomock database (initialised by the `app` fixture)."""
    return connection.get_db()


@pytest.fixture(autouse=True)
def _clear_user_cache():
    """The auth middleware caches user lookups in a module global (30s TTL).
    Clear it around every test so a user inserted/cached in one test can't leak
    into another that happens to reuse the same id."""
    from auth import auth_middleware
    auth_middleware._user_cache.clear()
    yield
    auth_middleware._user_cache.clear()
