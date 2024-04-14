# from flask import after_this_request
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd
import numpy as np
import csv
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from utils.saveTrainedModel import saveTrainedModel

def get_column_names(csv_file):
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        column_names = next(reader)  # Read the first row which contains column names
    return column_names
    
# @after_this_request
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

def save_predictions(dataset, predictions, output_file):
    dataset_copy = dataset.copy()
    dataset_copy['Predictions'] = predictions
    dataset_copy.to_csv(output_file, index=False)


def simpleLinearRegression(request):
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
        # Construct file path
        filepath = os.path.join(directory, data['filename'])
        columnNames = get_column_names(filepath)

        try:
            # Read CSV file
            dataset = pd.read_csv(filepath)
            X = dataset.iloc[:, :-1].values
            y = dataset.iloc[:, -1].values
        except FileNotFoundError:
            return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Neither X and y nor filename provided"}

    # Splitting the dataset into the Training set and Test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1/3, random_state=0)

    # Fitting Simple Linear Regression to the Training set
    model = LinearRegression()
    model.fit(X_train, y_train)

    saveTrainedModel(model, "simple_linear_regression", "scikit-learn")

    # Predicting the Test set results
    y_pred = model.predict(X_test)

    # Save predictions
    predictions_output_file = os.path.join('predictions/', 'simple_linear_regression.csv')
    save_predictions(pd.DataFrame(X_test, columns=columnNames[:-1]), y_pred, predictions_output_file)

    # Evaluation metrics
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    outputImageDir = 'static/images'
    outputImageUrls = [
        os.path.join(outputImageDir, 'linearRegressionTrainGraph.jpg'),
        os.path.join(outputImageDir, 'linearRegressionTestGraph.jpg')
    ]

    # Visualising the Training set results
    save_result_images(X_train, y_train, X_train, model, title='Training', xlabel=columnNames[0], ylabel=columnNames[1], output_path=outputImageUrls[0])

    # Visualising the Test set results
    save_result_images(X_test, y_test, X_train, model, title='Test', xlabel=columnNames[0], ylabel=columnNames[1], output_path=outputImageUrls[1])

    # Return results
    return {
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_,
        "predictions": y_pred.tolist(),
        "outputImageUrls": outputImageUrls,
        "predictions_output_file": predictions_output_file,
        "evaluation_metrics": {
            "MAE": mae,
            "MSE": mse,
            "R2": r2
        }
    }

