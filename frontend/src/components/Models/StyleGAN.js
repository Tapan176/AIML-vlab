import { useState, useEffect, useRef } from 'react';
import useReplaySession from '../../hooks/useReplaySession';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import useDatasetCache from '../../hooks/useDatasetCache';
import { formatMetric } from '../../utils/formatMetric';
import '../ModelCss/ModelPage.css';
import { streamTraining } from '../../services/api';

const MODEL_CODE = 'stylegan';

export default function StyleGAN() {
    const { hyperparams: replayHyperparams, restoredResults, liveStatus, liveLogs } = useReplaySession(MODEL_CODE);
    const [hyperparams, setHyperparams] = useState(replayHyperparams);
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
        if (replayActive && liveLogs.length > 0) setLogs(liveLogs);
    }, [replayActive, liveLogs]);

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

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
            await streamTraining('/stylegan', bodyPayload, (parsed) => {
                if (parsed.log) setLogs(prev => [...prev, parsed.log]);
                if (parsed.error) setError(parsed.error);
                if (parsed.status === 'completed' || parsed.status === 'training_complete') setResults(parsed);
            });
        } catch (err) { setError(err.message); }
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
