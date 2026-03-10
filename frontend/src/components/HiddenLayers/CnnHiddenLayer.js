import '../ModelCss/ModelPage.css';

const HiddenLayer = ({ index, layer, onChange, onRemove }) => {
    const handleChange = (key, value) => {
        onChange(index, { ...layer, [key]: value });
    };

    return (
        <div className="hidden-layer-card">
            <div className="layer-card-header">
                <h4>Layer {index + 1}</h4>
                <button type="button" className="btn-remove-layer" onClick={() => onRemove(index)}>✕ Remove</button>
            </div>
            <div className="layer-params">
                <div>
                    <label>Type</label>
                    <select value={layer.type} onChange={(e) => handleChange('type', e.target.value)}>
                        <option value="conv">Convolutional</option>
                        <option value="pooling">Pooling</option>
                        <option value="flatten">Flatten</option>
                        <option value="dense">Dense</option>
                        <option value="dropout">Dropout</option>
                    </select>
                </div>

                {layer.type === 'conv' && (
                    <>
                        <div>
                            <label>Neurons</label>
                            <input type="number" value={layer.numberOfNeurons || 64} onChange={(e) => handleChange('numberOfNeurons', parseInt(e.target.value))} />
                        </div>
                        <div>
                            <label>Kernel Size</label>
                            <input type="text" value={Array.isArray(layer.kernel) ? layer.kernel.join(',') : layer.kernel} onChange={(e) => handleChange('kernel', e.target.value.split(',').map(Number))} />
                        </div>
                        <div>
                            <label>Activation</label>
                            <select value={layer.activationFunction || 'relu'} onChange={(e) => handleChange('activationFunction', e.target.value)}>
                                <option value="relu">ReLU</option>
                                <option value="leaky_relu">Leaky ReLU</option>
                                <option value="softmax">Softmax</option>
                                <option value="prelu">PReLU</option>
                                <option value="elu">ELU</option>
                                <option value="tanh">Tanh</option>
                                <option value="sigmoid">Sigmoid</option>
                            </select>
                        </div>
                    </>
                )}

                {layer.type === 'pooling' && (
                    <>
                        <div>
                            <label>Pooling Type</label>
                            <select value={layer.poolingType || 'maxPool'} onChange={(e) => handleChange('poolingType', e.target.value)}>
                                <option value="maxPool">Max Pooling</option>
                                <option value="avgPool">Average Pooling</option>
                                <option value="minPool">Min Pooling</option>
                            </select>
                        </div>
                        <div>
                            <label>Pool Size</label>
                            <input type="text" value={Array.isArray(layer.poolingSize) ? layer.poolingSize.join(',') : layer.poolingSize} onChange={(e) => handleChange('poolingSize', e.target.value.split(',').map(Number))} />
                        </div>
                    </>
                )}

                {layer.type === 'dense' && (
                    <>
                        <div>
                            <label>Units</label>
                            <input type="number" value={layer.units || 128} onChange={(e) => handleChange('units', parseInt(e.target.value))} />
                        </div>
                        <div>
                            <label>Activation</label>
                            <select value={layer.activationFunction || 'relu'} onChange={(e) => handleChange('activationFunction', e.target.value)}>
                                <option value="relu">ReLU</option>
                                <option value="softmax">Softmax</option>
                                <option value="sigmoid">Sigmoid</option>
                                <option value="tanh">Tanh</option>
                            </select>
                        </div>
                    </>
                )}

                {layer.type === 'dropout' && (
                    <div>
                        <label>Dropout Rate</label>
                        <input type="number" step="0.05" min="0" max="1" value={layer.dropoutRate || 0.5} onChange={(e) => handleChange('dropoutRate', parseFloat(e.target.value))} />
                    </div>
                )}
            </div>
        </div>
    );
};

const CnnHiddenLayer = ({ layers, onChange, onAddLayer, onRemoveLayer }) => {
    return (
        <div className="hidden-layers-section">
            <div className="hidden-layers-header">
                <h3>🧱 Hidden Layers ({layers.length})</h3>
            </div>
            <div className="hidden-layers-list">
                {layers.map((layer, index) => (
                    <HiddenLayer
                        key={index}
                        index={index}
                        layer={layer}
                        onChange={onChange}
                        onRemove={onRemoveLayer}
                    />
                ))}
                <button type="button" className="btn-add-layer" onClick={onAddLayer}>
                    ＋ Add Layer
                </button>
            </div>
        </div>
    );
};

export default CnnHiddenLayer;
