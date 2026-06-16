import React, { useState, useEffect } from 'react';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import ShowDataset from '../Dataset/ShowDataset';
import CachedDatasetBadge from '../shared/CachedDatasetBadge';
import useReplaySession from '../../hooks/useReplaySession';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import useDatasetCache from '../../hooks/useDatasetCache';
import ColumnSelect from '../shared/ColumnSelect';
import '../shared/ModelStyles.css';

const MODEL_CODE = 'bert_finetune';

const DEFAULT_HYPERPARAMS = {
    model_name: 'bert-base-uncased',
    epochs: 3,
    batch_size: 16,
    learning_rate: 2e-5,
    max_length: 256,
    test_size: 0.2,
    freeze_base: false,
};

/**
 * BERT Fine-Tuning component.
 * Fine-tunes a pre-trained BERT model on user-provided text classification data.
 */
const FinetuneBERT = () => {
    const { hyperparams: replayHyperparams, datasetConfig, restoredResults, liveStatus, liveLogs } = useReplaySession(MODEL_CODE);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);
    const [availableColumns, setAvailableColumns] = useState([]);
    const [textColumn, setTextColumn] = useState(datasetConfig?.text_column || 'text');
    const [labelColumn, setLabelColumn] = useState(datasetConfig?.label_column || 'label');
    const [hyperparams, setHyperparams] = useState(() => ({ ...DEFAULT_HYPERPARAMS, ...(replayHyperparams || {}) }));

    const [logs, setLogs] = useState([]);
    const [results, setResults] = useState(null);
    const [training, setTraining] = useState(false);
    const [error, setError] = useState(null);
    const [infoOpen, setInfoOpen] = useState(false);

    // Replay restore: completed session results, or live progress of a run
    // still training (re-opened from the Dashboard).
    const replayActive = liveStatus === 'running' || liveStatus === 'pending';
    useEffect(() => {
        if (restoredResults) setResults(restoredResults);
    }, [restoredResults]);
    useEffect(() => {
        if (replayActive && liveLogs.length > 0) setLogs(liveLogs);
    }, [replayActive, liveLogs]);

    // Once the dataset's columns are known, keep the user's / replayed choice if
    // it's still valid, otherwise auto-detect sensible text & label columns.
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
        setLogs(['🚀 Starting BERT fine-tuning...']);

        try {
            const { API_URL } = await import('../../constants');
            const token = localStorage.getItem('aiml_token');

            const response = await fetch(`${API_URL}/finetune/bert`, {
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
                                if (parsed.log) {
                                    setLogs(prev => [...prev, parsed.log]);
                                } else if (parsed.status === 'completed' || parsed.evaluation_metrics) {
                                    setResults(parsed);
                                    try { window.dispatchEvent(new CustomEvent('aiml:trained')); } catch (e) {}
                                }
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
                <h2>🧠 BERT Fine-Tuning (Text Classification)</h2>
                <p>Fine-tune a pre-trained BERT model on your text dataset.</p>
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
                                <option value="bert-base-uncased">BERT Base Uncased</option>
                                <option value="bert-base-cased">BERT Base Cased</option>
                                <option value="distilbert-base-uncased">DistilBERT Base</option>
                                <option value="roberta-base">RoBERTa Base</option>
                                <option value="albert-base-v2">ALBERT Base v2</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Epochs</label>
                            <input type="number" value={hyperparams.epochs} onChange={e => handleChange('epochs', parseInt(e.target.value))} min={1} max={50} />
                        </div>
                        <div className="form-group">
                            <label>Batch Size</label>
                            <input type="number" value={hyperparams.batch_size} onChange={e => handleChange('batch_size', parseInt(e.target.value))} min={1} max={128} />
                        </div>
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label>Learning Rate</label>
                            <input type="number" step="0.0000001" value={hyperparams.learning_rate} onChange={e => handleChange('learning_rate', parseFloat(e.target.value))} />
                        </div>
                        <div className="form-group">
                            <label>Max Token Length</label>
                            <input type="number" value={hyperparams.max_length} onChange={e => handleChange('max_length', parseInt(e.target.value))} min={32} max={512} />
                        </div>
                        <div className="form-group">
                            <label>Test Split</label>
                            <input type="number" step="0.05" value={hyperparams.test_size} onChange={e => handleChange('test_size', parseFloat(e.target.value))} min={0.05} max={0.5} />
                        </div>
                    </div>
                    <div className="form-row">
                        <label className="toggle-label">
                            <input type="checkbox" checked={hyperparams.freeze_base} onChange={e => handleChange('freeze_base', e.target.checked)} />
                            Freeze BERT Base Layers (faster, use for small datasets)
                        </label>
                    </div>
                </div>

                <button type="submit" className="btn-train" disabled={training}>
                    {training ? '⏳ Fine-Tuning...' : '🚀 Start Fine-Tuning'}
                </button>
            </form>

            {error && <div className="error-banner">{error}</div>}

            {replayActive && !training && (
                <div className="error-banner" style={{ background: 'rgba(255,149,0,0.1)', borderColor: 'rgba(255,149,0,0.3)', color: '#ff9500' }}>
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
                    <h3>Training Results</h3>
                    <div className="metrics-grid">
                        {results.evaluation_metrics?.accuracy != null && (
                            <div className="metric-item">
                                <span className="metric-label">Validation Accuracy</span>
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
                            <DownloadTrainedModel selectedModel="bert_finetune" extension=".zip" sessionId={results.session_id} label="Download Fine-Tuned Model" />
                        </div>
                    )}
                </div>
            )}

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
};

export default FinetuneBERT;
