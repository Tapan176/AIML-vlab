"""Single source of truth for ML model hyperparameters (Pydantic v2).

Every model_code gets one ``BaseModel`` here. Each field carries *all* of its
metadata natively:

* default value          -> ``Field(default=...)``
* numeric range          -> ``ge=`` / ``le=`` (rendered as ``min`` / ``max``)
* enum / choices         -> ``Literal[...]``
* nullable               -> ``Optional[...]`` with a default
* UI label               -> ``Field(title=...)``      (legacy ``PARAM_LABELS``)
* UI help text           -> ``Field(description=...)`` (legacy ``PARAM_NOTES``)

The legacy structures the rest of the codebase still imports
(``DEFAULT_HYPERPARAMS``, ``VALIDATION_SCHEMAS``, ``PARAM_LABELS``,
``PARAM_NOTES``) are **derived** from these models by the ``build_*`` helpers
below, so no constraint/label/note is ever hand-maintained twice.

IMPORTANT: this module must NOT import ``config`` (config imports *us* to build
its ``DEFAULT_HYPERPARAMS``, so importing config here would be circular). It
depends only on pydantic + the standard library.
"""
from __future__ import annotations

import typing
from typing import Literal, Optional, get_args, get_origin

import annotated_types
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.fields import FieldInfo


# ── Shared bool coercion ────────────────────────────────────────────────────
# The legacy validator treated the strings "true"/"1"/"yes" (case-insensitive)
# as True and *anything else* (including "false"/"0"/"no"/"") as False, and it
# never raised on a bad bool. Pydantic v2's native bool parsing is stricter (it
# raises on unrecognised strings), so we pre-coerce with the exact legacy rule
# via a reusable validator mixed into every model that has a bool field.
_TRUTHY = {"true", "1", "yes"}


def _coerce_legacy_bool(value):
    """Mirror the legacy ``str.lower() in ('true','1','yes')`` bool rule.

    Non-string values fall through to Python ``bool()`` (so real bools and
    ints behave as before); ``None`` is left untouched so ``Optional`` bools
    can still be null where allowed.
    """
    if value is None:
        return value
    if isinstance(value, str):
        return value.lower() in _TRUTHY
    return bool(value)


class _BoolCoercionMixin:
    """Adds the legacy-compatible bool coercion to any model that needs it.

    The validator runs in ``mode="before"`` for every field; it only rewrites
    values whose declared type is ``bool`` (or ``Optional[bool]``) and leaves
    all other fields to pydantic's normal parsing.
    """

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_bools(cls, value, info):
        field = cls.model_fields.get(info.field_name)
        if field is not None and _field_is_bool(field):
            return _coerce_legacy_bool(value)
        return value


# A label is the UI title for a param. The same param name (e.g. ``test_size``)
# appears across many models with an identical label, matching the legacy flat
# ``PARAM_LABELS`` dict. Defining them once here keeps every field's ``title``
# consistent without retyping the string in 20 models.
PARAM_LABELS_BY_NAME = {
    "C": "C",
    "alpha": "Alpha",
    "augment": "Augment",
    "batch_size": "Batch size",
    "criterion": "Criterion",
    "degree": "Polynomial degree",
    "disc_lr": "Discriminator learning rate",
    "eps": "Epsilon (eps)",
    "epochs": "Epochs",
    "gamma": "Gamma",
    "imgsz": "Image size (imgsz)",
    "init": "Initialization strategy",
    "kernel": "Kernel",
    "learning_rate": "Learning rate",
    "log_resolution": "Log2 resolution",
    "loss": "Loss function",
    "lr0": "Initial learning rate (lr0)",
    "lrf": "Final LR multiplier (lrf)",
    "max_depth": "Max depth",
    "max_features": "Max features",
    "max_iter": "Max iterations",
    "metric": "Distance metric",
    "min_samples": "Minimum samples",
    "min_samples_leaf": "Min samples per leaf",
    "min_samples_split": "Min samples to split",
    "momentum": "Momentum",
    "mosaic": "Mosaic augmentation",
    "n_clusters": "Number of clusters",
    "n_estimators": "Number of estimators",
    "n_init": "Number of initializations",
    "n_neighbors": "Number of neighbors",
    "optimizer": "Optimizer",
    "p": "Minkowski power (p)",
    "r1_penalty": "R1 penalty",
    "random_state": "Random state",
    "sequence_length": "Sequence length",
    "solver": "Solver",
    "test_size": "Test split",
    "validation_split": "Validation split",
    "var_smoothing": "Variance smoothing",
    "w_dim": "W latent dimension",
    "warmup_epochs": "Warmup epochs",
    "weight_decay": "Weight decay",
    "weights": "Neighbor weights",
    "z_dim": "Z latent dimension",
    # Fine-tuning
    "model_name": "Base Model",
    "max_length": "Max Token Length",
    "warmup_steps": "Warmup Steps",
    "freeze_base": "Freeze Base Layers",
}


