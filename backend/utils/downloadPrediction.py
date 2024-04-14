def get_model_predictions(request):
    model_name = request.args.get('model_name')
    extension = request.args.get('extension')
    model_path = f'predictions/{model_name}{extension}'
    return model_path
