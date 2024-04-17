from flask import request, jsonify
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')  # To avoid GUI when saving plots
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import csv
from utils.saveTrainedModel import saveTrainedModel

def get_column_names(csv_file):
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        column_names = next(reader)  # Read the first row which contains column names
    return column_names

def save_result_images(X, y, classifier, title, xlabel, ylabel, output_path):
    # Remove the old image if it exists
    if os.path.exists(output_path):
        os.remove(output_path)

    X_set, y_set = X, y
    X1, X2 = np.meshgrid(np.arange(start = X_set[:, 0].min() - 1, stop = X_set[:, 0].max() + 1, step = 0.01),
                        np.arange(start = X_set[:, 1].min() - 1, stop = X_set[:, 1].max() + 1, step = 0.01))
    plt.contourf(X1, X2, classifier.predict(np.array([X1.ravel(), X2.ravel()]).T).reshape(X1.shape), alpha = 0.75, cmap = ListedColormap(('red', 'green')))
    plt.xlim(X1.min(), X1.max())
    plt.ylim(X2.min(), X2.max())

    for i, j in enumerate(np.unique(y_set)):
        plt.scatter(X_set[y_set == j, 0], X_set[y_set == j, 1],
                    c = ListedColormap(('red', 'green'))(i), label = j)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def knn(request):
    data = request.json
    directory = 'static/uploads'

    X = None
    y = None

    if 'X' in data and 'y' in data:  # If X and y are provided
        X = np.array(data['X'])
        y = np.array(data['y'])
        X = X.reshape(-1, 1)
        columnNames = ['X', 'y']
    elif 'filename' in data:  # If filename is provided
        filepath = os.path.join(directory, data['filename'])
        columnNames = get_column_names(filepath)
        try:
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, [2, 3]].values
            y = dataset.iloc[:, 4].values
        except FileNotFoundError:
            return jsonify({"error": "File not found"})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"error": "Neither X and y nor filename provided"})

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=0)

    sc = StandardScaler()
    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)

    classifier = KNeighborsClassifier(n_neighbors = 5, metric = 'minkowski', p = 2)
    classifier.fit(X_train, y_train)
    
    saveTrainedModel(classifier, "knn", "scikit-learn") 

    y_pred = classifier.predict(X_test)

    confusion = confusion_matrix(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    outputImageDir = 'static/images'
    if not os.path.exists(outputImageDir):
        os.makedirs(outputImageDir)

    outputImageUrls = [
        os.path.join(outputImageDir, 'knnTrainGraph.jpg'),
        os.path.join(outputImageDir, 'knnTestGraph.jpg')
    ]

    # print(columnNames)

    save_result_images(X_train, y_train, classifier, title='Training', xlabel=columnNames[2], ylabel=columnNames[3], output_path=outputImageUrls[0])
    save_result_images(X_test, y_test, classifier, title='Test', xlabel=columnNames[2], ylabel=columnNames[3], output_path=outputImageUrls[1])

    return {
        "predictions": y_pred.tolist(),
        "confusion_matrix": confusion.tolist(),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "outputImageUrls": outputImageUrls
    }
