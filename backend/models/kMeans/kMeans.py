from flask import request, jsonify
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import csv

def get_column_names(csv_file):
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        column_names = next(reader)  # Read the first row which contains column names
    return column_names

def save_cluster_plot(X, labels, centers, output_path):
    plt.figure(figsize=(8, 6))
    plt.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', s=50, alpha=0.5)
    plt.scatter(centers[:, 0], centers[:, 1], c='red', s=200, alpha=0.75, label='Centroids')
    plt.title('Clusters of Data Points')
    plt.xlabel('Feature 1')
    plt.ylabel('Feature 2')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()

def kMeans(request):
    data = request.json
    directory = 'static/uploads'

    X = None
    k = None

    if 'X' in data and 'k' in data:  # If X and y are provided
        X = np.array(data['X'])
        k = data['k']
        X = X.reshape(-1, 1)
        columnNames = ['X', 'k']
    elif 'filename' in data:  # If filename is provided
        filepath = os.path.join(directory, data['filename'])
        columnNames = get_column_names(filepath)
        try:
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, [3, 4]].values
            k = data['k']
        except FileNotFoundError:
            return jsonify({"error": "File not found"})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"error": "Neither X and k nor filename provided"})

    kmeans = KMeans(n_clusters=k, init='k-means++', random_state=42)
    y_kmeans = kmeans.fit_predict(X)
    centers = kmeans.cluster_centers_
    silhouette = silhouette_score(X, y_kmeans)

    # Save cluster plot
    outputImageDir = 'static/images'
    if not os.path.exists(outputImageDir):
        os.makedirs(outputImageDir)

    outputImageUrls = [
        os.path.join(outputImageDir, 'kmeansClusterPlotElbowMethod.jpg'),
        os.path.join(outputImageDir, 'kmeansClusterPlot.jpg')
    ]

    wcss = []
    for i in range(1, 11):
        kmeans = KMeans(n_clusters = i, init = 'k-means++', random_state = 42)
        kmeans.fit(X)
        wcss.append(kmeans.inertia_)
    plt.plot(range(1, 11), wcss)
    plt.title('The Elbow Method')
    plt.xlabel('Number of clusters')
    plt.ylabel('WCSS')
    plt.savefig(outputImageUrls[0])
    plt.close()

    # Visualising the clusters
    for i in range(k):  # Iterate over each cluster
        plt.scatter(X[y_kmeans == i, 0], X[y_kmeans == i, 1], s=100, c=np.random.rand(3,), label=f'Cluster {i+1}')
    
    # plt.scatter(X[y_kmeans == 0, 0], X[y_kmeans == 0, 1], s = 100, c = 'red', label = 'Cluster 1')
    # plt.scatter(X[y_kmeans == 1, 0], X[y_kmeans == 1, 1], s = 100, c = 'blue', label = 'Cluster 2')
    # plt.scatter(X[y_kmeans == 2, 0], X[y_kmeans == 2, 1], s = 100, c = 'green', label = 'Cluster 3')
    # plt.scatter(X[y_kmeans == 3, 0], X[y_kmeans == 3, 1], s = 100, c = 'cyan', label = 'Cluster 4')
    # plt.scatter(X[y_kmeans == 4, 0], X[y_kmeans == 4, 1], s = 100, c = 'magenta', label = 'Cluster 5')
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s = 300, c = 'yellow', label = 'Centroids')
    plt.title('Clusters')
    plt.xlabel(columnNames[3])
    plt.ylabel(columnNames[4])
    plt.legend()
    plt.savefig(outputImageUrls[1])
    plt.close()

    return {
        'labels': y_kmeans.tolist(),
        'centers': centers.tolist(),
        'silhouette_score': silhouette,
        'outputImageUrls': outputImageUrls
    }
