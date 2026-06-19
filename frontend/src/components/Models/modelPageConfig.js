/**
 * Per-model config driving the generic <ModelPage> (Phase 6).
 *
 * Each entry fully describes a classical model's page: its endpoint, title, the
 * metrics to render, and which optional bits it shows (manual inputs, image
 * carousel, predictions download). Adding a classical model = one entry here +
 * one line in Home.js — no new component file.
 *
 * Faithfully mirrors the 14 hand-written components this replaced. Fields:
 *   endpoint                  POST target for useModelTrain
 *   title                     <h1> text
 *   runIdle / runBusy         run-button labels (idle / loading)
 *   heading                   results-card <h2>
 *   metrics[]                 { label, key|get, format, cond? } rendered in order
 *                             format: 'percent' | 'dec2' | 'raw' | undefined(default)
 *                             get(results) overrides key; cond(results) gates render
 *   inputMode                 'none' | 'xy' (manual X/y) | 'text-label' (NLP columns)
 *   textPlaceholder/labelPlaceholder   placeholders for inputMode 'text-label'
 *   showImages                render <ImageCarousel> (default true)
 *   hasPredictionsDownload    show the predictions CSV download (default false)
 *   alwaysShowModelDownload   render the trained-model download unconditionally
 *                             (clustering pages did; classical ones gate on drive id)
 *   cacheKey                  useDatasetCache key (defaults to model code; a few
 *                             legacy pages used a squashed key — preserved so a
 *                             user's remembered dataset selection survives)
 */

const CLASSIFICATION_METRICS = [
  { label: 'Accuracy', key: 'accuracy', format: 'percent' },
  { label: 'Precision', key: 'precision', format: 'percent' },
  { label: 'Recall', key: 'recall', format: 'percent' },
  { label: 'F1 Score', key: 'f1_score', format: 'percent' },
];

const REGRESSION_METRICS = [
  { label: 'MAE', key: 'MAE' },
  { label: 'MSE', key: 'MSE' },
  { label: 'R² Score', key: 'R2' },
];

export const MODEL_PAGE_CONFIG = {
  // ── Regression (manual X/y fallback input + predictions download) ──────────
  simple_linear_regression: {
    endpoint: '/linear-regression',
    title: 'Simple Linear Regression',
    heading: 'Regression Results',
    metrics: REGRESSION_METRICS,
    inputMode: 'xy',
    hasPredictionsDownload: true,
  },
  multivariable_linear_regression: {
    endpoint: '/multivariable-linear-regression',
    title: 'Multivariable Linear Regression',
    heading: 'Regression Results',
    metrics: REGRESSION_METRICS,
    inputMode: 'xy',
    hasPredictionsDownload: true,
  },

  // ── Classification (dataset → metrics, with image carousel) ────────────────
  logistic_regression: {
    endpoint: '/logistic-regression',
    title: 'Logistic Regression',
    heading: 'Classification Results',
    metrics: CLASSIFICATION_METRICS,
  },
  knn: {
    endpoint: '/knn',
    title: 'K-Nearest Neighbors',
    heading: 'Classification Results',
    metrics: CLASSIFICATION_METRICS,
  },
  decision_tree: {
    endpoint: '/decision-tree',
    title: 'Decision Tree',
    heading: 'Classification Results',
    metrics: CLASSIFICATION_METRICS,
  },
  random_forest: {
    endpoint: '/random-forest',
    title: 'Random Forest',
    heading: 'Classification Results',
    metrics: CLASSIFICATION_METRICS,
  },
  svm: {
    endpoint: '/support-vector-machine',
    title: 'Support Vector Machine',
    heading: 'Classification Results',
    metrics: CLASSIFICATION_METRICS,
  },
  naive_bayes: {
    endpoint: '/naive-bayes',
    title: 'Naïve Bayes',
    heading: 'Classification Results',
    metrics: CLASSIFICATION_METRICS,
  },

  // ── Clustering (no carousel-less; raw metrics; unconditional model download) ─
  k_means: {
    endpoint: '/k-means',
    title: 'K-Means Clustering',
    heading: 'Clustering Results',
    metrics: [
      { label: 'Clusters', key: 'n_clusters', format: 'raw', cond: (r) => r.n_clusters != null },
      { label: 'Inertia', key: 'inertia', format: 'dec2' },
    ],
    alwaysShowModelDownload: true,
  },
  dbscan: {
    endpoint: '/dbscan',
    title: 'DBSCAN',
    heading: 'Clustering Results',
    metrics: [
      { label: 'Clusters', key: 'n_clusters', format: 'raw', cond: (r) => r.n_clusters != null },
      {
        label: 'Noise Points',
        get: (r) => r.n_noise ?? r.n_noise_points,
        format: 'raw',
        cond: (r) => r.n_noise != null || r.n_noise_points != null,
      },
    ],
    alwaysShowModelDownload: true,
  },

  // ── Boosting (classification; "Train Model" label; no carousel) ────────────
  gradient_boosting: {
    endpoint: '/gradient-boosting',
    title: 'Gradient Boosting Classifier',
    runIdle: '▶ Train Model',
    heading: 'Results',
    metrics: CLASSIFICATION_METRICS,
    showImages: false,
    cacheKey: 'gradientboosting',
  },
  xgboost: {
    endpoint: '/xgboost',
    title: 'XGBoost Classifier',
    runIdle: '▶ Train Model',
    heading: 'Results',
    metrics: CLASSIFICATION_METRICS,
    showImages: false,
  },

  // ── NLP (text/label column inputs; no carousel) ────────────────────────────
  sentiment_analysis: {
    endpoint: '/sentiment-analysis',
    title: 'Sentiment Analysis',
    runIdle: '▶ Analyze Sentiment',
    runBusy: '⏳ Analyzing...',
    heading: 'Results',
    metrics: CLASSIFICATION_METRICS,
    inputMode: 'text-label',
    textPlaceholder: 'e.g. review',
    labelPlaceholder: 'e.g. sentiment',
    showImages: false,
    cacheKey: 'sentimentanalysis',
  },
  text_classification: {
    endpoint: '/text-classification',
    title: 'Text Classification',
    runIdle: '▶ Classify Text',
    runBusy: '⏳ Classifying...',
    heading: 'Results',
    metrics: CLASSIFICATION_METRICS,
    inputMode: 'text-label',
    textPlaceholder: 'e.g. text',
    labelPlaceholder: 'e.g. category',
    showImages: false,
    cacheKey: 'textclassification',
  },
};

export default MODEL_PAGE_CONFIG;
