from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, AvgPool2D, Lambda
import keras.backend as K
from keras.metrics import Precision, Recall
from keras.optimizers import SGD, Adam, RMSprop, Adagrad, Adadelta
from keras.callbacks import EarlyStopping
from keras.preprocessing.image import ImageDataGenerator
from utils.saveTrainedModel import saveTrainedModel
import os
import tempfile

# Define a Min Pooling Layer with customizable parameters
def min_pooling(pool_size=(2, 2), strides=None):
    def min_pooling_fn(x):
        return K.pool2d(x, pool_size=pool_size, strides=strides, padding='valid', pool_mode='min')
    return Lambda(min_pooling_fn)

# Define F1 score function
def f1_score(y_true, y_pred):
    precision = Precision()(y_true, y_pred)
    recall = Recall()(y_true, y_pred)
    return 2 * ((precision * recall) / (precision + recall + K.epsilon()))

def build_cnn_model(
        numberOfNeuronsInInputLayer,
        inputKernelSize,
        inputLayerActivationFunction,
        inputShape,
        hiddenLayerArray,
        optimizerObject,
        lossFunction,
        evaluationMetrics,
        num_classes=None,
    ):
    classifier = Sequential()
    classifier.add(Conv2D(numberOfNeuronsInInputLayer, kernel_size=inputKernelSize, activation=inputLayerActivationFunction, input_shape=inputShape))

    has_flatten = False
    for hiddenLayer in hiddenLayerArray:
        layer_type = hiddenLayer['type']
        if layer_type == 'conv':
            classifier.add(Conv2D(hiddenLayer.get('numberOfNeurons', 64), tuple(hiddenLayer.get('kernel', [3, 3])), activation=hiddenLayer.get('activationFunction', 'relu')))
        elif layer_type in ('pooling', 'pool'):
            pool_size = tuple(hiddenLayer.get('poolingSize', (2, 2)))
            pooling_type = hiddenLayer.get('poolingType', 'maxPool').replace('Pool', '')
            if pooling_type in ('maxPool', 'max'):
                classifier.add(MaxPooling2D(pool_size=pool_size))
            elif pooling_type in ('minPool', 'min'):
                strides = tuple(hiddenLayer.get('minPoolStride', pool_size))
                classifier.add(min_pooling(pool_size=pool_size, strides=strides))
            elif pooling_type in ('averagePool', 'avgPool', 'avg', 'average'):
                strides = tuple(hiddenLayer.get('avgPoolStride', pool_size))
                classifier.add(AvgPool2D(pool_size=pool_size, strides=strides))
        elif layer_type == 'flatten':
            classifier.add(Flatten())
            has_flatten = True
        elif layer_type == 'dense':
            # Ensure flatten before dense if not already done
            if not has_flatten:
                classifier.add(Flatten())
                has_flatten = True
            units = hiddenLayer.get('units') or hiddenLayer.get('numberOfNeurons', 128)
            classifier.add(Dense(units=int(units), activation=hiddenLayer.get('activationFunction', 'relu')))
        elif layer_type == 'dropout':
            classifier.add(Dropout(hiddenLayer.get('dropoutRate', 0.5)))

    # Ensure flatten before output layer if not already done
    if not has_flatten:
        classifier.add(Flatten())

    # Output layer for classification: must match dataset num_classes
    if num_classes is not None and lossFunction['type'] in ('categorical_crossentropy', 'sparse_categorical_crossentropy'):
        classifier.add(Dense(units=int(num_classes), activation='softmax'))
    elif num_classes is not None and lossFunction['type'] == 'binary_crossentropy':
        classifier.add(Dense(units=1, activation='sigmoid'))

    # Determine the optimizer based on the 'type' parameter in optimizerObject
    if optimizerObject['type'] == 'adam':
        optimizer = Adam(learning_rate=optimizerObject['learning_rate'])
    elif optimizerObject['type'] == 'sgd':
        optimizer = SGD(learning_rate=optimizerObject['learning_rate'], momentum=optimizerObject.get('momentum', 0.0))
    elif optimizerObject['type'] == 'rmsprop':
        optimizer = RMSprop(learning_rate=optimizerObject['learning_rate'])
    elif optimizerObject['type'] == 'adagrad':
        optimizer = Adagrad(learning_rate=optimizerObject['learning_rate'])
    elif optimizerObject['type'] == 'adadelta':
        optimizer = Adadelta(learning_rate=optimizerObject['learning_rate'])
    else:
        raise ValueError("Unsupported optimizer type.")
    
    if lossFunction['type'] == 'mean_squared_error':
        loss_function = 'mean_squared_error'
    
    # Determine the loss function based on the 'type' parameter in lossFunction
    if lossFunction['type'] == 'mean_squared_error':
        loss_function = 'mean_squared_error'
    elif lossFunction['type'] == 'binary_crossentropy':
        loss_function = 'binary_crossentropy'
    elif lossFunction['type'] == 'categorical_crossentropy':
        loss_function = 'categorical_crossentropy'
    elif lossFunction['type'] == 'sparse_categorical_crossentropy':
        loss_function = 'sparse_categorical_crossentropy'
    else:
        raise ValueError("Unsupported loss function type.")

    # Determine the evaluation metrics based on the types specified in metrics_params
    metrics_list = []
    for metric_type in evaluationMetrics:
        if metric_type == 'accuracy':
            metrics_list.append('accuracy')
        elif metric_type == 'precision':
            metrics_list.append(Precision())
        elif metric_type == 'recall':
            metrics_list.append(Recall())
        elif metric_type == 'f1':
            metrics_list.append(f1_score)
        # Add more conditions for other metric types as needed
        else:
            raise ValueError("Unsupported metric type.")

    # Compile the model with the determined optimizer
    classifier.compile(optimizer=optimizer, loss=loss_function, metrics=metrics_list)

    return classifier

