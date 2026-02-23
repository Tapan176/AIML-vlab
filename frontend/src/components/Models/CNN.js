import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import ShowDataset from '../Dataset/ShowDataset';
import CnnHiddenLayer from '../HiddenLayers/CnnHiddenLayer';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'cnn';

const DEFAULT_LAYER = { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' };

export default function CNN() {
    const [datasetData, setDatasetData] = useState('');
    const [layers, setLayers] = useState([{ ...DEFAULT_LAYER }]);
    const [classMode, setClassMode] = useState('categorical');
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);


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

    const addLayer = () => setLayers([...layers, { ...DEFAULT_LAYER }]);
    const removeLayer = (index) => setLayers(layers.filter((_, i) => i !== index));

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
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
            const responseData = await api.post('/cnn', bodyPayload);
            setResults(responseData);
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
                    {loading ? '⏳ Training...' : '▶ Train CNN'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

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
                </div>
            )}

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
