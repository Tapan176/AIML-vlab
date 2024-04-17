import bcrypt
import jwt
from mongoDb.connection import get_db
from bson import ObjectId

def login(email, password):
    db = get_db()
    user = db.users.find_one({"email": email})
    
    if not user:
        raise Exception("user_not_found")
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        raise Exception("incorrect_password")

    # Convert ObjectId to string for JSON serialization
    user['_id'] = str(user['_id'])

    return user

def signup(first_name, last_name, email, password, phone, countryCode, termsAccepted,):
    db = get_db()
    existing_user = db.users.find_one({"email": email})
    
    if existing_user:
        raise Exception("user_already_exists")
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_password,
        "phone": phone,
        "countryCode": countryCode,
        "termsAccepted": termsAccepted,
    }
    
    # Insert user data into the database
    result = db.users.insert_one(user_data)

    # Get the inserted user's _id
    inserted_id = result.inserted_id

    # Convert ObjectId to string for serialization
    if isinstance(inserted_id, ObjectId):
        user_data['_id'] = str(inserted_id)  # Convert ObjectId to string

    return user_data['_id']

def forgot_password(email):
    db = get_db()
    user = db.users.find_one({"email": email})
    
    if not user:
        raise Exception("user_not_found")
    
    # Implement your token generation and email sending logic here
    reset_token = jwt.encode({"email": email}, 'your_secret_key').decode('utf-8')
    # Send email with reset link
    
    return user

def reset_password(token, new_password):
    db = get_db()
    decoded = jwt.decode(token, 'your_secret_key')
    
    user = db.users.find_one({"email": decoded['email']})
    
    if not user:
        raise Exception("user_not_found")
    
    if bcrypt.checkpw(new_password.encode('utf-8'), user['password'].encode('utf-8')):
        raise Exception("new_password_same_as_old_password")
    
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db.users.update_one({"email": decoded['email']}, {"$set": {"password": hashed_password}})
    
    return user
