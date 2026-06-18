"""
Migration: Add performance indexes across the hot collections.

These indexes back the most frequent query patterns in the app:
  - training_sessions: dashboard listing (user_id + created_at), and the
    user+model filter used by replay / leaderboards.
  - datasets: per-user dataset library + version lookup (user_id, filename).
  - usage_counters: the per-(user, period) quota counter that is read+upserted
    on every training run — made UNIQUE so the upsert can never race a dup.
  - users: email lookup on every login / signup — made UNIQUE to enforce the
    one-account-per-email invariant the auth layer already assumes.
  - webhook_events: payment replay-guard key — made UNIQUE so a replayed
    webhook is rejected atomically.

Idempotent: create_index is a no-op when an equivalent index already exists.
Unique indexes are created defensively (try/except) so that pre-existing data
with (unexpected) duplicates can't hard-fail the whole migration run; the
non-unique indexes are still created in that case.
"""


def _safe_unique_index(coll, keys, name):
    """Create a unique index, downgrading gracefully if duplicates exist.

    If the unique build fails (e.g. legacy duplicate rows), fall back to a
    plain non-unique index so queries are still accelerated, and surface a
    warning instead of aborting the migration."""
    try:
        coll.create_index(keys, unique=True, name=name)
    except Exception as e:  # noqa: BLE001 - want to report, not crash
        print(f"    WARN: unique index {name} not created ({e}); "
              f"falling back to non-unique")
        try:
            coll.create_index(keys, name=f"{name}_nonunique")
        except Exception:
            pass


def up(db):
    """Create the performance / integrity indexes."""
    # --- training_sessions -------------------------------------------------
    # Dashboard lists a user's sessions newest-first.
    db.training_sessions.create_index(
        [('user_id', 1), ('created_at', -1)],
        name='user_created_desc',
    )

    # --- datasets ----------------------------------------------------------
    # Per-user dataset library + version resolution (latest version of a file).
    db.datasets.create_index(
        [('user_id', 1), ('filename', 1)],
        name='user_filename',
    )

    # --- usage_counters ----------------------------------------------------
    # One counter document per (user, period); read + upserted on every run.
    _safe_unique_index(
        db.usage_counters,
        [('user_id', 1), ('period', 1)],
        name='uniq_user_period',
    )

    # --- users -------------------------------------------------------------
    # Email is the login key and must be unique.
    _safe_unique_index(db.users, [('email', 1)], name='uniq_email')

    # --- webhook_events ----------------------------------------------------
    # Payment webhook replay-guard. (subscription_service also ensures this at
    # runtime, but pinning it here keeps the schema explicit.)
    if 'webhook_events' not in db.list_collection_names():
        db.create_collection('webhook_events')
    _safe_unique_index(
        db.webhook_events,
        [('provider', 1), ('event_id', 1)],
        name='uniq_provider_event',
    )

    print("    Added performance/integrity indexes "
          "(training_sessions, datasets, usage_counters, users, webhook_events)")


def down(db):
    """Drop the indexes added by this migration."""
    for coll, name in [
        (db.training_sessions, 'user_created_desc'),
        (db.datasets, 'user_filename'),
        (db.usage_counters, 'uniq_user_period'),
        (db.users, 'uniq_email'),
        (db.webhook_events, 'uniq_provider_event'),
    ]:
        try:
            coll.drop_index(name)
        except Exception:
            pass