def train_cnn(request, validated_params=None, user_id=None, session_version=None):
    data = request.json
    # input_shape = tuple(data['inputShape'])
    numberOfNeuronsInInputLayer = data['numberOfNeuronsInInputLayer']
    inputKernelSize = tuple(data['inputKernelSize'])
    inputLayerActivationFunction = data['inputLayerActivationFunction']
    inputShape = tuple(data['inputShape'])
    hiddenLayerArray = data['hiddenLayerArray']
    optimizerObject = data['optimizerObject']
    lossFunction = data['lossFunction']
    evaluationMetrics = data['evaluationMetrics']
    # Use validated hyperparameters for epochs and batch_size (from frontend hyperparams.epochs/batch_size)
    numberOfEpochs = int(validated_params.get('epochs', data.get('numberOfEpochs', 50))) if validated_params else int(data.get('numberOfEpochs', 50))
    batchSize = int(validated_params.get('batch_size', data.get('batchSize', 32))) if validated_params else int(data.get('batchSize', 32))
    classMode = data['classMode']
    
    filename = data.get('filename')
    file_path = data.get('filePath')

    # Resolve dataset path from Drive/DB/local
    from services.dataset_resolver import resolve_image_dataset_path
    
    import json
    import time
    
    yield f"data: {json.dumps({'log': 'Resolving dataset and loading image directories...'})}\n\n"
    
    try:
        datasetPath = resolve_image_dataset_path(user_id, filename=filename, file_path=file_path)
    except FileNotFoundError as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    train_dataset_path = os.path.join(datasetPath, 'train')
    test_dataset_path = os.path.join(datasetPath, 'test')

    train_datagen = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True)
    test_datagen = ImageDataGenerator(rescale=1./255)

    try:
        training_set = train_datagen.flow_from_directory(train_dataset_path,
                                                        target_size=inputShape[:2],
                                                        batch_size=batchSize,
                                                        class_mode=classMode)

        test_set = test_datagen.flow_from_directory(test_dataset_path,
                                                    target_size=inputShape[:2],
                                                    batch_size=batchSize,
                                                    class_mode=classMode)
    except Exception as e:
        yield f"data: {json.dumps({'error': f'Failed to load image directory: {str(e)}'})}\n\n"
        return

    num_classes = training_set.num_classes
    yield f"data: {json.dumps({'log': f'Found {training_set.samples} training images and {test_set.samples} validation images. Classes: {num_classes}'})}\n\n"

    yield f"data: {json.dumps({'log': 'Compiling Convolutional Neural Network Architecture...'})}\n\n"

    model = build_cnn_model(
        numberOfNeuronsInInputLayer,
        inputKernelSize,
        inputLayerActivationFunction,
        inputShape,
        hiddenLayerArray,
        optimizerObject,
        lossFunction,
        evaluationMetrics,
        num_classes=num_classes,
    )

    best_val_loss = float('inf')
    patience = 3
    patience_counter = 0
    total_epochs = int(numberOfEpochs)
    
    # Use a cross-platform temp directory for weights
    temp_weights_path = os.path.join(tempfile.gettempdir(), f'best_cnn_weights_{user_id or "guest"}.h5')

    yield f"data: {json.dumps({'log': f'Starting CNN Training for {total_epochs} epochs...'})}\n\n"

    last_val_accuracy = 0
    last_val_loss = 0
    stopped_epoch = total_epochs

    for epoch in range(1, total_epochs + 1):
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

            yield f"data: {json.dumps({'log': f'Epoch [{epoch}/{total_epochs}] loss: {train_loss:.4f} - accuracy: {train_acc:.4f} - val_loss: {val_loss:.4f} - val_accuracy: {val_acc:.4f}'})}\n\n"

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                try:
                    model.save_weights(temp_weights_path)
                except Exception as save_err:
                    yield f"data: {json.dumps({'log': f'Warning: Could not save checkpoint weights: {save_err}'})}\n\n"
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
    
    # Clean up temp weights file
    try:
        if os.path.exists(temp_weights_path):
            os.remove(temp_weights_path)
    except:
        pass
            
    yield f"data: {json.dumps({'log': 'Training Complete. Saving model artifacts...'})}\n\n"
    
    # Save the model
    save_path = saveTrainedModel(model, "cnn", "Keras", user_id=user_id, version=session_version)

    yield f"data: {json.dumps({'status': 'training_complete', 'accuracy': float(last_val_accuracy), 'loss': float(last_val_loss), 'epochs_trained': stopped_epoch, 'trained_model_path': save_path})}\n\n"
