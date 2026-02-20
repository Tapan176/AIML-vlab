from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = None
db = None


def init_db():
    global client, db
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]


def get_db():
    return db


def close_connection():
    if client:
        client.close()
