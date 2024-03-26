from flask import request, jsonify
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')  # To avoid GUI when saving plots
import matplotlib.pyplot as plt

def save_result_images(X, y, X_train, model, title, xlabel, ylabel, output_path):
    # Remove the old image if it exists
    if os.path.exists(output_path):
        os.remove(output_path)

    plt.scatter(X, y, color='red')
    plt.plot(X_train, model.predict(X_train), color='blue')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(output_path)
    plt.close()

def multivariateLinearRegression(request):
    data = request.json
    directory = 'static/uploads'

    X = None
    y = None

    if 'X' in data and 'y' in data:  # If X and y are provided
        X = np.array(data['X'])
        y = np.array(data['y'])
    elif 'filename' in data:  # If filename is provided
        filepath = os.path.join(directory, data['filename'])
        try:
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, :-1].values
            y = dataset.iloc[:, -1].values
        except FileNotFoundError:
            return jsonify({"error": "File not found"})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"error": "Neither X and y nor filename provided"})

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1/3, random_state=0)

    regressor = LinearRegression()
    regressor.fit(X_train, y_train)

    y_pred = regressor.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    outputImageDir = 'static/images'
    if not os.path.exists(outputImageDir):
        os.makedirs(outputImageDir)

    outputImageUrls = [
        os.path.join(outputImageDir, 'linearRegressionTrainGraph.jpg'),
        os.path.join(outputImageDir, 'linearRegressionTestGraph.jpg')
    ]

    save_result_images(X_train[:, 0], y_train, X_train[:, 0], regressor, title='Training', xlabel='X', ylabel='y', output_path=outputImageUrls[0])
    save_result_images(X_test[:, 0], y_test, X_train[:, 0], regressor, title='Test', xlabel='X', ylabel='y', output_path=outputImageUrls[1])

    return {
        "coefficients": regressor.coef_.tolist(),
        "intercept": regressor.intercept_,
        "predictions": y_pred.tolist(),
        "evaluation_metrics": {
            "MAE": mae,
            "MSE": mse,
            "R2": r2
        },
        "outputImageUrls": outputImageUrls
    }
