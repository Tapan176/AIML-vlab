import { useState, useEffect } from 'react';
import useReplaySession from '../../hooks/useReplaySession';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import CachedDatasetBadge from '../shared/CachedDatasetBadge';
import ResNetHiddenLayer from '../HiddenLayers/ResNetHiddenLayer';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import useDatasetCache from '../../hooks/useDatasetCache';
import { formatMetric } from '../../utils/formatMetric';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'resnet';

export default function ResNet() {
    const { hyperparams: replayHyperparams, restoredResults, liveStatus, liveLogs } = useReplaySession(MODEL_CODE);
    const [layers, setLayers] = useState([
        { units: 256, activation: 'relu', dropout: 0.5 },
        { units: 128, activation: 'relu', dropout: 0.3 },
    ]);
    const [isFrozen, setIsFrozen] = useState(true);
    const [classMode, setClassMode] = useState('categorical');
    const [hyperparams, setHyperparams] = useState(replayHyperparams);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);
    const [logs, setLogs] = useState([]);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);

    // Replay restore: a completed session's results, or the live progress of a
    // session still training (re-opened from the Dashboard).
    const replayActive = liveStatus === 'running' || liveStatus === 'pending';
    useEffect(() => {
        if (restoredResults) setResults(restoredResults);
    }, [restoredResults]);
    useEffect(() => {
        if (replayActive && liveLogs.length > 0) setLogs(liveLogs);
    }, [replayActive, liveLogs]);

    const lossOptions = classMode === 'binary'
        ? ['binary_crossentropy']
        : classMode === 'sparse'
            ? ['sparse_categorical_crossentropy']
            : ['categorical_crossentropy'];

    const handleClassModeChange = (value) => {
        setClassMode(value);
        setHyperparams(prev => ({
            ...prev,
            loss: value === 'binary'
                ? 'binary_crossentropy'
                : value === 'sparse'
                    ? 'sparse_categorical_crossentropy'
                    : 'categorical_crossentropy'
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setLogs([]);
        setResults(null);
        try {
            const bodyPayload = {
                filePath: datasetData?.extracted_file_path || datasetData?.filepath || datasetData?.path || datasetData?.filename,
                filename: datasetData?.filename,
                dataset_id: datasetData?.dataset_id || null,
                inputShape: [224, 224, 3],
                hyperparams,
                hiddenLayerArray: layers,
                isBaseFrozen: isFrozen,
                classMode: classMode,
            };

            const response = await fetch(`${constants.API_URL}/resnet`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('aiml_token')}`
                },
                body: JSON.stringify(bodyPayload)
            });

            if (!response.ok) {
                const errData = await response.json();
                if (response.status === 429 && errData && errData.error === 'quota_exceeded') {
                    window.dispatchEvent(new CustomEvent('aiml:quota', { detail: errData }));
                }
                throw new Error(errData.message || errData.error || 'Training failed');
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
                                } else if (parsed.status === 'completed' || parsed.status === 'training_complete') {
                                    // Simulated results object since it's a stub
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
                <h1>ResNet (Residual Networks)</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['zip']} initialFilename={datasetData?.filename} />
                <CachedDatasetBadge filename={datasetData?.filename} label="Cached image directory" />
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Class Mode</label>
                        <select value={classMode} onChange={(e) => handleClassModeChange(e.target.value)}>
                            <option value="categorical">Categorical</option>
                            <option value="binary">Binary</option>
                            <option value="sparse">Sparse</option>
                        </select>
                    </div>
                </div>

                <HyperparamPanel
                    modelCode={MODEL_CODE}
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                    schemaOverrides={{ loss: { options: lossOptions, default: lossOptions[0] } }}
                />

                <ResNetHiddenLayer
                    layers={layers}
                    onChange={(index, updatedLayer) => {
                        const newLayers = [...layers];
                        newLayers[index] = updatedLayer;
                        setLayers(newLayers);
                    }}
                    onAddLayer={(newLayer) => setLayers([...layers, newLayer])}
                    onRemoveLayer={(index) => setLayers(layers.filter((_, i) => i !== index))}
                    isFrozen={isFrozen}
                    onToggleFrozen={setIsFrozen}
                />

                <button type="submit" className="btn-run" disabled={loading} style={{ marginTop: 16 }}>
                    {loading ? '⏳ Training...' : '▶ Train ResNet'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {replayActive && !loading && (
                <div className="model-info-banner" style={{ marginTop: '16px', padding: '12px 16px', borderRadius: '8px', background: 'rgba(255,149,0,0.1)', border: '1px solid rgba(255,149,0,0.3)', color: '#ff9500' }}>
                    ⏳ This training session is still in progress — showing live progress below. Results will appear automatically when it finishes.
                </div>
            )}

            {(logs.length > 0 || replayActive) && (
                <div className="terminal-container" style={{ marginTop: '20px', background: '#1e1e1e', color: '#00ff00', padding: '15px', borderRadius: '8px', fontFamily: 'monospace', height: '300px', overflowY: 'auto' }}>
                    <div style={{ borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '10px', color: '#888' }}>
                        🖥️ Live Training Console
                    </div>
                    {logs.map((log, index) => (
                        <div key={index}>{log}</div>
                    ))}
                    {(loading || replayActive) && <div className="cursor-blink" style={{ marginTop: '10px' }}>_</div>}
                </div>
            )}

            {results && (
                <div className="results-card">
                    <h2>Training Results</h2>
                    {results.message && <p>{results.message}</p>}
                    <div className="metrics-grid">
                        <div className="metric-item"><div className="metric-label">Accuracy</div><div className="metric-value">{formatMetric(results.accuracy, { percent: true, decimals: 2 })}</div></div>
                        <div className="metric-item"><div className="metric-label">Loss</div><div className="metric-value">{formatMetric(results.loss)}</div></div>
                    </div>
                </div>
            )}

            {results && (
                <div className="download-section" style={{ marginTop: '20px' }}>
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel={MODEL_CODE} extension=".h5" sessionId={results.session_id} label="Download" />
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
