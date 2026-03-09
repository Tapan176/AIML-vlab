"""
Database migration runner for ML-vlab.
Tracks applied migrations in a `_migrations` collection.
Run: python -m migrations.migration_runner
"""
import os
import sys
import importlib
from datetime import datetime

# Add parent directory to path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mongoDb.connection import init_db, get_db


MIGRATIONS_DIR = os.path.dirname(__file__)


def get_migration_files():
    """Get all migration files sorted by name."""
    files = []
    for f in sorted(os.listdir(MIGRATIONS_DIR)):
        if f.startswith('0') and f.endswith('.py'):
            files.append(f)
    return files


def get_applied_migrations(db):
    """Get list of already applied migration names."""
    collection = db['_migrations']
    return set(doc['name'] for doc in collection.find({}, {'name': 1}))


def run_migrations():
    """Run all pending migrations."""
    init_db()
    db = get_db()

    applied = get_applied_migrations(db)
    migration_files = get_migration_files()

    if not migration_files:
        print("No migration files found.")
        return

    pending = [f for f in migration_files if f.replace('.py', '') not in applied]

    if not pending:
        print("All migrations are up to date.")
        return

    print(f"Found {len(pending)} pending migration(s)...")

    for filename in pending:
        module_name = filename.replace('.py', '')
        print(f"  Running: {module_name}...", end=' ')

        try:
            # Import the migration module
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(MIGRATIONS_DIR, filename)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Run the 'up' function
            module.up(db)

            # Record the migration
            db['_migrations'].insert_one({
                'name': module_name,
                'applied_at': datetime.utcnow()
            })

            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            sys.exit(1)

    print(f"\nAll {len(pending)} migration(s) applied successfully.")


if __name__ == '__main__':
    run_migrations()
