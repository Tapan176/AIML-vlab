from config import TRAINED_MODELS_DIR
import os

def get_model_path(request):
    model_name = request.args.get('model_name')
    extension = request.args.get('extension', '.pkl')
    user_id = request.args.get('user_id')
    version = request.args.get('version')
    
    if user_id:
        save_dir = os.path.join(TRAINED_MODELS_DIR, str(user_id))
    else:
        save_dir = TRAINED_MODELS_DIR
        
    filename = model_name
    if version:
        filename = f"{model_name}_v{version}"
        
    model_path = os.path.join(save_dir, filename + extension)
    return model_path