def _lbl(param_name: str) -> str:
    return PARAM_LABELS_BY_NAME[param_name]


# Per-(model, param) help text. Authored here so each field's ``description``
# (used to derive the legacy nested ``PARAM_NOTES``) lives in one place.
_FINETUNE_TEXT_NOTES = {
    "model_name": "Which pretrained checkpoint to start from. Larger checkpoints can be more accurate but train slower and need more memory.",
    "epochs": "How many full passes over your text the model fine-tunes for. 2–4 is usually enough; more can overfit small datasets.",
    "batch_size": "How many text examples are processed per optimizer step. Lower it if you hit out-of-memory errors.",
    "learning_rate": "Step size for fine-tuning. Transformers like very small rates (around 2e-5); larger values often destabilize training.",
    "max_length": "Maximum number of tokens kept per text sample. Longer captures more context but costs more memory and time; shorter truncates long inputs.",
    "warmup_steps": "Number of initial steps where the learning rate ramps up from zero, which can stabilize the start of fine-tuning.",
    "weight_decay": "L2-style regularization on the weights. A small value (around 0.01) helps reduce overfitting.",
    "test_size": "Fraction of rows held out to validate accuracy after fine-tuning.",
    "freeze_base": "When enabled, only the new classification head trains and the transformer backbone stays frozen — faster and safer for small datasets.",
}
_VIT_NOTES = {
    "model_name": "Which pretrained Vision Transformer checkpoint to start from. Larger variants can be more accurate but train slower.",
    "epochs": "How many full passes over your images the model fine-tunes for. A few epochs is usually enough for transfer learning.",
    "batch_size": "How many images are processed per optimizer step. Lower it if you run out of GPU/CPU memory.",
    "learning_rate": "Step size for fine-tuning. ViT fine-tuning uses very small rates (around 2e-5).",
    "weight_decay": "L2-style regularization on the weights to reduce overfitting.",
    "test_size": "Fraction of images held out to validate accuracy after fine-tuning.",
    "freeze_base": "When enabled, only the new classification head trains and the ViT encoder stays frozen — recommended for small datasets.",
}


