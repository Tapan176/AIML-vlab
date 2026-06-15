"""Canonical model catalog used for UI model info and DB seeding."""

from copy import deepcopy

from config import DEFAULT_HYPERPARAMS
from services.hyperparam_validator import VALIDATION_SCHEMAS


MODEL_CATALOG_VERSION = 3


PARAM_LABELS = {
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

PARAM_NOTES = {
    "simple_linear_regression": {
        "test_size": "Fraction of rows reserved for holdout evaluation before fitting the regression line.",
        "random_state": "Seed used for the train/test split so repeated runs are reproducible.",
    },
    "multivariable_linear_regression": {
        "test_size": "Fraction of rows reserved for holdout evaluation before fitting the regression model.",
        "random_state": "Seed used for the train/test split so repeated runs are reproducible.",
    },
    "logistic_regression": {
        "C": "Inverse regularization strength. Smaller values regularize harder and usually reduce overfitting.",
        "solver": "Optimization algorithm used to fit the logistic regression coefficients.",
        "max_iter": "Upper bound on solver iterations before convergence stops.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
        "random_state": "Seed used for the split and for solvers that rely on randomization.",
    },
    "knn": {
        "n_neighbors": "How many nearest training samples vote when predicting the class of a new point.",
        "metric": "Distance function used to decide which points count as nearest neighbors.",
        "p": "Only affects the Minkowski metric: 1 behaves like Manhattan distance and 2 behaves like Euclidean distance.",
        "weights": "Whether every neighbor votes equally or closer neighbors get more influence.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
        "random_state": "Seed used for the train/test split.",
    },
    "decision_tree": {
        "criterion": "Split quality function used to choose the next branch in the tree.",
        "max_depth": "Maximum number of split levels. Null removes the depth cap completely.",
        "min_samples_split": "Smallest sample count a node must contain before the tree is allowed to split it.",
        "min_samples_leaf": "Smallest sample count allowed in any terminal leaf after a split.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
        "random_state": "Seed used for the split and any stochastic behavior inside the estimator.",
    },
    "random_forest": {
        "n_estimators": "How many decision trees are trained in the ensemble.",
        "criterion": "Split quality function used inside every tree.",
        "max_depth": "Maximum depth of each tree. Null removes the cap.",
        "min_samples_split": "Smallest sample count a node must contain before a tree can split it.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
        "random_state": "Seed used for the split and forest randomness.",
    },
    "svm": {
        "kernel": "Kernel function that defines the separating surface between classes.",
        "C": "Penalty for margin violations. Larger values fit the training data more aggressively.",
        "gamma": "Kernel coefficient for rbf, poly, and sigmoid kernels.",
        "degree": "Polynomial order used only when the kernel is set to poly.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
        "random_state": "Seed used for the split and any randomized estimator behavior.",
    },
    "naive_bayes": {
        "var_smoothing": "Small positive value added to feature variances so GaussianNB remains numerically stable.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
        "random_state": "Seed used for the train/test split.",
    },
    "k_means": {
        "n_clusters": "How many clusters the algorithm will try to discover.",
        "init": "Strategy used to place the initial centroids before iterative refinement starts.",
        "max_iter": "Maximum Lloyd updates allowed for one initialization run.",
        "n_init": "How many separate centroid initializations are tried before the best run is kept.",
        "random_state": "Seed used when initialization depends on randomness.",
    },
    "dbscan": {
        "eps": "Maximum neighborhood radius for two points to count as density-connected.",
        "min_samples": "Minimum neighborhood size required for a point to become a core point.",
        "metric": "Distance function used when DBSCAN measures neighborhood radius.",
    },
    "gradient_boosting": {
        "n_estimators": "How many shallow trees are added sequentially to correct previous errors.",
        "learning_rate": "Shrinkage applied to each boosting step. Smaller values slow training but can generalize better.",
        "max_depth": "Maximum depth for each boosting tree.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
    },
    "xgboost": {
        "n_estimators": "How many boosted trees are trained.",
        "learning_rate": "Shrinkage applied to each boosting step.",
        "max_depth": "Maximum tree depth for each boosted estimator.",
        "test_size": "Fraction of rows reserved for holdout evaluation.",
    },
    "sentiment_analysis": {
        "max_features": "Vocabulary cap for the TF-IDF vectorizer. Higher values keep more unique n-grams.",
        "max_iter": "Maximum iterations allowed for the logistic regression classifier.",
        "C": "Inverse regularization strength for the logistic regression classifier.",
        "test_size": "Fraction of text rows reserved for holdout evaluation.",
    },
    "text_classification": {
        "max_features": "Vocabulary cap for the count vectorizer.",
        "alpha": "Laplace smoothing strength for Multinomial Naive Bayes.",
        "test_size": "Fraction of text rows reserved for holdout evaluation.",
    },
}

OPTION_NOTES = {
    ("logistic_regression", "solver"): {
        "lbfgs": "Good default for most dense problems.",
        "liblinear": "Useful for smaller binary problems.",
        "newton-cg": "Second-order solver for smooth multiclass optimization.",
        "sag": "Stochastic Average Gradient; better on larger datasets.",
        "saga": "SAGA solver; supports large sparse problems and more regularization variants.",
    },
    ("knn", "metric"): {
        "euclidean": "Straight-line distance in feature space.",
        "manhattan": "City-block distance that sums absolute differences.",
        "minkowski": "Generalized distance controlled by the p parameter.",
        "chebyshev": "Maximum coordinate difference across features.",
    },
    ("knn", "weights"): {
        "uniform": "All neighbors vote equally.",
        "distance": "Closer neighbors vote more strongly.",
    },
    ("decision_tree", "criterion"): {
        "gini": "Gini impurity; usually the fastest default.",
        "entropy": "Information gain based on entropy.",
        "log_loss": "Cross-entropy style split scoring.",
    },
    ("random_forest", "criterion"): {
        "gini": "Gini impurity across all trees.",
        "entropy": "Information gain based split scoring.",
        "log_loss": "Cross-entropy style split scoring.",
    },
    ("svm", "kernel"): {
        "linear": "Best when the decision boundary is close to linear.",
        "rbf": "Flexible non-linear kernel and the safest general-purpose choice.",
        "poly": "Polynomial decision surface controlled by degree.",
        "sigmoid": "Neural-network-like kernel with tanh behavior.",
    },
    ("svm", "gamma"): {
        "scale": "Recommended default based on feature variance.",
        "auto": "Uses only the feature count and ignores variance.",
    },
    ("k_means", "init"): {
        "k-means++": "Smarter centroid seeding that usually converges faster.",
        "random": "Random initial centroids.",
    },
    ("dbscan", "metric"): {
        "euclidean": "Straight-line neighborhood distance.",
        "manhattan": "City-block neighborhood distance.",
        "cosine": "Angular similarity turned into a distance.",
    },
}

ACTIVATION_NOTES = {
    "relu": "Zeroes negative values and is the default hidden-layer activation in this project.",
    "sigmoid": "Squashes outputs into the 0 to 1 range.",
    "tanh": "Squashes outputs into the -1 to 1 range.",
    "softmax": "Turns a vector of logits into a normalized class probability distribution.",
    "elu": "Smooth ReLU-style activation with negative saturation for negative inputs.",
    "leaky_relu": "ReLU variant that keeps a small negative slope so units do not die completely.",
    "prelu": "Parametric ReLU with a learned negative slope.",
}

PARAM_NOTES.update(
    {
        "ann": {
            "epochs": "Maximum full passes through the training split before early stopping can halt training.",
            "batch_size": "Number of rows processed before every optimizer update.",
            "optimizer": "Weight update algorithm used during backpropagation.",
            "loss": "Objective function that determines the output layer shape and how prediction error is measured.",
            "learning_rate": "Base step size passed into the selected optimizer.",
            "validation_split": "Fraction of the training split reserved internally for validation during each epoch.",
            "test_size": "Fraction of rows reserved for the final holdout test set.",
        },
        "cnn": {
            "epochs": "Maximum training epochs before patience-based early stopping can stop the run.",
            "batch_size": "Number of images loaded per optimizer update.",
            "optimizer": "Weight update algorithm used during backpropagation.",
            "loss": "Objective function used to train the classifier head. This must stay compatible with the selected class mode.",
            "learning_rate": "Base step size passed into the selected optimizer.",
            "momentum": "Only used by SGD. Adds inertia so updates keep moving in the previous direction.",
        },
        "resnet": {
            "epochs": "Maximum training epochs before early stopping can stop the run.",
            "batch_size": "Number of images loaded per optimizer update.",
            "optimizer": "Weight update algorithm used during fine-tuning.",
            "loss": "Objective function used for the final classification layer. Keep it aligned with the selected class mode.",
            "learning_rate": "Base step size passed into the selected optimizer.",
        },
        "lstm": {
            "epochs": "Maximum sequence-training epochs before early stopping can stop the run.",
            "batch_size": "Number of sequences processed per optimizer update.",
            "optimizer": "Weight update algorithm used during sequence training.",
            "loss": "Regression loss for linear mode, or the requested classification loss when classification mode is selected.",
            "validation_split": "Fraction of the generated sequence set reserved internally for validation each epoch.",
            "sequence_length": "Sliding window length used when converting the tabular sequence into supervised training samples.",
            "learning_rate": "Base step size passed into the selected optimizer.",
        },
        "yolo": {
            "epochs": "Maximum detector training epochs.",
            "batch_size": "Number of images per optimizer step.",
            "imgsz": "Square image resolution used during training and validation.",
            "optimizer": "Ultralytics optimizer selection. Case matters here because the backend forwards the exact string.",
            "lr0": "Initial learning rate at the start of training.",
            "lrf": "Final learning rate multiplier used by the scheduler relative to lr0.",
            "momentum": "Momentum term used by supported optimizers.",
            "weight_decay": "L2-style regularization applied to model weights.",
            "warmup_epochs": "How many early epochs are spent warming up the optimizer schedule.",
            "augment": "Whether Ultralytics data augmentation is enabled.",
            "mosaic": "Strength of mosaic augmentation between 0 and 1.",
        },
        "stylegan": {
            "epochs": "Maximum adversarial training epochs.",
            "batch_size": "Number of images loaded into each GAN optimization step.",
            "z_dim": "Dimensionality of the random input noise vector.",
            "w_dim": "Dimensionality of the intermediate latent W space produced by the mapping network.",
            "log_resolution": "Log2 of the generated output resolution. For example, 7 means 128x128 images.",
            "learning_rate": "Generator and mapping-network learning rate.",
            "optimizer": "Optimizer family used for generator and discriminator training.",
            "disc_lr": "Learning rate used for the discriminator. If omitted, it falls back to the generator learning rate.",
            "r1_penalty": "Strength of the R1 regularization term applied to real-image gradients.",
        },
    }
)

OPTION_NOTES.update(
    {
        ("ann", "optimizer"): {
            "adam": "Adaptive moment estimation and the default choice for most dense nets.",
            "sgd": "Plain stochastic gradient descent with a fixed learning rate.",
            "rmsprop": "Adaptive learning-rate optimizer often strong on noisy gradients.",
            "adagrad": "Per-parameter adaptive learning rate that favors sparse updates.",
        },
        ("ann", "loss"): {
            "binary_crossentropy": "Binary classification loss with a sigmoid output unit.",
            "categorical_crossentropy": "Multiclass classification loss with one-hot labels and a softmax output.",
            "sparse_categorical_crossentropy": "Multiclass classification loss with integer labels and a softmax output.",
            "mse": "Regression loss that switches the ANN output layer to linear.",
        },
        ("cnn", "optimizer"): {
            "adam": "Adaptive moment estimation and the default CNN optimizer.",
            "sgd": "Stochastic gradient descent; can use momentum.",
            "rmsprop": "Adaptive learning-rate optimizer.",
            "adagrad": "Per-parameter adaptive learning rate.",
            "adadelta": "Adagrad variant with an adaptive moving window.",
        },
        ("cnn", "loss"): {
            "binary_crossentropy": "Binary image classification loss with a single sigmoid output.",
            "categorical_crossentropy": "Multiclass image classification loss with one-hot labels.",
            "sparse_categorical_crossentropy": "Multiclass image classification loss with integer labels.",
        },
        ("resnet", "optimizer"): {
            "adam": "Adaptive optimizer and the current default.",
            "sgd": "Classic fine-tuning optimizer.",
            "rmsprop": "Adaptive optimizer often used for convolutional training.",
            "adagrad": "Per-parameter adaptive learning rate.",
            "adadelta": "Adagrad variant with a decaying accumulator.",
        },
        ("resnet", "loss"): {
            "binary_crossentropy": "Binary classification loss for a single sigmoid output.",
            "categorical_crossentropy": "Multiclass loss for one-hot labels.",
            "sparse_categorical_crossentropy": "Multiclass loss for integer labels.",
        },
        ("lstm", "optimizer"): {
            "adam": "Adaptive optimizer and the current default.",
            "sgd": "Plain stochastic gradient descent.",
            "rmsprop": "Often effective for recurrent networks.",
            "adagrad": "Adaptive learning rate that emphasizes infrequent features.",
            "adadelta": "Adagrad variant with a rolling window.",
        },
        ("lstm", "loss"): {
            "mse": "Mean squared error for regression sequences.",
            "mae": "Mean absolute error for regression sequences.",
            "huber": "Hybrid regression loss that is less sensitive to outliers than MSE.",
            "binary_crossentropy": "Binary classification sequence loss.",
            "categorical_crossentropy": "One-hot multiclass sequence loss.",
            "sparse_categorical_crossentropy": "Integer-label multiclass sequence loss.",
        },
        ("yolo", "optimizer"): {
            "auto": "Lets Ultralytics pick the optimizer automatically.",
            "SGD": "Ultralytics SGD optimizer.",
            "Adam": "Ultralytics Adam optimizer.",
            "AdamW": "Ultralytics AdamW optimizer with decoupled weight decay.",
            "RMSProp": "Ultralytics RMSProp optimizer.",
        },
        ("stylegan", "optimizer"): {
            "adam": "Adam with StyleGAN-style betas for both generator and discriminator.",
            "rmsprop": "RMSProp for both generator and discriminator.",
        },
    }
)

MODEL_BASE = {
    "simple_linear_regression": {"name": "Simple Linear Regression", "url": "simple-linear-regression", "useCases": ["Trend prediction from one main input feature", "Baseline regression for numeric forecasting", "Interpretable slope and intercept analysis"]},
    "multivariable_linear_regression": {"name": "Multivariable Linear Regression", "url": "multivariable-linear-regression", "useCases": ["Tabular regression with multiple input columns", "Interpretable coefficient-based forecasting", "Baseline model for multi-feature numeric targets"]},
    "logistic_regression": {"name": "Logistic Regression", "url": "logistic-regression", "useCases": ["Binary classification on structured data", "Probability scoring and threshold-based decisions", "Interpretable linear classification"]},
    "knn": {"name": "KNN", "url": "knn", "useCases": ["Distance-based classification", "Small to medium tabular classification tasks", "Similarity-driven prediction baselines"]},
    "decision_tree": {"name": "Decision Tree", "url": "decision-tree", "useCases": ["Rule-based classification", "Interpretable tree decisions", "Quick tabular classification baselines"]},
    "random_forest": {"name": "Random Forest", "url": "random-forest", "useCases": ["Robust tabular classification", "Tree ensemble baselines", "Feature-interaction-heavy structured data"]},
    "svm": {"name": "SVM", "url": "svm", "useCases": ["Margin-based classification", "Non-linear decision boundaries", "High-signal low-to-medium-sized tabular datasets"]},
    "naive_bayes": {"name": "Naive Bayes", "url": "naive-bayes", "useCases": ["Fast probabilistic classification", "Simple tabular baselines", "Low-latency classical ML experiments"]},
    "k_means": {"name": "K-Means", "url": "k-means", "useCases": ["Unsupervised clustering", "Customer or behavior segmentation", "Centroid-based pattern discovery"]},
    "dbscan": {"name": "DBSCAN", "url": "dbscan", "useCases": ["Density-based clustering", "Noise and outlier detection", "Irregularly shaped cluster discovery"]},
    "gradient_boosting": {"name": "Gradient Boosting", "url": "gradient-boosting", "useCases": ["Strong tabular classification baseline", "Sequential error-correcting tree ensembles", "Structured datasets with non-linear interactions"]},
    "xgboost": {"name": "XGBoost", "url": "xgboost", "useCases": ["High-performance boosted tree classification", "Competitive tabular ML", "Strong gradient-boosted baseline"]},
    "sentiment_analysis": {"name": "Sentiment Analysis", "url": "sentiment-analysis", "useCases": ["Opinion mining from text", "Review polarity classification", "Labeling text by sentiment categories"]},
    "text_classification": {"name": "Text Classification", "url": "text-classification", "useCases": ["Topic or intent classification", "Document routing", "Bag-of-words text categorization"]},
    "ann": {"name": "ANN", "url": "ann", "useCases": ["Configurable dense neural networks on CSV data", "Tabular classification and regression", "Custom hidden-layer experimentation"]},
    "cnn": {"name": "CNN", "url": "cnn", "useCases": ["Image classification from folder-based datasets", "Custom convolutional architecture experiments", "Learning local spatial features from images"]},
    "resnet": {"name": "ResNet", "url": "resnet", "useCases": ["Transfer learning on image datasets", "Fine-tuning a pretrained ResNet50 backbone", "Image classification with a custom dense head"]},
    "lstm": {"name": "LSTM", "url": "lstm", "useCases": ["Sequence forecasting from CSV data", "Sequence classification and regression", "Sliding-window recurrent experiments"]},
    "yolo": {"name": "YOLOv8", "url": "object-detection", "useCases": ["Object detection on labeled image datasets", "Bounding-box training with Ultralytics", "Real-time detector fine-tuning"]},
    "stylegan": {"name": "StyleGAN", "url": "stylegan", "useCases": ["Image generation from unlabeled image collections", "Latent-space generative experiments", "Adversarial image synthesis"]},
}

MODEL_SUMMARIES = {
    "simple_linear_regression": {
        "brief": "Learns a straight-line relationship to predict one numeric value.",
        "detailed": "Use this when the target rises or falls in a mostly straight trend as the input changes. It is one of the easiest models to explain because the learned slope directly tells you how much the prediction changes when an input changes.",
        "examples": ["Predicting house price from floor area.", "Predicting sales from ad spend."],
    },
    "multivariable_linear_regression": {
        "brief": "Predicts one numeric target from several input columns at the same time.",
        "detailed": "Use this when many features all influence the answer together and you still want a simple, explainable baseline. Each coefficient gives a directional clue about how that feature affects the prediction after preprocessing.",
        "examples": ["Predicting salary from experience, education, and location score.", "Predicting energy use from weather, occupancy, and building size."],
    },
    "logistic_regression": {
        "brief": "Predicts class probabilities, usually for yes or no style decisions.",
        "detailed": "This is a strong beginner classification model because training is usually stable, fast, and easy to interpret. The output can be read as a probability, which is useful when you need both a class and a confidence score.",
        "examples": ["Spam vs not spam.", "Customer churn vs no churn."],
    },
    "knn": {
        "brief": "Predicts by looking at the most similar training examples nearby.",
        "detailed": "KNN works well when similar rows should have similar labels. It does not learn a compact formula first; instead, it compares a new sample to stored training examples, so feature scaling and distance choices matter a lot.",
        "examples": ["Classifying fruit from size and weight.", "Assigning a customer segment from similar behavior."],
    },
    "decision_tree": {
        "brief": "Learns flowchart-like rules such as if this, then go left, otherwise go right.",
        "detailed": "A decision tree is popular for teaching because each prediction can be traced through simple rule splits. Small trees are easy to understand, while deep trees can become too specific and memorize noise from the training data.",
        "examples": ["Loan approval rules.", "Basic risk triage."],
    },
    "random_forest": {
        "brief": "Combines many decision trees and lets them vote on the final answer.",
        "detailed": "Random forests are usually more stable than a single tree because each tree sees a slightly different view of the data. They are a strong default for structured tabular data when you want good performance without heavy tuning.",
        "examples": ["Fraud detection.", "Customer retention prediction."],
    },
    "svm": {
        "brief": "Finds a separating boundary between classes with a strong margin.",
        "detailed": "SVM can work very well on small or medium structured datasets, especially when classes are cleanly separated. The kernel decides whether the boundary stays simple and linear or becomes more flexible and curved.",
        "examples": ["Structured binary classification.", "Non-linear category separation with an RBF kernel."],
    },
    "naive_bayes": {
        "brief": "A fast probability-based classifier that makes strong independence assumptions.",
        "detailed": "Naive Bayes is useful when you want a lightweight baseline that trains quickly and gives sensible results fast. It is often surprisingly competitive on text-like problems even though its assumptions are simple.",
        "examples": ["Quick email labeling baseline.", "Fast topic prediction prototype."],
    },
    "k_means": {
        "brief": "Groups unlabeled data into a chosen number of clusters.",
        "detailed": "Use K-Means when you believe the data naturally falls into a few groups and you can guess a reasonable cluster count. It is best for numeric data and works most cleanly when clusters are fairly compact and rounded.",
        "examples": ["Customer segmentation.", "Grouping products by behavior or price pattern."],
    },
    "dbscan": {
        "brief": "Finds dense groups and marks isolated points as noise.",
        "detailed": "DBSCAN is useful when clusters are irregularly shaped or when outlier detection matters. Unlike K-Means, you do not need to tell it the number of clusters first, but you do need to choose a neighborhood radius carefully.",
        "examples": ["Geographic hotspot discovery.", "Finding isolated sensor anomalies."],
    },
    "gradient_boosting": {
        "brief": "Builds many small trees in sequence so each new tree fixes earlier mistakes.",
        "detailed": "This is a strong classical model for tabular data when simple models miss non-linear interactions. It usually performs well out of the box, but too many trees or overly deep trees can overfit slower and more expensively.",
        "examples": ["Risk scoring.", "Business classification on mixed numeric features."],
    },
    "xgboost": {
        "brief": "A highly optimized boosted-tree model for structured tabular datasets.",
        "detailed": "XGBoost is widely used because it is fast, powerful, and usually competitive on real-world tabular problems. It can outperform simpler tree models, but it also becomes easier to over-tune if you keep increasing capacity without validation checks.",
        "examples": ["Credit scoring.", "Competition-style tabular prediction."],
    },
    "sentiment_analysis": {
        "brief": "Turns text into TF-IDF features and predicts sentiment labels.",
        "detailed": "This is a practical beginner text model because the pipeline is easy to explain: the vectorizer counts important words and phrases, then logistic regression learns which ones push the prediction toward each class. It is a strong baseline before moving to transformers.",
        "examples": ["Movie review polarity.", "Product review sentiment."],
    },
    "text_classification": {
        "brief": "Uses bag-of-words counts and Naive Bayes to predict text categories.",
        "detailed": "This model is simple, fast, and useful for first-pass text experiments. It usually trains in a short time and helps you learn how word counts, vocabulary size, and smoothing affect document classification.",
        "examples": ["Support ticket routing.", "News topic classification."],
    },
    "ann": {
        "brief": "A configurable dense neural network for CSV-based learning.",
        "detailed": "Use ANN when simple linear models are too limited and you want the model to learn richer feature interactions. More layers and neurons increase learning power, but they also raise overfitting risk and make tuning more important.",
        "examples": ["Tabular classification with non-linear feature interactions.", "Tabular regression where simple lines are not enough."],
    },
    "cnn": {
        "brief": "Learns image patterns such as edges, textures, and shapes for image classification.",
        "detailed": "CNN is one of the best beginner models for vision because each layer learns increasingly complex visual features. More filters and deeper stacks can improve pattern learning, but very aggressive pooling or too much complexity can remove useful detail or overfit small datasets.",
        "examples": ["Cats vs dogs classification.", "Plant disease image classification."],
    },
    "resnet": {
        "brief": "Uses a pretrained ResNet50 backbone and adds your own classification head.",
        "detailed": "ResNet is ideal when you want strong image performance without training a large vision model from scratch. Starting from pretrained weights often means better accuracy with less data, especially if you first freeze the backbone and only train the new head.",
        "examples": ["Medical image transfer learning.", "Custom product image categories with limited data."],
    },
    "lstm": {
        "brief": "Learns from ordered sequences where earlier steps can affect later ones.",
        "detailed": "LSTM is useful for time series and sequence problems because it can keep memory of past context. Shorter windows train faster, while longer windows give more history but can add noise, memory cost, and training instability.",
        "examples": ["Forecasting future values from earlier time steps.", "Sequence classification from ordered events."],
    },
    "yolo": {
        "brief": "Detects objects and predicts both their class and their bounding box.",
        "detailed": "Use YOLO when you need to know what is in an image and where it is. Higher image sizes and longer training can improve small-object detection, but they also increase GPU memory use and training time quickly.",
        "examples": ["Helmet detection.", "Vehicle detection in traffic scenes."],
    },
    "stylegan": {
        "brief": "Generates new images that resemble the images in the training set.",
        "detailed": "StyleGAN is a generative model rather than a classifier. It learns a latent space that can create new samples with similar style and structure, but GAN training is much more sensitive to batch size, learning rate balance, and dataset quality than ordinary supervised models.",
        "examples": ["Generating face-like images from a face dataset.", "Learning a visual style from an art collection."],
    },
}

COMPONENT_GUIDES = {
    "sentiment_analysis": [
        {
            "parameter": "Vectorizer",
            "description": "TF-IDF turns text into weighted word and phrase features. Rare but informative terms get more importance than very common words.",
            "sub_parameters": [
                {
                    "parameter": "max_features",
                    "description": "Controls how many terms the vectorizer keeps. Lower values make the model simpler and faster. Higher values keep more vocabulary and can improve detail, but they also add noise and memory cost.",
                }
            ],
        },
        {
            "parameter": "Classifier",
            "description": "Logistic regression learns which words and phrases push the prediction toward each sentiment class.",
            "sub_parameters": [
                {
                    "parameter": "C",
                    "description": "Lower values regularize more strongly and usually make the model simpler. Higher values fit the training text more aggressively and can overfit noisy wording.",
                },
                {
                    "parameter": "max_iter",
                    "description": "Allows more solver steps. If training stops before convergence, increasing this value can help.",
                },
            ],
        },
    ],
    "text_classification": [
        {
            "parameter": "Vectorizer",
            "description": "CountVectorizer converts text into simple token counts. It is easier to explain than embeddings and works well for first-pass text classification.",
            "sub_parameters": [
                {
                    "parameter": "max_features",
                    "description": "Controls vocabulary size. Smaller vocabularies are faster and cleaner; larger vocabularies preserve more detail but can include more noise.",
                }
            ],
        },
        {
            "parameter": "Classifier",
            "description": "Multinomial Naive Bayes estimates how strongly each token suggests each class.",
            "sub_parameters": [
                {
                    "parameter": "alpha",
                    "description": "Smoothing strength. Lower values trust the observed token counts more; higher values smooth more aggressively and can help when many words are rare.",
                }
            ],
        },
    ],
    "ann": [
        {
            "parameter": "Dense layer",
            "description": "Dense layers combine input features to learn non-linear patterns.",
            "sub_parameters": [
                {
                    "parameter": "units",
                    "description": "Controls layer width. Fewer units train faster and act simpler. More units learn richer patterns but use more memory and can overfit if the dataset is small.",
                },
                {
                    "parameter": "activation",
                    "description": "Chooses how the layer transforms its weighted sum. ReLU is the usual beginner start. Sigmoid and tanh compress values, while softmax is mainly for output-style probability behavior rather than hidden layers.",
                },
                {
                    "parameter": "dropout",
                    "description": "Randomly disables part of the layer during training. Small dropout such as 0.1 to 0.3 can reduce overfitting. Too much dropout can make learning slow or weak.",
                },
            ],
        },
        {
            "parameter": "Output layer",
            "description": "The backend creates the output layer automatically from the selected loss and the label structure.",
            "sub_parameters": [
                {
                    "parameter": "binary classification",
                    "description": "Uses a single sigmoid output and binary_crossentropy.",
                },
                {
                    "parameter": "multiclass classification",
                    "description": "Uses a softmax output with categorical or sparse categorical crossentropy.",
                },
                {
                    "parameter": "regression",
                    "description": "Uses a linear output and mse loss for numeric prediction.",
                },
            ],
        },
    ],
    "cnn": [
        {
            "parameter": "Convolution layer",
            "description": "Convolution layers scan the image with learnable filters to detect visual patterns.",
            "sub_parameters": [
                {
                    "parameter": "numberOfNeurons / filters",
                    "description": "More filters let the model learn more pattern types, such as different edges or textures. Lower values train faster. Higher values can improve representation power but increase memory use.",
                },
                {
                    "parameter": "kernel",
                    "description": "The filter window size such as 3x3 or 5x5. Smaller kernels capture fine detail and are the most common choice. Larger kernels see more context but smooth over local detail faster.",
                },
                {
                    "parameter": "activationFunction",
                    "description": "Controls the non-linear response after convolution. ReLU is the standard start. Leaky ReLU and PReLU help keep some signal for negative values.",
                },
            ],
        },
        {
            "parameter": "Pooling layer",
            "description": "Pooling reduces feature-map size so the model becomes more compact and less sensitive to small shifts.",
            "sub_parameters": [
                {
                    "parameter": "poolingType",
                    "description": "maxPool keeps the strongest signal in each region, avgPool keeps the average response, and minPool keeps the smallest value. Max pooling is the most common beginner choice.",
                },
                {
                    "parameter": "poolingSize",
                    "description": "Controls the downsampling window. A 2x2 pool is a common default. Larger windows shrink feature maps faster but can remove too much detail.",
                },
                {
                    "parameter": "stride",
                    "description": "Controls how far the pooling window moves each step. Smaller stride keeps more overlap and more detail. Larger stride reduces size more aggressively and speeds later layers up.",
                },
            ],
        },
        {
            "parameter": "Dense layer",
            "description": "Dense layers near the end turn learned visual features into class decisions.",
            "sub_parameters": [
                {
                    "parameter": "units",
                    "description": "More units give the classifier head more capacity. This can help when classes are complex, but too many units can overfit small image datasets.",
                },
                {
                    "parameter": "activationFunction",
                    "description": "The activation for that dense layer. ReLU is the common start. ELU, Leaky ReLU, and PReLU can help when you want smoother or non-zero negative responses.",
                },
                {
                    "parameter": "dropoutRate",
                    "description": "Adds dropout right after the dense layer. Small values often improve generalization. High values can make the head underfit and learn too slowly.",
                },
            ],
        },
        {
            "parameter": "Standalone dropout layer",
            "description": "Lets you place dropout exactly where you want it in the stack. Use it when the model memorizes training data too easily.",
        },
    ],
    "resnet": [
        {
            "parameter": "Pretrained backbone",
            "description": "ResNet50 already knows many useful image features from ImageNet, such as edges, textures, and object parts.",
            "sub_parameters": [
                {
                    "parameter": "freezeBase",
                    "description": "Keeping the backbone frozen is safer and faster for small datasets. Unfreezing it lets the model adapt more deeply, but it needs more data, more care, and usually a lower learning rate.",
                }
            ],
        },
        {
            "parameter": "Custom dense head",
            "description": "Your dense head learns how to map pretrained image features to your own classes.",
            "sub_parameters": [
                {
                    "parameter": "units",
                    "description": "Controls the size of each added dense layer. More units mean more capacity but also more overfitting risk.",
                },
                {
                    "parameter": "activation",
                    "description": "ReLU is the most common hidden activation here. Simpler choices are usually enough because the pretrained backbone already provides strong features.",
                },
                {
                    "parameter": "dropout",
                    "description": "Reduces overfitting in the custom head by randomly dropping activations during training.",
                },
            ],
        },
        {
            "parameter": "Class mode and loss pairing",
            "description": "Binary mode uses a sigmoid output. Sparse and categorical modes both use a softmax output. The chosen loss must match the label format you provide.",
        },
    ],
    "lstm": [
        {
            "parameter": "Sequence generation",
            "description": "The backend converts the CSV into sliding windows before training.",
            "sub_parameters": [
                {
                    "parameter": "sequence_length",
                    "description": "Shorter windows are faster and easier to train but may miss long-term patterns. Longer windows include more history but increase memory cost and can make training less stable.",
                }
            ],
        },
        {
            "parameter": "LSTM layer",
            "description": "Each LSTM layer learns how earlier steps in the sequence influence later steps.",
            "sub_parameters": [
                {
                    "parameter": "units",
                    "description": "More units let the model store more sequence information. Too many units can overfit or slow training without helping.",
                },
                {
                    "parameter": "return_sequences",
                    "description": "Enable this when another sequence-processing layer follows. Disable it on the last recurrent layer when you want one final summary vector.",
                },
                {
                    "parameter": "dropout",
                    "description": "Drops part of the recurrent representation during training to reduce overfitting.",
                },
            ],
        },
        {
            "parameter": "Dense head",
            "description": "Dense layers after the LSTM stack turn sequence features into final numeric or class outputs.",
            "sub_parameters": [
                {
                    "parameter": "units",
                    "description": "Adds capacity to the final decision layers. More units can help but can also make the head overfit.",
                },
                {
                    "parameter": "activation",
                    "description": "ReLU is a common hidden-layer start. Softmax is mainly for multiclass-style output behavior rather than intermediate hidden layers.",
                },
                {
                    "parameter": "dropout",
                    "description": "Useful when the dense head memorizes the training sequences too easily.",
                },
            ],
        },
    ],
    "yolo": [
        {
            "parameter": "Pretrained detector",
            "description": "This project starts from pretrained yolov8n weights. That gives a small, fast detector and avoids training from scratch.",
        },
        {
            "parameter": "Image size",
            "description": "imgsz changes the training resolution. Lower values are faster and lighter. Higher values help with small objects but increase memory use and training time quickly.",
        },
        {
            "parameter": "Augmentation settings",
            "description": "augment and mosaic control how much synthetic variety is added during training. More augmentation can improve robustness, but too much can make the training distribution less realistic.",
        },
    ],
    "stylegan": [
        {
            "parameter": "Latent spaces",
            "description": "StyleGAN starts from random latent vectors and transforms them into image styles.",
            "sub_parameters": [
                {
                    "parameter": "z_dim",
                    "description": "Size of the random input noise vector. Larger values can represent more variation, but they also add model complexity.",
                },
                {
                    "parameter": "w_dim",
                    "description": "Size of the intermediate style space. Larger values can support richer style control, but they also increase model size and training cost.",
                },
            ],
        },
        {
            "parameter": "Progressive image resolution",
            "description": "log_resolution controls the generated image size as 2 raised to that power. Higher resolution can produce more detail, but it makes GAN training much harder and more expensive.",
        },
        {
            "parameter": "Generator and discriminator balance",
            "description": "GAN training depends on both sides learning at a similar pace. If one side becomes much stronger, image quality can collapse or training can oscillate.",
            "sub_parameters": [
                {
                    "parameter": "learning_rate and disc_lr",
                    "description": "These control how fast the generator and discriminator update. When training becomes unstable, lowering one or both is usually safer than raising them.",
                },
                {
                    "parameter": "r1_penalty",
                    "description": "Regularizes the discriminator on real images. Too little can make training unstable; too much can slow learning and produce weak feedback.",
                },
            ],
        },
    ],
}


def _label(param_name):
    return PARAM_LABELS.get(param_name, param_name.replace("_", " ").title())


def _section(name, description, sub_parameters=None):
    item = {"parameter": name, "description": description}
    if sub_parameters:
        item["sub_parameters"] = sub_parameters
    return item


def _sub(name, description):
    return {"parameter": name, "description": description}


def _format_default(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _format_options(model_code, param_name, options):
    option_notes = OPTION_NOTES.get((model_code, param_name), {})
    parts = []
    for option in options:
        note = option_notes.get(option)
        parts.append(f"{option}: {note}" if note else str(option))
    return "; ".join(parts)


def _param_brief(model_code, param_name):
    note = PARAM_NOTES.get(model_code, {}).get(param_name)
    if note:
        return note
    if param_name in ("epochs", "max_iter"):
        return "Controls how long the model is allowed to keep learning."
    if param_name in ("learning_rate", "lr0", "lrf", "disc_lr"):
        return "Controls how large each training update step is."
    if param_name == "batch_size":
        return "Controls how many samples are processed before one optimizer update."
    if param_name == "optimizer":
        return "Chooses the algorithm used to update model weights during training."
    if param_name == "loss":
        return "Chooses how the model measures error while learning."
    if param_name in ("test_size", "validation_split"):
        return "Controls how much data is reserved for evaluation instead of fitting."
    return f"Controls `{param_name}` for this model."


def _numeric_effect_text(param_name):
    if param_name in ("epochs", "max_iter"):
        return (
            "Lower values train faster but may stop before the model has learned enough.",
            "Higher values give the model more time to learn, but can overfit or waste time once improvement has flattened.",
            "Example: if validation metrics are still improving at the final epoch, raising this value can help. If validation gets worse while training keeps improving, it is likely too high.",
        )
    if param_name in ("learning_rate", "lr0", "disc_lr"):
        return (
            "Lower values are safer and more stable, but learning becomes slower.",
            "Higher values learn faster but can become unstable or even diverge.",
            "Example: 0.001 is a common safe start for many neural models. If loss jumps around heavily, reduce it.",
        )
    if param_name == "lrf":
        return (
            "Lower values decay the learning rate more strongly by the end of training.",
            "Higher values keep later training more aggressive.",
            "Example: if late YOLO training stays noisy, lowering lrf can help it settle.",
        )
    if param_name == "batch_size":
        return (
            "Smaller batches use less memory and sometimes generalize better, but updates are noisier.",
            "Larger batches give smoother updates and often faster epochs, but need more memory.",
            "Example: 8 or 16 is common on limited hardware, while 32 or 64 is useful when memory allows.",
        )
    if param_name in ("test_size", "validation_split"):
        return (
            "Lower values leave more data for training.",
            "Higher values give a more trustworthy evaluation but leave less data for fitting.",
            "Example: 0.2 is a common beginner starting point.",
        )
    if param_name == "max_depth":
        return (
            "Lower depth keeps trees simpler and easier to explain.",
            "Higher depth makes trees more expressive but also more likely to memorize noise.",
            "Example: depth 3 to 6 is often a readable start, while very deep trees can overfit quickly.",
        )
    if param_name == "n_estimators":
        return (
            "Fewer estimators train faster but may underfit.",
            "More estimators usually improve performance up to a point, then mostly add cost.",
            "Example: moving from 50 to 200 often helps more than moving from 500 to 1000.",
        )
    if param_name == "n_neighbors":
        return (
            "Smaller values react strongly to local detail and noise.",
            "Larger values smooth decisions but can blur class boundaries.",
            "Example: K=5 is a common beginner start because K=1 is often noisy.",
        )
    if param_name == "sequence_length":
        return (
            "Shorter windows are cheaper and easier to train but may miss long patterns.",
            "Longer windows give more context but increase compute and instability risk.",
            "Example: for hourly data, a sequence length of 24 gives roughly one day of history.",
        )
    if param_name == "imgsz":
        return (
            "Lower resolutions train faster and use less memory.",
            "Higher resolutions help with small-object detail but cost much more memory and time.",
            "Example: 640 is a common YOLO start. Raise it only if small objects are being missed.",
        )
    if param_name == "n_clusters":
        return (
            "Too few clusters merge different patterns together.",
            "Too many clusters split one real group into artificial subgroups.",
            "Example: if you expect low, medium, and high-value customers, starting at 3 is sensible.",
        )
    if param_name == "momentum":
        return (
            "Lower values make updates react more directly to the latest gradient.",
            "Higher values keep more inertia from previous updates and can speed training in stable directions, but too much can overshoot.",
            "Example: SGD momentum around 0.9 is common when you want faster, smoother progress.",
        )
    if param_name == "weight_decay":
        return (
            "Lower values let weights grow more freely.",
            "Higher values regularize more strongly and can reduce overfitting, but too much can underfit.",
            "Example: a small value like 0.0005 is common in vision models.",
        )
    if param_name == "C":
        return (
            "Lower values regularize more strongly and usually make the model simpler.",
            "Higher values fit the training data more aggressively and can overfit.",
            "Example: if logistic regression or SVM overfits noisy data, try reducing C.",
        )
    if param_name == "alpha":
        return (
            "Lower values apply less smoothing and trust observed counts more closely.",
            "Higher values smooth more aggressively and help when many features are rare.",
            "Example: Naive Bayes often benefits from small but non-zero smoothing such as 0.1 to 1.0.",
        )
    if param_name == "eps":
        return (
            "Lower values require points to be very close before they count as neighbors.",
            "Higher values connect broader neighborhoods and can merge nearby groups together.",
            "Example: if DBSCAN marks almost everything as noise, eps may be too low.",
        )
    if param_name in ("min_samples", "min_samples_split", "min_samples_leaf"):
        return (
            "Lower values make the model react more easily to small local patterns.",
            "Higher values require stronger evidence before forming clusters or tree branches and usually make behavior smoother.",
            "Example: raising these values often reduces overfitting or tiny noisy clusters.",
        )
    if param_name == "max_features":
        return (
            "Lower values keep the representation smaller and faster.",
            "Higher values preserve more vocabulary detail but can add memory use and noise.",
            "Example: text baselines often start at 5000 to 10000 features.",
        )
    if param_name == "var_smoothing":
        return (
            "Lower values keep the model closer to the raw estimated variances.",
            "Higher values add more numerical smoothing and can help stability when features are awkwardly scaled.",
            "Example: if Gaussian Naive Bayes behaves erratically, a slightly larger smoothing value can help.",
        )
    if param_name in ("z_dim", "w_dim"):
        return (
            "Lower values keep the latent representation smaller and simpler.",
            "Higher values allow richer variation but increase model size and training cost.",
            "Example: if StyleGAN is already unstable, increasing latent dimensions is rarely the first fix.",
        )
    if param_name == "log_resolution":
        return (
            "Lower values generate smaller images that are much easier to train.",
            "Higher values generate larger, more detailed images but make GAN training much heavier and less stable.",
            "Example: 7 means 128x128 and is far easier to train than 10, which means 1024x1024.",
        )
    if param_name == "r1_penalty":
        return (
            "Lower values regularize the discriminator less.",
            "Higher values make the discriminator smoother and more constrained, but too much can slow learning.",
            "Example: if GAN training oscillates badly, moderate R1 regularization often helps more than increasing learning rates.",
        )
    return (
        "Lower values usually make the setting weaker, safer, or simpler.",
        "Higher values usually make the setting stronger, larger, or more aggressive.",
        "Start from the default value first, then move one step at a time while checking validation results.",
    )


def _toggle_effect_text(param_name):
    if param_name == "augment":
        return (
            "Off keeps training closer to the raw dataset.",
            "On adds more variation and often improves robustness when labels are clean.",
            "Example: turn this on when the same object can appear at different positions, scales, or orientations.",
        )
    return (
        "Off disables this behavior.",
        "On enables this behavior.",
        "Example: start with the default and switch it only when you know why you want the feature.",
    )


def _selection_text(param_name):
    if param_name == "optimizer":
        return "Adam is usually the easiest beginner start for neural models. SGD is useful when you want explicit momentum-based control. RMSProp and related adaptive optimizers can help on noisy gradients."
    if param_name == "loss":
        return "Pick the loss to match the target type. Use binary_crossentropy for two classes, categorical or sparse categorical crossentropy for multiclass labels, and mse or related regression losses for numeric targets."
    if param_name == "solver":
        return "lbfgs is the safest dense default. liblinear is often good for smaller binary problems. saga is useful when you need a scalable solver for larger or sparse data."
    if param_name == "kernel":
        return "linear is the simplest choice. rbf is the safest flexible default for non-linear boundaries. poly is more specialized and can become harder to tune."
    if param_name == "criterion":
        return "gini is usually the fastest and most common default. entropy and log_loss are information-gain style alternatives that can behave slightly differently on the same data."
    if param_name == "metric":
        return "Euclidean distance is the common start for numeric data. Manhattan can work better when absolute differences matter more. Cosine is useful when direction matters more than magnitude."
    if param_name == "weights":
        return "uniform gives every neighbor equal influence. distance gives more influence to closer neighbors and is useful when nearby samples should matter more."
    if param_name == "init":
        return "k-means++ is the usual default because it chooses better starting centroids. random is mainly for experiments or comparison."
    if param_name == "random_state":
        return "This is a reproducibility control, not a quality knob. Changing it changes the random split or initialization but does not reliably make the model better."
    return "This is a choice parameter rather than a low-versus-high scale. Use the option explanations to decide which behavior matches your dataset."


def _build_param_guide(model_code, param_name):
    rules = VALIDATION_SCHEMAS[model_code][param_name]
    default = DEFAULT_HYPERPARAMS.get(model_code, {}).get(param_name)
    guide = {
        "parameter": param_name,
        "label": _label(param_name),
        "type": rules["type"].__name__,
        "default": default,
        "brief": _param_brief(model_code, param_name),
    }

    if "min" in rules:
        guide["min"] = rules["min"]
    if "max" in rules:
        guide["max"] = rules["max"]
    if rules.get("nullable"):
        guide["nullable"] = True

    if "options" in rules:
        guide["options"] = list(rules["options"])
        guide["options_explained"] = [
            {
                "value": option,
                "effect": OPTION_NOTES.get((model_code, param_name), {}).get(
                    option, f"Valid option for `{param_name}`."
                ),
            }
            for option in rules["options"]
        ]
        guide["selection_advice"] = _selection_text(param_name)
    elif rules["type"] == bool:
        disabled_text, enabled_text, example_text = _toggle_effect_text(param_name)
        guide["false_value_typically_does"] = disabled_text
        guide["true_value_typically_does"] = enabled_text
        guide["example_effect"] = example_text
    elif param_name == "random_state":
        guide["selection_advice"] = _selection_text(param_name)
        guide["example_effect"] = "Example: keep the same seed when you want comparable runs, and change it only when you intentionally want a different split."
    else:
        low_text, high_text, example_text = _numeric_effect_text(param_name)
        guide["lower_values_typically_do"] = low_text
        guide["higher_values_typically_do"] = high_text
        guide["example_effect"] = example_text

    return guide


def _build_param_doc(model_code, param_name):
    guide = _build_param_guide(model_code, param_name)

    details = [guide["brief"], f"Type: {guide['type']}."]
    if guide.get("default") is not None or guide.get("nullable"):
        details.append(f"Default: {_format_default(guide.get('default'))}.")
    if "options" in guide:
        details.append(f"Options: {_format_options(model_code, param_name, guide['options'])}.")
        details.append(guide["selection_advice"])
    else:
        if "min" in guide and "max" in guide:
            details.append(f"Allowed range: {guide['min']} to {guide['max']}.")
        elif "min" in guide:
            details.append(f"Minimum allowed value: {guide['min']}.")
        elif "max" in guide:
            details.append(f"Maximum allowed value: {guide['max']}.")
        if "false_value_typically_does" in guide:
            details.append(f"When false: {guide['false_value_typically_does']}")
            details.append(f"When true: {guide['true_value_typically_does']}")
        elif "selection_advice" in guide:
            details.append(guide["selection_advice"])
        else:
            details.append(f"Lower values usually: {guide['lower_values_typically_do']}")
            details.append(f"Higher values usually: {guide['higher_values_typically_do']}")
    if guide.get("example_effect"):
        details.append(f"Example: {guide['example_effect']}")
    if guide.get("nullable"):
        details.append("Null is allowed.")
    return _sub(guide["label"], " ".join(details))


def _hyperparams_section(model_code, intro=None, extra_params=None):
    sub_parameters = [_build_param_doc(model_code, param_name) for param_name in VALIDATION_SCHEMAS[model_code]]
    for extra in extra_params or []:
        sub_parameters.append(extra)
    return _section("User-controlled hyperparameters", intro or "These are the values exposed to users before training starts. A good beginner approach is to keep most defaults, change one setting at a time, and compare validation results.", sub_parameters=sub_parameters)


def _activation_section(title, activations):
    return _section(title, "These activation functions are available in the relevant layer editors for this model.", sub_parameters=[_sub(name, ACTIVATION_NOTES[name]) for name in activations])


def _metrics_section(metrics):
    return _section("Outputs and metrics", "These are the main artifacts or evaluation values produced after training.", sub_parameters=[_sub(name, description) for name, description in metrics])


def _summary_sections(model_code):
    summary = MODEL_SUMMARIES[model_code]
    return [
        _section("Quick explanation", summary["brief"]),
        _section("Detailed explanation", summary["detailed"]),
        _section(
            "Beginner examples",
            "These examples show the kind of problem this model is meant to solve.",
            sub_parameters=[
                _sub(f"Example {index}", example)
                for index, example in enumerate(summary["examples"], start=1)
            ],
        ),
    ]


def _component_guide_section(model_code):
    components = deepcopy(COMPONENT_GUIDES.get(model_code, []))
    if not components:
        return None
    return _section(
        "Layer and component guide",
        "These are the main building blocks users can configure directly or should understand before training.",
        sub_parameters=components,
    )


def _classical_description(model_code, overview, dataset_description, metrics, extra_sections=None):
    description = [_section("Overview", overview), _section("Dataset and preprocessing", dataset_description), _hyperparams_section(model_code), _metrics_section(metrics)]
    for section in extra_sections or []:
        description.insert(-1, section)
    return description


def _deep_description(model_code, overview, dataset_description, layer_section, metrics, extra_sections=None):
    description = [_section("Overview", overview), _section("Dataset and runtime behavior", dataset_description), layer_section, _hyperparams_section(model_code)]
    description.extend(extra_sections or [])
    description.append(_metrics_section(metrics))
    return description


def _build_description(model_code):
    if model_code == "simple_linear_regression":
        return _classical_description(
            model_code,
            "Fits scikit-learn LinearRegression to predict one numeric target from one or more numeric input columns. The implementation writes both prediction CSV output and train/test plots.",
            "Accepts manual X/y arrays or a CSV. When a CSV is used, every column except the last becomes a feature and the last column becomes the target. No feature scaling is applied in this model.",
            [("Coefficients", "Slope values learned for each input feature."), ("Intercept", "Baseline prediction when every feature is zero."), ("MAE / MSE / R2", "Absolute error, squared error, and coefficient of determination on the holdout split."), ("Prediction CSV", "A CSV file with actual values and model predictions.")],
        )
    if model_code == "multivariable_linear_regression":
        return _classical_description(
            model_code,
            "Fits scikit-learn LinearRegression to a multi-column CSV target prediction problem.",
            "Requires a CSV dataset. Every column except the last is treated as a feature and the last column is treated as the numeric target. Features are standardized before fitting.",
            [("Coefficients", "Weight assigned to each standardized input feature."), ("Intercept", "Baseline prediction after the model coefficients are applied."), ("MAE / MSE / R2", "Standard regression metrics on the holdout split."), ("Actual vs predicted plot", "Scatter plot comparing true target values with predictions.")],
        )
    if model_code == "logistic_regression":
        return _classical_description(
            model_code,
            "Trains scikit-learn LogisticRegression for classification on tabular CSV data.",
            "Accepts manual X/y arrays or a CSV. With a CSV, every column except the last becomes a feature and the last column becomes the label. Features are standardized before fitting. Decision-boundary images are only generated when the dataset has exactly two feature columns.",
            [("Accuracy / precision / recall / F1", "Classification quality on the holdout split."), ("Confusion matrix", "Counts of true vs predicted classes."), ("Boundary plots", "Only available when exactly two features are present.")],
        )
    if model_code == "knn":
        return _classical_description(
            model_code,
            "Trains scikit-learn KNeighborsClassifier for distance-based tabular classification.",
            "Accepts manual X/y arrays or a CSV. With a CSV, every column except the last becomes a feature and the last column becomes the label. Features are standardized before fitting. Decision-boundary images are only generated when the dataset has exactly two features.",
            [("Accuracy / precision / recall / F1", "Classification quality on the holdout split."), ("Confusion matrix", "Counts of true vs predicted classes."), ("Boundary plots", "Only available when exactly two features are present.")],
        )
    if model_code == "decision_tree":
        return _classical_description(
            model_code,
            "Trains scikit-learn DecisionTreeClassifier for rule-based tabular classification.",
            "Accepts manual X/y arrays or a CSV. With a CSV, every column except the last becomes a feature and the last column becomes the label. Features are standardized before fitting. Decision-boundary images are only generated when the dataset has exactly two features.",
            [("Accuracy / precision / recall / F1", "Classification quality on the holdout split."), ("Confusion matrix", "Counts of true vs predicted classes."), ("Boundary plots", "Only available when exactly two features are present.")],
        )
    if model_code == "random_forest":
        return _classical_description(
            model_code,
            "Trains scikit-learn RandomForestClassifier as an ensemble of decision trees.",
            "Accepts manual X/y arrays or a CSV. With a CSV, every column except the last becomes a feature and the last column becomes the label. Features are standardized before fitting. Decision-boundary images are only generated when the dataset has exactly two features.",
            [("Accuracy / precision / recall / F1", "Classification quality on the holdout split."), ("Confusion matrix", "Counts of true vs predicted classes."), ("Boundary plots", "Only available when exactly two features are present.")],
        )
    if model_code == "svm":
        return _classical_description(
            model_code,
            "Trains scikit-learn SVC for margin-based tabular classification.",
            "Accepts manual X/y arrays or a CSV. With a CSV, every column except the last becomes a feature and the last column becomes the label. Features are standardized before fitting. Decision-boundary images are only generated when the dataset has exactly two features.",
            [("Accuracy / precision / recall / F1", "Classification quality on the holdout split."), ("Confusion matrix", "Counts of true vs predicted classes."), ("Boundary plots", "Only available when exactly two features are present.")],
        )
    if model_code == "naive_bayes":
        return _classical_description(
            model_code,
            "Trains scikit-learn GaussianNB for probabilistic tabular classification.",
            "Accepts manual X/y arrays or a CSV. With a CSV, every column except the last becomes a feature and the last column becomes the label. Features are standardized before fitting. Decision-boundary images are only generated when the dataset has exactly two features.",
            [("Accuracy / precision / recall / F1", "Classification quality on the holdout split."), ("Confusion matrix", "Counts of true vs predicted classes."), ("Boundary plots", "Only available when exactly two features are present.")],
        )
    if model_code == "k_means":
        return _classical_description(
            model_code,
            "Runs scikit-learn KMeans on the numeric portion of a dataset.",
            "Accepts a raw X array or a CSV. When a CSV is used, the backend keeps only numeric columns and drops rows with missing values. At least two numeric columns are required. The first two numeric features are used for the saved cluster plot.",
            [("Cluster labels", "Assigned cluster index for each input row."), ("Cluster centers", "Centroid coordinates learned by K-Means."), ("Inertia", "Within-cluster sum of squares for the final fit."), ("Elbow plot", "WCSS curve from k=1 up to the internal elbow-search cap.")],
        )
    if model_code == "dbscan":
        return _classical_description(
            model_code,
            "Runs scikit-learn DBSCAN on the numeric portion of a dataset.",
            "Accepts a raw X array or a CSV. When a CSV is used, the backend keeps only numeric columns and drops rows with missing values. At least two numeric columns are required. The first two numeric features are used for the saved cluster plot.",
            [("Cluster labels", "Assigned cluster index for each row, with -1 reserved for noise."), ("Cluster count", "Number of discovered non-noise clusters."), ("Noise count", "How many rows DBSCAN labeled as noise."), ("Cluster plot", "Visualization built from the first two numeric features.")],
        )
    if model_code == "gradient_boosting":
        return _classical_description(
            model_code,
            "Trains scikit-learn GradientBoostingClassifier for sequential tree boosting on tabular data.",
            "Requires a CSV dataset. Every column except the last becomes a feature and the last column becomes the label. String labels are label-encoded automatically. The estimator uses a fixed random_state of 42 internally.",
            [("Accuracy / precision / recall / F1", "Weighted classification metrics on the holdout split.")],
        )
    if model_code == "xgboost":
        return _classical_description(
            model_code,
            "Trains XGBClassifier for boosted-tree tabular classification.",
            "Requires a CSV dataset. Every column except the last becomes a feature and the last column becomes the label. String labels are label-encoded automatically. The objective is selected automatically: binary:logistic for two classes and multi:softmax for more than two classes.",
            [("Accuracy / precision / recall / F1", "Weighted classification metrics on the holdout split.")],
        )
    if model_code == "sentiment_analysis":
        return _classical_description(
            model_code,
            "Builds a TF-IDF plus logistic-regression pipeline for sentiment-style text classification.",
            "Requires a CSV dataset with at least one text column and one label column. Text is cast to string before vectorization. The backend auto-detects text and label columns when they are not specified explicitly.",
            [("Accuracy / precision / recall / F1", "Weighted classification metrics on the holdout split.")],
            extra_sections=[_section("Text pipeline", "This model is a fixed scikit-learn Pipeline rather than a layer-based neural network.", sub_parameters=[_sub("Vectorizer", "TfidfVectorizer with max_features from the user and a fixed ngram_range of (1, 2)."), _sub("Classifier", "LogisticRegression with user-controlled max_iter and C."), _sub("Column selection", "If text_column and label_column are not provided, the backend auto-detects object columns and falls back to the last column as the label.")])],
        )
    if model_code == "text_classification":
        return _classical_description(
            model_code,
            "Builds a CountVectorizer plus Multinomial Naive Bayes pipeline for document or intent classification.",
            "Requires a CSV dataset with at least one text column and one label column. Text is cast to string before vectorization. The backend auto-detects text and label columns when they are not specified explicitly.",
            [("Accuracy / precision / recall / F1", "Weighted classification metrics on the holdout split.")],
            extra_sections=[_section("Text pipeline", "This model is a fixed scikit-learn Pipeline rather than a layer-based neural network.", sub_parameters=[_sub("Vectorizer", "CountVectorizer with max_features from the user and a fixed ngram_range of (1, 2)."), _sub("Classifier", "MultinomialNB with user-controlled alpha."), _sub("Column selection", "If text_column and label_column are not provided, the backend auto-detects object columns and falls back to the last column as the label.")])],
        )
    if model_code == "ann":
        return _deep_description(
            model_code,
            "Builds a configurable Keras Sequential dense network for CSV-based tabular learning.",
            "Requires a CSV dataset. Every column except the last becomes a feature and the last column becomes the target. The backend creates a train/test split first, then uses validation_split inside the training portion on every epoch.",
            _section("Layer editor and runtime architecture", "Users build the ANN by stacking dense layers in the frontend editor.", sub_parameters=[_sub("Dense layer", "Each configured hidden layer exposes units, activation, and dropout. The backend inserts Dense, then optionally Dropout, in the same order."), _sub("Available dense activations", "relu, sigmoid, tanh, softmax, leaky_relu, elu."), _sub("Output layer behavior", "The backend derives the output layer automatically from the selected loss and the target labels: sigmoid for binary classification, softmax for multiclass classification, and linear for regression when loss is mse."), _sub("Preprocessing", "Features are standardized with StandardScaler. String targets are label-encoded automatically."), _sub("Early stopping", "Training saves the best validation weights and stops after 5 epochs without validation-loss improvement.")]),
            [("Test accuracy and loss", "Metrics computed on the holdout test split after training ends."), ("Validation accuracy and loss", "Best-seen validation statistics from the epoch loop."), ("Epochs trained", "Actual epoch count after early stopping."), ("Saved model", "The trained Keras model is stored for download.")],
            extra_sections=[_activation_section("Activation functions", ["relu", "sigmoid", "tanh", "softmax", "elu", "leaky_relu"])],
        )
    if model_code == "cnn":
        return _deep_description(
            model_code,
            "Builds a configurable Keras Sequential convolutional classifier for folder-based image datasets.",
            "Requires an extracted image dataset with train/ and test/ subdirectories that Keras flow_from_directory can read. Validation comes from the test folder rather than a percentage split.",
            _section("Layer editor and runtime architecture", "Users configure the first convolutional input block plus additional hidden layers in the CNN editor.", sub_parameters=[_sub("Class mode", "Frontend options are categorical, binary, or sparse. The selected loss must stay compatible with the selected class mode."), _sub("Input layer", "The first layer card controls the initial Conv2D input layer by setting filter count, kernel size, and activation. The current frontend sends a fixed input shape of 64x64x3."), _sub("Convolutional layer", "Hidden conv layers expose numberOfNeurons, kernel, and activationFunction. Supported activations are relu, sigmoid, tanh, softmax, elu, leaky_relu, and prelu."), _sub("Pooling layer", "Pooling layers expose poolingType, poolingSize, and an optional stride. Supported pooling types are maxPool, avgPool, and minPool."), _sub("Flatten layer", "Flattens spatial feature maps into a 1D vector before dense layers."), _sub("Dense layer", "Dense layers expose units, activationFunction, and optional dropoutRate. If dropoutRate is set, the backend inserts Dropout immediately after that Dense layer."), _sub("Standalone dropout layer", "Adds Dropout with dropoutRate exactly where the layer appears in the stack."), _sub("Runtime behavior", "The backend also uses fixed ImageDataGenerator settings: rescale=1/255 for both splits, plus shear, zoom, and horizontal_flip augmentation on the training split."), _sub("Early stopping", "Training restores the best validation weights after 3 epochs without validation-loss improvement.")]),
            [("Validation accuracy and loss", "Metrics from the streamed epoch loop using the test directory as validation data."), ("Epochs trained", "Actual epoch count after early stopping."), ("Saved model", "The trained Keras CNN is stored for download.")],
            extra_sections=[_activation_section("Activation functions", ["relu", "sigmoid", "tanh", "softmax", "elu", "leaky_relu", "prelu"])],
        )
    if model_code == "resnet":
        return _deep_description(
            model_code,
            "Builds a ResNet50 transfer-learning classifier with a user-configurable dense head.",
            "Requires an extracted image dataset with train/ and test/ subdirectories that Keras flow_from_directory can read. Validation comes from the test folder rather than a percentage split.",
            _section("Transfer-learning controls", "Users configure a custom dense classification head on top of a pretrained ResNet50 backbone.", sub_parameters=[_sub("Backbone", "The base model is keras.applications.ResNet50 with ImageNet weights, include_top=False, and a fixed frontend input shape of 224x224x3."), _sub("Freeze base model weights", "When enabled, every backbone layer is frozen. When disabled, the full ResNet50 backbone is fine-tuned."), _sub("Class mode", "Frontend options are categorical, sparse, and binary. Categorical and sparse use a softmax output head; binary uses a single sigmoid output."), _sub("Custom dense head", "Each configured layer exposes units, activation, and dropout. The backend adds GlobalAveragePooling2D, then each Dense layer, then optional Dropout."), _sub("Available head activations", "relu, sigmoid, tanh, softmax, elu."), _sub("Early stopping", "Training restores the best validation weights after 3 epochs without validation-loss improvement.")]),
            [("Validation accuracy and loss", "Metrics from the streamed epoch loop using the test directory as validation data."), ("Epochs trained", "Actual epoch count after early stopping."), ("Saved model", "The fine-tuned Keras model is stored for download.")],
            extra_sections=[_activation_section("Activation functions", ["relu", "sigmoid", "tanh", "softmax", "elu"])],
        )
    if model_code == "lstm":
        return _deep_description(
            model_code,
            "Builds a configurable Keras LSTM network for sequence classification or regression from CSV data.",
            "Requires a CSV dataset. The backend uses the generated sequence set directly and reserves validation_split from those sequences during training.",
            _section("Layer editor and runtime architecture", "Users configure an ordered stack of recurrent and dense layers for sequence modeling.", sub_parameters=[_sub("Output mode", "Frontend options are categorical for classification and linear for regression."), _sub("Sequence generation", "The backend converts the CSV into sliding windows of length sequence_length. Every column except the last becomes a feature and the last column becomes the target."), _sub("LSTM layer", "Each LSTM layer exposes units, return_sequences, and dropout. The backend automatically keeps return_sequences true on stacked LSTMs unless the user overrides it."), _sub("Dense head layer", "Dense layers expose units, activation, and dropout and are appended after the recurrent stack."), _sub("Available dense activations", "relu, sigmoid, tanh, softmax."), _sub("Preprocessing", "Features are scaled with MinMaxScaler. Non-numeric features and labels are encoded when necessary."), _sub("Output layer behavior", "Regression mode uses Dense(1, linear). Classification mode auto-selects sigmoid or softmax depending on the number of classes."), _sub("Early stopping", "Training restores the best validation weights after 5 epochs without validation-loss improvement.")]),
            [("Validation loss", "Best streamed validation loss from the epoch loop."), ("Accuracy", "Only reported in classification mode."), ("RMSE", "Approximate RMSE derived from validation loss when regression metrics are available."), ("Epochs trained", "Actual epoch count after early stopping."), ("Saved model", "The trained Keras sequence model is stored for download.")],
            extra_sections=[_activation_section("Activation functions", ["relu", "sigmoid", "tanh", "softmax"])],
        )
    if model_code == "yolo":
        return _deep_description(
            model_code,
            "Runs Ultralytics YOLOv8 object-detection training with user-selected training hyperparameters.",
            "Requires an extracted image dataset in a YOLO-compatible directory layout. The backend resolves the dataset path, fixes or creates data.yaml, and then starts Ultralytics training.",
            _section("Fixed architecture and dataset behavior", "YOLO uses a fixed model family rather than a user-built layer editor in this project.", sub_parameters=[_sub("Model family", "The backend always starts from pretrained yolov8n.pt weights."), _sub("Supported task in this UI", "Object detection only. The current training backend does not switch into segmentation mode."), _sub("Dataset structure", "The backend accepts common YOLO layouts such as images/train plus labels/train, train/images plus train/labels, or train/ and val/ flat directories."), _sub("data.yaml handling", "If data.yaml is missing, the backend auto-detects classes from label files and writes a minimal config file.")]),
            [("mAP50 and mAP50-95", "Detection quality metrics returned when Ultralytics exposes them."), ("Epoch logs", "Box loss, total loss, and mAP50 streamed per epoch."), ("Saved model", "The trained detector is saved for download.")],
        )
    if model_code == "stylegan":
        return _deep_description(
            model_code,
            "Runs a StyleGAN-like adversarial training loop for image generation using PyTorch.",
            "Requires an extracted image dataset. Labels are ignored; the model only needs images. The backend trains on GPU when available and falls back to CPU otherwise.",
            _section("Fixed GAN architecture", "StyleGAN training uses a fixed generator, discriminator, and mapping network implementation rather than a user-built layer editor.", sub_parameters=[_sub("Generator", "Built from a mapping network, style blocks, progressive upsampling blocks, and ToRGB layers."), _sub("Discriminator", "Built from EqualizedConv2d blocks plus a minibatch standard-deviation head."), _sub("Resolution", "The generated image size is 2**log_resolution. For example, 7 means 128x128 and 10 means 1024x1024."), _sub("Dataset loading", "The backend first loads images from any flat directory structure. If none are found, it falls back to torchvision ImageFolder for class-subfolder layouts."), _sub("Regularization", "R1 gradient penalty is applied to real images when r1_penalty is greater than zero.")]),
            [("Generator loss", "Average adversarial generator loss from the last completed epoch."), ("Discriminator loss", "Average adversarial discriminator loss from the last completed epoch."), ("Epochs trained", "Total completed GAN epochs."), ("Saved generator", "The trained generator is stored for download.")],
        )
    raise KeyError(f"Unsupported model code: {model_code}")


def get_model_catalog():
    """Return the canonical model catalog for seeding and API responses."""
    models = []
    for model_code, base in MODEL_BASE.items():
        model = deepcopy(base)
        summary = MODEL_SUMMARIES[model_code]
        component_guide = deepcopy(COMPONENT_GUIDES.get(model_code, []))
        description = _summary_sections(model_code) + _build_description(model_code)
        component_section = _component_guide_section(model_code)
        if component_section:
            description.insert(-1, component_section)
        model["code"] = model_code
        model["metadata_version"] = MODEL_CATALOG_VERSION
        model["brief_description"] = summary["brief"]
        model["detailed_description"] = summary["detailed"]
        model["beginner_examples"] = list(summary["examples"])
        model["hyperparameter_guide"] = [
            _build_param_guide(model_code, param_name)
            for param_name in VALIDATION_SCHEMAS[model_code]
        ]
        if component_guide:
            model["component_guide"] = component_guide
        model["description"] = description
        models.append(model)
    return models
