"""
Training session service — manages per-user model training sessions with versioning.
"""
from datetime import datetime
from mongoDb.connection import get_db
from bson import ObjectId


def create_session(user_id, model_code, hyperparams, dataset_id=None):
    """Create a new training session for a user. Auto-increments version number."""
    db = get_db()

    # Get the latest version for this user + model combination
    latest = db.training_sessions.find_one(
        {'user_id': str(user_id), 'model_code': model_code},
        sort=[('version', -1)]
    )
    version = (latest['version'] + 1) if latest else 1

    session = {
        'user_id': str(user_id),
        'model_code': model_code,
        'version': version,
        'session_label': f"{model_code}_v{version}",
        'hyperparams': hyperparams,
        'dataset_id': str(dataset_id) if dataset_id else None,
        'results': None,
        'output_images': [],
        'trained_model_path': None,
        'predictions_path': None,
        'status': 'pending',
        'created_at': datetime.utcnow(),
        'completed_at': None,
    }

    result = db.training_sessions.insert_one(session)
    session['_id'] = str(result.inserted_id)
    return session


def update_session_results(session_id, results, output_images, model_path, predictions_path=None):
    """Update a training session with results after training completes."""
    db = get_db()

    db.training_sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {
            'results': results,
            'output_images': output_images,
            'trained_model_path': model_path,
            'predictions_path': predictions_path,
            'status': 'completed',
            'completed_at': datetime.utcnow(),
        }}
    )


def update_session_error(session_id, error_message):
    """Mark a training session as failed."""
    db = get_db()

    db.training_sessions.update_one(
        {'_id': ObjectId(session_id)},
        {'$set': {
            'status': 'failed',
            'error': error_message,
            'completed_at': datetime.utcnow(),
        }}
    )


def get_user_sessions(user_id, model_code=None):
    """Get all training sessions for a user, optionally filtered by model."""
    db = get_db()
    query = {'user_id': str(user_id)}
    if model_code:
        query['model_code'] = model_code

    sessions = list(db.training_sessions.find(query).sort('created_at', -1))

    for s in sessions:
        s['_id'] = str(s['_id'])

    return sessions


def get_session(session_id):
    """Get a single training session by ID."""
    db = get_db()
    session = db.training_sessions.find_one({'_id': ObjectId(session_id)})

    if not session:
        raise Exception("session_not_found")

    session['_id'] = str(session['_id'])
    return session
