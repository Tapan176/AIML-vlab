from flask import jsonify
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import csv
from utils.saveTrainedModel import saveTrainedModel
from config import UPLOAD_DIR, IMAGES_DIR, ensure_dir


def get_column_names(csv_file):
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        column_names = next(reader)
    return column_names


def save_result_images(X, y, classifier, title, xlabel, ylabel, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)
    X_set, y_set = X, y
    X1, X2 = np.meshgrid(np.arange(start=X_set[:, 0].min() - 1, stop=X_set[:, 0].max() + 1, step=0.01),
                          np.arange(start=X_set[:, 1].min() - 1, stop=X_set[:, 1].max() + 1, step=0.01))
    plt.contourf(X1, X2, classifier.predict(np.array([X1.ravel(), X2.ravel()]).T).reshape(X1.shape), alpha=0.75, cmap=ListedColormap(('red', 'green')))
    plt.xlim(X1.min(), X1.max())
    plt.ylim(X2.min(), X2.max())
    for i, j in enumerate(np.unique(y_set)):
        plt.scatter(X_set[y_set == j, 0], X_set[y_set == j, 1], c=ListedColormap(('red', 'green'))(i), label=j)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.savefig(output_path)
    plt.close()


def knn(request, validated_params=None, user_id=None, session_version=None):
    data = request.json

    params = validated_params or {}
    n_neighbors = params.get('n_neighbors', 5)
    metric = params.get('metric', 'minkowski')
    p = params.get('p', 2)
    weights = params.get('weights', 'uniform')
    test_size = params.get('test_size', 0.25)
    random_state = params.get('random_state', 0)

    X = None
    y = None

    if 'X' in data and 'y' in data:
        X = np.array(data['X'])
        y = np.array(data['y'])
        X = X.reshape(-1, 1)
        columnNames = ['X', 'y']
    elif 'filename' in data:
        filepath = os.path.join(UPLOAD_DIR, data['filename'])
        columnNames = get_column_names(filepath)
        try:
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, [2, 3]].values
            y = dataset.iloc[:, 4].values
        except FileNotFoundError:
            return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Neither X and y nor filename provided"}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    sc = StandardScaler()
    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)

    classifier = KNeighborsClassifier(n_neighbors=n_neighbors, metric=metric, p=p, weights=weights)
    classifier.fit(X_train, y_train)

    model_path = saveTrainedModel(classifier, "knn", "scikit-learn", user_id=user_id, version=session_version)

    y_pred = classifier.predict(X_test)

    confusion = confusion_matrix(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    img_dir = ensure_dir(IMAGES_DIR)
    outputImageUrls = [
        os.path.join(img_dir, 'knnTrainGraph.jpg'),
        os.path.join(img_dir, 'knnTestGraph.jpg')
    ]

    save_result_images(X_train, y_train, classifier, title='Training', xlabel=columnNames[2], ylabel=columnNames[3], output_path=outputImageUrls[0])
    save_result_images(X_test, y_test, classifier, title='Test', xlabel=columnNames[2], ylabel=columnNames[3], output_path=outputImageUrls[1])

    return {
        "predictions": y_pred.tolist(),
        "confusion_matrix": confusion.tolist(),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "outputImageUrls": outputImageUrls,
        "trained_model_path": model_path,
        "evaluation_metrics": {"accuracy": accuracy, "precision": precision, "recall": recall, "f1_score": f1},
        "hyperparams_used": params,
    }
