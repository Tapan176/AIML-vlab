"""
Batch prediction on new data using a previously-trained model (ROADMAP D3).

Scope: CLASSICAL scikit-learn estimators (the synchronous models whose run
class is 'classical'). These are persisted as a bare estimator via joblib
(`.pkl`), so prediction is a matter of:
  1. loading the estimator from Google Drive (or local fallback),
  2. lining the uploaded CSV's feature columns up with what the estimator was
     trained on (sklearn records `n_features_in_` and, when a DataFrame was
     used, `feature_names_in_`),
  3. calling `.predict()` (and `.predict_proba()` when available).

Deep-learning / fine-tuning / clustering models are intentionally NOT handled
here — they need their bespoke preprocessing (tokenizers, image pipelines,
scalers) which isn't round-tripped through the bare artifact, so a naive
predict would be misleading. The route guards against those up front.
"""
import io
import os

import numpy as np
import pandas as pd

from services.training_session_service import get_session


# Estimators that expose .predict but whose output isn't a supervised label
# (clustering) — we still allow predict but label the column generically.
_CLUSTERING = {"k_means", "dbscan"}


def _load_estimator(session):
    """Load the joblib estimator for a session from Drive (local fallback).

    Returns the unpickled sklearn estimator. Raises on failure.
    """
    import joblib

    drive_id = session.get("trained_model_drive_id")
    if drive_id:
        from services.google_drive_service import stream_file_from_drive
        fh, _ = stream_file_from_drive(drive_id)
        # stream_file_from_drive may return a SpooledTemporaryFile; normalise to
        # a seekable BytesIO so joblib can read it on any Python version.
        try:
            fh.seek(0)
        except Exception:
            pass
        buf = io.BytesIO(fh.read())
        return joblib.load(buf)

    local_path = session.get("trained_model_path")
    if local_path and os.path.exists(local_path):
        return joblib.load(local_path)

    raise FileNotFoundError("Trained model artifact is not available.")


def _align_features(estimator, df):
    """Select / order the uploaded columns to match what the estimator expects.

    Strategy:
      - If the estimator recorded `feature_names_in_` (trained on a DataFrame),
        require those exact columns (order them accordingly).
      - Else fall back to `n_features_in_`: take that many numeric columns.
      - Else use all numeric columns.
    Returns (X dataframe/ndarray, used_columns list). Raises ValueError with a
    helpful message when the upload can't satisfy the estimator.
    """
    names = getattr(estimator, "feature_names_in_", None)
    if names is not None:
        names = list(names)
        missing = [c for c in names if c not in df.columns]
        if missing:
            raise ValueError(
                f"Uploaded data is missing required feature column(s): {', '.join(missing)}."
            )
        return df[names], names

    numeric = df.select_dtypes(include=[np.number])
    n_expected = getattr(estimator, "n_features_in_", None)
    if n_expected is not None:
        if numeric.shape[1] < n_expected:
            raise ValueError(
                f"Model expects {n_expected} numeric feature(s); the upload has "
                f"only {numeric.shape[1]}."
            )
        used = list(numeric.columns[:n_expected])
        return numeric[used], used

    if numeric.shape[1] == 0:
        raise ValueError("No numeric feature columns found in the uploaded data.")
    return numeric, list(numeric.columns)


def predict_with_session(session_id, user_id, df, max_rows=10000):
    """Run batch prediction for `df` using the model trained in `session_id`.

    Ownership is enforced (the session must belong to `user_id`). Returns a
    JSON-serialisable dict:
        { columns_used, n_rows, predictions, probabilities? }
    """
    session = get_session(session_id)
    if session.get("user_id") != str(user_id):
        raise PermissionError("unauthorized")
    if session.get("status") != "completed":
        raise ValueError("This session has no completed model to predict with.")

    model_code = session.get("model_code")
    # Guard: only classical sklearn estimators are supported here.
    from services.subscription_service import run_class
    if run_class(model_code) != "classical":
        raise ValueError(
            "Predict-on-new-data currently supports classical ML models only "
            "(regression, classification, clustering)."
        )

    if df is None or df.empty:
        raise ValueError("Uploaded data is empty.")
    if len(df) > max_rows:
        df = df.head(max_rows)

    estimator = _load_estimator(session)
    if not hasattr(estimator, "predict"):
        raise ValueError("The trained artifact does not support prediction.")

    X, used_cols = _align_features(estimator, df)

    preds = estimator.predict(X)
    result = {
        "session_id": str(session_id),
        "model_code": model_code,
        "columns_used": used_cols,
        "n_rows": int(len(X)),
        "prediction_label": "cluster" if model_code in _CLUSTERING else "prediction",
        "predictions": [_to_native(v) for v in np.asarray(preds).ravel().tolist()],
    }

    # Class probabilities when the estimator supports them (classifiers).
    if hasattr(estimator, "predict_proba"):
        try:
            proba = estimator.predict_proba(X)
            classes = getattr(estimator, "classes_", None)
            result["classes"] = [_to_native(c) for c in np.asarray(classes).tolist()] if classes is not None else None
            result["probabilities"] = [[round(float(p), 6) for p in row] for row in np.asarray(proba).tolist()]
        except Exception:
            pass

    return result


def read_uploaded_csv(file_storage):
    """Parse an uploaded CSV FileStorage into a DataFrame. Raises ValueError on
    a non-CSV / unparseable upload."""
    filename = (file_storage.filename or "").lower()
    if not filename.endswith(".csv"):
        raise ValueError("Please upload a .csv file.")
    try:
        return pd.read_csv(file_storage.stream)
    except Exception as e:
        raise ValueError(f"Could not parse CSV: {e}")


def _to_native(v):
    """Coerce numpy scalars to JSON-native python types."""
    try:
        if isinstance(v, (np.generic,)):
            return v.item()
    except Exception:
        pass
    return v
