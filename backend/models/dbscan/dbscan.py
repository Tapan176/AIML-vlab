from flask import jsonify
from sklearn.cluster import DBSCAN as DBSCANModel
import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
from config import UPLOAD_DIR, IMAGES_DIR, ensure_dir


def dbscan(request, validated_params=None, user_id=None, session_version=None):
    data = request.json
    params = validated_params or {}
    eps = params.get('eps', float(data.get('eps', 0.5)))
    min_samples = params.get('min_samples', int(data.get('min_samples', 5)))
    metric = params.get('metric', 'euclidean')

    X = None
    if 'filename' in data:
        try:
            from services.dataset_service import get_dataset_df
            dataset = get_dataset_df(user_id, data['filename'])
            numeric_dataset = dataset.select_dtypes(include=[np.number]).dropna()
            if numeric_dataset.empty or numeric_dataset.shape[1] < 2:
                return {"error": "Dataset must contain at least 2 numeric columns and valid rows for clustering."}
            X = numeric_dataset.values
        except FileNotFoundError:
            return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
    elif 'X' in data:
        X = np.array(data['X'])
    else:
        return {"error": "Neither X nor filename provided"}

    clustering = DBSCANModel(eps=eps, min_samples=min_samples, metric=metric)
    labels = clustering.fit_predict(X)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)

    img_dir = ensure_dir(IMAGES_DIR)
    cluster_path = os.path.join(img_dir, 'dbscanClusters.jpg')
    if os.path.exists(cluster_path):
        os.remove(cluster_path)

    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    for k, col in zip(sorted(unique_labels), colors):
        if k == -1:
            col = [0, 0, 0, 1]  # Black for noise
        class_mask = (labels == k)
        plt.scatter(X[class_mask, 0], X[class_mask, 1], c=[col], s=50, label=f'Cluster {k}' if k != -1 else 'Noise')
    plt.title(f'DBSCAN Clustering (eps={eps}, min_samples={min_samples})')
    plt.xlabel('Feature 1')
    plt.ylabel('Feature 2')
    plt.legend()
    plt.savefig(cluster_path)
    plt.close()

    from utils.saveTrainedModel import saveTrainedModel
    model_path = saveTrainedModel(clustering, "dbscan", "scikit-learn", user_id=user_id, version=session_version)

    return {
        "cluster_labels": labels.tolist(),
        "n_clusters": n_clusters,
        "n_noise_points": n_noise,
        "outputImageUrls": [cluster_path],
        "trained_model_path": model_path,
        "results": {"n_clusters": n_clusters, "n_noise_points": n_noise},
        "hyperparams_used": params,
    }
