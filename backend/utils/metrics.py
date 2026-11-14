"""Small helpers shared by the classical classifiers."""
import numpy as np


def metric_average(y_true, y_pred):
    """Pick the `average=` mode for precision/recall/F1.

    sklearn's default ('binary') raises on multiclass targets and on binary
    targets whose labels aren't {0, 1} (e.g. 'yes'/'no'), which crashed every
    classifier on datasets like Iris. Use 'binary' only when it is valid.
    """
    labels = np.unique(np.concatenate([np.asarray(y_true).ravel(), np.asarray(y_pred).ravel()]))
    try:
        if len(labels) <= 2 and set(labels.astype(float).tolist()) <= {0.0, 1.0}:
            return 'binary'
    except (TypeError, ValueError):
        pass
    return 'weighted'
