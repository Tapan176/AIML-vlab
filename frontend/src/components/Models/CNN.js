import React, { useState, useEffect } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import CnnHiddenLayer from '../HiddenLayers/CnnHiddenLayer';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'cnn';

const DEFAULT_LAYERS = [
    { type: 'conv', numberOfNeurons: 32, kernel: [3, 3], activationFunction: 'relu' },
    { type: 'pool', poolType: 'max', poolingSize: [2, 2] },
    { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' },
    { type: 'pool', poolType: 'max', poolingSize: [2, 2] },
    { type: 'flatten' },
    { type: 'dense', numberOfNeurons: 128, activationFunction: 'relu', dropout: 0.3 },
];

export default function CNN() {
    const [datasetData, setDatasetData] = useState('');
    const [layers, setLayers] = useState(DEFAULT_LAYERS.map(l => ({ ...l })));
    const [classMode, setClassMode] = useState('categorical');
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);
    const [logs, setLogs] = useState([]);


    useEffect(() => {
        const cached = localStorage.getItem(`cnn_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`cnn_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`cnn_dataset`);
        }
    };
    const handleLayerChange = (index, updatedLayer) => {
        const newLayers = [...layers];
        newLayers[index] = updatedLayer;
        setLayers(newLayers);
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
                filePath: datasetData?.extracted_file_path || datasetData?.filepath || datasetData?.path || datasetData?.filename, 
                numberOfNeuronsInInputLayer: layers.length > 0 ? (layers[0].numberOfNeurons || 64) : 64,
                inputKernelSize: layers.length > 0 ? (layers[0].kernel || [3, 3]) : [3, 3],
                inputLayerActivationFunction: layers.length > 0 ? (layers[0].activationFunction || 'relu') : 'relu',
                inputShape: [64, 64, 3], 
                hiddenLayerArray: layers.length > 0 ? layers.slice(1) : [],
                optimizerObject: { type: hyperparams.optimizer || 'adam', learning_rate: 0.001 },
                lossFunction: { type: hyperparams.loss || 'categorical_crossentropy' },
                evaluationMetrics: ['accuracy'],
                numberOfEpochs: hyperparams.epochs || 10,
                batchSize: hyperparams.batch_size || 32,
                hyperparams,
                classMode: classMode,
            };

            const response = await fetch(`${constants.API_URL}/cnn`, {
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
                <h1>Convolutional Neural Network</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['zip']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached image directory: <strong>{datasetData.filename}</strong>
                    </div>
                )}
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                {/* Training Settings — generic parameters */}
                <div className="form-grid">
                    <div className="form-group">
                        <label>Class Mode</label>
                        <select value={classMode} onChange={(e) => setClassMode(e.target.value)}>
                            <option value="categorical">Categorical</option>
                            <option value="binary">Binary</option>
                            <option value="sparse">Sparse</option>
                        </select>
                    </div>
                </div>

                <HyperparamPanel
                    modelCode="cnn"
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                />

                {/* Layer Builder */}
                <CnnHiddenLayer
                    layers={layers}
                    onChange={handleLayerChange}
                    onAddLayer={addLayer}
                    onRemoveLayer={removeLayer}
                />

                <button type="submit" className="btn-run" disabled={loading} style={{ marginTop: 16 }}>
                    {loading ? 'â³ Training...' : '▶ Train CNN'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {logs.length > 0 && (
                <div className="terminal-container" style={{ marginTop: '20px', background: '#1e1e1e', color: '#00ff00', padding: '15px', borderRadius: '8px', fontFamily: 'monospace', height: '300px', overflowY: 'auto' }}>
                    <div style={{ borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '10px', color: '#888' }}>
                        Live Training Console
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
                        {results.accuracy != null && <div className="metric-item"><div className="metric-label">Accuracy</div><div className="metric-value">{(results.accuracy * 100).toFixed(2)}%</div></div>}
                        {results.loss != null && <div className="metric-item"><div className="metric-label">Loss</div><div className="metric-value">{results.loss.toFixed(4)}</div></div>}
                    </div>
                </div>
            )}

            {results && (
                <div className="download-section" style={{ marginTop: '20px' }}>
                    <DownloadTrainedModel selectedModel="cnn" extension=".h5" sessionId={results.session_id} />
                    <DownloadResultsZip sessionId={results.session_id} />
                </div>
            )}

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}


