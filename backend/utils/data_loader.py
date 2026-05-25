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
