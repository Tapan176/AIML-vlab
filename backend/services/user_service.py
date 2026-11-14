"""
User service — profile reads/updates, password change, photo, deletion.
"""
from datetime import datetime

import bcrypt
from bson import ObjectId

from mongoDb.connection import get_db
from auth.auth_middleware import invalidate_user_cache
from utils.validators import normalize_email, validate_password, clean_str, ValidationError

ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_PHOTO_BYTES = 5 * 1024 * 1024


def get_user_by_id(user_id):
    """Fetch user by ID, excluding secrets."""
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0, 'token_version': 0})
    if not user:
        raise Exception("user_not_found")
    user['_id'] = str(user['_id'])
    return user


def update_user_profile(user_id, data):
    """Update profile fields. Values are type/length checked (they used to be
    written verbatim, including dicts). Changing the email clears
    email_verified so the new address has to be proven again."""
    db = get_db()
    limits = {'first_name': 80, 'last_name': 80, 'phone': 32, 'countryCode': 8}
    update = {}
    for field, max_len in limits.items():
        if field in data:
            update[field] = clean_str(data[field], field, max_len, required=(field == 'first_name')) or ''

    if 'email' in data:
        email = normalize_email(data['email'])
        current = db.users.find_one({'_id': ObjectId(user_id)}, {'email': 1})
        if current and current.get('email') != email:
            if db.users.find_one({'email': email, '_id': {'$ne': ObjectId(user_id)}}, {'_id': 1}):
                raise ValidationError("email_already_in_use")
            update['email'] = email
            update['email_verified'] = False

    if not update:
        raise ValidationError("no_valid_fields_to_update")

    update['updated_at'] = datetime.utcnow()
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update})
    invalidate_user_cache(user_id)
    return get_user_by_id(user_id)


def change_password(user_id, old_password, new_password):
    """Change the password after verifying the old one.

    Revokes every other session (token_version bump) and returns a fresh JWT
    so the caller's own session continues seamlessly.
    """
    from auth.authController import generate_token
    validate_password(new_password)
    if not isinstance(old_password, str):
        raise ValidationError("incorrect_old_password")

    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise Exception("user_not_found")
    stored = user.get('password')
    if not stored or not bcrypt.checkpw(old_password.encode('utf-8'), stored.encode('utf-8')):
        raise ValidationError("incorrect_old_password")
    if bcrypt.checkpw(new_password.encode('utf-8'), stored.encode('utf-8')):
        raise ValidationError("new_password_same_as_old")

    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'password': hashed, 'password_changed_at': datetime.utcnow()},
         '$inc': {'token_version': 1}},
    )
    invalidate_user_cache(user_id)
    fresh = db.users.find_one({'_id': ObjectId(user_id)})
    return generate_token(fresh)


def verify_user_password(user_id, password):
    """True if `password` matches. Used to confirm destructive actions."""
    user = get_db().users.find_one({'_id': ObjectId(user_id)}, {'password': 1})
    stored = (user or {}).get('password')
    if not stored or not isinstance(password, str):
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
    except ValueError:
        return False


def delete_user(user_id):
    """Delete a user account AND all data it owns (see account_service)."""
    from services.account_service import purge_user_data
    return purge_user_data(user_id)


def update_profile_photo(user_id, file):
    """Replace the user's profile photo (stored on Google Drive)."""
    import os
    from services.google_drive_service import upload_file_to_drive, delete_file_from_drive

    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        raise ValidationError("unsupported_image_type")
    if not (file.mimetype or '').startswith('image/'):
        raise ValidationError("unsupported_image_type")
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_PHOTO_BYTES:
        raise ValidationError("image_too_large")

    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)}, {'profile_photo_id': 1})

    drive_res = upload_file_to_drive(file, f"profile{ext}", folder_type='profile', user_id=user_id)
    file_id = drive_res.get('id')

    # Delete the old photo only after the new one uploaded successfully.
    if user and user.get('profile_photo_id'):
        try:
            delete_file_from_drive(user['profile_photo_id'])
        except Exception:
            pass

    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'profile_photo_id': file_id, 'profile_photo_url': drive_res.get('webContentLink')}},
    )
    invalidate_user_cache(user_id)
    return get_user_by_id(user_id)
