from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, AvgPool2D, Lambda
import keras.backend as K
from keras.metrics import Precision, Recall
from keras.optimizers import SGD, Adam, RMSprop, Adagrad, Adadelta
from keras.callbacks import EarlyStopping
from keras.preprocessing.image import ImageDataGenerator
from utils.saveTrainedModel import saveTrainedModel
import os

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
    ):
    classifier = Sequential()
    classifier.add(Conv2D(numberOfNeuronsInInputLayer, kernel_size=inputKernelSize, activation=inputLayerActivationFunction, input_shape=inputShape))

    for hiddenLayer in hiddenLayerArray:
        if hiddenLayer['type'] == 'conv':
            classifier.add(Conv2D(hiddenLayer['numberOfNeurons'], tuple(hiddenLayer['kernel']), activation=hiddenLayer['activationFunction']))
        elif hiddenLayer['type'] == 'pooling':
            pool_size = tuple(hiddenLayer.get('poolingSize', (2, 2)))
            if hiddenLayer['poolingType'] == 'maxPool':
                classifier.add(MaxPooling2D(pool_size=pool_size))
            elif hiddenLayer['poolingType'] == 'minPool':
                strides = tuple(hiddenLayer.get('minPoolStride', pool_size))
                classifier.add(min_pooling(pool_size=pool_size, strides=strides))
            elif hiddenLayer['poolingType'] in ['averagePool', 'avgPool']:
                strides = tuple(hiddenLayer.get('avgPoolStride', pool_size))
                classifier.add(AvgPool2D(pool_size=pool_size, strides=strides))
        elif hiddenLayer['type'] == 'flatten':
            classifier.add(Flatten())
        elif hiddenLayer['type'] == 'dense':
            classifier.add(Dense(units=hiddenLayer['units'], activation=hiddenLayer['activationFunction']))
        elif hiddenLayer['type'] == 'dropout':
            classifier.add(Dropout(hiddenLayer['dropoutRate']))

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
    numberOfEpochs = data['numberOfEpochs']
    batchSize = data['batchSize']
    classMode = data['classMode']
    datasetPath = data['filePath']

    train_dataset_path = os.path.join(datasetPath, 'train')
    test_dataset_path = os.path.join(datasetPath, 'test')

    model = build_cnn_model(
        numberOfNeuronsInInputLayer,
        inputKernelSize,
        inputLayerActivationFunction,
        inputShape,
        hiddenLayerArray,
        optimizerObject,
        lossFunction,
        evaluationMetrics,
    )

    import json
    import time
    yield f"data: {json.dumps({'log': 'Compiling Convolutional Neural Network Architecture...'})}\n\n"

    # Fitting the CNN
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

    yield f"data: {json.dumps({'log': f'Found {training_set.samples} training images and {test_set.samples} validation images in {train_dataset_path}.'})}\n\n"

    best_val_loss = float('inf')
    patience = 3
    patience_counter = 0
    total_epochs = int(numberOfEpochs)

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
                model.save_weights('/tmp/best_cnn_weights.h5')
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    yield f"data: {json.dumps({'log': f'Early stopping triggered at epoch {epoch}. Restoring best weights...'})}\n\n"
                    try:
                        model.load_weights('/tmp/best_cnn_weights.h5')
                    except:
                        pass
                    stopped_epoch = epoch
                    break
                    
            time.sleep(0.05)
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Training aborted during epoch {epoch}: {str(e)}'})}\n\n"
            return
            
    yield f"data: {json.dumps({'log': 'Training Complete. Saving model artifacts...'})}\n\n"
    
    # Save the model
    save_path = saveTrainedModel(model, "cnn", "Keras", user_id=user_id, version=session_version)

    yield f"data: {json.dumps({'status': 'completed', 'accuracy': float(last_val_accuracy), 'loss': float(last_val_loss), 'epochs_trained': stopped_epoch, 'trained_model_path': save_path})}\n\n"
