import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import useAbortController from '../../hooks/useAbortController';
import useReplaySession from '../../hooks/useReplaySession';
import useHyperparamCache from '../../hooks/useHyperparamCache';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import useDatasetCache from '../../hooks/useDatasetCache';
import { formatMetric } from '../../utils/formatMetric';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'stylegan';

export default function StyleGAN() {
    const { hyperparams: replayHyperparams, restoredResults, liveStatus, liveLogs } = useReplaySession(MODEL_CODE);
    const [, setSearchParams] = useSearchParams();
    const [hyperparams, setHyperparams] = useHyperparamCache(MODEL_CODE, replayHyperparams);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);
    const [logs, setLogs] = useState([]);
    const logsEndRef = useRef(null);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);

    // Replay restore: completed session results, or live progress of a run
    // still training (re-opened from the Dashboard).
    const replayActive = liveStatus === 'running' || liveStatus === 'pending';
    useEffect(() => {
        if (restoredResults) setResults(restoredResults);
    }, [restoredResults]);
    useEffect(() => {
        // Mirror persisted progress when reconnecting (replay / refresh), not
        // while THIS page is actively streaming (the SSE loop owns it then).
        if (!loading && replayActive && liveLogs.length > 0) setLogs(liveLogs);
    }, [loading, replayActive, liveLogs]);

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    const nextSignal = useAbortController();

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
                hyperparams
            };
            const token = localStorage.getItem(constants.TOKEN_KEY);
            const response = await fetch(`${constants.API_URL}/stylegan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(bodyPayload),
                signal: nextSignal(),
            });

            if (!response.ok) {
                const errData = await response.json();
                if (response.status === 429 && errData && errData.error === 'quota_exceeded') {
                    window.dispatchEvent(new CustomEvent('aiml:quota', { detail: errData }));
                }
                throw new Error(errData.message || errData.error || 'Failed to start generative process');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let done = false;

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                if (value) {
                    const chunkValue = decoder.decode(value);
                    const lines = chunkValue.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.replace('data: ', '').trim();
                            if (dataStr) {
                                try {
                                    const parsed = JSON.parse(dataStr);
                                    if (parsed.session_id && parsed.status === 'started') {
                                        setSearchParams((p) => { const n = new URLSearchParams(p); n.set('session', parsed.session_id); return n; }, { replace: true });
                                    }
                                    if (parsed.log) {
                                        setLogs(prev => [...prev, parsed.log]);
                                    }
                                    if (parsed.error) {
                                        setError(parsed.error);
                                    }
                                    if (parsed.status === 'completed' || parsed.status === 'training_complete') {
                                        setResults(parsed);
                                        try { window.dispatchEvent(new CustomEvent('aiml:trained')); } catch (e) {}
                                    }
                                } catch (e) {
                                    console.error("Parse stream err:", e);
                                }
                            }
                        }
                    }
                }
            }
        } catch (err) { if (err.name !== 'AbortError') setError(err.message); }
        finally { setLoading(false); }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>StyleGAN Model Generation</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['zip']} initialFilename={datasetData?.filename} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: 'var(--success)' }}>
                        ✓ Cached Image ZIP Dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                <HyperparamPanel
                    modelCode={MODEL_CODE}
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                />

                <button type="submit" className="btn-run" disabled={loading} style={{ marginTop: 16 }}>
                    {loading ? '⏳ Generating StyleGAN Model...' : '▶ Train Generative Model'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {replayActive && !loading && (
                <div className="model-info-banner" style={{ marginTop: '16px', padding: '12px 16px', borderRadius: '8px', background: 'var(--warning-soft)', border: '1px solid var(--warning)', color: 'var(--warning)' }}>
                    ⏳ This training session is still in progress — showing live progress below. Results will appear automatically when it finishes.
                </div>
            )}

            {(logs.length > 0 || replayActive) && (
                <div className="terminal-log-container" style={{
                    backgroundColor: 'var(--terminal-bg)', color: 'var(--terminal-text)', padding: '15px',
                    borderRadius: '8px', fontFamily: 'monospace', marginTop: '20px',
                    maxHeight: '300px', overflowY: 'auto', textAlign: 'left',
                    boxShadow: 'inset 0 0 10px rgba(0,0,0,0.5)'
                }}>
                    <h3 style={{ color: 'var(--terminal-title)', borderBottom: '1px solid var(--terminal-border)', paddingBottom: '10px', marginBottom: '10px' }}>
                        🖥️ Live Training Console
                    </h3>
                    <div className="log-scroll">
                        {logs.map((log, idx) => (
                            <div key={idx} style={{ margin: '4px 0', fontSize: '13px' }}>
                                <span style={{ color: 'var(--terminal-muted)' }}>[{new Date().toLocaleTimeString()}]</span> {log}
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                </div>
            )}

            {results && (
                <div className="results-card" style={{ marginTop: '20px' }}>
                    <h2>Training Complete</h2>
                    {results.message && <p>{results.message}</p>}
                    <div className="metrics-grid">
                        <div className="metric-item"><div className="metric-label">Discriminator Loss</div><div className="metric-value">{formatMetric(results.loss_d)}</div></div>
                        <div className="metric-item"><div className="metric-label">Generator Loss</div><div className="metric-value">{formatMetric(results.loss_g)}</div></div>
                        {results.epochs_trained != null && <div className="metric-item"><div className="metric-label">Epochs Trained</div><div className="metric-value">{results.epochs_trained}</div></div>}
                    </div>

                    <div className="download-section" style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                        {(results.trained_model_drive_id || !results.session_id) && (
                            <DownloadTrainedModel
                                selectedModel={MODEL_CODE}
                                extension=".pt"
                                sessionId={results.session_id} label="Download"
                            />
                        )}
                        {results.results_zip_drive_id && (
                            <DownloadResultsZip sessionId={results.session_id} />
                        )}
                    </div>

                    <p style={{ color: 'var(--text-secondary)', marginTop: '10px' }}>* Models are stored in your personal cloud namespace.</p>
                </div>
            )}

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
