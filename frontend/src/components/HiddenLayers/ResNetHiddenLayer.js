import React from 'react';

const DEFAULT_DENSE_LAYER = { units: 128, activation: 'relu', dropout: 0.3 };

export default function ResNetHiddenLayer({ layers, onChange, onAddLayer, onRemoveLayer, isFrozen = true, onToggleFrozen }) {
    
    const handleValueChange = (index, key, value) => {
        onChange(index, { ...layers[index], [key]: value });
    };

    return (
        <div className="hidden-layers-section" style={{ marginTop: '20px' }}>
            <div className="hidden-layers-header">
                <h3>🧩 Custom Classification Head ({layers.length})</h3>
            </div>
            
            <div style={{ background: '#f8f9fa', border: '1px solid #dee2e6', borderRadius: '8px', padding: '15px', marginBottom: '20px' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#495057' }}>ResNet50 Backbone (Pre-trained on ImageNet)</h4>
                <div className="form-group" style={{ margin: 0 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', margin: 0 }}>
                        <input 
                            type="checkbox" 
                            checked={isFrozen} 
                            onChange={(e) => onToggleFrozen(e.target.checked)} 
                            style={{ width: 'auto', margin: 0 }}
                        />
                        <strong>Freeze Base Model Weights</strong>
                    </label>
                    <p style={{ margin: '5px 0 0 25px', fontSize: '0.85em', color: '#6c757d' }}>
                        If checked, only the Custom Classification Head (listed below) will be trained. If unchecked, the entire ResNet50 base network will be fine-tuned alongside your custom layers.
                    </p>
                </div>
            </div>

            <div className="hidden-layers-list">
                {layers.map((layer, index) => (
                    <div className="hidden-layer-card" key={index} style={{ borderLeft: '4px solid #ff9500' }}>
                        <div className="layer-card-header">
                            <h4>Dense Layer {index + 1}</h4>
                            <button type="button" className="btn-remove-layer" onClick={() => onRemoveLayer(index)}>✕ Remove</button>
                        </div>
                        
                        <div className="layer-params">
                            <div>
                                <label>Units / Neurons</label>
                                <input type="number" min="1" max="4096" value={layer.units || 128} onChange={(e) => handleValueChange(index, 'units', parseInt(e.target.value))} />
                            </div>

                            <div>
                                <label>Activation</label>
                                <select className="layer-type-select" value={layer.activation || 'relu'} onChange={(e) => handleValueChange(index, 'activation', e.target.value)}>
                                    <option value="relu">ReLU</option>
                                    <option value="sigmoid">Sigmoid</option>
                                    <option value="tanh">Tanh</option>
                                    <option value="softmax">Softmax</option>
                                    <option value="elu">ELU</option>
                                </select>
                            </div>

                            <div>
                                <label>Dropout (Regularization)</label>
                                <input type="number" step="0.05" min="0" max="0.9" value={layer.dropout || 0} onChange={(e) => handleValueChange(index, 'dropout', parseFloat(e.target.value))} />
                            </div>
                        </div>
                    </div>
                ))}
                
                <button type="button" className="btn-add-layer" onClick={() => onAddLayer(DEFAULT_DENSE_LAYER)} style={{ width: '100%', background: '#fff5e6', color: '#cc7700', borderColor: '#ffcc80' }}>
                    ＋ Add Custom Dense Layer
                </button>
            </div>
        </div>
    );
}
