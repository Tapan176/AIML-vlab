import React, { useState, useEffect } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'ann';

const DEFAULT_LAYERS = [
    { units: 128, activation: 'relu', dropout: 0.2 },
    { units: 64, activation: 'relu', dropout: 0.2 },
    { units: 32, activation: 'relu', dropout: 0 },
];

export default function ANN() {
    const [datasetData, setDatasetData] = useState('');
    const [layers, setLayers] = useState(DEFAULT_LAYERS.map(l => ({ ...l })));
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);
    const [logs, setLogs] = useState([]);


    useEffect(() => {
        const cached = localStorage.getItem(`ann_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`ann_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`ann_dataset`);
        }
    };
    const handleLayerChange = (index, key, value) => {
        const updated = [...layers];
        updated[index] = { ...updated[index], [key]: value };
        setLayers(updated);
    };

    const addLayer = () => setLayers([...layers, { ...DEFAULT_LAYERS[0] }]);
    const removeLayer = (index) => setLayers(layers.filter((_, i) => i !== index));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setLogs([]);
        setResults(null);
        try {
            const bodyPayload = {
                filename: datasetData?.filename,
                hidden_layers: layers,
                epochs: hyperparams.epochs || 50,
                batch_size: hyperparams.batch_size || 32,
                optimizer: hyperparams.optimizer || 'adam',
                loss: hyperparams.loss || 'binary_crossentropy',
                hyperparams,
            };

            const response = await fetch(`${constants.API_URL}/ann`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('aiml_token')}`
                },
                body: JSON.stringify(bodyPayload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Training failed');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let done = false;

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    const chunk = decoder.decode(value, { stream: true });
                    const events = chunk.split('\n\n');
                    events.forEach(event => {
                        if (event.startsWith('data: ')) {
                            try {
                                const parsed = JSON.parse(event.replace('data: ', ''));
                                if (parsed.log) {
                                    setLogs(prev => [...prev, parsed.log]);
                                } else if (parsed.status === 'completed') {
                                    setResults(parsed);
                                } else if (parsed.error) {
                                    setError(parsed.error);
                                }
                            } catch (e) { }
                        }
                    });
                }
            }
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>Artificial Neural Network</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                {/* Training Settings */}
                <HyperparamPanel
                    modelCode="ann"
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                />

                {/* ANN Layer Builder */}
                <div className="hidden-layers-section">
                    <div className="hidden-layers-header">
                        <h3>ðŸ§  Dense Layers ({layers.length})</h3>
                    </div>
                    <div className="hidden-layers-list">
                        {layers.map((layer, index) => (
                            <div className="hidden-layer-card" key={index}>
                                <div className="layer-card-header">
                                    <h4>Layer {index + 1}</h4>
                                    <button type="button" className="btn-remove-layer" onClick={() => removeLayer(index)}>✖ Remove</button>
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
                            ï¼‹ Add Dense Layer
                        </button>
                    </div>
                </div>

                <button type="submit" className="btn-run" disabled={loading} style={{ marginTop: 16 }}>
                    {loading ? '⏳ Training...' : '▶ Train ANN'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {logs.length > 0 && (
                <div className="terminal-container" style={{ marginTop: '20px', background: '#1e1e1e', color: '#00ff00', padding: '15px', borderRadius: '8px', fontFamily: 'monospace', height: '300px', overflowY: 'auto' }}>
                    <div style={{ borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '10px', color: '#888' }}>
                        🖥️ Live Training Console
                    </div>
                    {logs.map((log, index) => (
                        <div key={index}>{log}</div>
                    ))}
                    {loading && <div className="cursor-blink" style={{ marginTop: '10px' }}>_</div>}
                </div>
            )}

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

            {results && (
                <div className="download-section">
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel="ann" extension=".h5" sessionId={results.session_id} label="Download" />
                    )}
                    {results.results_zip_drive_id && (
                        <DownloadResultsZip sessionId={results.session_id} />
                    )}
                </div>
            )}

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}


