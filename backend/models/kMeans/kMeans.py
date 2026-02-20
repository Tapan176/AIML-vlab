from flask import jsonify
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
from utils.saveTrainedModel import saveTrainedModel
from config import UPLOAD_DIR, IMAGES_DIR, ensure_dir


def kMeans(request, validated_params=None, user_id=None, session_version=None):
    data = request.json
    params = validated_params or {}
    n_clusters = params.get('n_clusters', int(data.get('k', 5)))
    init = params.get('init', 'k-means++')
    max_iter = params.get('max_iter', 300)
    n_init = params.get('n_init', 10)
    random_state = params.get('random_state', 42)

    X = None
    if 'filename' in data:
        filepath = os.path.join(UPLOAD_DIR, data['filename'])
        try:
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, [2, 3]].values
        except FileNotFoundError:
            return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
    elif 'X' in data:
        X = np.array(data['X'])
    else:
        return {"error": "Neither X nor filename provided"}

    # Elbow method
    img_dir = ensure_dir(IMAGES_DIR)
    wcss = []
    max_k = min(11, len(X))
    for i in range(1, max_k):
        km = KMeans(n_clusters=i, init=init, max_iter=max_iter, n_init=n_init, random_state=random_state)
        km.fit(X)
        wcss.append(km.inertia_)

    elbow_path = os.path.join(img_dir, 'kMeansElbow.jpg')
    if os.path.exists(elbow_path):
        os.remove(elbow_path)
    plt.plot(range(1, max_k), wcss)
    plt.title('The Elbow Method')
    plt.xlabel('Number of clusters')
    plt.ylabel('WCSS')
    plt.savefig(elbow_path)
    plt.close()

    # Final clustering
    kmeans = KMeans(n_clusters=n_clusters, init=init, max_iter=max_iter, n_init=n_init, random_state=random_state)
    y_kmeans = kmeans.fit_predict(X)

    model_path = saveTrainedModel(kmeans, "k_means", "scikit-learn", user_id=user_id, version=session_version)

    # Cluster plot
    cluster_path = os.path.join(img_dir, 'kMeansClusters.jpg')
    if os.path.exists(cluster_path):
        os.remove(cluster_path)

    colors = ['red', 'blue', 'green', 'cyan', 'magenta', 'yellow', 'orange', 'purple', 'brown', 'pink']
    for i in range(n_clusters):
        plt.scatter(X[y_kmeans == i, 0], X[y_kmeans == i, 1], s=100, c=colors[i % len(colors)], label=f'Cluster {i+1}')
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=300, c='black', marker='x', label='Centroids')
    plt.title('Clusters of customers')
    plt.xlabel('Feature 1')
    plt.ylabel('Feature 2')
    plt.legend()
    plt.savefig(cluster_path)
    plt.close()

    return {
        "cluster_labels": y_kmeans.tolist(),
        "cluster_centers": kmeans.cluster_centers_.tolist(),
        "inertia": kmeans.inertia_,
        "n_clusters": n_clusters,
        "outputImageUrls": [elbow_path, cluster_path],
        "trained_model_path": model_path,
        "results": {"n_clusters": n_clusters, "inertia": kmeans.inertia_},
        "hyperparams_used": params,
    }
