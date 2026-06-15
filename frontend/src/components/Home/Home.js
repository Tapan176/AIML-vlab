import { useState, lazy, Suspense } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import './Home.css';

// Dynamic imports for all model components
// Add new models here — they automatically appear everywhere
const MODEL_COMPONENTS = {
    simple_linear_regression: lazy(() => import('../Models/SimpleLinearRegression')),
    multivariable_linear_regression: lazy(() => import('../Models/MultivariableLinearRegression')),
    logistic_regression: lazy(() => import('../Models/LogisticRegression')),
    knn: lazy(() => import('../Models/KNN')),
    decision_tree: lazy(() => import('../Models/DecisionTree')),
    random_forest: lazy(() => import('../Models/RandomForest')),
    svm: lazy(() => import('../Models/SVM')),
    naive_bayes: lazy(() => import('../Models/NaiveBayes')),
    k_means: lazy(() => import('../Models/KMeans')),
    dbscan: lazy(() => import('../Models/DBSCAN')),
    ann: lazy(() => import('../Models/ANN')),
    cnn: lazy(() => import('../Models/CNN')),
    gradient_boosting: lazy(() => import('../Models/GradientBoosting')),
    xgboost: lazy(() => import('../Models/XGBoost')),
    sentiment_analysis: lazy(() => import('../Models/SentimentAnalysis')),
    text_classification: lazy(() => import('../Models/TextClassification')),
    resnet: lazy(() => import('../Models/ResNet')),
    lstm: lazy(() => import('../Models/LSTM')),
    yolo: lazy(() => import('../Models/ObjectDetection')),
    stylegan: lazy(() => import('../Models/StyleGAN')),
    // 🆕 Fine-Tuning models
    bert_finetune: lazy(() => import('../Models/FinetuneBERT')),
    vit_finetune: lazy(() => import('../Models/FinetuneViT')),
    distilbert_finetune: lazy(() => import('../Models/FinetuneDistilBERT')),
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
                        <div className="welcome-icon">🧠</div>
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
