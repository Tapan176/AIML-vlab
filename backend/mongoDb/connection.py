from pymongo import MongoClient
import os

# MongoDB connection URL, change this as per your MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'aiml-lab')

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
