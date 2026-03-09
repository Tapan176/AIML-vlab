"""
Migration: Create datasets collection with indexes.
"""


def up(db):
    """Create datasets collection and indexes."""
    if 'datasets' not in db.list_collection_names():
        db.create_collection('datasets')

    # Index for querying user's datasets
    db.datasets.create_index('user_id')
    # Index for ordering by upload date
    db.datasets.create_index('uploaded_at')

    print("    Created 'datasets' collection with indexes")


def down(db):
    """Drop datasets collection."""
    db.drop_collection('datasets')
