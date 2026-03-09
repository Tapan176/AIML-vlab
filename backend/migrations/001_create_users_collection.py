"""
Migration: Create users collection with indexes.
"""


def up(db):
    """Create users collection and indexes."""
    # Create the collection if it doesn't exist
    if 'users' not in db.list_collection_names():
        db.create_collection('users')

    # Create unique index on email
    db.users.create_index('email', unique=True)

    print("    Created 'users' collection with email unique index")


def down(db):
    """Drop users collection."""
    db.drop_collection('users')
