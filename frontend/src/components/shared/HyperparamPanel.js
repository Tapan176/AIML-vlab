import React, { useState, useEffect } from 'react';
import constants from '../../constants';

/**
 * HyperparamPanel — Fetches schema from /model-schema/<code> and renders inputs.
 * Props:
 *   modelCode: string — e.g. 'simple_linear_regression'
 *   hyperparams: object — current hyperparam values from parent
 *   onChange: (paramName, value) => void
 */
export default function HyperparamPanel({ modelCode, hyperparams, onChange }) {
    const [schema, setSchema] = useState(null);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!modelCode) return;
        setLoading(true);
        fetch(`${constants.API_BASE_URL}/model-schema/${modelCode}`)
            .then(res => res.json())
            .then(data => {
                setSchema(data.schema || null);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [modelCode]);

    if (!schema && !loading) return null;

    const paramEntries = schema ? Object.entries(schema) : [];

    const labelOverrides = {
        'imgsz': 'Image Resolution (imgsz)',
        'cos_lr': 'Cosine Learning Rate',
        'lr': 'Learning Rate',
        'fliplr': 'Horizontal Flip (fliplr)',
        'mosaic': 'Mosaic Augmentation'
    };

    const formatLabel = (name) => {
        if (labelOverrides[name]) return labelOverrides[name];
        
        return name
            .replace(/_/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
    };

    const renderInput = (name, rules) => {
        const currentVal = hyperparams[name] !== undefined ? hyperparams[name] : rules.default;

        // Enum / select
        if (rules.options) {
            return (
                <div className="form-group" key={name}>
                    <label htmlFor={`hp-${name}`}>{formatLabel(name)}</label>
                    <select
                        id={`hp-${name}`}
                        value={currentVal ?? ''}
                        onChange={e => onChange(name, e.target.value)}
                    >
                        {rules.options.map(opt => (
                            <option key={opt} value={opt}>{opt}</option>
                        ))}
                    </select>
                    <div className="param-hint">Options: {rules.options.join(', ')}</div>
                </div>
            );
        }

        // Number (int or float)
        if (rules.type === 'int' || rules.type === 'float') {
            return (
                <div className="form-group" key={name}>
                    <label htmlFor={`hp-${name}`}>{formatLabel(name)}</label>
                    <input
                        type="number"
                        id={`hp-${name}`}
                        value={currentVal ?? ''}
                        min={rules.min}
                        max={rules.max}
                        step={rules.type === 'float' ? 0.01 : 1}
                        onChange={e => {
                            const val = e.target.value === '' ? null :
                                rules.type === 'float' ? parseFloat(e.target.value) : parseInt(e.target.value, 10);
                            onChange(name, val);
                        }}
                        placeholder={`Default: ${rules.default ?? 'None'}`}
                    />
                    <div className="param-hint">
                        {rules.min !== undefined && rules.max !== undefined
                            ? `Range: ${rules.min} – ${rules.max}`
                            : rules.nullable ? 'Optional (nullable)' : ''}
                    </div>
                </div>
            );
        }

        // Fallback: text input
        return (
            <div className="form-group" key={name}>
                <label htmlFor={`hp-${name}`}>{formatLabel(name)}</label>
                <input
                    type="text"
                    id={`hp-${name}`}
                    value={currentVal ?? ''}
                    onChange={e => onChange(name, e.target.value)}
                    placeholder={`Default: ${rules.default ?? ''}`}
                />
            </div>
        );
    };

    return (
        <div className="hyperparam-panel">
            <div className="hyperparam-toggle" onClick={() => setIsOpen(!isOpen)}>
                <h3>⚙️ Hyperparameters</h3>
                <span className={`toggle-icon ${isOpen ? 'open' : ''}`}>▾</span>
            </div>
            {isOpen && (
                <div className="hyperparam-body">
                    {loading ? (
                        <div className="model-loading">
                            <div className="spinner" />
                            Loading schema...
                        </div>
                    ) : (
                        paramEntries.map(([name, rules]) => renderInput(name, rules))
                    )}
                </div>
            )}
        </div>
    );
}
