from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from utils.saveTrainedModel import saveTrainedModel
from utils.data_loader import load_data_with_fallback
from config import IMAGES_DIR, ensure_dir


def save_result_images(X, y, classifier, title, xlabel, ylabel, output_path):
    if os.path.exists(output_path):
        os.remove(output_path)
    X_set, y_set = X, y
    X1, X2 = np.meshgrid(np.arange(start=X_set[:, 0].min() - 1, stop=X_set[:, 0].max() + 1, step=0.01),
                          np.arange(start=X_set[:, 1].min() - 1, stop=X_set[:, 1].max() + 1, step=0.01))
    plt.contourf(X1, X2, classifier.predict(np.array([X1.ravel(), X2.ravel()]).T).reshape(X1.shape), alpha=0.75, cmap=ListedColormap(('red', 'green')))
    plt.xlim(X1.min(), X1.max())
    plt.ylim(X2.min(), X2.max())
    for i, j in enumerate(np.unique(y_set)):
        plt.scatter(X_set[y_set == j, 0], X_set[y_set == j, 1], c=ListedColormap(('red', 'green'))(i), label=j)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.savefig(output_path)
    plt.close()


def decisionTree(request, validated_params=None, user_id=None, session_version=None):
    data = request.json
    params = validated_params or {}
    criterion = params.get('criterion', 'entropy')
    max_depth = params.get('max_depth', None)
    min_samples_split = params.get('min_samples_split', 2)
    min_samples_leaf = params.get('min_samples_leaf', 1)
    test_size = params.get('test_size', 0.25)
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
    sc = StandardScaler()
    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)

    classifier = DecisionTreeClassifier(criterion=criterion, max_depth=max_depth, min_samples_split=min_samples_split, min_samples_leaf=min_samples_leaf, random_state=random_state)
    classifier.fit(X_train, y_train)
    model_path = saveTrainedModel(classifier, "decision_tree", "scikit-learn", user_id=user_id, version=session_version)

    y_pred = classifier.predict(X_test)
    confusion = confusion_matrix(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    img_dir = ensure_dir(IMAGES_DIR)
    outputImageUrls = []
    # Only generate 2D decision boundary plots if exactly 2 features
    if X_train.shape[1] == 2:
        outputImageUrls = [
            os.path.join(img_dir, 'decisionTreeTrainGraph.jpg'),
            os.path.join(img_dir, 'decisionTreeTestGraph.jpg')
        ]
        save_result_images(X_train, y_train, classifier, title='Training', xlabel=columnNames[-3], ylabel=columnNames[-2], output_path=outputImageUrls[0])
        save_result_images(X_test, y_test, classifier, title='Test', xlabel=columnNames[-3], ylabel=columnNames[-2], output_path=outputImageUrls[1])

    return {
        "predictions": y_pred.tolist(),
        "confusion_matrix": confusion.tolist(),
        "accuracy": accuracy, "precision": precision, "recall": recall, "f1_score": f1,
        "outputImageUrls": outputImageUrls,
        "trained_model_path": model_path,
        "evaluation_metrics": {"accuracy": accuracy, "precision": precision, "recall": recall, "f1_score": f1},
        "hyperparams_used": params,
    }
