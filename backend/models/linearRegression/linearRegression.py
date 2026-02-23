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
from config import UPLOAD_DIR, IMAGES_DIR, PREDICTIONS_DIR, ensure_dir


def get_column_names(csv_file):
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        column_names = next(reader)
    return column_names


def save_result_images(X, y, X_train, model, title, xlabel, ylabel, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)
    plt.scatter(X, y, color='red')
    plt.plot(X_train, model.predict(X_train), color='blue')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.savefig(output_path)
    plt.close()


def save_predictions(X_test, y_test, columnNames, predictions, output_file):
    dataset = pd.DataFrame(X_test, columns=columnNames[:-1])
    dataset[columnNames[1]] = y_test
    dataset['Predictions'] = predictions
    dataset.to_csv(output_file, index=False)


def simpleLinearRegression(request, validated_params=None, user_id=None, session_version=None):
    data = request.json

    # Use validated hyperparams or defaults
    params = validated_params or {}
    test_size = params.get('test_size', 0.33)
    random_state = params.get('random_state', 0)

    X = None
    y = None

    if 'X' in data and 'y' in data:
        X = np.array(data['X'])
        y = np.array(data['y'])
        X = X.reshape(-1, 1)
        columnNames = ['X', 'y']
    elif 'filename' in data:
        try:
            from services.dataset_service import get_dataset_df
            dataset = get_dataset_df(user_id, data['filename'])
            columnNames = dataset.columns.tolist()
            X = dataset.iloc[:, :-1].values
            y = dataset.iloc[:, -1].values
        except FileNotFoundError:
            return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Neither X and y nor filename provided"}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    model = LinearRegression()
    model.fit(X_train, y_train)

    model_path = saveTrainedModel(model, "simple_linear_regression", "scikit-learn", user_id=user_id, version=session_version)

    y_pred = model.predict(X_test)

    # Save predictions
    pred_dir = ensure_dir(PREDICTIONS_DIR)
    predictions_output_file = os.path.join(pred_dir, 'simple_linear_regression.csv')
    save_predictions(X_test, y_test, columnNames, y_pred, predictions_output_file)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    img_dir = ensure_dir(IMAGES_DIR)
    outputImageUrls = [
        os.path.join(img_dir, 'linearRegressionTrainGraph.jpg'),
        os.path.join(img_dir, 'linearRegressionTestGraph.jpg')
    ]

    save_result_images(X_train, y_train, X_train, model, title='Training', xlabel=columnNames[0], ylabel=columnNames[-1], output_path=outputImageUrls[0])
    save_result_images(X_test, y_test, X_train, model, title='Test', xlabel=columnNames[0], ylabel=columnNames[-1], output_path=outputImageUrls[1])

    return {
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_,
        "predictions": y_pred.tolist(),
        "outputImageUrls": outputImageUrls,
        "predictions_output_file": predictions_output_file,
        "trained_model_path": model_path,
        "evaluation_metrics": {"MAE": mae, "MSE": mse, "R2": r2},
        "X_values": X_test.flatten().tolist(),
        "actual_values": y_test.tolist(),
        "hyperparams_used": params,
    }
