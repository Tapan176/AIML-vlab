import os
import zipfile
from werkzeug.utils import secure_filename

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

def get_image_links(directory):
    # Get image links from directory (you may implement your logic to get image links)
    image_links = []
    print(directory)
    for root, dirs, files in os.walk(directory):
        print(root)
        print(files)
        for filename in files:
            if filename.endswith('.jpg') or filename.endswith('.png'):
                image_links.append(os.path.join(root, filename))
    return image_links

def remove_extension(filename):
    base_name, extension = os.path.splitext(filename)
    return base_name

def handle_upload_file(request):
    if 'file' not in request.files:
        return ({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return ({'error': 'No selected file'})

    filename = secure_filename(file.filename)
    filepath = os.path.join('static/uploads', filename)
    file.save(filepath)

    if filename.endswith('.csv'):
        # Parse CSV file and send data to frontend
        csv_data = parse_csv(filepath)
        return ({'csv_data': csv_data, 'filename': filename})

    elif filename.endswith('.zip'):
        # Extract zip file
        extracted_path = os.path.join('static/uploads', 'extracted')
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extracted_path)
        
        # Get image links from extracted directory
        image_links = get_image_links(os.path.join(extracted_path, remove_extension(filename), 'train'))

        return ({'image_links': image_links, 'filepath': extracted_path})

    return ({'message': 'File uploaded successfully', 'filename': filename})
