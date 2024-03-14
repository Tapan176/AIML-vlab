from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, AvgPool2D, Lambda
import keras.backend as K
from keras.metrics import Precision, Recall
from keras.optimizers import SGD, Adam, RMSprop, Adagrad, Adadelta
from keras.callbacks import EarlyStopping
from keras.preprocessing.image import ImageDataGenerator
import os
# import zipfile
# from werkzeug.utils import secure_filename

from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)
CORS(app)

# UPLOAD_FOLDER = 'frontend/public/uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part'})

#     file = request.files['file']

#     if file.filename == '':
#         return jsonify({'error': 'No selected file'})

#     filename = secure_filename(file.filename)
#     filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     file.save(filepath)

#     if filename.endswith('.csv'):
#         # Parse CSV file and send data to frontend
#         csv_data = parse_csv(filepath)
#         return jsonify({'csv_data': csv_data})

#     elif filename.endswith('.zip'):
#         # Extract zip file
#         extracted_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted')
#         with zipfile.ZipFile(filepath, 'r') as zip_ref:
#             zip_ref.extractall(extracted_path)

#         # Get image links from extracted directory
#         image_links = get_image_links(extracted_path)
#         return jsonify({'image_links': image_links})

#     return jsonify({'message': 'File uploaded successfully'})

# def parse_csv(filepath):
#     # Parse CSV file and return data as list of dictionaries
#     csv_data = []
#     with open(filepath, 'r') as file:
#         lines = file.readlines()
#         headers = lines[0].strip().split(',')
#         for line in lines[1:]:
#             values = line.strip().split(',')
#             csv_data.append({header: value for header, value in zip(headers, values)})
#     return csv_data

# def get_image_links(directory):
#     # Get image links from directory (you may implement your logic to get image links)
#     image_links = []
#     for filename in os.listdir(directory):
#         if filename.endswith('.jpg') or filename.endswith('.png'):
#             image_links.append(os.path.join('uploads', 'extracted', filename))
#     return image_links

@app.route('/linear-regression', methods=['POST'])
def linear_regression():
    data = request.json
    X = np.array(data['X'])
    y = np.array(data['y'])

    # Fit linear regression model
    model = LinearRegression()
    model.fit(X.reshape(-1, 1), y)

    # Predict
    y_pred = model.predict(X.reshape(-1, 1))

    # Return results
    return jsonify({"coefficients": model.coef_.tolist(), "intercept": model.intercept_, "predictions": y_pred.tolist()})

# def build_cnn_model(input_shape, activation_function, layers):
#     classifier = Sequential()
#     classifier.add(Conv2D(32, (3, 3), input_shape=input_shape, activation=activation_function))

#     for layer in layers:
#         if layer['type'] == 'conv':
#             classifier.add(Conv2D(layer['filters'], (3, 3), activation=activation_function))
#         elif layer['type'] == 'maxpool':
#             classifier.add(MaxPooling2D(pool_size=(2, 2)))

#     classifier.add(Flatten())
#     classifier.add(Dense(units=128, activation=activation_function))
#     classifier.add(Dropout(0.5))
#     classifier.add(Dense(units=1, activation='sigmoid'))

#     optimizer = Adam(learning_rate=0.0001)
#     classifier.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])

#     return classifier

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

@app.route('/cnn', methods=['POST'])
def cnn():
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

    training_set = train_datagen.flow_from_directory('./models/Deep Learning/02. Convolutional Neural Networks (CNN)/dataset/training_set',
                                                     target_size=inputShape[:2],
                                                     batch_size=batchSize,
                                                     class_mode=classMode)

    test_set = test_datagen.flow_from_directory('./models/Deep Learning/02. Convolutional Neural Networks (CNN)/dataset/test_set',
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
    model.save("cnn.h5")

    return jsonify({'message': 'Model trained successfully.'})

@app.route('/download-trained-model', methods=['GET'])
def download_model():
    model_name = request.args.get('model_name')
    extension = request.args.get('extension')
    model_path = f'./trainedModels/{model_name}{extension}'
    return send_file(model_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
