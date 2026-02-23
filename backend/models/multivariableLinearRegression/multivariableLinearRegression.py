from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
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


def multivariateLinearRegression(request, validated_params=None, user_id=None, session_version=None):
    data = request.json
    params = validated_params or {}
    test_size = params.get('test_size', 0.33)
    random_state = params.get('random_state', 0)

    X = None
    y = None

    if 'filename' in data:
        try:
            from services.dataset_service import get_dataset_df
            dataset = get_dataset_df(user_id, data['filename'])
            X = dataset.iloc[:, :-1].values
            y = dataset.iloc[:, -1].values
            columnNames = dataset.columns.tolist()
        except FileNotFoundError:
            return {"error": "File not found"}
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Filename required for multivariate regression"}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    sc = StandardScaler()
    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)

    model = LinearRegression()
    model.fit(X_train, y_train)

    model_path = saveTrainedModel(model, "multivariable_linear_regression", "scikit-learn", user_id=user_id, version=session_version)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Save predictions
    pred_dir = ensure_dir(PREDICTIONS_DIR)
    predictions_output_file = os.path.join(pred_dir, 'multivariable_linear_regression.csv')
    pred_dataset = pd.DataFrame(X_test, columns=columnNames[:-1])
    pred_dataset[columnNames[-1]] = y_test
    pred_dataset['Predictions'] = y_pred
    pred_dataset.to_csv(predictions_output_file, index=False)

    # Actual vs Predicted plot
    img_dir = ensure_dir(IMAGES_DIR)
    plot_path = os.path.join(img_dir, 'multivariableLinearRegression.jpg')
    if os.path.exists(plot_path):
        os.remove(plot_path)
    plt.scatter(y_test, y_pred, color='blue', alpha=0.6)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    plt.title('Actual vs Predicted')
    plt.xlabel('Actual')
    plt.ylabel('Predicted')
    plt.savefig(plot_path)
    plt.close()

    return {
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_,
        "predictions": y_pred.tolist(),
        "outputImageUrls": [plot_path],
        "predictions_output_file": predictions_output_file,
        "trained_model_path": model_path,
        "evaluation_metrics": {"MAE": mae, "MSE": mse, "R2": r2},
        "actual_values": y_test.tolist(),
        "hyperparams_used": params,
    }
