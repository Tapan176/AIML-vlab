import { useState, useEffect } from 'react';
import { useModelRegistry } from '../../hooks/useModelRegistry';
import './styles.css';

const Sidebar = ({ loadComponent, activeModel }) => {
    const [collapsed, setCollapsed] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [collapsedCategories, setCollapsedCategories] = useState({});
    const registry = useModelRegistry();

    // Auto-select a model when redirected from a Dashboard replay, once the
    // registry confirms the code exists.
    useEffect(() => {
        if (!registry) return;
        const autoSelect = sessionStorage.getItem('auto_select_model');
        if (autoSelect && registry.models[autoSelect]) {
            loadComponent(autoSelect);
            sessionStorage.removeItem('auto_select_model');
        }
    }, [registry, loadComponent]);

    const toggleCategory = (cat) => {
        setCollapsedCategories(prev => ({ ...prev, [cat]: !prev[cat] }));
    };

    const term = searchTerm.toLowerCase();
    // categories preserve the backend's display order (Regression → … → Fine-Tuning)
    const categories = registry ? Object.values(registry.categories) : [];

    const modelsForCategory = (cat) =>
        cat.models
            .map(code => registry.models[code])
            .filter(Boolean)
            .filter(m => m.name.toLowerCase().includes(term));

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
                        {categories.map((cat) => {
                            const categoryModels = modelsForCategory(cat);
                            if (categoryModels.length === 0) return null;
                            const isOpen = !collapsedCategories[cat.name];

                            return (
                                <div className="category" key={cat.name}>
                                    <button className="category-header" onClick={() => toggleCategory(cat.name)}>
                                        <span>{cat.icon} {cat.name}</span>
                                        <span className={`chevron ${isOpen ? 'open' : ''}`}>▸</span>
                                    </button>
                                    {isOpen && (
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
