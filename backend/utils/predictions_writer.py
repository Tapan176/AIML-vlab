"""
Shared helper for writing model predictions to a CSV file.

Every classical-ML model in backend/models/*/ defines an identical
`save_predictions` function. This module owns the canonical implementation.

Note on the column-naming fix: the original per-file copies used
`dataset[columnNames[1]] = y_test`, which only happens to be correct when
columnNames has exactly two entries (Simple Linear Regression). For any
multi-feature dataset that overwrites a feature column with the target.
This helper uses `columnNames[-1]` so it works for any column count.
"""
import pandas as pd


def save_predictions_csv(X_test, y_test, column_names, predictions, output_file):
    """Write a CSV with the test features, the true target, and the predictions.

    Args:
        X_test: 2-D array-like of test features, shape (n_samples, n_features).
        y_test: 1-D array-like of true target values, length n_samples.
        column_names: column names from the source dataset. Expected layout is
            features first and target last — only `column_names[:-1]` and
            `column_names[-1]` are used.
        predictions: model predictions on X_test, length n_samples.
        output_file: path to the output CSV (overwrites if it exists).
    """
    feature_columns = list(column_names[:-1])
    target_column = column_names[-1]

    df = pd.DataFrame(X_test, columns=feature_columns)
    df[target_column] = y_test
    df['Predictions'] = predictions
    df.to_csv(output_file, index=False)
