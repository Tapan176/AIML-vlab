import json
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
OUTPUT_PATH = os.path.join(REPO_ROOT, "docs", "model_catalog.mongoimport.json")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.model_catalog import get_model_catalog


def export_json():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    catalog = get_model_catalog()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, indent=2, ensure_ascii=False)
    print(f"Wrote {len(catalog)} model documents to {OUTPUT_PATH}")


if __name__ == "__main__":
    export_json()
