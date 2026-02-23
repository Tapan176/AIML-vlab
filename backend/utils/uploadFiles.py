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
    
    # Remove the old files if it exists
    if os.path.exists(filepath):
        os.remove(filepath)

    file.save(filepath)

    if filename.endswith('.csv'):
        csv_data = parse_csv(filepath)
        drive_res = upload_file_to_drive(file, filename, folder_type='datasets', user_id=user_id)
        # record inside dataset registry
        save_dataset(user_id, filename, filepath, file_type='csv', csv_data=csv_data, drive_id=drive_res.get('id'))
        
        return ({'csv_data': csv_data, 'filename': filename, 'drive_id': drive_res.get('id')})

    elif filename.endswith('.zip'):
        extracted_path = os.path.join('static/uploads', 'extracted')
        extracted_file_path = os.path.join('static/uploads', 'extracted', remove_extension(filename))
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extracted_path)
        
        image_links = get_image_links(os.path.join(extracted_path, remove_extension(filename), 'train'))
        
        # upload raw zip to drive
        drive_res = upload_file_to_drive(filepath, filename, folder_type='datasets', user_id=user_id)
        # record inside dataset registry
        save_dataset(user_id, filename, filepath, file_type='zip', image_links=image_links, extracted_path=extracted_file_path, drive_id=drive_res.get('id'))

        return ({'image_links': image_links, 'filepath': extracted_path, 'filename': filename, 'extracted_file_path': extracted_file_path, 'drive_id': drive_res.get('id') })

    # Generic file
    drive_res = upload_file_to_drive(file, filename, folder_type='datasets', user_id=user_id)
    save_dataset(user_id, filename, filepath, file_type='other', drive_id=drive_res.get('id'))
    return ({'message': 'File uploaded successfully', 'filename': filename, 'drive_id': drive_res.get('id')})
