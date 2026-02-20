import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import CnnHiddenLayer from '../HiddenLayers/CnnHiddenLayer';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'cnn';

const DEFAULT_LAYER = { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' };

export default function CNN() {
    const [datasetData, setDatasetData] = useState('');
    const [layers, setLayers] = useState([{ ...DEFAULT_LAYER }]);
    const [epochs, setEpochs] = useState(10);
    const [batchSize, setBatchSize] = useState(32);
    const [optimizer, setOptimizer] = useState('adam');
    const [lossFunction, setLossFunction] = useState('categorical_crossentropy');
    const [classMode, setClassMode] = useState('categorical');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);

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
            const response = await fetch(`${constants.API_BASE_URL}/cnn`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: datasetData?.filename,
                    hidden_layers: layers,
                    epochs,
                    batch_size: batchSize,
                    optimizer,
                    loss: lossFunction,
                    class_mode: classMode,
                }),
            });
            if (!response.ok) { const err = await response.json(); throw new Error(err.error || 'Failed'); }
            setResults(await response.json());
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
                <ShowDataset onDatasetUpload={setDatasetData} />
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                {/* Training Settings — all dropdowns for enum values */}
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
                            <option value="adadelta">Adadelta</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Loss Function</label>
                        <select value={lossFunction} onChange={(e) => setLossFunction(e.target.value)}>
                            <option value="categorical_crossentropy">Categorical Crossentropy</option>
                            <option value="binary_crossentropy">Binary Crossentropy</option>
                            <option value="sparse_categorical_crossentropy">Sparse Categorical Crossentropy</option>
                            <option value="mse">Mean Squared Error</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Class Mode</label>
                        <select value={classMode} onChange={(e) => setClassMode(e.target.value)}>
                            <option value="categorical">Categorical</option>
                            <option value="binary">Binary</option>
                            <option value="sparse">Sparse</option>
                        </select>
                    </div>
                </div>

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

            <div className="download-section">
                <DownloadTrainedModel selectedModel="cnn" extension=".h5" />
            </div>

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
