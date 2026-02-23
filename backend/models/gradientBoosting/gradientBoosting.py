"""Gradient Boosting Classifier — scikit-learn."""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import LabelEncoder
from utils.saveTrainedModel import saveTrainedModel
import os


def train_gradient_boosting(request, validated_params=None, user_id=None, session_version=None):
    data = request.json or {}
    filename = data.get('filename')
    if not filename:
        raise ValueError("No dataset filename provided.")

    from services.dataset_service import get_dataset_df
    df = get_dataset_df(user_id, filename)
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    if y.dtype == 'object':
        le = LabelEncoder()
        y = le.fit_transform(y)

    p = validated_params or {}
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=p.get('test_size', 0.2), random_state=42)

    model = GradientBoostingClassifier(
        n_estimators=p.get('n_estimators', 100),
        learning_rate=p.get('learning_rate', 0.1),
        max_depth=p.get('max_depth', 3),
        random_state=42,
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    saveTrainedModel(model, "gradient_boosting", "sklearn", user_id=user_id, version=session_version)

    return {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
    }
