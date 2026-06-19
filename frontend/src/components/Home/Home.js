import { useState, lazy, Suspense } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import './Home.css';

// Classical models share one config-driven page (Phase 6); behaviour per model
// lives in Models/modelPageConfig.js. `page(code)` is a stable wrapper that
// renders the lazily-loaded <ModelPage> for that code. Deep-learning / streaming
// / generative models keep their own bespoke components.
const ModelPage = lazy(() => import('../Models/ModelPage'));
const page = (modelCode) => () => <ModelPage modelCode={modelCode} />;

// Add a classical model: one entry here + one entry in modelPageConfig.js.
// Add a bespoke model: a lazy() import of its own component (as below).
const MODEL_COMPONENTS = {
    simple_linear_regression: page('simple_linear_regression'),
    multivariable_linear_regression: page('multivariable_linear_regression'),
    logistic_regression: page('logistic_regression'),
    knn: page('knn'),
    decision_tree: page('decision_tree'),
    random_forest: page('random_forest'),
    svm: page('svm'),
    naive_bayes: page('naive_bayes'),
    k_means: page('k_means'),
    dbscan: page('dbscan'),
    gradient_boosting: page('gradient_boosting'),
    xgboost: page('xgboost'),
    sentiment_analysis: page('sentiment_analysis'),
    text_classification: page('text_classification'),
    // Bespoke (SSE streaming, layer builders, generative) — own components
    ann: lazy(() => import('../Models/ANN')),
    cnn: lazy(() => import('../Models/CNN')),
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
