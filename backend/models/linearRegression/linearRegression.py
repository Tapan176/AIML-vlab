from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import matplotlib.pyplot as plt
from utils.saveTrainedModel import saveTrainedModel
from utils.data_loader import load_data_with_fallback
from utils.predictions_writer import save_predictions_csv
from config import IMAGES_DIR, get_user_predictions_dir, ensure_dir


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


def simpleLinearRegression(request, validated_params=None, user_id=None, session_version=None):
    data = request.json

    # Use validated hyperparams or defaults
    params = validated_params or {}
    test_size = params.get('test_size', 0.33)
    random_state = params.get('random_state', 0)

    try:
        X, y, columnNames = load_data_with_fallback(data, user_id, reshape_x_to_2d=True)
    except FileNotFoundError:
        return {"error": "File not found"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    model = LinearRegression()
    model.fit(X_train, y_train)

    model_path = saveTrainedModel(model, "simple_linear_regression", "scikit-learn", user_id=user_id, version=session_version)

    y_pred = model.predict(X_test)

    pred_dir = ensure_dir(get_user_predictions_dir(user_id))
    predictions_output_file = os.path.join(pred_dir, 'simple_linear_regression.csv')
    save_predictions_csv(X_test, y_test, columnNames, y_pred, predictions_output_file)

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
