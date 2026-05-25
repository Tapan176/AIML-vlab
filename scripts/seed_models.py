import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from mongoDb.connection import init_db, get_db
from services.model_catalog import get_model_catalog, MODEL_CATALOG_VERSION


def seed():
    init_db()
    db = get_db()
    models_data = get_model_catalog()

    db.models.delete_many({})
    db.models.insert_many(models_data)
    print(f"Seeded {len(models_data)} models into MongoDB with metadata_version={MODEL_CATALOG_VERSION}.")


if __name__ == "__main__":
    seed()
