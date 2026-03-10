import { useState, useEffect, useRef } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'stylegan';

export default function StyleGAN() {
    const [datasetData, setDatasetData] = useState('');
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);
    const [logs, setLogs] = useState([]);
    const logsEndRef = useRef(null);

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs]);

    useEffect(() => {
        const cached = localStorage.getItem(`${MODEL_CODE}_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`${MODEL_CODE}_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`${MODEL_CODE}_dataset`);
        }
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
                hyperparams
            };
            const token = localStorage.getItem('aiml_token');
            const response = await fetch(`${constants.API_URL}/stylegan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(bodyPayload)
            });
            
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Failed to start generative process');
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
                                    if (parsed.log) {
                                        setLogs(prev => [...prev, parsed.log]);
                                    }
                                    if (parsed.error) {
                                        setError(parsed.error);
                                    }
                                    if (parsed.status === 'completed' || parsed.status === 'training_complete') {
                                        setResults(parsed);
                                    }
                                } catch (e) {
                                    console.error("Parse stream err:", e);
                                }
                            }
                        }
                    }
                }
            }
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
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['zip']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
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

            {logs.length > 0 && (
                <div className="terminal-log-container" style={{
                    backgroundColor: '#1e1e1e', color: '#00ff00', padding: '15px', 
                    borderRadius: '8px', fontFamily: 'monospace', marginTop: '20px',
                    maxHeight: '300px', overflowY: 'auto', textAlign: 'left',
                    boxShadow: 'inset 0 0 10px rgba(0,0,0,0.5)'
                }}>
                    <h3 style={{ color: '#fff', borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '10px' }}>
                        🖥️ Live Training Console
                    </h3>
                    <div className="log-scroll">
                        {logs.map((log, idx) => (
                            <div key={idx} style={{ margin: '4px 0', fontSize: '13px' }}>
                                <span style={{ color: '#888' }}>[{new Date().toLocaleTimeString()}]</span> {log}
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
                        {results.loss_d != null && <div className="metric-item"><div className="metric-label">Discriminator Loss</div><div className="metric-value">{results.loss_d.toFixed(4)}</div></div>}
                        {results.loss_g != null && <div className="metric-item"><div className="metric-label">Generator Loss</div><div className="metric-value">{results.loss_g.toFixed(4)}</div></div>}
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

                    <p style={{ color: '#aaa', marginTop: '10px' }}>* Models are stored in your personal cloud namespace.</p>
                </div>
            )}

            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}

