import os
import json
import time
import tempfile
from keras.applications import ResNet50
from keras.models import Sequential
from keras.layers import Dense, Flatten, GlobalAveragePooling2D, Dropout
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import SGD, Adam, RMSprop, Adagrad, Adadelta
from utils.saveTrainedModel import saveTrainedModel
from services.dataset_resolver import resolve_image_dataset_path


def _get_optimizer(validated_params):
    """Build optimizer from validated hyperparameters."""
    opt_type = validated_params.get('optimizer', 'adam')
    lr = float(validated_params.get('learning_rate', 0.0001))
    
    if opt_type == 'adam':
        return Adam(learning_rate=lr)
    elif opt_type == 'sgd':
        return SGD(learning_rate=lr)
    elif opt_type == 'rmsprop':
        return RMSprop(learning_rate=lr)
    elif opt_type == 'adagrad':
        return Adagrad(learning_rate=lr)
    elif opt_type == 'adadelta':
        return Adadelta(learning_rate=lr)
    else:
        return Adam(learning_rate=lr)


def train_resnet(request, validated_params, hidden_layer_array=None, class_mode='categorical', is_base_frozen=True, user_id=None, session_version=None):
    """Real implementation for ResNet50 deep learning model.
    
    Builds a ResNet50 transfer-learning model based on user-configured
    hyperparameters and hidden layers, trains on the user's dataset,
    and streams epoch progress via SSE.
    """
    data = request.json
    epochs = int(validated_params.get('epochs', 25))
    batch_size = int(validated_params.get('batch_size', 16))
    loss_type = validated_params.get('loss', 'categorical_crossentropy')
    
    filename = data.get('filename')
    file_path = data.get('filePath')
    input_shape = tuple(data.get('inputShape', (224, 224, 3)))

    yield f"data: {json.dumps({'log': f'ResNet50 Process initialized. Base Frozen: {is_base_frozen}'})}\n\n"

    # --- Resolve dataset path ---
    try:
        dataset_path = resolve_image_dataset_path(user_id, filename=filename, file_path=file_path)
    except FileNotFoundError as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    train_dataset_path = os.path.join(dataset_path, 'train')
    test_dataset_path = os.path.join(dataset_path, 'test')

    if not os.path.isdir(train_dataset_path):
        yield f"data: {json.dumps({'error': f'Train directory not found at {train_dataset_path}. Dataset must have train/ and test/ subdirectories.'})}\n\n"
        return

    try:
        # Data preparation
        train_datagen = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True)
        test_datagen = ImageDataGenerator(rescale=1./255)

        training_set = train_datagen.flow_from_directory(
            train_dataset_path,
            target_size=input_shape[:2],
            batch_size=batch_size,
            class_mode=class_mode
        )

        test_set = test_datagen.flow_from_directory(
            test_dataset_path,
            target_size=input_shape[:2],
            batch_size=batch_size,
            class_mode=class_mode
        )

        yield f"data: {json.dumps({'log': f'Found {training_set.samples} training images and {test_set.samples} validation images.'})}\n\n"

        # --- Build model ---
        yield f"data: {json.dumps({'log': 'Loading ResNet50 base model (pre-trained on ImageNet)...'})}\n\n"
        base_model = ResNet50(weights='imagenet', include_top=False, input_shape=input_shape)

        if is_base_frozen:
            for layer in base_model.layers:
                layer.trainable = False
            yield f"data: {json.dumps({'log': f'Base model frozen — {len(base_model.layers)} layers locked.'})}\n\n"
        else:
            yield f"data: {json.dumps({'log': f'Base model unfrozen — all {len(base_model.layers)} layers will be fine-tuned.'})}\n\n"

        model = Sequential()
        model.add(base_model)
        model.add(GlobalAveragePooling2D())

        # Add user-configured hidden layers
        if hidden_layer_array:
            for i, layer_config in enumerate(hidden_layer_array):
                units = int(layer_config.get('units', 256))
                activation = layer_config.get('activation', 'relu')
                dropout = float(layer_config.get('dropout', 0))
                model.add(Dense(units, activation=activation))
                if dropout > 0:
                    model.add(Dropout(dropout))
                yield f"data: {json.dumps({'log': f'  Added Dense({units}, activation={activation}) + Dropout({dropout})'})}\n\n"

        # Output layer
        num_classes = training_set.num_classes
        final_activation = 'softmax' if class_mode == 'categorical' else 'sigmoid'
        final_units = num_classes if class_mode == 'categorical' else 1
        model.add(Dense(final_units, activation=final_activation))

        yield f"data: {json.dumps({'log': f'Output layer: Dense({final_units}, activation={final_activation}) — {num_classes} classes detected.'})}\n\n"

        # Compile with user-selected optimizer and loss
        optimizer = _get_optimizer(validated_params)
        model.compile(optimizer=optimizer, loss=loss_type, metrics=['accuracy'])

        yield f"data: {json.dumps({'log': f'Model compiled. Optimizer: {validated_params.get("optimizer", "adam")}, Loss: {loss_type}, LR: {validated_params.get("learning_rate", 0.0001)}'})}\n\n"
        yield f"data: {json.dumps({'log': f'Starting Fine-Tuning for {epochs} epochs...'})}\n\n"

        # --- Training loop with early stopping ---
        best_val_loss = float('inf')
        patience = 3
        patience_counter = 0
        last_val_accuracy = 0
        last_val_loss = 0
        stopped_epoch = epochs

        for epoch in range(1, epochs + 1):
            try:
                history = model.fit(
                    training_set,
                    steps_per_epoch=len(training_set),
                    epochs=1,
                    validation_data=test_set,
                    validation_steps=len(test_set),
                    verbose=0
                )

                train_loss = history.history['loss'][0]
                train_acc = history.history.get('accuracy', history.history.get('acc', [0]))[0]
                val_loss = history.history.get('val_loss', [0])[0]
                val_acc = history.history.get('val_accuracy', history.history.get('val_acc', [0]))[0]

                last_val_accuracy = val_acc
                last_val_loss = val_loss

                yield f"data: {json.dumps({'log': f'Epoch [{epoch}/{epochs}] loss: {train_loss:.4f} - accuracy: {train_acc:.4f} - val_loss: {val_loss:.4f} - val_accuracy: {val_acc:.4f}'})}\n\n"

                # Use cross-platform temp directory for weights
                temp_weights_path = os.path.join(tempfile.gettempdir(), f'best_resnet_weights_{user_id or "guest"}.h5')
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    try:
                        model.save_weights(temp_weights_path)
                    except Exception:
                        pass
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        yield f"data: {json.dumps({'log': f'Early stopping triggered at epoch {epoch}. Restoring best weights...'})}\n\n"
                        try:
                            if os.path.exists(temp_weights_path):
                                model.load_weights(temp_weights_path)
                        except:
                            pass
                        stopped_epoch = epoch
                        break

                time.sleep(0.05)
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Training aborted during epoch {epoch}: {str(e)}'})}\n\n"
                return

        yield f"data: {json.dumps({'log': 'Training Complete. Saving model artifacts...'})}\n\n"

        save_path = saveTrainedModel(model, "resnet", "Keras", user_id=user_id, version=session_version)

        yield f"data: {json.dumps({'status': 'training_complete', 'accuracy': float(last_val_accuracy), 'loss': float(last_val_loss), 'epochs_trained': stopped_epoch, 'trained_model_path': save_path})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': f'ResNet Training failed: {str(e)}'})}\n\n"
