import pandas as pd
from io import BytesIO
from mongoDb.connection import get_db
from services.google_drive_service import stream_file_from_drive, upload_file_to_drive
from services.dataset_service import save_dataset

def ensure_unique_filename(user_id, base_filename):
    """Appends a counter if the filename already exists."""
    db = get_db()
    name, ext = base_filename.rsplit('.', 1) if '.' in base_filename else (base_filename, '')
    
    counter = 1
    new_filename = base_filename
    while db.datasets.find_one({'user_id': str(user_id), 'filename': new_filename}):
        new_filename = f"{name}_processed_v{counter}.{ext}" if ext else f"{name}_processed_v{counter}"
        counter += 1
        
    return new_filename

def perform_preprocessing(current_user, dataset_id, operations):
    """
    Retrieves a dataset, applies a list of Pandas operations, 
    and saves the result as a new dataset in Google Drive.
    """
    db = get_db()
    from bson import ObjectId
    
    dataset = db.datasets.find_one({'_id': ObjectId(dataset_id), 'user_id': current_user['_id']})
    if not dataset:
        raise ValueError("Dataset not found or unauthorized")
        
    if dataset.get('file_type') != 'csv':
        raise ValueError("Preprocessing is currently only supported for CSV files.")
        
    # 1. Fetch dataframe natively from Google Drive
    if not dataset.get('drive_id'):
        raise ValueError("Dataset is missing Google Drive configuration.")
        
    fh, _ = stream_file_from_drive(dataset['drive_id'])
    df = pd.read_csv(fh)
    
    # 2. Apply Operations iteratively
    for op in operations:
        action = op.get('action')
        columns = op.get('columns', [])
        
        if not columns or len(columns) == 0:
            columns = df.columns # Apply to all if empty
            
        try:
            if action == 'dropna':
                df = df.dropna(subset=columns)
            
            elif action == 'fillna_mean':
                for col in columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df[col] = df[col].fillna(df[col].mean())
                        
            elif action == 'fillna_median':
                for col in columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df[col] = df[col].fillna(df[col].median())
                        
            elif action == 'fillna_mode':
                for col in columns:
                    df[col] = df[col].fillna(df[col].mode()[0])
                    
            elif action == 'drop_columns':
                df = df.drop(columns=[c for c in columns if c in df.columns])
                
            elif action == 'standard_scale':
                from sklearn.preprocessing import StandardScaler
                scaler = StandardScaler()
                num_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
                if num_cols:
                    df[num_cols] = scaler.fit_transform(df[num_cols])
                    
            elif action == 'minmax_scale':
                from sklearn.preprocessing import MinMaxScaler
                scaler = MinMaxScaler()
                num_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
                if num_cols:
                    df[num_cols] = scaler.fit_transform(df[num_cols])
                    
            elif action == 'label_encode':
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                for col in columns:
                    df[col] = le.fit_transform(df[col].astype(str))
                    
            elif action == 'one_hot_encode':
                df = pd.get_dummies(df, columns=[c for c in columns if c in df.columns])
                
        except Exception as e:
            raise ValueError(f"Failed to apply {action} on columns {columns}: {str(e)}")

    # 3. Export new dataframe to Bytes stream
    output_stream = BytesIO()
    df.to_csv(output_stream, index=False)
    output_stream.seek(0)
    
    # 4. Save to Google Drive
    new_filename = ensure_unique_filename(current_user['_id'], dataset['filename'])
    
    # Fake file-like object to satisfy googleapiclient which needs a read() interface
    class StreamFile:
        def __init__(self, stream): self.stream = stream
        def read(self): return self.stream.read()
            
    drive_res = upload_file_to_drive(StreamFile(output_stream), new_filename, folder_type='datasets', user_id=current_user['_id'])
    
    # 5. Record inside MongoDB catalogue
    new_dataset_meta = save_dataset(
        user_id=current_user['_id'], 
        filename=new_filename, 
        filepath="", # Deprecated by architecture
        file_type='csv', 
        drive_id=drive_res.get('id')
    )
    
    return new_dataset_meta
