"""
User service — CRUD operations for user profiles.
"""
import bcrypt
from mongoDb.connection import get_db
from bson import ObjectId
from gridfs import GridFS


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

def delete_user(user_id):
    """Delete a user account and associated data."""
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if user and 'profile_photo_id' in user:
        try:
            delete_file_from_drive(user['profile_photo_id'])
        except Exception:
            pass
    db.users.delete_one({'_id': ObjectId(user_id)})
    return True

from services.google_drive_service import upload_file_to_drive, delete_file_from_drive

def update_profile_photo(user_id, file):
    """Update user's profile photo in Google Drive."""
    db = get_db()
    
    # Check if user already has a photo
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if user and 'profile_photo_id' in user:
        try:
            delete_file_from_drive(user['profile_photo_id'])
        except Exception:
            pass
            
    # Save new file to Google Drive
    drive_res = upload_file_to_drive(file, file.filename, folder_type='profile', user_id=user_id)
    file_id = drive_res.get('id')
    photo_url = drive_res.get('webContentLink')
    
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'profile_photo_id': file_id, 'profile_photo_url': photo_url}}
    )
    return get_user_by_id(user_id)

