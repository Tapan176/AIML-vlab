def saveTrainedModel(model, filename, model_type):
  """Saves a trained model to a file with a suitable extension.

  Args:
    model: The trained model object.
    filename: The base path to save the model file (without extension).
    model_type: The type of model (e.g., "scikit-learn", "Keras", "PyTorch").
  """
  saveModelDirectory = f"trainedModels/"
  if model_type in ("scikit-learn", "nlp-learn"):
    import joblib
    extension = ".pkl"  # Pickle extension for scikit-learn models
    joblib.dump(model, saveModelDirectory + filename + extension)
  elif model_type in ("Keras", "TensorFlow"):
    extension = ".h5"  # HDF5 extension for Keras/TensorFlow models
    model.save(saveModelDirectory + filename + extension)
  elif model_type == "PyTorch":
    import torch
    extension = ".pt"  # PyTorch model weights extension
    torch.save(model.state_dict(), saveModelDirectory + filename + extension)
  else:
    raise NotImplementedError(f"Saving logic not implemented for {model_type} models yet.")
