from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import matplotlib.pyplot as plt
from utils.saveTrainedModel import saveTrainedModel
from utils.data_loader import load_data_with_fallback
from utils.predictions_writer import save_predictions_csv
from config import IMAGES_DIR, get_user_predictions_dir, ensure_dir


def multivariateLinearRegression(request, validated_params=None, user_id=None, session_version=None):
    data = request.json
    params = validated_params or {}
    test_size = params.get('test_size', 0.33)
    random_state = params.get('random_state', 0)

    try:
        X, y, columnNames = load_data_with_fallback(data, user_id)
    except FileNotFoundError:
        return {"error": "File not found"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

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

    pred_dir = ensure_dir(get_user_predictions_dir(user_id))
    predictions_output_file = os.path.join(pred_dir, 'multivariable_linear_regression.csv')
    save_predictions_csv(X_test, y_test, columnNames, y_pred, predictions_output_file)

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
