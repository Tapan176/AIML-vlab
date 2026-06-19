"""Migration 007: partial TTL index for dead sessions — must spare completed runs.

The safety property under test: the TTL filter never covers 'completed' (carries
Drive artifact ids + history) or 'running' (active) sessions, so auto-cleanup
can't orphan Drive files or kill a live run.
"""
import importlib.util
import os


def _load_migration():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations', '007_session_ttl_cleanup.py',
    )
    spec = importlib.util.spec_from_file_location('m007', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ttl_filter_excludes_completed_and_running():
    m = _load_migration()
    assert 'completed' not in m.DEAD_STATUSES
    assert 'running' not in m.DEAD_STATUSES
    assert set(m.DEAD_STATUSES) == {'failed', 'cancelled', 'pending'}


def test_migration_creates_the_ttl_index(app, db):
    m = _load_migration()
    m.up(db)   # must not raise
    info = db.training_sessions.index_information()
    assert m.TTL_INDEX_NAME in info
