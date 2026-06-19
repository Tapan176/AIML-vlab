import { useState, useEffect } from 'react';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import ShowDataset from '../Dataset/ShowDataset';
import CachedDatasetBadge from '../shared/CachedDatasetBadge';
import useReplaySession from '../../hooks/useReplaySession';
import useHyperparamCache from '../../hooks/useHyperparamCache';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import useDatasetCache from '../../hooks/useDatasetCache';
import ColumnSelect from '../shared/ColumnSelect';
import '../shared/ModelStyles.css';

const MODEL_CODE = 'distilbert_finetune';

const DEFAULT_HYPERPARAMS = {
    model_name: 'distilbert-base-uncased',
    epochs: 3,
    batch_size: 16,
    learning_rate: 2e-5,
    max_length: 256,
    test_size: 0.2,
    freeze_base: false,
};

const FinetuneDistilBERT = () => {
    const { hyperparams: replayHyperparams, datasetConfig, restoredResults, liveStatus, liveLogs } = useReplaySession(MODEL_CODE);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);
    const [availableColumns, setAvailableColumns] = useState([]);
    const [textColumn, setTextColumn] = useState(datasetConfig?.text_column || 'text');
    const [labelColumn, setLabelColumn] = useState(datasetConfig?.label_column || 'label');
    // Persist hyperparams across refresh/remount; seed = defaults + replay values.
    const [hyperparams, setHyperparams] = useHyperparamCache(MODEL_CODE, { ...DEFAULT_HYPERPARAMS, ...(replayHyperparams || {}) });

    const [logs, setLogs] = useState([]);
    const [results, setResults] = useState(null);
    const [training, setTraining] = useState(false);
    const [error, setError] = useState(null);
    const [infoOpen, setInfoOpen] = useState(false);

    const replayActive = liveStatus === 'running' || liveStatus === 'pending';
    useEffect(() => {
        if (restoredResults) setResults(restoredResults);
    }, [restoredResults]);
    useEffect(() => {
        // Mirror persisted progress when reconnecting (replay / refresh), not
        // while THIS page is actively streaming (the SSE loop owns it then).
        if (!training && replayActive && liveLogs.length > 0) setLogs(liveLogs);
    }, [training, replayActive, liveLogs]);

    useEffect(() => {
        if (availableColumns.length === 0) return;
        setTextColumn(prev => availableColumns.includes(prev)
            ? prev
            : (availableColumns.find(c => /text|review|comment|sentence|message|body/i.test(c)) || availableColumns[0]));
        setLabelColumn(prev => availableColumns.includes(prev)
            ? prev
            : (availableColumns.find(c => /label|target|class|sentiment|category|rating/i.test(c)) || availableColumns[availableColumns.length - 1]));
    }, [availableColumns]);

    const handleChange = (name, value) => setHyperparams(prev => ({ ...prev, [name]: value }));

    const startTraining = async (e) => {
        e.preventDefault();
        if (!datasetData?.filename) {
            setError('Please select or upload a CSV dataset first.');
            return;
        }
        setTraining(true);
        setError(null);
        setResults(null);
        setLogs(['🚀 Starting DistilBERT fine-tuning...']);

        try {
            const { API_URL, TOKEN_KEY } = await import('../../constants');
            const token = localStorage.getItem(TOKEN_KEY);

            const response = await fetch(`${API_URL}/finetune/distilbert`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    filename: datasetData.filename,
                    dataset_id: datasetData.dataset_id || null,
                    text_column: textColumn,
                    label_column: labelColumn,
                    hyperparams,
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                if (response.status === 429 && err && err.error === 'quota_exceeded') {
                    window.dispatchEvent(new CustomEvent('aiml:quota', { detail: err }));
                }
                throw new Error(err.message || err.error || 'Training failed');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let done = false;

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                if (value) {
                    buffer += decoder.decode(value, { stream: true });
                    const events = buffer.split('\n\n');
                    buffer = events.pop() || '';
                    events.forEach(event => {
                        if (event.startsWith('data: ')) {
                            try {
                                const parsed = JSON.parse(event.replace('data: ', ''));
                                if (parsed.log) setLogs(prev => [...prev, parsed.log]);
                                else if (parsed.status === 'completed' || parsed.evaluation_metrics) { setResults(parsed); try { window.dispatchEvent(new CustomEvent('aiml:trained')); } catch (e) {} }
                            } catch (e) {}
                        }
                    });
                }
                done = readerDone;
            }
        } catch (err) {
            setError(err.message);
            setLogs(prev => [...prev, `❌ Error: ${err.message}`]);
        }
        setTraining(false);
    };

    return (
        <div className="model-container">
            <div className="model-header">
                <h2>⚡ DistilBERT Fine-Tuning (NLP)</h2>
                <p>Lightweight, fast text fine-tuning with DistilBERT — 40% smaller than BERT.</p>
                <div className="model-badge fine-tuning">HuggingFace Transformers</div>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <ShowDataset
                onDatasetUpload={handleDatasetSelect}
                allowedTypes={['csv']}
                initialFilename={datasetData?.filename}
                onColumnsDetected={setAvailableColumns}
            />
            <CachedDatasetBadge filename={datasetData?.filename} />

            <form className="model-form" onSubmit={startTraining}>
                <div className="form-section">
                    <h4>Column Mapping</h4>
                    <div className="form-row">
                        <ColumnSelect
                            label="Text Column"
                            value={textColumn}
                            columns={availableColumns}
                            onChange={setTextColumn}
                            placeholder="Column with text"
                        />
                        <ColumnSelect
                            label="Label Column"
                            value={labelColumn}
                            columns={availableColumns}
                            onChange={setLabelColumn}
                            placeholder="Column with labels"
                        />
                    </div>
                </div>

                <div className="form-section">
                    <h4>Hyperparameters</h4>
                    <div className="form-row">
                        <div className="form-group">
                            <label>Base Model</label>
                            <select value={hyperparams.model_name} onChange={e => handleChange('model_name', e.target.value)}>
                                <option value="distilbert-base-uncased">DistilBERT Base</option>
                                <option value="bert-base-uncased">BERT Base</option>
                                <option value="roberta-base">RoBERTa Base</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Epochs</label>
                            <input type="number" value={hyperparams.epochs} onChange={e => handleChange('epochs', parseInt(e.target.value))} min={1} max={50} />
                        </div>
                        <div className="form-group">
                            <label>Batch Size</label>
                            <input type="number" value={hyperparams.batch_size} onChange={e => handleChange('batch_size', parseInt(e.target.value))} />
                        </div>
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label>Learning Rate</label>
                            <input type="number" step="0.0000001" value={hyperparams.learning_rate} onChange={e => handleChange('learning_rate', parseFloat(e.target.value))} />
                        </div>
                        <div className="form-group">
                            <label>Max Length</label>
                            <input type="number" value={hyperparams.max_length} onChange={e => handleChange('max_length', parseInt(e.target.value))} />
                        </div>
                        <div className="form-group">
                            <label>Test Split</label>
                            <input type="number" step="0.05" value={hyperparams.test_size} onChange={e => handleChange('test_size', parseFloat(e.target.value))} />
                        </div>
                    </div>
                    <label className="toggle-label">
                        <input type="checkbox" checked={hyperparams.freeze_base} onChange={e => handleChange('freeze_base', e.target.checked)} />
                        Freeze Base Layers
                    </label>
                </div>

                <button type="submit" className="btn-train" disabled={training}>
                    {training ? '⏳ Fine-Tuning...' : '🚀 Start Fine-Tuning'}
                </button>
            </form>

            {error && <div className="error-banner">{error}</div>}

            {replayActive && !training && (
                <div className="error-banner" style={{ background: 'var(--warning-soft)', borderColor: 'var(--warning)', color: 'var(--warning)' }}>
                    ⏳ This fine-tuning session is still in progress — showing live progress below. Results will appear automatically when it finishes.
                </div>
            )}

            {(logs.length > 0 || replayActive) && (
                <div className="training-console">
                    <h3>Training Logs</h3>
                    <div className="console-output">
                        {logs.map((log, i) => <div key={i}>{log}</div>)}
                    </div>
                </div>
            )}

            {results && (
                <div className="results-panel">
                    <h3>Results</h3>
                    <div className="metrics-grid">
                        {results.evaluation_metrics?.accuracy != null && (
                            <div className="metric-item">
                                <span className="metric-label">Accuracy</span>
                                <span className="metric-value">{(results.evaluation_metrics.accuracy * 100).toFixed(2)}%</span>
                            </div>
                        )}
                        {results.evaluation_metrics?.val_loss != null && (
                            <div className="metric-item">
                                <span className="metric-label">Val Loss</span>
                                <span className="metric-value">{results.evaluation_metrics.val_loss.toFixed(4)}</span>
                            </div>
                        )}
                    </div>
                    {results.session_id && (
                        <div className="download-section">
                            <DownloadTrainedModel selectedModel="distilbert_finetune" extension=".zip" sessionId={results.session_id} label="Download Fine-Tuned Model" />
                        </div>
                    )}
                </div>
            )}

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
};

export default FinetuneDistilBERT;
