import React from 'react';

const DEFAULT_LSTM_LAYER = { units: 64, return_sequences: true, dropout: 0.2 };
const DEFAULT_DENSE_LAYER = { units: 32, activation: 'relu', dropout: 0 };

export default function LstmHiddenLayer({ layers, onChange, onAddLayer, onRemoveLayer }) {
    
    const handleValueChange = (index, key, value) => {
        onChange(index, { ...layers[index], [key]: value });
    };

    const handleTypeChange = (index, newType) => {
        if (newType === 'lstm') {
            onChange(index, { type: 'lstm', ...DEFAULT_LSTM_LAYER });
        } else {
            onChange(index, { type: 'dense', ...DEFAULT_DENSE_LAYER });
        }
    };

    return (
        <div className="hidden-layers-section" style={{ marginTop: '20px' }}>
            <div className="hidden-layers-header">
                <h3>🔄 Recurrent & Dense Layers ({layers.length})</h3>
            </div>
            
            <p style={{ color: '#666', fontSize: '0.9em', marginBottom: '15px' }}>
                Note: Standard practice is to stack LSTM layers with <strong>Return Sequences = True</strong>, 
                except for the final LSTM layer before transitioning to Dense layers.
            </p>

            <div className="hidden-layers-list">
                {layers.map((layer, index) => (
                    <div className="hidden-layer-card" key={index} style={{ borderLeft: layer.type === 'lstm' ? '4px solid #34c759' : '4px solid #6c63ff' }}>
                        <div className="layer-card-header">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <h4>Layer {index + 1}</h4>
                                <select 
                                    className="layer-type-select"
                                    value={layer.type || 'lstm'} 
                                    onChange={(e) => handleTypeChange(index, e.target.value)}
                                    style={{ marginLeft: '10px' }}
                                >
                                    <option value="lstm">LSTM Cell</option>
                                    <option value="dense">Dense Head</option>
                                </select>
                            </div>
                            <button type="button" className="btn-remove-layer" onClick={() => onRemoveLayer(index)}>✕</button>
                        </div>
                        
                        <div className="layer-params">
                            <div>
                                <label>Units / Neurons</label>
                                <input type="number" min="1" max="1024" value={layer.units || 64} onChange={(e) => handleValueChange(index, 'units', parseInt(e.target.value))} />
                            </div>

                            {layer.type === 'lstm' ? (
                                <div>
                                    <label>Return Sequences</label>
                                    <select value={layer.return_sequences ? 'true' : 'false'} onChange={(e) => handleValueChange(index, 'return_sequences', e.target.value === 'true')}>
                                        <option value="true">True (Output 3D Tensor)</option>
                                        <option value="false">False (Output 2D Tensor)</option>
                                    </select>
                                </div>
                            ) : (
                                <div>
                                    <label>Activation</label>
                                    <select value={layer.activation || 'relu'} onChange={(e) => handleValueChange(index, 'activation', e.target.value)}>
                                        <option value="relu">ReLU</option>
                                        <option value="sigmoid">Sigmoid</option>
                                        <option value="tanh">Tanh</option>
                                        <option value="softmax">Softmax</option>
                                    </select>
                                </div>
                            )}

                            <div>
                                <label>Dropout</label>
                                <input type="number" step="0.05" min="0" max="0.9" value={layer.dropout || 0} onChange={(e) => handleValueChange(index, 'dropout', parseFloat(e.target.value))} />
                            </div>
                        </div>
                    </div>
                ))}
                
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                    <button type="button" className="btn-add-layer" onClick={() => onAddLayer('lstm')} style={{ flex: 1, background: '#e8f5e9', color: '#2e7d32', borderColor: '#a5d6a7' }}>
                        ＋ Add LSTM Layer
                    </button>
                    <button type="button" className="btn-add-layer" onClick={() => onAddLayer('dense')} style={{ flex: 1 }}>
                        ＋ Add Dense Layer
                    </button>
                </div>
            </div>
        </div>
    );
}
