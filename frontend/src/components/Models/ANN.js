import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'ann';

const DEFAULT_LAYER = { units: 64, activation: 'relu', dropout: 0 };

export default function ANN() {
    const [datasetData, setDatasetData] = useState('');
    const [layers, setLayers] = useState([{ ...DEFAULT_LAYER }, { units: 32, activation: 'relu', dropout: 0 }]);
    const [epochs, setEpochs] = useState(50);
    const [batchSize, setBatchSize] = useState(32);
    const [optimizer, setOptimizer] = useState('adam');
    const [lossFunction, setLossFunction] = useState('binary_crossentropy');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);

    const handleLayerChange = (index, key, value) => {
        const updated = [...layers];
        updated[index] = { ...updated[index], [key]: value };
        setLayers(updated);
    };

    const addLayer = () => setLayers([...layers, { ...DEFAULT_LAYER }]);
    const removeLayer = (index) => setLayers(layers.filter((_, i) => i !== index));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${constants.API_BASE_URL}/ann`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: datasetData?.filename,
                    hidden_layers: layers,
                    epochs,
                    batch_size: batchSize,
                    optimizer,
                    loss: lossFunction,
                    hyperparams: { epochs, batch_size: batchSize, optimizer, loss: lossFunction },
                }),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Failed');
            }
            setResults(await response.json());
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>Artificial Neural Network</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={setDatasetData} />
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                {/* Training Settings */}
                <div className="form-grid">
                    <div className="form-group">
                        <label>Epochs</label>
                        <input type="number" min="1" max="500" value={epochs} onChange={(e) => setEpochs(parseInt(e.target.value))} />
                    </div>
                    <div className="form-group">
                        <label>Batch Size</label>
                        <select value={batchSize} onChange={(e) => setBatchSize(parseInt(e.target.value))}>
                            <option value={8}>8</option>
                            <option value={16}>16</option>
                            <option value={32}>32</option>
                            <option value={64}>64</option>
                            <option value={128}>128</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Optimizer</label>
                        <select value={optimizer} onChange={(e) => setOptimizer(e.target.value)}>
                            <option value="adam">Adam</option>
                            <option value="sgd">SGD</option>
                            <option value="rmsprop">RMSprop</option>
                            <option value="adagrad">Adagrad</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Loss Function</label>
                        <select value={lossFunction} onChange={(e) => setLossFunction(e.target.value)}>
                            <option value="binary_crossentropy">Binary Crossentropy</option>
                            <option value="categorical_crossentropy">Categorical Crossentropy</option>
                            <option value="sparse_categorical_crossentropy">Sparse Categorical Crossentropy</option>
                            <option value="mse">Mean Squared Error</option>
                        </select>
                    </div>
                </div>

                {/* ANN Layer Builder */}
                <div className="hidden-layers-section">
                    <div className="hidden-layers-header">
                        <h3>🧠 Dense Layers ({layers.length})</h3>
                    </div>
                    <div className="hidden-layers-list">
                        {layers.map((layer, index) => (
                            <div className="hidden-layer-card" key={index}>
                                <div className="layer-card-header">
                                    <h4>Layer {index + 1}</h4>
                                    <button type="button" className="btn-remove-layer" onClick={() => removeLayer(index)}>✕ Remove</button>
                                </div>
                                <div className="layer-params">
                                    <div>
                                        <label>Units</label>
                                        <input type="number" min="1" value={layer.units} onChange={(e) => handleLayerChange(index, 'units', parseInt(e.target.value))} />
                                    </div>
                                    <div>
                                        <label>Activation</label>
                                        <select value={layer.activation} onChange={(e) => handleLayerChange(index, 'activation', e.target.value)}>
                                            <option value="relu">ReLU</option>
                                            <option value="sigmoid">Sigmoid</option>
                                            <option value="tanh">Tanh</option>
                                            <option value="softmax">Softmax</option>
                                            <option value="leaky_relu">Leaky ReLU</option>
                                            <option value="elu">ELU</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label>Dropout</label>
                                        <input type="number" step="0.05" min="0" max="0.9" value={layer.dropout} onChange={(e) => handleLayerChange(index, 'dropout', parseFloat(e.target.value))} />
                                    </div>
                                </div>
                            </div>
                        ))}
                        <button type="button" className="btn-add-layer" onClick={addLayer}>
                            ＋ Add Dense Layer
                        </button>
                    </div>
                </div>

                <button type="submit" className="btn-run" disabled={loading} style={{ marginTop: 16 }}>
                    {loading ? '⏳ Training...' : '▶ Train ANN'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {results && (
                <div className="results-card">
                    <h2>Training Results</h2>
                    {results.message && <p>{results.message}</p>}
                    <div className="metrics-grid">
                        {results.accuracy != null && <div className="metric-item"><div className="metric-label">Test Accuracy</div><div className="metric-value">{(results.accuracy * 100).toFixed(2)}%</div></div>}
                        {results.loss != null && <div className="metric-item"><div className="metric-label">Test Loss</div><div className="metric-value">{results.loss.toFixed(4)}</div></div>}
                        {results.val_accuracy != null && <div className="metric-item"><div className="metric-label">Val Accuracy</div><div className="metric-value">{(results.val_accuracy * 100).toFixed(2)}%</div></div>}
                        {results.val_loss != null && <div className="metric-item"><div className="metric-label">Val Loss</div><div className="metric-value">{results.val_loss.toFixed(4)}</div></div>}
                        {results.epochs_trained != null && <div className="metric-item"><div className="metric-label">Epochs</div><div className="metric-value">{results.epochs_trained}</div></div>}
                    </div>
                </div>
            )}

            <div className="download-section">
                <DownloadTrainedModel selectedModel="ann" extension=".h5" />
            </div>

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
