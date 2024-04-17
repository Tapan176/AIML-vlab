from flask import request, jsonify
from sklearn.cluster import DBSCAN
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import csv
from utils.saveTrainedModel import saveTrainedModel

def get_column_names(csv_file):
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        column_names = next(reader)  # Read the first row which contains column names
    return column_names

def save_cluster_plot(X, labels, title, xlabel, ylabel, output_path):
  plt.figure(figsize=(6.4, 4.8))
  unique_labels = set(labels)
  colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
  
  for k, col in zip(unique_labels, colors):
    if k == -1:
      # Black used for noise.
      col = [0, 0, 0, 1]

    class_member_mask = (labels == k)
    xy = X[class_member_mask]

    # Check for empty data after filtering
    if xy.shape[0] == 0:
      continue  # Skip plotting for empty clusters

    # Handle single-feature data or data with one remaining dimension
    if xy.ndim == 1:
      xy = xy.reshape(-1, 1)  # Reshape for single feature
    elif xy.shape[1] == 1:
      # If only one dimension remains after filtering, add a dummy dimension
      xy = np.c_[xy, np.zeros_like(xy)]  # Add a column of zeros

    plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col),
             markeredgecolor='k', markersize=6)

  plt.title(title)
  plt.xlabel(xlabel)
  plt.ylabel(ylabel)
  plt.grid(True)
  plt.savefig(output_path)
  plt.close()

def dbscan(request):
    data = request.json
    directory = 'static/uploads'

    X = None
    eps = None
    min_samples = None

    if 'X' in data and 'eps' in data and 'min_samples' in data:
        X = np.array(data['X'])
        X = X.reshape(-1, 1)
        eps = float(data['eps'])
        min_samples = int(data['min_samples'])
        columnNames = ['X', 'eps', 'min_samples']
    elif 'filename' in data and 'eps' in data and 'min_samples' in data:
        filepath = os.path.join(directory, data['filename'])
        columnNames = get_column_names(filepath)
        try:
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, [2, 3]].values
            eps = float(data['eps'])
            min_samples = int(data['min_samples'])
        except FileNotFoundError:
            return jsonify({"error": "File not found"})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"error": "Incomplete data provided"})

    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    y_dbscan = dbscan.fit_predict(X)
    
    saveTrainedModel(dbscan, "dbscan", "scikit-learn")

    # Save cluster plot
    outputImageDir = 'static/images'
    if not os.path.exists(outputImageDir):
        os.makedirs(outputImageDir)

    outputImageUrls = [ os.path.join(outputImageDir, 'dbscanCluster.jpg') ]
    save_cluster_plot(X, y_dbscan, 'DBSCAN Clustering', 'Feature 1', 'Feature 2', outputImageUrls[0])

    return {
        'labels': y_dbscan.tolist(),
        'outputImageUrls': outputImageUrls
    }
