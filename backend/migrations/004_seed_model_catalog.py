"""
Migration: Seed the `models` collection from the canonical catalog.

Makes MongoDB the runtime source of truth for model info (used by the in-app
ModelInfoPanel drawer and any future catalog consumers). The catalog code in
`services/model_catalog.py` remains the AUTHORING source — this migration just
materialises it into the DB so the API can read from one place.

Idempotent + version-aware:
  - Upserts one document per model, keyed by `code`.
  - Each doc carries `metadata_version` (== MODEL_CATALOG_VERSION). Bumping that
    constant and re-running migrations refreshes every stale document.
  - Includes the fine-tuning models (bert_finetune, distilbert_finetune,
    vit_finetune) with the same structure as every other model.

Note: this migration is recorded once in `_migrations`, so it runs a single
time. To force a re-seed after editing the catalog, bump MODEL_CATALOG_VERSION
and add a follow-up migration (or run scripts/seed/equivalent), keeping the
migration ledger honest.
"""
import os
import sys

# Allow `from services...` when run via the migration runner.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.model_catalog import get_model_catalog, MODEL_CATALOG_VERSION


def up(db):
    """Create the `models` collection (if needed) and upsert the catalog."""
    if 'models' not in db.list_collection_names():
        db.create_collection('models')

    # Unique lookup key — model `code` is the stable identifier the frontend
    # and training routes use everywhere.
    db.models.create_index('code', unique=True)

    catalog = get_model_catalog()
    upserted = 0
    for model in catalog:
        code = model.get('code')
        if not code:
            continue
        # Ensure version is stamped even if the generator changes later.
        model['metadata_version'] = MODEL_CATALOG_VERSION
        db.models.update_one(
            {'code': code},
            {'$set': model},
            upsert=True,
        )
        upserted += 1

    print(f"    Seeded 'models' collection ({upserted} models, v{MODEL_CATALOG_VERSION})")


def down(db):
    """Drop the `models` collection."""
    db.drop_collection('models')
