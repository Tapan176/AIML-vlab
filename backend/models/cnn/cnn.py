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
            if hiddenLayer['poolingType'] == 'maxPool':
                classifier.add(MaxPooling2D(pool_size=tuple(hiddenLayer['poolingSize'])))
            elif hiddenLayer['poolingType'] == 'minPool':
                classifier.add(min_pooling(pool_size=tuple(hiddenLayer['poolingSize']), strides=tuple(hiddenLayer['minPoolStride'])))
            elif hiddenLayer['poolingType'] == 'averagePool':
                classifier.add(AvgPool2D(pool_size=tuple(hiddenLayer['poolingSize']), strides=tuple(hiddenLayer['avgPoolStride'])))
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

def train_cnn(request):
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

    # Fitting the CNN
    # Note: You should replace these paths with your actual dataset paths
    train_datagen = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True)
    test_datagen = ImageDataGenerator(rescale=1./255)

    training_set = train_datagen.flow_from_directory(train_dataset_path,
                                                     target_size=inputShape[:2],
                                                     batch_size=batchSize,
                                                     class_mode=classMode)

    test_set = test_datagen.flow_from_directory(test_dataset_path,
                                                target_size=inputShape[:2],
                                                batch_size=batchSize,
                                                class_mode=classMode)

    early_stopping = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

    model.fit_generator(training_set,
                        steps_per_epoch=len(training_set),
                        epochs=numberOfEpochs,
                        validation_data=test_set,
                        validation_steps=len(test_set),
                        callbacks=[early_stopping])

    # Save the model
    saveTrainedModel(model, "cnn", "Keras")
    # model.save("cnn.h5")

    return ({'message': 'Model trained successfully.'})
