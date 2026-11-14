from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = None
db = None


def init_db():
    global client, db
    # Explicit timeouts so a bad URI / unreachable cluster fails a request in
    # seconds instead of hanging a worker for the 30 s pymongo default.
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=60000,
        maxPoolSize=50,
        retryWrites=True,
    )
    db = client[DB_NAME]

    # Ensure database integrity: email must be unique
    db.users.create_index("email", unique=True)


def get_db():
    return db


def close_connection():
    if client:
        client.close()
