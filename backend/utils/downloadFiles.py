def get_model_path(request):
    model_name = request.args.get('model_name')
    extension = request.args.get('extension')
    model_path = f'./trainedModels/{model_name}{extension}'
    return model_path
