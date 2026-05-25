"""
Shared dataset loader for model training functions.

Every classical-ML model in backend/models/*/ duplicates the same try/except
chain to accept either inline `X`/`y` arrays or a `filename` referring to a
user-uploaded CSV. This module centralises that pattern.
"""
import numpy as np


def load_data_with_fallback(data, user_id, *, reshape_x_to_2d=False):
    """Resolve X, y, and column names from a model-training request payload.

    Args:
        data: parsed JSON request body — must contain either both `X` and `y`,
            or a `filename` referring to a dataset the caller can read.
        user_id: owner id used by `get_dataset_df` to scope the dataset lookup
            (may be None for default datasets).
        reshape_x_to_2d: when True, reshapes a 1-D `X` to shape (-1, 1). Set
            this for single-feature regression (Simple Linear Regression).
            Leave False for multi-feature models.

    Returns:
        (X, y, column_names): X and y as numpy arrays, column_names as a list.
        For the inline X/y path the column_names default to ['X', 'y'].

    Raises:
        ValueError: neither inline arrays nor filename were supplied.
        FileNotFoundError: filename was given but the dataset could not be
            resolved. Surfaces from `get_dataset_df`.
    """
    if 'X' in data and 'y' in data:
        X = np.array(data['X'])
        y = np.array(data['y'])
        if reshape_x_to_2d:
            X = X.reshape(-1, 1)
        # Column names need to match the actual feature width so downstream
        # consumers (predictions CSV writer, decision-boundary plot labels)
        # don't crash on multi-feature inline payloads.
        n_features = X.shape[1] if X.ndim > 1 else 1
        if n_features == 1:
            column_names = ['X', 'y']
        else:
            column_names = [f'X{i + 1}' for i in range(n_features)] + ['y']
        return X, y, column_names

    if 'filename' in data:
        # Local import keeps this module light when callers want only the
        # inline-array path (e.g. in unit tests).
        from services.dataset_service import get_dataset_df
        df = get_dataset_df(user_id, data['filename'])
        column_names = df.columns.tolist()
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
        return X, y, column_names

    raise ValueError("Request must include either both 'X' and 'y', or 'filename'")


def load_clustering_features(data, user_id, *, min_columns=2):
    """Resolve a features-only X for clustering models (kMeans, DBSCAN).

    No target column is involved. For the filename path the dataset is
    pre-filtered to numeric columns with NaN rows dropped, since clustering
    algorithms can't handle categorical features or missing values.

    Args:
        data: parsed JSON request body — must contain either `X` (inline)
            or `filename` (CSV upload).
        user_id: owner id used by `get_dataset_df` (may be None for defaults).
        min_columns: filename-path datasets must have at least this many
            numeric columns after filtering, else ValueError. Defaults to 2
            because every clustering plot in the codebase assumes 2-D features.

    Returns:
        X: a numpy array of features.

    Raises:
        ValueError: neither X nor filename was supplied, or the filename
            dataset has too few usable numeric columns / rows.
        FileNotFoundError: filename was given but couldn't be resolved.
    """
    if 'X' in data:
        return np.array(data['X'])

    if 'filename' in data:
        from services.dataset_service import get_dataset_df
        df = get_dataset_df(user_id, data['filename'])
        numeric = df.select_dtypes(include=[np.number]).dropna()
        if numeric.empty or numeric.shape[1] < min_columns:
            raise ValueError(
                f"Dataset must contain at least {min_columns} numeric columns "
                "and valid rows for clustering."
            )
        return numeric.values

    raise ValueError("Request must include either 'X' or 'filename'")


def load_text_classification_data(data, user_id):
    """Resolve (X_text, y) for text-classification training requests.

    The caller may supply explicit `text_column` and `label_column` keys in
    `data`. Anything not supplied is auto-detected from the dataset's
    object-typed columns, mirroring the heuristic that sentimentAnalysis and
    textClassification have used identically:

      - 2+ object columns  → first is text, second is label (unless
        label_column was given, in which case keep it).
      - exactly 1 object column → that's the text; label defaults to the
        last column of the dataset.
      - 0 object columns → error.

    Args:
        data: parsed JSON body. Must contain `filename`. Optional keys:
            `text_column`, `label_column`.
        user_id: owner id used by `get_dataset_df`.

    Returns:
        (X_text, y): pandas Series of strings (text features) and Series for
        the target. Returned as Series so sklearn Pipelines can vectorise
        them directly.

    Raises:
        ValueError: no filename, or no text column found in the dataset.
        FileNotFoundError: filename was given but couldn't be resolved.
    """
    filename = data.get('filename')
    if not filename:
        raise ValueError("No dataset filename provided.")

    text_column = data.get('text_column')
    label_column = data.get('label_column')

    from services.dataset_service import get_dataset_df
    df = get_dataset_df(user_id, filename)

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

    X_text = df[text_column].astype(str)
    y = df[label_column]
    return X_text, y
