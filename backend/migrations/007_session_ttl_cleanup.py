"""
Migration: TTL auto-cleanup for dead / abandoned training sessions.

Adds a TTL index on training_sessions.created_at that expires ONLY sessions in a
junk-terminal or never-started state — failed, cancelled, or pending — after a
retention window. Completed (and in-flight running) sessions are deliberately
EXCLUDED via a partialFilterExpression.

Why not TTL completed runs: a completed session carries the user's run history
plus Drive artifact ids (trained model + results zip). A blind TTL would delete
the DB record while leaving those Drive files orphaned, AND erase history the
owner is entitled to keep. Proper cleanup of completed runs needs a retention
job that also deletes the Drive artifacts (roadmap item E) — not an index.

failed/cancelled/pending sessions never reach update_session_results, so they
have NO Drive artifacts — safe to drop once they're old.

Defensive: partial TTL needs MongoDB 3.2+; on an engine that rejects the options
(e.g. mongomock) we log + skip so the rest of the migration run isn't blocked.
"""

# 30 days — long enough to still inspect a recent failure, short enough that
# abandoned/failed junk doesn't pile up forever.
TTL_SECONDS = 30 * 24 * 60 * 60
TTL_INDEX_NAME = 'ttl_dead_sessions'
DEAD_STATUSES = ['failed', 'cancelled', 'pending']


def up(db):
    try:
        db.training_sessions.create_index(
            [('created_at', 1)],
            name=TTL_INDEX_NAME,
            expireAfterSeconds=TTL_SECONDS,
            partialFilterExpression={'status': {'$in': DEAD_STATUSES}},
        )
        print(f"    Added TTL index {TTL_INDEX_NAME} on training_sessions "
              f"(status in {DEAD_STATUSES}, expire after {TTL_SECONDS}s); "
              f"completed/running runs untouched")
    except Exception as e:  # noqa: BLE001 - report, don't abort the run
        print(f"    WARN: TTL index {TTL_INDEX_NAME} not created ({e}); skipping")


def down(db):
    try:
        db.training_sessions.drop_index(TTL_INDEX_NAME)
    except Exception:
        pass
