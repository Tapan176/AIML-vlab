"""
Migration: Create training_sessions collection with indexes.
"""


def up(db):
    """Create training_sessions collection and indexes."""
    if 'training_sessions' not in db.list_collection_names():
        db.create_collection('training_sessions')

    # Index for querying user's sessions
    db.training_sessions.create_index('user_id')
    # Compound index for user + model
    db.training_sessions.create_index([('user_id', 1), ('model_code', 1)])
    # Index for ordering by creation date
    db.training_sessions.create_index('created_at')

    print("    Created 'training_sessions' collection with indexes")


def down(db):
    """Drop training_sessions collection."""
    db.drop_collection('training_sessions')
