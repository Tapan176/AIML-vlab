import json
import os
import sys

# Add backend directory to path so we can import config & mongoDb
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mongoDb.connection import init_db, get_db

def seed():
    init_db()
    db = get_db()
    
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'components', 'models.json')
    
    with open(json_path, 'r', encoding='utf-8') as f:
        models_data = json.load(f)
        
    db.models.delete_many({})
    db.models.insert_many(models_data)
    print(f"Successfully seeded {len(models_data)} models into MongoDB.")

if __name__ == '__main__':
    seed()
