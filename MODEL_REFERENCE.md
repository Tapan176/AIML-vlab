# AIML-vlab — Complete Model Reference

> Auto-generated from backend source code analysis.
> Use this to populate the database with model info so users understand every parameter, layer, activation function, optimizer, etc.

---

## Table of Contents

1. [Simple Linear Regression](#1-simple-linear-regression)
2. [Multivariable Linear Regression](#2-multivariable-linear-regression)
3. [Logistic Regression](#3-logistic-regression)
4. [K-Nearest Neighbors (KNN)](#4-k-nearest-neighbors-knn)
5. [Decision Tree](#5-decision-tree)
6. [Random Forest](#6-random-forest)
7. [Support Vector Machine (SVM)](#7-support-vector-machine-svm)
8. [Naive Bayes](#8-naive-bayes)
9. [K-Means Clustering](#9-k-means-clustering)
10. [DBSCAN](#10-dbscan)
11. [Gradient Boosting](#11-gradient-boosting)
12. [XGBoost](#12-xgboost)
13. [Sentiment Analysis](#13-sentiment-analysis)
14. [Text Classification](#14-text-classification)
15. [ANN (Artificial Neural Network)](#15-ann-artificial-neural-network)
16. [CNN (Convolutional Neural Network)](#16-cnn-convolutional-neural-network)
17. [ResNet (Residual Network)](#17-resnet-residual-network)
18. [LSTM (Long Short-Term Memory)](#18-lstm-long-short-term-memory)
19. [YOLO (Object Detection)](#19-yolo-object-detection)
20. [StyleGAN (Generative Adversarial Network)](#20-stylegan-generative-adversarial-network)
21. [Verification & Issues Found](#21-verification--issues-found)

---

## 1. Simple Linear Regression

**Model Code:** `simple_linear_regression`
**Library:** scikit-learn (`LinearRegression`)
**Type:** Regression
**Dataset:** CSV (tabular) — uses all columns except last as features, last column as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Evaluation Metrics Returned
- MAE (Mean Absolute Error)
- MSE (Mean Squared Error)
- R² (R-squared / Coefficient of Determination)

---

## 2. Multivariable Linear Regression

**Model Code:** `multivariable_linear_regression`
**Library:** scikit-learn (`LinearRegression`)
**Type:** Regression (multiple features)
**Dataset:** CSV (tabular) — all columns except last as features, last column as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Evaluation Metrics Returned
- MAE (Mean Absolute Error)
- MSE (Mean Squared Error)
- R² (R-squared)

---

## 3. Logistic Regression

**Model Code:** `logistic_regression`
**Library:** scikit-learn (`LogisticRegression`)
**Type:** Classification
**Dataset:** CSV (tabular) — uses columns [2,3] as features, column [4] as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `C` | float | 10.0 | 0.01 | 1000.0 | — | Inverse of regularization strength. Smaller = stronger regularization |
| `solver` | str | `lbfgs` | — | — | `lbfgs`, `liblinear`, `newton-cg`, `sag`, `saga` | Algorithm for optimization |
| `max_iter` | int | 1000 | 50 | 10000 | — | Maximum iterations for solver convergence |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Solver Descriptions
- **lbfgs** — Limited-memory Broyden–Fletcher–Goldfarb–Shanno. Good for small datasets, supports L2 penalty only.
- **liblinear** — Library for large linear classification. Good for small datasets, supports L1 and L2.
- **newton-cg** — Newton's method with conjugate gradient. Supports L2 only.
- **sag** — Stochastic Average Gradient. Fast for large datasets, supports L2 only.
- **saga** — Extension of SAG. Supports L1, L2, and elastic-net penalties.

### Evaluation Metrics Returned
- Accuracy, Precision, Recall, F1 Score, Confusion Matrix

---

## 4. K-Nearest Neighbors (KNN)

**Model Code:** `knn`
**Library:** scikit-learn (`KNeighborsClassifier`)
**Type:** Classification
**Dataset:** CSV (tabular) — uses columns [2,3] as features, column [4] as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `n_neighbors` | int | 5 | 1 | 50 | — | Number of nearest neighbors to consider |
| `metric` | str | `minkowski` | — | — | `euclidean`, `manhattan`, `minkowski`, `chebyshev` | Distance metric used |
| `p` | int | 2 | 1 | 5 | — | Power parameter for Minkowski metric (1=Manhattan, 2=Euclidean) |
| `weights` | str | `distance` | — | — | `uniform`, `distance` | Weight function for prediction |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Distance Metric Descriptions
- **euclidean** — Straight-line distance (L2 norm). `p=2` in Minkowski.
- **manhattan** — Sum of absolute differences (L1 norm). `p=1` in Minkowski.
- **minkowski** — Generalized distance metric. Controlled by `p` parameter.
- **chebyshev** — Maximum absolute difference along any dimension (L∞ norm).

### Weight Function Descriptions
- **uniform** — All neighbors weighted equally.
- **distance** — Closer neighbors have more influence (weighted by inverse of distance).

### Evaluation Metrics Returned
- Accuracy, Precision, Recall, F1 Score, Confusion Matrix

---

## 5. Decision Tree

**Model Code:** `decision_tree`
**Library:** scikit-learn (`DecisionTreeClassifier`)
**Type:** Classification
**Dataset:** CSV (tabular) — uses columns [2,3] as features, column [4] as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `criterion` | str | `gini` | — | — | `gini`, `entropy`, `log_loss` | Function to measure split quality |
| `max_depth` | int (nullable) | 10 | 1 | 100 | — | Maximum depth of the tree. `null` = unlimited |
| `min_samples_split` | int | 5 | 2 | 50 | — | Minimum samples required to split an internal node |
| `min_samples_leaf` | int | 2 | 1 | 50 | — | Minimum samples required at a leaf node |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Criterion Descriptions
- **gini** — Gini impurity. Measures probability of incorrect classification.
- **entropy** — Information gain. Measures reduction in entropy after split.
- **log_loss** — Log loss / cross-entropy. Equivalent to entropy but uses logarithmic loss.

### Evaluation Metrics Returned
- Accuracy, Precision, Recall, F1 Score, Confusion Matrix

---

## 6. Random Forest

**Model Code:** `random_forest`
**Library:** scikit-learn (`RandomForestClassifier`)
**Type:** Classification (ensemble)
**Dataset:** CSV (tabular) — uses columns [2,3] as features, column [4] as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `n_estimators` | int | 100 | 1 | 500 | — | Number of trees in the forest |
| `criterion` | str | `gini` | — | — | `gini`, `entropy`, `log_loss` | Function to measure split quality |
| `max_depth` | int (nullable) | 15 | 1 | 100 | — | Maximum depth of each tree. `null` = unlimited |
| `min_samples_split` | int | 3 | 2 | 50 | — | Minimum samples required to split an internal node |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Evaluation Metrics Returned
- Accuracy, Precision, Recall, F1 Score, Confusion Matrix

---

## 7. Support Vector Machine (SVM)

**Model Code:** `svm`
**Library:** scikit-learn (`SVC`)
**Type:** Classification
**Dataset:** CSV (tabular) — uses columns [2,3] as features, column [4] as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `kernel` | str | `rbf` | — | — | `linear`, `rbf`, `poly`, `sigmoid` | Kernel function for the SVM |
| `C` | float | 10.0 | 0.01 | 1000.0 | — | Regularization parameter. Higher = less regularization |
| `gamma` | str | `scale` | — | — | `scale`, `auto` | Kernel coefficient for rbf/poly/sigmoid |
| `degree` | int | 3 | 1 | 10 | — | Degree of polynomial kernel (only used when kernel=`poly`) |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Kernel Descriptions
- **linear** — Linear kernel: `K(x,y) = x·y`. Best for linearly separable data.
- **rbf** — Radial Basis Function (Gaussian): `K(x,y) = exp(-γ||x-y||²)`. Most versatile, works well for non-linear data.
- **poly** — Polynomial: `K(x,y) = (γ·x·y + r)^d`. Controlled by `degree` parameter.
- **sigmoid** — Sigmoid/tanh: `K(x,y) = tanh(γ·x·y + r)`. Similar to neural network activation.

### Gamma Descriptions
- **scale** — `1 / (n_features * X.var())`. Recommended default.
- **auto** — `1 / n_features`. Simpler calculation.

### Evaluation Metrics Returned
- Accuracy, Precision, Recall, F1 Score, Confusion Matrix

---

## 8. Naive Bayes

**Model Code:** `naive_bayes`
**Library:** scikit-learn (`GaussianNB`)
**Type:** Classification
**Dataset:** CSV (tabular) — uses columns [2,3] as features, column [4] as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `var_smoothing` | float | 1e-9 | 1e-12 | 1.0 | — | Portion of the largest variance added to all variances for stability |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Evaluation Metrics Returned
- Accuracy, Precision, Recall, F1 Score, Confusion Matrix

---

## 9. K-Means Clustering

**Model Code:** `k_means`
**Library:** scikit-learn (`KMeans`)
**Type:** Unsupervised Clustering
**Dataset:** CSV (tabular) — uses all numeric columns

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `n_clusters` | int | 3 | 2 | 20 | — | Number of clusters to form |
| `init` | str | `k-means++` | — | — | `k-means++`, `random` | Method for centroid initialization |
| `max_iter` | int | 300 | 100 | 1000 | — | Maximum iterations for a single run |
| `n_init` | int | 10 | 1 | 50 | — | Number of times algorithm runs with different centroid seeds |
| `random_state` | int (nullable) | 42 | 0 | 9999 | — | Random seed for reproducibility |

### Init Method Descriptions
- **k-means++** — Smart initialization that spreads initial centroids apart. Faster convergence.
- **random** — Random selection of data points as initial centroids.

### Results Returned
- Cluster labels, Cluster centers, Inertia (WCSS), Elbow plot, Cluster plot

---

## 10. DBSCAN

**Model Code:** `dbscan`
**Library:** scikit-learn (`DBSCAN`)
**Type:** Unsupervised Clustering (density-based)
**Dataset:** CSV (tabular) — uses all numeric columns (minimum 2)

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `eps` | float | 0.5 | 0.01 | 10.0 | — | Maximum distance between two points to be considered neighbors |
| `min_samples` | int | 5 | 1 | 50 | — | Minimum points required to form a dense region (core point) |
| `metric` | str | `euclidean` | — | — | `euclidean`, `manhattan`, `cosine` | Distance metric used |

### Metric Descriptions
- **euclidean** — Straight-line distance (L2 norm).
- **manhattan** — Sum of absolute differences (L1 norm).
- **cosine** — Cosine similarity-based distance. Good for high-dimensional sparse data.

### Results Returned
- Cluster labels, Number of clusters, Number of noise points, Cluster visualization

---

## 11. Gradient Boosting

**Model Code:** `gradient_boosting`
**Library:** scikit-learn (`GradientBoostingClassifier`)
**Type:** Classification (ensemble, boosting)
**Dataset:** CSV (tabular) — all columns except last as features, last column as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `n_estimators` | int | 200 | 10 | 1000 | — | Number of boosting stages (trees) |
| `learning_rate` | float | 0.05 | 0.001 | 1.0 | — | Shrinks contribution of each tree. Lower = more robust but slower |
| `max_depth` | int | 5 | 1 | 20 | — | Maximum depth of individual trees |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |

### Evaluation Metrics Returned
- Accuracy, Precision (weighted), Recall (weighted), F1 Score (weighted)

---

## 12. XGBoost

**Model Code:** `xgboost`
**Library:** xgboost (`XGBClassifier`)
**Type:** Classification (ensemble, gradient boosting)
**Dataset:** CSV (tabular) — all columns except last as features, last column as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `n_estimators` | int | 200 | 10 | 1000 | — | Number of boosting rounds |
| `learning_rate` | float | 0.05 | 0.001 | 1.0 | — | Step size shrinkage to prevent overfitting |
| `max_depth` | int | 6 | 1 | 20 | — | Maximum depth of each tree |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |

### Auto-detected Settings
- **objective**: `binary:logistic` (2 classes) or `multi:softmax` (3+ classes) — auto-detected from data

### Evaluation Metrics Returned
- Accuracy, Precision (weighted), Recall (weighted), F1 Score (weighted)

---

## 13. Sentiment Analysis

**Model Code:** `sentiment_analysis`
**Library:** scikit-learn (`TfidfVectorizer` + `LogisticRegression` pipeline)
**Type:** NLP / Text Classification
**Dataset:** CSV with text column and label column (auto-detected)

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `max_features` | int | 10000 | 100 | 50000 | — | Maximum number of TF-IDF features (vocabulary size) |
| `max_iter` | int | 1000 | 100 | 5000 | — | Maximum iterations for Logistic Regression solver |
| `C` | float | 5.0 | 0.01 | 100.0 | — | Inverse regularization strength for Logistic Regression |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |

### Additional Input Parameters (from request body)
| Parameter | Type | Description |
|-----------|------|-------------|
| `text_column` | str (optional) | Name of the text column. Auto-detected if not provided |
| `label_column` | str (optional) | Name of the label column. Auto-detected if not provided |

### Pipeline Details
- **TfidfVectorizer**: Converts text to TF-IDF feature vectors. Uses unigrams and bigrams (`ngram_range=(1,2)`).
- **LogisticRegression**: Classifies based on TF-IDF features.

### Evaluation Metrics Returned
- Accuracy, Precision (weighted), Recall (weighted), F1 Score (weighted)

---

## 14. Text Classification

**Model Code:** `text_classification`
**Library:** scikit-learn (`CountVectorizer` + `MultinomialNB` pipeline)
**Type:** NLP / Text Classification
**Dataset:** CSV with text column and label column (auto-detected)

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `max_features` | int | 10000 | 100 | 50000 | — | Maximum number of bag-of-words features (vocabulary size) |
| `alpha` | float | 0.5 | 0.001 | 10.0 | — | Laplace/Lidstone smoothing parameter for Naive Bayes |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data used for testing |

### Additional Input Parameters (from request body)
| Parameter | Type | Description |
|-----------|------|-------------|
| `text_column` | str (optional) | Name of the text column. Auto-detected if not provided |
| `label_column` | str (optional) | Name of the label column. Auto-detected if not provided |

### Pipeline Details
- **CountVectorizer**: Converts text to bag-of-words feature vectors. Uses unigrams and bigrams (`ngram_range=(1,2)`).
- **MultinomialNB**: Multinomial Naive Bayes classifier. Good for text classification with word counts.

### Evaluation Metrics Returned
- Accuracy, Precision (weighted), Recall (weighted), F1 Score (weighted)

---

## 15. ANN (Artificial Neural Network)

**Model Code:** `ann`
**Library:** Keras (`Sequential`)
**Type:** Deep Learning — Classification (tabular data)
**Dataset:** CSV (tabular) — all columns except last as features, last column as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `epochs` | int | 100 | 1 | 500 | — | Number of complete passes through the training data |
| `batch_size` | int | 32 | 1 | 512 | — | Number of samples per gradient update |
| `optimizer` | str | `adam` | — | — | `adam`, `sgd`, `rmsprop`, `adagrad` | Optimization algorithm |
| `loss` | str | `binary_crossentropy` | — | — | `binary_crossentropy`, `categorical_crossentropy`, `sparse_categorical_crossentropy`, `mse` | Loss function |
| `validation_split` | float | 0.15 | 0.05 | 0.5 | — | Fraction of training data used for validation during training |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | Fraction of data held out for final testing |

### Optimizer Descriptions
- **adam** — Adaptive Moment Estimation. Combines momentum and RMSProp. Best general-purpose optimizer.
- **sgd** — Stochastic Gradient Descent. Simple but may need careful learning rate tuning.
- **rmsprop** — Root Mean Square Propagation. Good for recurrent networks and non-stationary objectives.
- **adagrad** — Adaptive Gradient. Adapts learning rate per parameter. Good for sparse data.

### Loss Function Descriptions
- **binary_crossentropy** — For binary classification (2 classes). Output: 1 neuron with sigmoid.
- **categorical_crossentropy** — For multi-class classification. Requires one-hot encoded labels. Output: N neurons with softmax.
- **sparse_categorical_crossentropy** — For multi-class classification. Uses integer labels (no one-hot). Output: N neurons with softmax.
- **mse** — Mean Squared Error. For regression tasks.

### Hidden Layers (User-Configurable Architecture)

The user sends a `hidden_layers` array. Each layer object:

| Layer Parameter | Type | Default | Description |
|----------------|------|---------|-------------|
| `units` | int | 64 | Number of neurons in the Dense layer |
| `activation` | str | `relu` | Activation function for this layer |
| `dropout` | float | 0 | Dropout rate (0 to 1). 0 = no dropout |

#### Available Activation Functions (for hidden layers)
- **relu** — Rectified Linear Unit: `max(0, x)`. Most common for hidden layers.
- **sigmoid** — Squashes output to (0, 1). Used for binary output.
- **tanh** — Squashes output to (-1, 1). Zero-centered version of sigmoid.
- **softmax** — Converts to probability distribution. Used for multi-class output.
- **linear** — No transformation. Used for regression output.
- **elu** — Exponential Linear Unit. Smooth version of ReLU for negative values.
- **selu** — Scaled ELU. Self-normalizing variant.
- **swish** — `x * sigmoid(x)`. Smooth, non-monotonic.
- **leaky_relu** — Allows small gradient for negative values.

### Auto-Configured Output Layer
- Binary classification → Dense(1, sigmoid) + binary_crossentropy
- Multi-class (categorical_crossentropy) → Dense(N, softmax) + one-hot encoding
- Multi-class (sparse_categorical_crossentropy) → Dense(N, softmax) + integer labels

### Built-in Features
- **Early Stopping**: patience=5 on validation loss
- **StandardScaler**: Features are standardized before training
- **LabelEncoder**: Categorical targets are auto-encoded

### Evaluation Metrics Returned
- Test Accuracy, Test Loss, Validation Accuracy, Validation Loss, Epochs Trained

---

## 16. CNN (Convolutional Neural Network)

**Model Code:** `cnn`
**Library:** Keras (`Sequential`)
**Type:** Deep Learning — Image Classification
**Dataset:** Image directory with `train/` and `test/` subdirectories, each containing class folders

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `epochs` | int | 50 | 1 | 500 | — | Number of training epochs |
| `batch_size` | int | 32 | 1 | 512 | — | Number of images per batch |
| `optimizer` | str | `adam` | — | — | `adam`, `sgd`, `rmsprop`, `adagrad`, `adadelta` | Optimization algorithm |
| `loss` | str | `categorical_crossentropy` | — | — | `binary_crossentropy`, `categorical_crossentropy`, `sparse_categorical_crossentropy`, `mse` | Loss function |
| `validation_split` | float | 0.15 | 0.05 | 0.5 | — | *(defined in schema but not used in CNN — validation comes from test set)* |
| `test_size` | float | 0.2 | 0.05 | 0.5 | — | *(defined in schema but not used in CNN — uses directory-based split)* |

### Additional Input Parameters (from request body)

| Parameter | Type | Description |
|-----------|------|-------------|
| `numberOfNeuronsInInputLayer` | int | Number of filters in the first Conv2D layer |
| `inputKernelSize` | [int, int] | Kernel size for the first Conv2D layer, e.g. `[3, 3]` |
| `inputLayerActivationFunction` | str | Activation function for the first Conv2D layer |
| `inputShape` | [int, int, int] | Input image dimensions, e.g. `[64, 64, 3]` (height, width, channels) |
| `classMode` | str | Keras class mode: `categorical`, `binary`, or `sparse` |

### Optimizer Descriptions
- **adam** — Adaptive Moment Estimation. Best general-purpose optimizer.
- **sgd** — Stochastic Gradient Descent. Supports momentum parameter.
- **rmsprop** — Root Mean Square Propagation. Good for image tasks.
- **adagrad** — Adaptive Gradient. Per-parameter learning rates.
- **adadelta** — Extension of Adagrad. No need to set initial learning rate.

### Hidden Layers (User-Configurable Architecture)

The user sends a `hiddenLayerArray`. Each layer object has a `type` field:

#### Layer Type: `conv` (Convolutional Layer)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | — | Must be `"conv"` |
| `numberOfNeurons` | int | 64 | Number of filters/feature maps |
| `kernel` | [int, int] | [3, 3] | Convolution kernel size |
| `activationFunction` | str | `relu` | Activation function |

#### Layer Type: `pooling` / `pool` (Pooling Layer)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | — | Must be `"pooling"` or `"pool"` |
| `poolingType` | str | `maxPool` | Type of pooling |
| `poolingSize` | [int, int] | [2, 2] | Pool window size |
| `minPoolStride` | [int, int] | same as poolingSize | Stride for min pooling |
| `avgPoolStride` | [int, int] | same as poolingSize | Stride for average pooling |

**Pooling Type Options:**
- **max** / **maxPool** — Takes maximum value in each window. Most common. Preserves strongest features.
- **min** / **minPool** — Takes minimum value in each window. Custom implementation using Lambda layer.
- **average** / **avgPool** / **avg** / **averagePool** — Takes average value in each window. Smoother downsampling.

#### Layer Type: `flatten` (Flatten Layer)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | — | Must be `"flatten"` |

Converts 2D feature maps to 1D vector. Required before Dense layers. Auto-inserted if missing before first Dense layer.

#### Layer Type: `dense` (Fully Connected Layer)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | — | Must be `"dense"` |
| `units` / `numberOfNeurons` | int | 128 | Number of neurons |
| `activationFunction` | str | `relu` | Activation function |

#### Layer Type: `dropout` (Dropout Layer)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | — | Must be `"dropout"` |
| `dropoutRate` | float | 0.5 | Fraction of neurons to randomly deactivate (0 to 1) |

### Evaluation Metrics (configurable)
User selects from `evaluationMetrics` array:
- **accuracy** — Fraction of correct predictions
- **precision** — True positives / (True positives + False positives)
- **recall** — True positives / (True positives + False negatives)
- **f1** — Harmonic mean of precision and recall

### Auto-Configured Output Layer
- categorical_crossentropy → Dense(num_classes, softmax)
- sparse_categorical_crossentropy → Dense(num_classes, softmax)
- binary_crossentropy → Dense(1, sigmoid)

### Built-in Features
- **ImageDataGenerator**: Rescaling (1/255), shear, zoom, horizontal flip for training
- **Early Stopping**: patience=3 on validation loss

### Data Augmentation (applied to training set)
- Rescale: 1./255
- Shear range: 0.2
- Zoom range: 0.2
- Horizontal flip: True

---

## 17. ResNet (Residual Network)

**Model Code:** `resnet`
**Library:** Keras (`ResNet50` pre-trained on ImageNet)
**Type:** Deep Learning — Transfer Learning / Image Classification
**Dataset:** Image directory with `train/` and `test/` subdirectories

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `epochs` | int | 25 | 1 | 500 | — | Number of fine-tuning epochs |
| `batch_size` | int | 16 | 1 | 512 | — | Number of images per batch |
| `optimizer` | str | `adam` | — | — | `adam`, `sgd`, `rmsprop`, `adagrad`, `adadelta` | Optimization algorithm |
| `loss` | str | `categorical_crossentropy` | — | — | `binary_crossentropy`, `categorical_crossentropy`, `sparse_categorical_crossentropy` | Loss function |
| `validation_split` | float | 0.15 | 0.05 | 0.5 | — | *(defined in schema but not used — validation comes from test set)* |
| `learning_rate` | float | 0.0001 | 0.00001 | 1.0 | — | Learning rate for the optimizer |

### Additional Input Parameters (from request body)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `inputShape` | [int, int, int] | [224, 224, 3] | Input image dimensions |
| `classMode` | str | `categorical` | Keras class mode: `categorical` or `binary` |
| `isBaseFrozen` | bool | true | Whether to freeze ResNet50 base layers (transfer learning) |

### Hidden Layers (User-Configurable — added on top of ResNet50)

Each layer in `hiddenLayerArray`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `units` | int | 256 | Number of neurons in Dense layer |
| `activation` | str | `relu` | Activation function |
| `dropout` | float | 0 | Dropout rate (0 to 1) |

### Architecture
1. **ResNet50 base** (pre-trained on ImageNet, optionally frozen)
2. **GlobalAveragePooling2D** (reduces spatial dimensions)
3. **User-configured Dense + Dropout layers**
4. **Output Dense layer** (auto-configured based on class_mode and num_classes)

### Built-in Features
- **Transfer Learning**: Uses ImageNet pre-trained weights
- **Freeze/Unfreeze**: User can freeze base model for feature extraction or unfreeze for fine-tuning
- **Early Stopping**: patience=3 on validation loss
- **Data Augmentation**: Same as CNN (rescale, shear, zoom, flip)

---

## 18. LSTM (Long Short-Term Memory)

**Model Code:** `lstm`
**Library:** Keras (`Sequential` with LSTM layers)
**Type:** Deep Learning — Sequence/Time-Series
**Dataset:** CSV (tabular) — all columns except last as features, last column as target

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `epochs` | int | 100 | 1 | 500 | — | Number of training epochs |
| `batch_size` | int | 32 | 1 | 512 | — | Number of sequences per batch |
| `optimizer` | str | `adam` | — | — | `adam`, `sgd`, `rmsprop`, `adagrad`, `adadelta` | Optimization algorithm |
| `loss` | str | `mse` | — | — | `mse`, `mae`, `huber_loss`, `binary_crossentropy`, `categorical_crossentropy` | Loss function |
| `validation_split` | float | 0.15 | 0.05 | 0.5 | — | Fraction of training data for validation |
| `sequence_length` | int | 20 | 1 | 100 | — | Number of time steps in each input sequence (sliding window size) |
| `learning_rate` | float | 0.001 | 0.00001 | 1.0 | — | Learning rate for the optimizer |

### Loss Function Descriptions
- **mse** — Mean Squared Error. Standard for regression/time-series prediction.
- **mae** — Mean Absolute Error. More robust to outliers than MSE.
- **huber_loss** — Combination of MSE and MAE. Less sensitive to outliers.
- **binary_crossentropy** — For binary sequence classification.
- **categorical_crossentropy** — For multi-class sequence classification.

### Additional Input Parameters (from request body)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `classMode` | str | `categorical` | `linear` for regression, `categorical` for classification |

### Hidden Layers (User-Configurable Architecture)

Each layer in `hiddenLayerArray`:

#### Layer Type: `lstm` (LSTM Layer)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | — | Must be `"lstm"` |
| `units` | int | 64 | Number of LSTM units (memory cells) |
| `dropout` | float | 0 | Dropout rate after this LSTM layer |
| `return_sequences` | bool | auto | Whether to return full sequence. Auto-set: True for stacked LSTMs (except last) |

#### Layer Type: `dense` (Dense Layer)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | — | Must be `"dense"` |
| `units` | int | 64 | Number of neurons |
| `activation` | str | `relu` | Activation function |
| `dropout` | float | 0 | Dropout rate after this Dense layer |

### Default Architecture (when no hidden layers provided)
1. LSTM(64, return_sequences=True)
2. Dropout(0.2)
3. LSTM(32, return_sequences=False)
4. Dropout(0.2)

### Auto-Configured Output Layer
- Regression (`classMode='linear'`) → Dense(1, linear), loss=mse, metric=mae
- Binary classification → Dense(1, sigmoid), loss=binary_crossentropy
- Multi-class → Dense(num_classes, softmax), loss=sparse_categorical_crossentropy

### Built-in Features
- **MinMaxScaler**: Features scaled to [0, 1]
- **Sliding Window**: Creates sequences from tabular data
- **Early Stopping**: patience=5 on validation loss
- **Auto Label Encoding**: Categorical targets auto-encoded

---

## 19. YOLO (Object Detection)

**Model Code:** `yolo`
**Library:** Ultralytics (`YOLOv8n`)
**Type:** Deep Learning — Object Detection
**Dataset:** Image directory with YOLO format (images + labels with bounding boxes)

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `epochs` | int | 50 | 1 | 500 | — | Number of training epochs |
| `batch_size` | int | 16 | 1 | 128 | — | Number of images per batch |
| `imgsz` | int | 640 | 32 | 1280 | — | Input image size (square). Images resized to this |
| `optimizer` | str | `auto` | — | — | `auto`, `SGD`, `Adam`, `AdamW`, `RMSProp` | Optimization algorithm |
| `lr0` | float | 0.01 | 0.00001 | 1.0 | — | Initial learning rate |
| `lrf` | float | 0.01 | 0.001 | 1.0 | — | Final learning rate as fraction of lr0 (cosine annealing) |
| `momentum` | float | 0.937 | 0.5 | 0.999 | — | SGD momentum / Adam beta1 |
| `weight_decay` | float | 0.0005 | 0.0 | 0.01 | — | L2 regularization penalty |
| `warmup_epochs` | int | 3 | 0 | 20 | — | Number of warmup epochs (gradual LR increase) |
| `augment` | bool | true | — | — | — | Enable/disable data augmentation |
| `mosaic` | float | 1.0 | 0.0 | 1.0 | — | Mosaic augmentation probability (combines 4 images) |

### Optimizer Descriptions
- **auto** — Automatically selects best optimizer based on dataset.
- **SGD** — Stochastic Gradient Descent with momentum.
- **Adam** — Adaptive Moment Estimation.
- **AdamW** — Adam with decoupled weight decay.
- **RMSProp** — Root Mean Square Propagation.

### Dataset Structure Required
```
dataset/
├── data.yaml          # Auto-generated if missing
├── images/
│   ├── train/         # Training images
│   └── val/           # Validation images
└── labels/
    ├── train/         # YOLO format label files (.txt)
    └── val/           # YOLO format label files (.txt)
```

### Results Returned
- mAP@50, mAP@50-95, Epochs trained, Model path

---

## 20. StyleGAN (Generative Adversarial Network)

**Model Code:** `stylegan`
**Library:** PyTorch (custom StyleGAN architecture)
**Type:** Deep Learning — Generative (Image Synthesis)
**Dataset:** Image directory (flat or with subfolders — class labels not needed)

### Hyperparameters

| Parameter | Type | Default | Min | Max | Options | Description |
|-----------|------|---------|-----|-----|---------|-------------|
| `epochs` | int | 300 | 1 | 1000 | — | Number of training epochs |
| `batch_size` | int | 8 | 1 | 128 | — | Number of images per batch |
| `z_dim` | int | 256 | 64 | 1024 | — | Latent space dimensionality (noise vector size) |
| `w_dim` | int | 256 | 64 | 1024 | — | Intermediate latent space dimensionality (style vector size) |
| `log_resolution` | int | 7 | 6 | 10 | — | Log2 of output resolution (6=64px, 7=128px, 8=256px, 9=512px, 10=1024px) |
| `learning_rate` | float | 0.0001 | 0.000001 | 0.1 | — | Learning rate for Generator + Mapping Network |
| `optimizer` | str | `adam` | — | — | `adam`, `rmsprop` | Optimization algorithm *(Note: only adam is actually used in code — see issues)* |
| `disc_lr` | float | — | 0.000001 | 0.1 | — | Learning rate for Discriminator *(defined in schema but NOT used in code — see issues)* |
| `r1_penalty` | float | — | 0.0 | 100.0 | — | R1 gradient penalty weight *(defined in schema but NOT used in code — see issues)* |

### Resolution Mapping
| `log_resolution` | Output Resolution |
|-------------------|-------------------|
| 6 | 64 × 64 |
| 7 | 128 × 128 |
| 8 | 256 × 256 |
| 9 | 512 × 512 |
| 10 | 1024 × 1024 |

### Architecture Components
- **Mapping Network**: 8 fully-connected layers. Maps z-space to w-space (style space).
- **Generator**: Progressive growing with style blocks. Uses weight modulation/demodulation.
- **Discriminator**: Progressive downsampling with residual connections and minibatch std.
- **Equalized Learning Rate**: Custom weight initialization for stable training.

### Results Returned
- Generator Loss, Discriminator Loss, Epochs trained, Model path

---

## 21. Verification & Issues Found

> ⚠️ **Point-in-time audit.** This section was captured during an early code
> review and is **not** kept in lockstep with the code. Re-verify before acting
> on any item. Confirmed status as of the latest review:
> - **Issue 5 (missing MODEL_CODES) — RESOLVED.** `gradient_boosting`, `xgboost`,
>   `sentiment_analysis`, and `text_classification` are all in `config.MODEL_CODES`
>   (verified against `services/model_registry.py`, zero drift).
> - **Issue 11 (hardcoded `iloc[:, [2,3]]` column indices) — RESOLVED.** The
>   classical models now use generic loaders; no hardcoded indices remain in
>   `backend/models/`.
> - Remaining items below are unverified against current code and may also be
>   outdated.

### ✅ Verified Correct

1. **All sklearn models** (Linear Regression, Logistic Regression, KNN, Decision Tree, Random Forest, SVM, Naive Bayes, K-Means, DBSCAN, Gradient Boosting) — hyperparameter options match scikit-learn's actual API.
2. **XGBoost** — parameters match xgboost API.
3. **ANN** — optimizer and loss options are valid Keras options.
4. **CNN** — layer types, pooling types, optimizer, and loss options are valid.
5. **LSTM** — optimizer, loss, and layer options are valid.
6. **ResNet** — optimizer and loss options are valid.
7. **YOLO** — optimizer options match Ultralytics API (case-sensitive: `SGD`, `Adam`, `AdamW`, `RMSProp`).
8. **Sentiment Analysis & Text Classification** — pipeline parameters are valid.

### ⚠️ Issues Found

#### Issue 1: StyleGAN — `disc_lr` and `r1_penalty` defined in schema but NOT used in code
- **File:** `hyperparam_validator.py` defines `disc_lr` and `r1_penalty` for StyleGAN
- **Problem:** `stylegan_model.py` uses a single `learning_rate` for both Generator and Discriminator. `disc_lr` and `r1_penalty` are never read from `validated_params`.
- **Impact:** Users can set these values but they have NO effect on training.
- **Fix:** Either implement separate discriminator LR and R1 penalty in the training loop, or remove them from the schema.

#### Issue 2: StyleGAN — `optimizer` option `rmsprop` defined but only `adam` is used
- **File:** `stylegan_model.py` hardcodes `optim.Adam` for both generator and discriminator
- **Problem:** The `optimizer` parameter from `validated_params` is never used to select the optimizer.
- **Impact:** User selecting `rmsprop` will still get Adam.
- **Fix:** Add optimizer selection logic similar to other models.

#### Issue 3: CNN — `validation_split` and `test_size` in schema but not used
- **File:** `cnn.py` uses directory-based train/test split (separate folders), not percentage-based
- **Problem:** These parameters are accepted and validated but have no effect on CNN training.
- **Impact:** Misleading to users who think they're controlling the split.
- **Fix:** Remove from CNN schema or document that CNN uses directory-based splitting.

#### Issue 4: ResNet — `validation_split` in schema but not used
- **File:** `resnet_model.py` uses directory-based validation (test folder), not validation_split
- **Problem:** Same as CNN — parameter accepted but ignored.
- **Fix:** Remove from ResNet schema or document.

#### Issue 5: Missing models in `MODEL_CODES` config
- **File:** `config.py` `MODEL_CODES` list is missing:
  - `gradient_boosting`
  - `xgboost`
  - `sentiment_analysis`
  - `text_classification`
- **Impact:** These models work (they have routes and schemas) but aren't in the canonical model list.

#### Issue 6: Missing `learning_rate` in ANN schema
- **File:** `ann.py` hardcodes `learning_rate=0.001` for all optimizers
- **Problem:** User cannot configure learning rate for ANN (unlike LSTM, ResNet which expose it).
- **Fix:** Add `learning_rate` to ANN validation schema and use it in the optimizer construction.

#### Issue 7: Missing `learning_rate` in CNN schema
- **File:** `cnn.py` reads `learning_rate` from `optimizerObject` (sent by frontend) but it's not in the hyperparam validator schema.
- **Problem:** Learning rate is controlled via the frontend's `optimizerObject.learning_rate` but not validated.
- **Fix:** Add `learning_rate` to CNN validation schema for consistency.

#### Issue 8: StyleGAN missing `DEFAULT_HYPERPARAMS` for `disc_lr` and `r1_penalty`
- **File:** `config.py` doesn't include defaults for `disc_lr` and `r1_penalty`
- **Impact:** If these are kept in the schema, they need defaults.

#### Issue 9: LSTM `learning_rate` has no default in `DEFAULT_HYPERPARAMS`
- **File:** `config.py` LSTM defaults don't include `learning_rate`
- **Problem:** The LSTM model code defaults to 0.001 internally, but the config doesn't declare it.
- **Fix:** Add `'learning_rate': 0.001` to LSTM defaults in config.

#### Issue 10: ANN `mse` loss option mismatch
- **File:** `hyperparam_validator.py` lists `mse` as a loss option for ANN
- **Problem:** The ANN code only handles `categorical_crossentropy` and `sparse_categorical_crossentropy` specially. `mse` would work but the output layer logic (sigmoid/softmax) may not be appropriate for regression.
- **Impact:** Minor — MSE would technically work but the auto-configured output layer assumes classification.

#### Issue 11: Several sklearn models hardcode column indices
- **Files:** `logisticRegression.py`, `knn.py`, `decisionTree.py`, `randomForest.py`, `naiveBayes.py`, `supportVectorMachine.py`
- **Problem:** These models hardcode `X = dataset.iloc[:, [2, 3]].values` and `y = dataset.iloc[:, 4].values`, assuming a specific dataset structure (like the Social_Network_Ads dataset).
- **Impact:** Only works with datasets that have features in columns 2-3 and target in column 4. Fails or gives wrong results with other datasets.
- **Fix:** Use generic column selection (all columns except last as features, last as target) like ANN, Gradient Boosting, and XGBoost do.

---

## Appendix: Complete Activation Functions Reference

These activation functions are available for Keras-based models (ANN, CNN, LSTM, ResNet):

| Activation | Formula | Range | Best For |
|-----------|---------|-------|----------|
| `relu` | max(0, x) | [0, ∞) | Hidden layers (default choice) |
| `sigmoid` | 1/(1+e^(-x)) | (0, 1) | Binary classification output |
| `tanh` | (e^x - e^(-x))/(e^x + e^(-x)) | (-1, 1) | Hidden layers, zero-centered |
| `softmax` | e^xi / Σe^xj | (0, 1), sums to 1 | Multi-class classification output |
| `linear` | x | (-∞, ∞) | Regression output |
| `elu` | x if x>0, α(e^x-1) if x≤0 | (-α, ∞) | Hidden layers, smooth ReLU |
| `selu` | λ·elu(x) | self-normalizing | Deep networks without batch norm |
| `swish` | x·sigmoid(x) | (-0.28, ∞) | Hidden layers, modern alternative to ReLU |
| `leaky_relu` | x if x>0, αx if x≤0 | (-∞, ∞) | Hidden layers, avoids dying ReLU |
| `softplus` | log(1+e^x) | (0, ∞) | Smooth approximation of ReLU |

## Appendix: Complete Optimizer Reference

| Optimizer | Models Available In | Key Properties |
|-----------|-------------------|----------------|
| `adam` | ANN, CNN, LSTM, ResNet, StyleGAN | Adaptive LR, momentum. Best general-purpose |
| `sgd` | ANN, CNN, LSTM, ResNet | Simple, supports momentum. Needs LR tuning |
| `rmsprop` | ANN, CNN, LSTM, ResNet, StyleGAN* | Adaptive LR. Good for RNNs |
| `adagrad` | ANN, CNN, LSTM, ResNet | Per-param adaptive LR. Good for sparse data |
| `adadelta` | CNN, LSTM, ResNet | Extension of Adagrad. No initial LR needed |
| `auto` | YOLO | Auto-selects best optimizer |
| `SGD` | YOLO | Ultralytics SGD (case-sensitive) |
| `Adam` | YOLO | Ultralytics Adam (case-sensitive) |
| `AdamW` | YOLO | Adam with weight decay (case-sensitive) |
| `RMSProp` | YOLO | Ultralytics RMSProp (case-sensitive) |

*StyleGAN lists `rmsprop` as option but only uses `adam` in code (see Issue #2)

## Appendix: Loss Functions Reference

| Loss Function | Models | Use Case |
|--------------|--------|----------|
| `binary_crossentropy` | ANN, CNN, LSTM, ResNet | Binary classification (2 classes) |
| `categorical_crossentropy` | ANN, CNN, LSTM, ResNet | Multi-class with one-hot labels |
| `sparse_categorical_crossentropy` | ANN, CNN, ResNet | Multi-class with integer labels |
| `mse` (mean_squared_error) | ANN, CNN, LSTM | Regression tasks |
| `mae` (mean_absolute_error) | LSTM | Regression, robust to outliers |
| `huber_loss` | LSTM | Regression, blend of MSE and MAE |
