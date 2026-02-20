import React, { useState } from 'react';
import models from '../models.json';
import './styles.css';

const MODEL_CATEGORIES = {
    'Regression': ['simple_linear_regression', 'multivariable_linear_regression'],
    'Classification': ['logistic_regression', 'knn', 'decision_tree', 'random_forest', 'svm', 'naive_bayes'],
    'Clustering': ['k_means', 'dbscan'],
    'Neural Networks': ['ann', 'cnn'],
    'Ensemble': ['gradient_boosting', 'xgboost'],
    'NLP': ['sentiment_analysis', 'text_classification'],
};

const CATEGORY_ICONS = {
    'Regression': '📈',
    'Classification': '🎯',
    'Clustering': '🔮',
    'Neural Networks': '🧠',
    'Ensemble': '🌲',
    'NLP': '📝',
};

const Sidebar = ({ loadComponent, activeModel }) => {
    const [collapsed, setCollapsed] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedCategories, setExpandedCategories] = useState(
        Object.keys(MODEL_CATEGORIES).reduce((acc, cat) => ({ ...acc, [cat]: true }), {})
    );

    const toggleCategory = (cat) => {
        setExpandedCategories(prev => ({ ...prev, [cat]: !prev[cat] }));
    };

    const filteredModels = models.filter(m =>
        m.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getModelsInCategory = (codes) => {
        return filteredModels.filter(m => codes.includes(m.code));
    };

    return (
        <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-header">
                {!collapsed && <h3>Models</h3>}
                <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)} title={collapsed ? 'Expand' : 'Collapse'}>
                    {collapsed ? '→' : '←'}
                </button>
            </div>

            {!collapsed && (
                <>
                    <div className="sidebar-search">
                        <input
                            type="text"
                            placeholder="Search models..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>

                    <div className="sidebar-categories">
                        {Object.entries(MODEL_CATEGORIES).map(([category, codes]) => {
                            const categoryModels = getModelsInCategory(codes);
                            if (categoryModels.length === 0) return null;

                            return (
                                <div className="category" key={category}>
                                    <button className="category-header" onClick={() => toggleCategory(category)}>
                                        <span>{CATEGORY_ICONS[category]} {category}</span>
                                        <span className={`chevron ${expandedCategories[category] ? 'open' : ''}`}>▸</span>
                                    </button>
                                    {expandedCategories[category] && (
                                        <div className="category-items">
                                            {categoryModels.map((model) => (
                                                <button
                                                    key={model.code}
                                                    className={`model-btn ${activeModel === model.code ? 'active' : ''}`}
                                                    onClick={() => loadComponent(model.code)}
                                                >
                                                    {model.name}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </>
            )}
        </aside>
    );
};

export default Sidebar;
