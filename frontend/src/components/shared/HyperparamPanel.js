import { useState, useEffect } from 'react';
import constants from '../../constants';

// Module-level cache: model schemas don't change at runtime, so one fetch per
// modelCode is enough for the lifetime of the SPA. Keyed by modelCode →
// either the resolved schema object or a pending Promise (so concurrent mounts
// during dev hot-reload don't trigger duplicate fetches).
const _schemaCache = new Map();

function fetchSchema(modelCode) {
    if (_schemaCache.has(modelCode)) return _schemaCache.get(modelCode);
    const promise = fetch(`${constants.API_BASE_URL}/model-schema/${modelCode}`)
        .then(res => res.json())
        .then(data => {
            const schema = data.schema || null;
            _schemaCache.set(modelCode, schema);
            return schema;
        })
        .catch(err => {
            _schemaCache.delete(modelCode);  // allow retry on next mount
            throw err;
        });
    _schemaCache.set(modelCode, promise);
    return promise;
}

/**
 * HyperparamPanel — Fetches schema from /model-schema/<code> and renders inputs.
 * Props:
 *   modelCode: string — e.g. 'simple_linear_regression'
 *   hyperparams: object — current hyperparam values from parent
 *   onChange: (paramName, value) => void
 *   schemaOverrides?: object — optional per-param schema overrides
 */
export default function HyperparamPanel({ modelCode, hyperparams, onChange, schemaOverrides = {} }) {
    const [schema, setSchema] = useState(null);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!modelCode) return;
        const cached = _schemaCache.get(modelCode);
        // Cached, non-Promise value — use immediately, skip the network round trip.
        if (cached && typeof cached.then !== 'function') {
            setSchema(cached);
            return;
        }
        setLoading(true);
        Promise.resolve(fetchSchema(modelCode))
            .then(resolved => {
                setSchema(resolved);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [modelCode]);

    if (!schema && !loading) return null;

    const mergedSchema = schema
        ? Object.fromEntries(
            Object.entries(schema).map(([name, rules]) => [
                name,
                { ...rules, ...(schemaOverrides[name] || {}) }
            ])
        )
        : null;

    const paramEntries = mergedSchema ? Object.entries(mergedSchema) : [];

    const labelOverrides = {
        'imgsz': 'Image Resolution (imgsz)',
        'cos_lr': 'Cosine Learning Rate',
        'lr': 'Learning Rate',
        'lr0': 'Initial Learning Rate (lr0)',
        'lrf': 'Final LR Multiplier (lrf)',
        'fliplr': 'Horizontal Flip (fliplr)',
        'mosaic': 'Mosaic Augmentation',
        'r1_penalty': 'R1 Penalty'
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

        if (rules.type === 'bool') {
            return (
                <div className="form-group" key={name}>
                    <label htmlFor={`hp-${name}`}>{formatLabel(name)}</label>
                    <select
                        id={`hp-${name}`}
                        value={String(currentVal ?? rules.default ?? false)}
                        onChange={e => onChange(name, e.target.value === 'true')}
                    >
                        <option value="true">true</option>
                        <option value="false">false</option>
                    </select>
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
                        step={rules.type === 'float' ? 'any' : 1}
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
