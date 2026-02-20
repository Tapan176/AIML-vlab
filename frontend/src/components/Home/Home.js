import React, { useState, lazy, Suspense } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import './Home.css';

// Lazy load model components
const SimpleLinearRegression = lazy(() => import('../Models/SimpleLinearRegression'));
const KNN = lazy(() => import('../Models/KNN'));
const DecisionTree = lazy(() => import('../Models/DecisionTree'));
const RandomForest = lazy(() => import('../Models/RandomForest'));
const SVM = lazy(() => import('../Models/SVM'));
const LogisticRegression = lazy(() => import('../Models/LogisticRegression'));
const NaiveBayes = lazy(() => import('../Models/NaiveBayes'));
const KMeans = lazy(() => import('../Models/KMeans'));
const DBSCAN = lazy(() => import('../Models/DBSCAN'));
const ANN = lazy(() => import('../Models/ANN'));
const CNN = lazy(() => import('../Models/CNN'));
const MultivariableLinearRegression = lazy(() => import('../Models/MultivariableLinearRegression'));
const GradientBoosting = lazy(() => import('../Models/GradientBoosting'));
const XGBoost = lazy(() => import('../Models/XGBoost'));
const SentimentAnalysis = lazy(() => import('../Models/SentimentAnalysis'));
const TextClassification = lazy(() => import('../Models/TextClassification'));

const MODEL_COMPONENTS = {
    simple_linear_regression: SimpleLinearRegression,
    multivariable_linear_regression: MultivariableLinearRegression,
    logistic_regression: LogisticRegression,
    knn: KNN,
    decision_tree: DecisionTree,
    random_forest: RandomForest,
    svm: SVM,
    naive_bayes: NaiveBayes,
    k_means: KMeans,
    dbscan: DBSCAN,
    ann: ANN,
    cnn: CNN,
    gradient_boosting: GradientBoosting,
    xgboost: XGBoost,
    sentiment_analysis: SentimentAnalysis,
    text_classification: TextClassification,
};

const Home = () => {
    const [activeModel, setActiveModel] = useState(null);

    const loadComponent = (modelCode) => {
        setActiveModel(modelCode);
    };

    const ActiveComponent = activeModel ? MODEL_COMPONENTS[activeModel] : null;

    return (
        <div className="home-layout">
            <Sidebar loadComponent={loadComponent} activeModel={activeModel} />
            <main className="main-content">
                {ActiveComponent ? (
                    <Suspense fallback={
                        <div className="model-loading">
                            <div className="spinner"></div>
                            <p>Loading model...</p>
                        </div>
                    }>
                        <ActiveComponent />
                    </Suspense>
                ) : (
                    <div className="welcome-panel">
                        <div className="welcome-icon">🧪</div>
                        <h2>Welcome to the AI/ML Lab</h2>
                        <p>Select a model from the sidebar to start training and experimenting.</p>
                        <div className="welcome-cards">
                            <div className="welcome-card">
                                <span>📊</span>
                                <h4>Upload Data</h4>
                                <p>CSV files supported</p>
                            </div>
                            <div className="welcome-card">
                                <span>⚙️</span>
                                <h4>Configure</h4>
                                <p>Tune hyperparameters</p>
                            </div>
                            <div className="welcome-card">
                                <span>🚀</span>
                                <h4>Train</h4>
                                <p>View results instantly</p>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default Home;
