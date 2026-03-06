import os
import io
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload, MediaFileUpload
from werkzeug.datastructures import FileStorage
from config import BASE_DIR

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# The ID of the root folder in Google Drive where app data will be stored.
# If None, the service will create an 'AIML_VLab_Data' folder in the root and use it.
APP_ROOT_FOLDER_ID = None

creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH', os.path.join(BASE_DIR, 'credentials.json'))
token_path = os.environ.get('GOOGLE_TOKEN_PATH', os.path.join(BASE_DIR, 'token.json'))

def get_drive_service():
    """Authenticate and return Google Drive v3 API service.
    Handles expired and revoked tokens gracefully.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"WARNING: Token refresh failed ({e}). Deleting stale token and re-authenticating...")
                # Delete the stale token so we can re-authenticate
                try:
                    os.remove(token_path)
                except Exception:
                    pass
                creds = None
        
        if not creds:
            if not os.path.exists(creds_path):
                print(f"WARNING: Google Drive credentials not found at {creds_path}. Drive integration will fail.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error connecting to Google Drive: {e}")
        return None

def get_or_create_app_folder(service):
    """Ensure the base app folder exists."""
    global APP_ROOT_FOLDER_ID
    if APP_ROOT_FOLDER_ID:
        return APP_ROOT_FOLDER_ID

    folder_name = 'AIML_VLab_Data'
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='nextPageToken, files(id, name)').execute()
    items = results.get('files', [])

    if not items:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        APP_ROOT_FOLDER_ID = folder.get('id')
    else:
        APP_ROOT_FOLDER_ID = items[0].get('id')
    
    return APP_ROOT_FOLDER_ID

def get_or_create_subfolder(service, parent_id, folder_name):
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])

    if not items:
        file_metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    else:
        return items[0].get('id')

def upload_file_to_drive(file_obj, filename, folder_type='datasets', user_id=None, subfolder=None):
    """
    Uploads a file to Google Drive.
    Folder hierarchy: AIML_VLab_Data / UserData / {user_id} / {folder_type} / [subfolder] /
    folder_type: 'datasets', 'trained_models', 'profile', etc.
    subfolder: optional extra nesting (e.g. session label for trained models).
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive service is not configured.")

    root_id = get_or_create_app_folder(service)

    if user_id:
        # UserData / {user_id} / {folder_type} [/ subfolder]
        user_data_id = get_or_create_subfolder(service, root_id, 'UserData')
        user_folder_id = get_or_create_subfolder(service, user_data_id, str(user_id))
        parent_folder_id = get_or_create_subfolder(service, user_folder_id, folder_type)
        print(f"DEBUG DIR: root={root_id} -> UserData={user_data_id} -> {user_id}={user_folder_id} -> {folder_type}={parent_folder_id}", flush=True)
        if subfolder:
            parent_folder_id = get_or_create_subfolder(service, parent_folder_id, subfolder)
            print(f"DEBUG DIR: subfolder={subfolder} -> {parent_folder_id}", flush=True)
    else:
        # Fallback for anonymous uploads: AIML_VLab_Data / {folder_type}
        parent_folder_id = get_or_create_subfolder(service, root_id, folder_type)
        print(f"DEBUG DIR: Anonymous -> folder_type={folder_type} -> {parent_folder_id}", flush=True)

    # 100MB chunks for scalable massive file streaming
    CHUNK_SIZE = 100 * 1024 * 1024 
    
    media = None
    if isinstance(file_obj, FileStorage):
        media = MediaIoBaseUpload(file_obj.stream, mimetype='application/octet-stream', chunksize=CHUNK_SIZE, resumable=True)
    elif isinstance(file_obj, str) and os.path.exists(file_obj):
        media = MediaFileUpload(file_obj, mimetype='application/octet-stream', chunksize=CHUNK_SIZE, resumable=True)
    elif hasattr(file_obj, 'read'):
        media = MediaIoBaseUpload(file_obj, mimetype='application/octet-stream', chunksize=CHUNK_SIZE, resumable=True)
    else:
        file_content = file_obj # Assume bytes
        media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='application/octet-stream', chunksize=CHUNK_SIZE, resumable=True)
    
    file_metadata = {
        'name': filename,
        'parents': [parent_folder_id]
    }

    # Upload iteratively in chunks to avoid OOM
    request = service.files().create(body=file_metadata, media_body=media, fields='id, webContentLink, webViewLink')
    response = None
    while response is None:
        status, response = request.next_chunk()
        
    file = response
    
    # Make it readable by anyone with the link so frontend can access images directly if needed
    try:
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'},
        ).execute()
    except Exception as e:
        print(f"Warning: Could not set public permission on file {filename}: {e}")
        
    return {
        'id': file.get('id'),
        'webContentLink': file.get('webContentLink'),
        'webViewLink': file.get('webViewLink')
    }

def download_file_from_drive(file_id, destination_path):
    """
    Downloads a file from Google Drive to the local path.
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive service is not configured.")

    request = service.files().get_media(fileId=file_id)
    CHUNK_SIZE = 100 * 1024 * 1024
    
    with open(destination_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=CHUNK_SIZE)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
    return destination_path

def stream_file_from_drive(file_id):
    """
    Streams a file from Google Drive into a BytesIO object. Returns (BytesIO, mimetype).
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive service is not configured.")

    request = service.files().get(fileId=file_id, fields='mimeType')
    file_metadata = request.execute()
    mime_type = file_metadata.get('mimeType', 'application/octet-stream')

    request = service.files().get_media(fileId=file_id)
    # Using SpooledTemporaryFile to spill to disk if > 100MB, avoiding RAM Exhaustion on 30GB Zips
    import tempfile
    CHUNK_SIZE = 100 * 1024 * 1024
    fh = tempfile.SpooledTemporaryFile(max_size=CHUNK_SIZE, mode='w+b')
    
    downloader = MediaIoBaseDownload(fh, request, chunksize=CHUNK_SIZE)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        
    fh.seek(0)
    return fh, mime_type

def delete_file_from_drive(file_id):
    """
    Deletes a file from Google Drive.
    """
    service = get_drive_service()
    if not service:
        raise Exception("Google Drive service is not configured.")
        
    try:
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting file from Drive: {e}")
        return False

def delete_session_folder_from_drive(file_id, expected_folder_name):
    """
    Finds the parent folder of a given file. If the parent folder matches 'expected_folder_name',
    it deletes the entire folder (which removes all files inside it). 
    """
    service = get_drive_service()
    if not service:
        return False
    try:
        file = service.files().get(fileId=file_id, fields='parents').execute()
        parents = file.get('parents')
        if parents:
            parent_id = parents[0]
            parent_folder = service.files().get(fileId=parent_id, fields='name').execute()
            if parent_folder.get('name') == expected_folder_name:
                service.files().delete(fileId=parent_id).execute()
                print(f"Deleted Drive folder {expected_folder_name}")
                return 'folder'
            else:
                # Fallback to just deleting the individual file if folder name mismatches
                service.files().delete(fileId=file_id).execute()
                return 'file'
        else:
            service.files().delete(fileId=file_id).execute()
            return 'file'
    except Exception as e:
        print(f"Error deleting session folder from Drive: {e}")
        return False
