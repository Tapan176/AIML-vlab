import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import useReplaySession from '../../hooks/useReplaySession';
import useHyperparamCache from '../../hooks/useHyperparamCache';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import LstmHiddenLayer from '../HiddenLayers/LstmHiddenLayer';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import TrainingChart from '../shared/TrainingChart';
import useDatasetCache from '../../hooks/useDatasetCache';
import { formatMetric } from '../../utils/formatMetric';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'lstm';

export default function LSTM() {
    const { hyperparams: replayHyperparams, restoredResults, liveStatus, liveLogs, liveMetrics } = useReplaySession(MODEL_CODE);
    const [layers, setLayers] = useState([
        { type: 'lstm', units: 128, return_sequences: true, dropout: 0.2 },
        { type: 'lstm', units: 64, return_sequences: false, dropout: 0.2 },
        { type: 'dense', units: 32, activation: 'relu', dropout: 0 },
    ]);
    const [, setSearchParams] = useSearchParams();
    const [classMode, setClassMode] = useState('categorical');
    const [hyperparams, setHyperparams] = useHyperparamCache(MODEL_CODE, replayHyperparams);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);
    const [logs, setLogs] = useState([]);
    const [metrics, setMetrics] = useState([]);
    const [runningSessionId, setRunningSessionId] = useState(null);
    const [cancelling, setCancelling] = useState(false);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);

    const cancelTraining = async () => {
        if (!runningSessionId) return;
        setCancelling(true);
        try {
            const { default: api } = await import('../../services/api');
            await api.post(`/training-sessions/${runningSessionId}/cancel`);
        } catch (e) { /* best-effort */ }
    };

    // Replay restore: a completed session's results, or the live progress of a
    // session still training (re-opened from the Dashboard).
    const replayActive = liveStatus === 'running' || liveStatus === 'pending';
    useEffect(() => {
        if (restoredResults) setResults(restoredResults);
    }, [restoredResults]);
    useEffect(() => {
        // Mirror persisted progress whenever reconnecting to a session (replay /
        // refresh) and not actively streaming here. Must NOT require the run to
        // still be active, or a COMPLETED replay would show no logs/chart.
        if (!loading && liveLogs.length > 0) setLogs(liveLogs);
    }, [loading, liveLogs]);
    useEffect(() => {
        if (!loading && liveMetrics.length > 0) setMetrics(liveMetrics);
    }, [loading, liveMetrics]);

    const lossOptions = classMode === 'linear'
        ? ['mse', 'mae', 'huber']
        : ['binary_crossentropy', 'categorical_crossentropy', 'sparse_categorical_crossentropy'];

    const handleClassModeChange = (value) => {
        setClassMode(value);
        setHyperparams(prev => ({
            ...prev,
            loss: value === 'linear' ? 'mse' : (prev.loss === 'categorical_crossentropy' ? prev.loss : 'sparse_categorical_crossentropy')
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setLogs([]);
        setMetrics([]);
        setResults(null);
        setRunningSessionId(null);
        setCancelling(false);
        try {
            const bodyPayload = {
                filePath: datasetData?.extracted_file_path || datasetData?.filepath || datasetData?.path || datasetData?.filename,
                filename: datasetData?.filename,
                dataset_id: datasetData?.dataset_id || null,
                hyperparams,
                hiddenLayerArray: layers,
                classMode: classMode,
            };

            const response = await fetch(`${constants.API_URL}/lstm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem(constants.TOKEN_KEY)}`
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
                                if (parsed.session_id && parsed.status === 'started') {
                                    setRunningSessionId(parsed.session_id);
                                    setSearchParams(prev => {
                                        const next = new URLSearchParams(prev);
                                        next.set('session', parsed.session_id);
                                        return next;
                                    }, { replace: true });
                                }
                                if (parsed.metrics) {
                                    setMetrics(prev => [...prev, parsed.metrics]);
                                }
                                if (parsed.status === 'cancelled') {
                                    setLogs(prev => [...prev, parsed.log || 'Training cancelled.']);
                                } else if (parsed.log) {
                                    setLogs(prev => [...prev, parsed.log]);
                                } else if (parsed.status === 'completed' || parsed.status === 'training_complete') {
                                    setResults(parsed);
                                    try { window.dispatchEvent(new CustomEvent('aiml:trained')); } catch (e) {}
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
                <h1>LSTM (Sequence Forecasting)</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv', 'txt']} initialFilename={datasetData?.filename} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: 'var(--success)' }}>
                        ✓ Cached sequence dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Output Mode</label>
                        <select value={classMode} onChange={(e) => handleClassModeChange(e.target.value)}>
                            <option value="categorical">Categorical (Classification)</option>
                            <option value="linear">Linear (Regression)</option>
                        </select>
                    </div>
                </div>

                <HyperparamPanel
                    modelCode={MODEL_CODE}
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                    schemaOverrides={{ loss: { options: lossOptions, default: lossOptions[0] } }}
                />

                <LstmHiddenLayer
                    layers={layers}
                    onChange={(index, updatedLayer) => {
                        const newLayers = [...layers];
                        newLayers[index] = updatedLayer;
                        setLayers(newLayers);
                    }}
                    onAddLayer={(type) => {
                        if (type === 'lstm') setLayers([...layers, { type: 'lstm', units: 64, return_sequences: true, dropout: 0.2 }]);
                        else setLayers([...layers, { type: 'dense', units: 32, activation: 'relu', dropout: 0 }]);
                    }}
                    onRemoveLayer={(index) => setLayers(layers.filter((_, i) => i !== index))}
                />

                <button type="submit" className="btn-run" disabled={loading} style={{ marginTop: 16 }}>
                    {loading ? '⏳ Training...' : '▶ Train LSTM'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {replayActive && !loading && (
                <div className="model-info-banner" style={{ marginTop: '16px', padding: '12px 16px', borderRadius: '8px', background: 'var(--warning-soft)', border: '1px solid var(--warning)', color: 'var(--warning)' }}>
                    ⏳ This training session is still in progress — showing live progress below. Results will appear automatically when it finishes.
                </div>
            )}

            {loading && runningSessionId && (
                <div style={{ marginTop: '16px' }}>
                    <button type="button" className="btn-cancel-training" onClick={cancelTraining} disabled={cancelling}>
                        {cancelling ? '⏳ Cancelling…' : '🛑 Cancel training'}
                    </button>
                </div>
            )}

            <TrainingChart metrics={metrics} />

            {(logs.length > 0 || replayActive) && (
                <div className="terminal-container" style={{ marginTop: '20px', background: 'var(--terminal-bg)', color: 'var(--terminal-text)', padding: '15px', borderRadius: '8px', fontFamily: 'monospace', height: '300px', overflowY: 'auto' }}>
                    <div style={{ borderBottom: '1px solid var(--terminal-border)', paddingBottom: '10px', marginBottom: '10px', color: 'var(--terminal-muted)' }}>
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
                        <div className="metric-item"><div className="metric-label">RMSE</div><div className="metric-value">{formatMetric(results.rmse)}</div></div>
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
