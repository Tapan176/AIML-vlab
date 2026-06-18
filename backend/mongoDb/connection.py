from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = None
db = None


def init_db(client_factory=None):
    """Initialise the module-level Mongo client + db.

    client_factory: optional zero-arg callable returning a MongoClient-like
    object. Production passes nothing (a real MongoClient is created from
    MONGO_URI); tests pass ``mongomock.MongoClient`` to get an isolated
    in-memory database without touching a real server.
    """
    global client, db
    client = client_factory() if client_factory is not None else MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Ensure database integrity: email must be unique
    db.users.create_index("email", unique=True)
    return db


def get_db():
    return db


def close_connection():
    if client:
        client.close()
