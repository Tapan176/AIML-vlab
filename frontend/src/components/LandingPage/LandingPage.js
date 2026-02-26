import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './LandingPage.css';

const FEATURES = [
    {
        icon: '🧠',
        title: 'Train ML Models',
        desc: 'Experiment with 19 different ML models from regression to deep learning — all in your browser.'
    },
    {
        icon: '⚙️',
        title: 'Tune Hyperparameters',
        desc: 'Fine-tune every parameter with real-time validation and see how it impacts performance.'
    },
    {
        icon: '📊',
        title: 'Visualize Results',
        desc: 'Automatic plots, confusion matrices, and evaluation metrics for every training run.'
    },
    {
        icon: '💾',
        title: 'Persist Everything',
        desc: 'Your datasets, models, and sessions are saved — pick up right where you left off.'
    },
    {
        icon: '📈',
        title: 'Version Control',
        desc: 'Every training run is versioned. Compare results across different configurations.'
    },
    {
        icon: '⬇️',
        title: 'Download Models',
        desc: 'Export your trained models as .pkl or .h5 files for production deployment.'
    }
];

const MODELS = [
    { name: 'Linear Regression', category: 'Regression', color: '#6c63ff' },
    { name: 'Multivariable LR', category: 'Regression', color: '#6c63ff' },
    { name: 'Logistic Regression', category: 'Classification', color: '#34c759' },
    { name: 'KNN', category: 'Classification', color: '#34c759' },
    { name: 'Decision Tree', category: 'Classification', color: '#34c759' },
    { name: 'Random Forest', category: 'Classification', color: '#34c759' },
    { name: 'SVM', category: 'Classification', color: '#34c759' },
    { name: 'Naive Bayes', category: 'Classification', color: '#34c759' },
    { name: 'K-Means', category: 'Clustering', color: '#ff9500' },
    { name: 'DBSCAN', category: 'Clustering', color: '#ff9500' },
    { name: 'ANN', category: 'Neural Networks', color: '#ff3b30' },
    { name: 'CNN', category: 'Neural Networks', color: '#ff3b30' },
    { name: 'ResNet50', category: 'Deep Learning', color: '#ff3b30' },
    { name: 'LSTM', category: 'Deep Learning', color: '#ff3b30' },
    { name: 'YOLOv8', category: 'Deep Learning', color: '#ff3b30' },
];

const STEPS = [
    { step: '01', title: 'Upload Dataset', desc: 'Upload your CSV or image dataset to get started.' },
    { step: '02', title: 'Configure & Train', desc: 'Select a model, tune hyperparameters, and hit train.' },
    { step: '03', title: 'Analyze & Export', desc: 'View results, compare versions, and download your model.' },
];

const LandingPage = () => {
    const { isAuthenticated } = useAuth();

    return (
        <div className="landing">
            {/* Hero Section */}
            <section className="hero">
                <div className="hero-bg-grid"></div>
                <div className="hero-content">
                    <span className="hero-badge">🧠 AIML Lab</span>
                    <h1>
                        Train. Tune. <span className="gradient-text">Understand.</span>
                    </h1>
                    <p className="hero-desc">
                        An interactive platform to learn and experiment with machine learning algorithms.
                        Train 19 different models, tune hyperparameters, and visualize results — all in your browser.
                    </p>
                    <div className="hero-actions">
                        <Link to="/lab" className="btn-primary">Open Lab →</Link>
                        {!isAuthenticated && (
                            <Link to="/signup" className="btn-secondary">Create Account</Link>
                        )}
                    </div>
                    <div className="hero-stats">
                        <div className="stat"><span className="stat-value">19</span><span className="stat-label">ML Models</span></div>
                        <div className="stat"><span className="stat-value">100%</span><span className="stat-label">Browser-Based</span></div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="features-section">
                <h2 className="section-title">Everything You Need</h2>
                <p className="section-subtitle">A complete ML experimentation platform</p>
                <div className="features-grid">
                    {FEATURES.map((f, i) => (
                        <div className="feature-card" key={i}>
                            <span className="feature-icon">{f.icon}</span>
                            <h3>{f.title}</h3>
                            <p>{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Models Showcase */}
            <section className="models-section">
                <h2 className="section-title">Supported Models</h2>
                <p className="section-subtitle">From regression to deep learning</p>
                <div className="models-grid">
                    {MODELS.map((m, i) => (
                        <div className="model-chip" key={i} style={{ '--chip-color': m.color }}>
                            <span className="model-category">{m.category}</span>
                            <span className="model-name">{m.name}</span>
                        </div>
                    ))}
                </div>
            </section>

            {/* How It Works */}
            <section className="steps-section">
                <h2 className="section-title">How It Works</h2>
                <div className="steps-grid">
                    {STEPS.map((s, i) => (
                        <div className="step-card" key={i}>
                            <span className="step-number">{s.step}</span>
                            <h3>{s.title}</h3>
                            <p>{s.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section className="cta-section">
                <h2>Ready to Start Experimenting?</h2>
                <p>Jump into the lab and train your first model in under 2 minutes.</p>
                <Link to="/lab" className="btn-primary btn-lg">Launch the Lab →</Link>
            </section>
        </div>
    );
};

export default LandingPage;
