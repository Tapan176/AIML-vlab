"""Text Classification — CountVectorizer + MultinomialNB pipeline."""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from utils.saveTrainedModel import saveTrainedModel
import os


def train_text_classification(request, validated_params=None, user_id=None, session_version=None):
    data = request.json or {}
    filename = data.get('filename')
    text_column = data.get('text_column', None)
    label_column = data.get('label_column', None)

    if not filename:
        raise ValueError("No dataset filename provided.")

    from services.dataset_service import get_dataset_df
    df = get_dataset_df(user_id, filename)

    # Auto-detect text and label columns
    if not text_column:
        text_cols = df.select_dtypes(include=['object']).columns
        if len(text_cols) >= 2:
            text_column = text_cols[0]
            label_column = label_column or text_cols[1]
        elif len(text_cols) == 1:
            text_column = text_cols[0]
            label_column = label_column or df.columns[-1]
        else:
            raise ValueError("No text column detected in dataset.")

    if not label_column:
        label_column = df.columns[-1]

    X = df[text_column].astype(str)
    y = df[label_column]

    p = validated_params or {}
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=p.get('test_size', 0.2), random_state=42)

    pipeline = Pipeline([
        ('vectorizer', CountVectorizer(max_features=p.get('max_features', 5000), ngram_range=(1, 2))),
        ('clf', MultinomialNB(alpha=p.get('alpha', 1.0))),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    saveTrainedModel(pipeline, "text_classification", "sklearn", user_id=user_id, version=session_version)

    return {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
    }
