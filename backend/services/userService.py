"""
User service — CRUD operations for user profiles.
"""
import bcrypt
from mongoDb.connection import get_db
from bson import ObjectId


def get_user_by_id(user_id):
    """Fetch user by ID, excluding password."""
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)})

    if not user:
        raise Exception("user_not_found")

    user['_id'] = str(user['_id'])
    user.pop('password', None)
    return user


def update_user_profile(user_id, data):
    """Update user profile fields (first_name, last_name, phone, email, countryCode)."""
    db = get_db()

    # Only allow updating specific fields
    allowed_fields = {'first_name', 'last_name', 'phone', 'email', 'countryCode'}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        raise Exception("no_valid_fields_to_update")

    # If email is being changed, check for duplicates
    if 'email' in update_data:
        existing = db.users.find_one({
            'email': update_data['email'],
            '_id': {'$ne': ObjectId(user_id)}
        })
        if existing:
            raise Exception("email_already_in_use")

    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data}
    )

    return get_user_by_id(user_id)


def change_password(user_id, old_password, new_password):
    """Change user's password after verifying the old one."""
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)})

    if not user:
        raise Exception("user_not_found")

    # Verify old password
    if not bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
        raise Exception("incorrect_old_password")

    # Check new password is different
    if bcrypt.checkpw(new_password.encode('utf-8'), user['password'].encode('utf-8')):
        raise Exception("new_password_same_as_old")

    # Hash and save new password
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'password': hashed}}
    )

    return True