def _F(default, *, note, ge=None, le=None):
    """Shorthand for ``Field(...)`` carrying default + label + note + range.

    ``note`` is the per-(model, param) help text (legacy PARAM_NOTES). The label
    (legacy PARAM_LABELS) is looked up from the param name at class-build time and
    attached in ``__init_subclass__``-free fashion below via field titles, so here
    we only need note + numeric bounds. We can't know the param name here, so the
    title is filled in by ``_attach_titles`` after the class body is parsed.
    """
    kwargs = {"default": default, "description": note}
    if ge is not None:
        kwargs["ge"] = ge
    if le is not None:
        kwargs["le"] = le
    return Field(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  One model per model_code. Field ORDER below must match the legacy
#  VALIDATION_SCHEMAS order (that's the order the frontend + catalog render in).
# ─────────────────────────────────────────────────────────────────────────────

class SimpleLinearRegression(BaseModel):
    model_config = ConfigDict(extra="ignore")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation before fitting the regression line.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the train/test split so repeated runs are reproducible.")


class MultivariableLinearRegression(BaseModel):
    model_config = ConfigDict(extra="ignore")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation before fitting the regression model.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the train/test split so repeated runs are reproducible.")


class LogisticRegression(BaseModel):
    model_config = ConfigDict(extra="ignore")
    C: float = _F(10.0, ge=0.01, le=1000.0, note="Inverse regularization strength. Smaller values regularize harder and usually reduce overfitting.")
    solver: Literal["lbfgs", "liblinear", "newton-cg", "sag", "saga"] = _F("lbfgs", note="Optimization algorithm used to fit the logistic regression coefficients.")
    max_iter: int = _F(1000, ge=50, le=10000, note="Upper bound on solver iterations before convergence stops.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the split and for solvers that rely on randomization.")


class KNN(BaseModel):
    model_config = ConfigDict(extra="ignore")
    n_neighbors: int = _F(5, ge=1, le=50, note="How many nearest training samples vote when predicting the class of a new point.")
    metric: Literal["euclidean", "manhattan", "minkowski", "chebyshev"] = _F("minkowski", note="Distance function used to decide which points count as nearest neighbors.")
    p: int = _F(2, ge=1, le=5, note="Only affects the Minkowski metric: 1 behaves like Manhattan distance and 2 behaves like Euclidean distance.")
    weights: Literal["uniform", "distance"] = _F("distance", note="Whether every neighbor votes equally or closer neighbors get more influence.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the train/test split.")


class DecisionTree(BaseModel):
    model_config = ConfigDict(extra="ignore")
    criterion: Literal["gini", "entropy", "log_loss"] = _F("gini", note="Split quality function used to choose the next branch in the tree.")
    max_depth: Optional[int] = _F(10, ge=1, le=100, note="Maximum number of split levels. Null removes the depth cap completely.")
    min_samples_split: int = _F(5, ge=2, le=50, note="Smallest sample count a node must contain before the tree is allowed to split it.")
    min_samples_leaf: int = _F(2, ge=1, le=50, note="Smallest sample count allowed in any terminal leaf after a split.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the split and any stochastic behavior inside the estimator.")


class RandomForest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    n_estimators: int = _F(100, ge=1, le=500, note="How many decision trees are trained in the ensemble.")
    criterion: Literal["gini", "entropy", "log_loss"] = _F("gini", note="Split quality function used inside every tree.")
    max_depth: Optional[int] = _F(15, ge=1, le=100, note="Maximum depth of each tree. Null removes the cap.")
    min_samples_split: int = _F(3, ge=2, le=50, note="Smallest sample count a node must contain before a tree can split it.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the split and forest randomness.")


class SVM(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kernel: Literal["linear", "rbf", "poly", "sigmoid"] = _F("rbf", note="Kernel function that defines the separating surface between classes.")
    C: float = _F(10.0, ge=0.01, le=1000.0, note="Penalty for margin violations. Larger values fit the training data more aggressively.")
    gamma: Literal["scale", "auto"] = _F("scale", note="Kernel coefficient for rbf, poly, and sigmoid kernels.")
    degree: int = _F(3, ge=1, le=10, note="Polynomial order used only when the kernel is set to poly.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the split and any randomized estimator behavior.")


class NaiveBayes(BaseModel):
    model_config = ConfigDict(extra="ignore")
    var_smoothing: float = _F(1e-9, ge=1e-12, le=1.0, note="Small positive value added to feature variances so GaussianNB remains numerically stable.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used for the train/test split.")


class KMeans(BaseModel):
    model_config = ConfigDict(extra="ignore")
    n_clusters: int = _F(3, ge=2, le=20, note="How many clusters the algorithm will try to discover.")
    init: Literal["k-means++", "random"] = _F("k-means++", note="Strategy used to place the initial centroids before iterative refinement starts.")
    max_iter: int = _F(300, ge=100, le=1000, note="Maximum Lloyd updates allowed for one initialization run.")
    n_init: int = _F(10, ge=1, le=50, note="How many separate centroid initializations are tried before the best run is kept.")
    random_state: Optional[int] = _F(42, ge=0, le=9999, note="Seed used when initialization depends on randomness.")


class DBSCAN(BaseModel):
    model_config = ConfigDict(extra="ignore")
    eps: float = _F(0.5, ge=0.01, le=10.0, note="Maximum neighborhood radius for two points to count as density-connected.")
    min_samples: int = _F(5, ge=1, le=50, note="Minimum neighborhood size required for a point to become a core point.")
    metric: Literal["euclidean", "manhattan", "cosine"] = _F("euclidean", note="Distance function used when DBSCAN measures neighborhood radius.")


class ANN(_BoolCoercionMixin, BaseModel):
    model_config = ConfigDict(extra="ignore")
    epochs: int = _F(100, ge=1, le=500, note="Maximum full passes through the training split before early stopping can halt training.")
    batch_size: int = _F(32, ge=1, le=512, note="Number of rows processed before every optimizer update.")
    optimizer: Literal["adam", "sgd", "rmsprop", "adagrad"] = _F("adam", note="Weight update algorithm used during backpropagation.")
    loss: Literal["binary_crossentropy", "categorical_crossentropy", "sparse_categorical_crossentropy", "mse"] = _F("binary_crossentropy", note="Objective function that determines the output layer shape and how prediction error is measured.")
    learning_rate: float = _F(0.001, ge=0.00001, le=1.0, note="Base step size passed into the selected optimizer.")
    validation_split: float = _F(0.15, ge=0.05, le=0.5, note="Fraction of the training split reserved internally for validation during each epoch.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for the final holdout test set.")


class GradientBoosting(BaseModel):
    model_config = ConfigDict(extra="ignore")
    n_estimators: int = _F(200, ge=10, le=1000, note="How many shallow trees are added sequentially to correct previous errors.")
    learning_rate: float = _F(0.05, ge=0.001, le=1.0, note="Shrinkage applied to each boosting step. Smaller values slow training but can generalize better.")
    max_depth: int = _F(5, ge=1, le=20, note="Maximum depth for each boosting tree.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")


class XGBoost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    n_estimators: int = _F(200, ge=10, le=1000, note="How many boosted trees are trained.")
    learning_rate: float = _F(0.05, ge=0.001, le=1.0, note="Shrinkage applied to each boosting step.")
    max_depth: int = _F(6, ge=1, le=20, note="Maximum tree depth for each boosted estimator.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of rows reserved for holdout evaluation.")


class SentimentAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    max_features: int = _F(10000, ge=100, le=50000, note="Vocabulary cap for the TF-IDF vectorizer. Higher values keep more unique n-grams.")
    max_iter: int = _F(1000, ge=100, le=5000, note="Maximum iterations allowed for the logistic regression classifier.")
    C: float = _F(5.0, ge=0.01, le=100.0, note="Inverse regularization strength for the logistic regression classifier.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of text rows reserved for holdout evaluation.")


class TextClassification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    max_features: int = _F(10000, ge=100, le=50000, note="Vocabulary cap for the count vectorizer.")
    alpha: float = _F(0.5, ge=0.001, le=10.0, note="Laplace smoothing strength for Multinomial Naive Bayes.")
    test_size: float = _F(0.2, ge=0.05, le=0.5, note="Fraction of text rows reserved for holdout evaluation.")


class CNN(BaseModel):
    model_config = ConfigDict(extra="ignore")
    epochs: int = _F(50, ge=1, le=500, note="Maximum training epochs before patience-based early stopping can stop the run.")
    batch_size: int = _F(32, ge=1, le=512, note="Number of images loaded per optimizer update.")
    optimizer: Literal["adam", "sgd", "rmsprop", "adagrad", "adadelta"] = _F("adam", note="Weight update algorithm used during backpropagation.")
    loss: Literal["binary_crossentropy", "categorical_crossentropy", "sparse_categorical_crossentropy"] = _F("categorical_crossentropy", note="Objective function used to train the classifier head. This must stay compatible with the selected class mode.")
    learning_rate: float = _F(0.001, ge=0.00001, le=1.0, note="Base step size passed into the selected optimizer.")
    momentum: float = _F(0.0, ge=0.0, le=0.999, note="Only used by SGD. Adds inertia so updates keep moving in the previous direction.")


class ResNet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    epochs: int = _F(25, ge=1, le=500, note="Maximum training epochs before early stopping can stop the run.")
    batch_size: int = _F(16, ge=1, le=512, note="Number of images loaded per optimizer update.")
    optimizer: Literal["adam", "sgd", "rmsprop", "adagrad", "adadelta"] = _F("adam", note="Weight update algorithm used during fine-tuning.")
    loss: Literal["binary_crossentropy", "categorical_crossentropy", "sparse_categorical_crossentropy"] = _F("categorical_crossentropy", note="Objective function used for the final classification layer. Keep it aligned with the selected class mode.")
    learning_rate: float = _F(0.0001, ge=0.00001, le=1.0, note="Base step size passed into the selected optimizer.")


class LSTM(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # NOTE: order matches the legacy VALIDATION_SCHEMAS (validation_split,
    # sequence_length, then learning_rate) — that is the canonical render order.
    epochs: int = _F(100, ge=1, le=500, note="Maximum sequence-training epochs before early stopping can stop the run.")
    batch_size: int = _F(32, ge=1, le=512, note="Number of sequences processed per optimizer update.")
    optimizer: Literal["adam", "sgd", "rmsprop", "adagrad", "adadelta"] = _F("adam", note="Weight update algorithm used during sequence training.")
    loss: Literal["mse", "mae", "huber", "binary_crossentropy", "categorical_crossentropy", "sparse_categorical_crossentropy"] = _F("mse", note="Regression loss for linear mode, or the requested classification loss when classification mode is selected.")
    validation_split: float = _F(0.15, ge=0.05, le=0.5, note="Fraction of the generated sequence set reserved internally for validation each epoch.")
    sequence_length: int = _F(20, ge=1, le=100, note="Sliding window length used when converting the tabular sequence into supervised training samples.")
    learning_rate: float = _F(0.001, ge=0.00001, le=1.0, note="Base step size passed into the selected optimizer.")


class YOLO(_BoolCoercionMixin, BaseModel):
    model_config = ConfigDict(extra="ignore")
    epochs: int = _F(50, ge=1, le=500, note="Maximum detector training epochs.")
    batch_size: int = _F(16, ge=1, le=128, note="Number of images per optimizer step.")
    imgsz: int = _F(640, ge=32, le=1280, note="Square image resolution used during training and validation.")
    optimizer: Literal["auto", "SGD", "Adam", "AdamW", "RMSProp"] = _F("auto", note="Ultralytics optimizer selection. Case matters here because the backend forwards the exact string.")
    lr0: float = _F(0.01, ge=0.00001, le=1.0, note="Initial learning rate at the start of training.")
    lrf: float = _F(0.01, ge=0.001, le=1.0, note="Final learning rate multiplier used by the scheduler relative to lr0.")
    momentum: float = _F(0.937, ge=0.5, le=0.999, note="Momentum term used by supported optimizers.")
    weight_decay: float = _F(0.0005, ge=0.0, le=0.01, note="L2-style regularization applied to model weights.")
    warmup_epochs: int = _F(3, ge=0, le=20, note="How many early epochs are spent warming up the optimizer schedule.")
    augment: bool = _F(True, note="Whether Ultralytics data augmentation is enabled.")
    mosaic: float = _F(1.0, ge=0.0, le=1.0, note="Strength of mosaic augmentation between 0 and 1.")


class StyleGAN(BaseModel):
    model_config = ConfigDict(extra="ignore")
    epochs: int = _F(300, ge=1, le=1000, note="Maximum adversarial training epochs.")
    batch_size: int = _F(8, ge=1, le=128, note="Number of images loaded into each GAN optimization step.")
    z_dim: int = _F(256, ge=64, le=1024, note="Dimensionality of the random input noise vector.")
    w_dim: int = _F(256, ge=64, le=1024, note="Dimensionality of the intermediate latent W space produced by the mapping network.")
    log_resolution: int = _F(7, ge=6, le=10, note="Log2 of the generated output resolution. For example, 7 means 128x128 images.")
    learning_rate: float = _F(0.0001, ge=0.000001, le=0.1, note="Generator and mapping-network learning rate.")
    optimizer: Literal["adam", "rmsprop"] = _F("adam", note="Optimizer family used for generator and discriminator training.")
    disc_lr: float = _F(0.0001, ge=0.000001, le=0.1, note="Learning rate used for the discriminator. If omitted, it falls back to the generator learning rate.")
    r1_penalty: float = _F(10.0, ge=0.0, le=100.0, note="Strength of the R1 regularization term applied to real-image gradients.")


# ── Fine-tuning models ──────────────────────────────────────────────────────

class BertFinetune(_BoolCoercionMixin, BaseModel):
    model_config = ConfigDict(extra="ignore")
    model_name: Literal["bert-base-uncased", "bert-base-cased", "distilbert-base-uncased", "roberta-base", "albert-base-v2"] = _F("bert-base-uncased", note=_FINETUNE_TEXT_NOTES["model_name"])
    epochs: int = _F(3, ge=1, le=50, note=_FINETUNE_TEXT_NOTES["epochs"])
    batch_size: int = _F(16, ge=1, le=128, note=_FINETUNE_TEXT_NOTES["batch_size"])
    learning_rate: float = _F(2e-5, ge=1e-7, le=0.1, note=_FINETUNE_TEXT_NOTES["learning_rate"])
    max_length: int = _F(256, ge=32, le=512, note=_FINETUNE_TEXT_NOTES["max_length"])
    warmup_steps: int = _F(0, ge=0, le=1000, note=_FINETUNE_TEXT_NOTES["warmup_steps"])
    weight_decay: float = _F(0.01, ge=0.0, le=1.0, note=_FINETUNE_TEXT_NOTES["weight_decay"])
    test_size: float = _F(0.2, ge=0.05, le=0.5, note=_FINETUNE_TEXT_NOTES["test_size"])
    freeze_base: bool = _F(False, note=_FINETUNE_TEXT_NOTES["freeze_base"])


class ViTFinetune(_BoolCoercionMixin, BaseModel):
    model_config = ConfigDict(extra="ignore")
    model_name: Literal["google/vit-base-patch16-224", "google/vit-base-patch16-224-in21k", "google/vit-large-patch16-224"] = _F("google/vit-base-patch16-224", note=_VIT_NOTES["model_name"])
    epochs: int = _F(3, ge=1, le=50, note=_VIT_NOTES["epochs"])
    batch_size: int = _F(16, ge=1, le=128, note=_VIT_NOTES["batch_size"])
    learning_rate: float = _F(2e-5, ge=1e-7, le=0.1, note=_VIT_NOTES["learning_rate"])
    weight_decay: float = _F(0.01, ge=0.0, le=1.0, note=_VIT_NOTES["weight_decay"])
    test_size: float = _F(0.2, ge=0.05, le=0.5, note=_VIT_NOTES["test_size"])
    freeze_base: bool = _F(False, note=_VIT_NOTES["freeze_base"])


class DistilBertFinetune(_BoolCoercionMixin, BaseModel):
    model_config = ConfigDict(extra="ignore")
    model_name: Literal["distilbert-base-uncased", "bert-base-uncased", "roberta-base"] = _F("distilbert-base-uncased", note=_FINETUNE_TEXT_NOTES["model_name"])
    epochs: int = _F(3, ge=1, le=50, note=_FINETUNE_TEXT_NOTES["epochs"])
    batch_size: int = _F(16, ge=1, le=128, note=_FINETUNE_TEXT_NOTES["batch_size"])
    learning_rate: float = _F(2e-5, ge=1e-7, le=0.1, note=_FINETUNE_TEXT_NOTES["learning_rate"])
    max_length: int = _F(256, ge=32, le=512, note=_FINETUNE_TEXT_NOTES["max_length"])
    warmup_steps: int = _F(0, ge=0, le=1000, note=_FINETUNE_TEXT_NOTES["warmup_steps"])
    weight_decay: float = _F(0.01, ge=0.0, le=1.0, note=_FINETUNE_TEXT_NOTES["weight_decay"])
    test_size: float = _F(0.2, ge=0.05, le=0.5, note=_FINETUNE_TEXT_NOTES["test_size"])
    freeze_base: bool = _F(False, note=_FINETUNE_TEXT_NOTES["freeze_base"])


# Registry: every code in config.MODEL_CODES must appear here (asserted by the
# test-suite). Order matches config.MODEL_CODES for readability, though the
# derived dicts are keyed so order here doesn't affect correctness.
HYPERPARAM_MODELS = {
    "simple_linear_regression": SimpleLinearRegression,
    "multivariable_linear_regression": MultivariableLinearRegression,
    "logistic_regression": LogisticRegression,
    "knn": KNN,
    "k_means": KMeans,
    "decision_tree": DecisionTree,
    "random_forest": RandomForest,
    "svm": SVM,
    "naive_bayes": NaiveBayes,
    "dbscan": DBSCAN,
    "ann": ANN,
    "cnn": CNN,
    "resnet": ResNet,
    "lstm": LSTM,
    "yolo": YOLO,
    "stylegan": StyleGAN,
    "gradient_boosting": GradientBoosting,
    "xgboost": XGBoost,
    "sentiment_analysis": SentimentAnalysis,
    "text_classification": TextClassification,
    "bert_finetune": BertFinetune,
    "vit_finetune": ViTFinetune,
    "distilbert_finetune": DistilBertFinetune,
}


# ── Attach UI labels (titles) to every field from PARAM_LABELS_BY_NAME ───────
# Done after class definition so the per-field ``_F`` helper doesn't need to
# know its own field name. This is the single point where the label is wired in.
def _attach_titles():
    for model_cls in HYPERPARAM_MODELS.values():
        for name, field in model_cls.model_fields.items():
            field.title = _lbl(name)
        # No re-validation of the schema is needed: title is metadata only.


_attach_titles()


# ─────────────────────────────────────────────────────────────────────────────
#  Field-metadata introspection -> legacy shapes
# ─────────────────────────────────────────────────────────────────────────────

def _unwrap_optional(annotation):
    """Return ``(inner_type, is_optional)`` for ``Optional[X]`` / ``X``."""
    origin = get_origin(annotation)
    if origin is typing.Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        is_optional = len(args) < len(get_args(annotation))
        if len(args) == 1:
            return args[0], is_optional
        return annotation, is_optional
    return annotation, False


def _literal_options(annotation):
    """Return the list of literal choices if ``annotation`` is a ``Literal``."""
    if get_origin(annotation) is Literal:
        return list(get_args(annotation))
    return None


def _base_type(annotation):
    """Map a field annotation to the legacy Python ``type`` (int/float/str/bool).

    ``Literal[...]`` resolves to the type of its members (always uniform here).
    """
    inner, _ = _unwrap_optional(annotation)
    options = _literal_options(inner)
    if options is not None:
        return type(options[0])
    return inner


def _field_is_bool(field: FieldInfo) -> bool:
    return _base_type(field.annotation) is bool


def _bounds(field: FieldInfo):
    """Extract ``(min, max)`` from a field's annotated_types metadata."""
    minimum = maximum = None
    for meta in field.metadata:
        if isinstance(meta, annotated_types.Ge):
            minimum = meta.ge
        elif isinstance(meta, annotated_types.Le):
            maximum = meta.le
    return minimum, maximum


def build_validation_schemas():
    """Reconstruct the legacy ``VALIDATION_SCHEMAS`` dict from the models.

    Shape per param: ``{'type': <python type>, 'min'?: , 'max'?: ,
    'options'?: [...], 'nullable'?: True}`` — key order matches the legacy file
    (type, then min/max, then options, then nullable) so downstream consumers
    that build help text in declaration order are unaffected.
    """
    schemas = {}
    for code, model_cls in HYPERPARAM_MODELS.items():
        params = {}
        for name, field in model_cls.model_fields.items():
            inner, is_optional = _unwrap_optional(field.annotation)
            options = _literal_options(inner)
            rule = {"type": _base_type(field.annotation)}
            minimum, maximum = _bounds(field)
            if minimum is not None:
                rule["min"] = minimum
            if maximum is not None:
                rule["max"] = maximum
            if options is not None:
                rule["options"] = options
            if is_optional:
                rule["nullable"] = True
            params[name] = rule
        schemas[code] = params
    return schemas


def build_defaults():
    """Reconstruct the legacy ``DEFAULT_HYPERPARAMS`` dict from the models."""
    defaults = {}
    for code, model_cls in HYPERPARAM_MODELS.items():
        defaults[code] = {
            name: field.get_default(call_default_factory=False)
            for name, field in model_cls.model_fields.items()
        }
    return defaults


def build_param_labels():
    """Reconstruct the legacy flat ``PARAM_LABELS`` dict (param -> label).

    Built from the field ``title`` metadata across all models; identical param
    names carry identical labels, so the flat collapse is lossless.
    """
    labels = {}
    for model_cls in HYPERPARAM_MODELS.values():
        for name, field in model_cls.model_fields.items():
            if field.title is not None:
                labels[name] = field.title
    return labels


def build_param_notes():
    """Reconstruct the legacy nested ``PARAM_NOTES`` dict (model -> param -> note)."""
    notes = {}
    for code, model_cls in HYPERPARAM_MODELS.items():
        notes[code] = {
            name: field.description
            for name, field in model_cls.model_fields.items()
            if field.description is not None
        }
    return notes


def get_model_schema(model_code):
    """Frontend-facing schema for one model, or ``None`` if unknown.

    Shape per param: ``{'type': '<int|float|str|bool>', 'default': <val>,
    'min'?: , 'max'?: , 'options'?: , 'nullable'?: True}`` — matches the legacy
    ``hyperparam_validator.get_model_schema`` byte-for-byte.
    """
    model_cls = HYPERPARAM_MODELS.get(model_code)
    if model_cls is None:
        return None
    schema = {}
    for name, field in model_cls.model_fields.items():
        inner, is_optional = _unwrap_optional(field.annotation)
        options = _literal_options(inner)
        minimum, maximum = _bounds(field)
        entry = {
            "type": _base_type(field.annotation).__name__,
            "default": field.get_default(call_default_factory=False),
        }
        if minimum is not None:
            entry["min"] = minimum
        if maximum is not None:
            entry["max"] = maximum
        if options is not None:
            entry["options"] = options
        if is_optional:
            entry["nullable"] = True
        schema[name] = entry
    return schema


def validate_hyperparams(model_code, user_params):
    """Validate + merge user params over defaults for ``model_code``.

    Behaviour preserved from the legacy validator:
      * unknown ``model_code`` -> ``Exception('Unknown model code: ...')``
      * returns ``dict(defaults)`` updated with validated user params
      * unknown params silently ignored
      * ``None`` allowed only for nullable params (else collected as an error)
      * type coercion for int/float/str/bool (incl. ``"true"/"false"`` -> bool)
      * enum check via ``options``; range check via ``min``/``max``
      * any failures -> ``Exception('Hyperparameter validation failed: ...')``
    """
    model_cls = HYPERPARAM_MODELS.get(model_code)
    if model_cls is None:
        raise Exception(f"Unknown model code: {model_code}")

    fields = model_cls.model_fields
    defaults = {
        name: field.get_default(call_default_factory=False)
        for name, field in fields.items()
    }
    validated = dict(defaults)

    if not user_params:
        return validated

    errors = []
    for param_name, value in user_params.items():
        field = fields.get(param_name)
        if field is None:
            continue  # unknown param: ignore silently

        inner, is_optional = _unwrap_optional(field.annotation)
        options = _literal_options(inner)
        expected_type = _base_type(field.annotation)
        minimum, maximum = _bounds(field)

        # None handling (only nullable params accept it)
        if value is None:
            if is_optional:
                validated[param_name] = None
            else:
                errors.append(f"'{param_name}' cannot be null")
            continue

        # Type coercion (mirror legacy semantics exactly)
        try:
            if expected_type is float:
                value = float(value)
            elif expected_type is int:
                value = int(value)
            elif expected_type is str:
                value = str(value)
            elif expected_type is bool:
                value = _coerce_legacy_bool(value)
        except (ValueError, TypeError):
            errors.append(f"'{param_name}' must be {expected_type.__name__}, got '{value}'")
            continue

        # Enum validation
        if options is not None and value not in options:
            errors.append(f"'{param_name}' must be one of {options}, got '{value}'")
            continue

        # Range validation
        if minimum is not None and value < minimum:
            errors.append(f"'{param_name}' must be >= {minimum}, got {value}")
            continue
        if maximum is not None and value > maximum:
            errors.append(f"'{param_name}' must be <= {maximum}, got {value}")
            continue

        validated[param_name] = value

    if errors:
        raise Exception("Hyperparameter validation failed: " + "; ".join(errors))

    return validated
