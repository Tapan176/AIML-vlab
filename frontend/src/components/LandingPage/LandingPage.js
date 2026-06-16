import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useState, useEffect } from 'react';
import { MODEL_CATEGORIES } from '../../constants';
import { fetchModelRegistry } from '../../hooks/useModelRegistry';
import './LandingPage.css';

const FEATURES = [
    {
        icon: '🧠',
        title: 'Train ML Models',
        desc: 'Experiment with 20 different ML models from regression to deep learning — all in your browser.'
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

const CATEGORY_COLORS = {
    'Regression': '#6c63ff',
    'Classification': '#34c759',
    'Clustering': '#ff9500',
    'Neural Networks': '#ff3b30',
    'Ensemble': '#c5fc00ff',
    'NLP': '#00a8f7ff',
    'Generative AI': '#7000f0ff',
    'Fine-Tuning': '#ff6b6b',
};

const STEPS = [
    { step: '01', title: 'Upload Dataset', desc: 'Upload your CSV or image dataset to get started.' },
    { step: '02', title: 'Configure & Train', desc: 'Select a model, tune hyperparameters, and hit train.' },
    { step: '03', title: 'Analyze & Export', desc: 'View results, compare versions, and download your model.' },
];

// Fallback shown until GET /api/models/registry resolves. Derived from the
// canonical MODEL_CATEGORIES so adding a model never requires touching this file.
const _prettify = (code) => code.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
const FALLBACK_MODELS = Object.entries(MODEL_CATEGORIES).flatMap(
    ([category, codes]) => codes.map((code) => ({ name: _prettify(code), category }))
);

const LandingPage = () => {
    const { isAuthenticated } = useAuth();
    const [models, setModels] = useState(FALLBACK_MODELS);
    const [modelCount, setModelCount] = useState(20);

    useEffect(() => {
        let active = true;
        // Use the shared, module-cached registry fetch so this reuses the same
        // request/cache as the rest of the app (no duplicate network call).
        fetchModelRegistry()
            .then(data => {
                if (!active || !data.models) return;
                const modelList = Object.values(data.models).map(m => ({
                    name: m.name,
                    category: m.category,
                    color: CATEGORY_COLORS[m.category] || '#6c63ff',
                }));
                if (modelList.length > 0) {
                    setModels(modelList);
                    setModelCount(modelList.length);
                }
            })
            .catch(() => {});
        return () => { active = false; };
    }, []);

    return (
        <div className="landing">
            {/* Hero Section */}
            <section className="hero">
                <div className="hero-bg-grid"></div>
                <div className="hero-content">
                    <span className="hero-badge">🧠 ML Lab</span>
                    <h1>
                        Train. Tune. <span className="gradient-text">Understand.</span>
                    </h1>
                    <p className="hero-desc">
                        An interactive platform to learn and experiment with machine learning algorithms.
                        Train 20 different models, tune hyperparameters, and visualize results — all in your browser.
                    </p>
                    <div className="hero-actions">
                        <Link to="/lab" className="btn-primary">Open Lab →</Link>
                        {!isAuthenticated && (
                            <Link to="/signup" className="btn-secondary">Create Account</Link>
                        )}
                    </div>
                    <div className="hero-stats">
                        <div className="stat"><span className="stat-value">{modelCount}+</span><span className="stat-label">ML Models</span></div>
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
                <div className="models-grid">
                    {models.map((m, i) => (
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
