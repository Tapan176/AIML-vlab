"""
ANN (Artificial Neural Network) — Keras Sequential model for tabular data.
Supports configurable dense layers with dropout.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import Adam, SGD, RMSprop, Adagrad
from keras.callbacks import EarlyStopping
from utils.saveTrainedModel import saveTrainedModel
import os


def train_ann(request, validated_params=None, user_id=None, session_version=None):
    """Train an ANN on uploaded CSV data with user-configured layers."""
    data = request.json or {}

    # Extract parameters
    filename = data.get('filename')
    hidden_layers = data.get('hidden_layers', [{'units': 64, 'activation': 'relu'}])
    epochs = data.get('epochs', validated_params.get('epochs', 50) if validated_params else 50)
    batch_size = data.get('batch_size', validated_params.get('batch_size', 32) if validated_params else 32)
    optimizer_name = data.get('optimizer', validated_params.get('optimizer', 'adam') if validated_params else 'adam')
    loss_fn = data.get('loss', validated_params.get('loss', 'binary_crossentropy') if validated_params else 'binary_crossentropy')
    validation_split = validated_params.get('validation_split', 0.2) if validated_params else 0.2
    test_size = validated_params.get('test_size', 0.2) if validated_params else 0.2

    if not filename:
        raise ValueError("No dataset filename provided.")

    # Load dataset
    from services.dataset_service import get_dataset_df
    df = get_dataset_df(user_id, filename)

    # Use last column as target
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # Encode target if categorical
    label_encoder = None
    num_classes = 1
    if y.dtype == 'object' or str(y.dtype) == 'category':
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y)
    num_classes = len(np.unique(y))

    # Convert to numpy
    X = X.values.astype(float)
    y = np.array(y)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # One-hot encode target for categorical crossentropy
    if loss_fn == 'categorical_crossentropy' and num_classes > 2:
        from keras.utils import to_categorical
        y_train = to_categorical(y_train, num_classes)
        y_test = to_categorical(y_test, num_classes)
        output_units = num_classes
        output_activation = 'softmax'
    elif loss_fn == 'sparse_categorical_crossentropy':
        output_units = num_classes
        output_activation = 'softmax'
    else:
        output_units = 1
        output_activation = 'sigmoid'

    # Build model
    model = Sequential()
    input_dim = X_train.shape[1]

    for i, layer_config in enumerate(hidden_layers):
        units = int(layer_config.get('units', 64))
        activation = layer_config.get('activation', 'relu')
        dropout = layer_config.get('dropout', 0)

        if i == 0:
            model.add(Dense(units, activation=activation, input_dim=input_dim))
        else:
            model.add(Dense(units, activation=activation))

        if dropout and float(dropout) > 0:
            model.add(Dropout(float(dropout)))

    # Output layer
    model.add(Dense(output_units, activation=output_activation))

    # Optimizer
    optimizers = {
        'adam': Adam,
        'sgd': SGD,
        'rmsprop': RMSprop,
        'adagrad': Adagrad,
    }
    OptimizerClass = optimizers.get(optimizer_name, Adam)
    optimizer = OptimizerClass(learning_rate=0.001)

    # Compile
    metrics = ['accuracy']
    model.compile(optimizer=optimizer, loss=loss_fn, metrics=metrics)

    # Train
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    history = model.fit(
        X_train, y_train,
        epochs=int(epochs),
        batch_size=int(batch_size),
        validation_split=float(validation_split),
        callbacks=[early_stopping],
        verbose=0,
    )

    # Evaluate on test set
    eval_results = model.evaluate(X_test, y_test, verbose=0)
    test_loss = eval_results[0]
    test_accuracy = eval_results[1]

    # Save model
    model_path = saveTrainedModel(model, "ann", "Keras", user_id=user_id, version=session_version)

    return {
        'message': 'ANN model trained successfully.',
        'accuracy': float(test_accuracy),
        'loss': float(test_loss),
        'val_accuracy': float(history.history.get('val_accuracy', [0])[-1]),
        'val_loss': float(history.history.get('val_loss', [0])[-1]),
        'epochs_trained': len(history.history['loss']),
        'trained_model_path': model_path,
    }
