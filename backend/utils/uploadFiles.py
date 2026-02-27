import os
import zipfile
from werkzeug.utils import secure_filename
import glob
from concurrent.futures import ThreadPoolExecutor

def parse_csv(filepath):
    # Parse CSV file and return data as list of dictionaries
    csv_data = []
    with open(filepath, 'r') as file:
        lines = file.readlines()
        headers = lines[0].strip().split(',')
        for line in lines[1:]:
            values = line.strip().split(',')
            csv_data.append({header: value for header, value in zip(headers, values)})
    return csv_data

# def get_image_links(directory):
#     # Get image links from directory (you may implement your logic to get image links)
#     image_links = []
#     print(directory)
#     for root, dirs, files in os.walk(directory):
#         print(root)
#         print(files)
#         for filename in files:
#             if filename.endswith('.jpg') or filename.endswith('.png'):
#                 image_links.append(os.path.join(root, filename))
#     return image_links

# def get_image_links(directory):
#     # Get image links from directory using glob
#     print(directory)
#     image_links = []
#     file_patterns = ['*.jpg', '*.jpeg', '*.png']  # Add more patterns if needed
#     for pattern in file_patterns:
#         files = glob.glob(os.path.join(directory, '**', pattern), recursive=True)
#         image_links.extend(files)
#     return image_links

def get_image_links(directory):
    # Get image links from directory using ThreadPoolExecutor
    image_links = []
    file_patterns = ['*.jpg', '*.jpeg', '*.png']  # Add more patterns if needed
    with ThreadPoolExecutor() as executor:
        # Use executor.map to process file patterns in parallel
        for pattern in file_patterns:
            files = glob.glob(os.path.join(directory, '**', pattern), recursive=True)
            image_links.extend(files)
    return image_links

def remove_extension(filename):
    base_name, extension = os.path.splitext(filename)
    return base_name

from services.google_drive_service import upload_file_to_drive
from services.dataset_service import save_dataset

def handle_upload_file(request, user_id):
    if 'file' not in request.files:
        return ({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return ({'error': 'No selected file'})

    filename = secure_filename(file.filename)
    filepath = os.path.join('static/uploads', filename)
    
    # Ensure upload directory exists
    os.makedirs('static/uploads', exist_ok=True)
    
    # Remove the old file if it exists
    if os.path.exists(filepath):
        os.remove(filepath)

    file.save(filepath)

    # Helper: try uploading to Google Drive, but don't crash if it fails
    def _try_drive_upload(fpath, fname):
        try:
            return upload_file_to_drive(fpath, fname, folder_type='datasets', user_id=user_id)
        except Exception as e:
            print(f"WARNING: Google Drive upload failed for {fname}: {e}")
            return {}

    if filename.endswith('.csv'):
        csv_data = parse_csv(filepath)
        drive_res = _try_drive_upload(filepath, filename)
        save_dataset(user_id, filename, filepath, file_type='csv', csv_data=csv_data, drive_id=drive_res.get('id'))
        
        try:
            os.remove(filepath)
        except Exception:
            pass
            
        return ({'csv_data': csv_data, 'filename': filename, 'drive_id': drive_res.get('id')})

    elif filename.endswith('.zip'):
        extracted_path = os.path.join('static/uploads', 'extracted')
        extracted_file_path = os.path.join('static/uploads', 'extracted', remove_extension(filename))
        os.makedirs(extracted_path, exist_ok=True)
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extracted_path)
        
        image_links = get_image_links(os.path.join(extracted_path, remove_extension(filename), 'train'))
        
        drive_res = _try_drive_upload(filepath, filename)
        save_dataset(user_id, filename, filepath, file_type='zip', image_links=image_links, extracted_path=extracted_file_path, drive_id=drive_res.get('id'))

        import shutil
        try:
            shutil.rmtree(extracted_path, ignore_errors=True)
            os.remove(filepath)
        except Exception:
            pass

        return ({'image_links': image_links, 'filepath': extracted_path, 'filename': filename, 'extracted_file_path': extracted_file_path, 'drive_id': drive_res.get('id') })

    # Generic file
    drive_res = _try_drive_upload(filepath, filename)
    save_dataset(user_id, filename, filepath, file_type='other', drive_id=drive_res.get('id'))
    try:
        os.remove(filepath)
    except Exception:
        pass
    return ({'message': 'File uploaded successfully', 'filename': filename, 'drive_id': drive_res.get('id')})
