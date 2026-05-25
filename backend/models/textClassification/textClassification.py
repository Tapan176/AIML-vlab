"""Text Classification — CountVectorizer + MultinomialNB pipeline."""
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from utils.saveTrainedModel import saveTrainedModel
from utils.data_loader import load_text_classification_data


def train_text_classification(request, validated_params=None, user_id=None, session_version=None):
    data = request.json or {}
    X, y = load_text_classification_data(data, user_id)

    p = validated_params or {}
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=p.get('test_size', 0.2), random_state=42)

    pipeline = Pipeline([
        ('vectorizer', CountVectorizer(max_features=p.get('max_features', 5000), ngram_range=(1, 2))),
        ('clf', MultinomialNB(alpha=p.get('alpha', 1.0))),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    model_path = saveTrainedModel(pipeline, "text_classification", "sklearn", user_id=user_id, version=session_version)

    return {
        'accuracy': float(accuracy_score(y_test, y_pred)),
        'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
        'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
        'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
        'trained_model_path': model_path,
    }
