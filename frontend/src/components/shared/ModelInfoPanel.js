import React, { useState, useEffect } from 'react';
import models from '../models.json';
import '../ModelCss/ModelPage.css';

/**
 * Slide-out drawer that shows model description & parameters.
 * Triggered by a toggle button in the model header.
 */
export default function ModelInfoPanel({ modelCode, isOpen, onClose }) {
    const [modelData, setModelData] = useState(null);

    useEffect(() => {
        const found = models.find(m => m.code === modelCode);
        setModelData(found || null);
    }, [modelCode]);

    if (!modelData) return null;

    return (
        <>
            {/* Overlay backdrop */}
            <div
                className={`model-info-drawer-overlay ${isOpen ? 'open' : ''}`}
                onClick={onClose}
            />
            {/* Drawer panel */}
            <div className={`model-info-drawer ${isOpen ? 'open' : ''}`}>
                <div className="drawer-header">
                    <h3>📖 {modelData.name}</h3>
                    <button className="btn-close-drawer" onClick={onClose}>✕</button>
                </div>
                <div className="drawer-body">
                    {modelData.description?.map((item, idx) => (
                        <div className="info-item" key={idx}>
                            <h4>{item.parameter}</h4>
                            <p>{item.description}</p>
                            {item.sub_parameters && (
                                <div className="info-sub-params">
                                    {item.sub_parameters.map((sub, sIdx) => (
                                        <div key={sIdx}>
                                            <h5>{sub.parameter}</h5>
                                            <p>{sub.description}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
}
