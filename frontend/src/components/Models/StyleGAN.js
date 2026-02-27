import React, { useState, useEffect, useRef } from 'react';
import { API_URL } from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'stylegan';

export default function StyleGAN() {
    const [datasetData, setDatasetData] = useState('');
    const [hyperparams, setHyperparams] = useState({
        epochs: 300,
        batch_size: 32,
        z_dim: 256,
        w_dim: 256,
        log_resolution: 10,  // 1024x1024
        learning_rate: 0.00002
    });
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
                hyperparams
            };
            const token = localStorage.getItem('aiml_token');
            const response = await fetch(`${API_URL}/stylegan`, {
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
                                    if (parsed.status === 'completed') {
                                        setResults(parsed);
                                    }
                                } catch (e) {
                                    // Ignore parse chunks issue that might arise from stream split
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

    const handleParamChange = (key, value) => {
        setHyperparams(prev => ({ ...prev, [key]: Number(value) }));
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
                <div className="hidden-layers-section" style={{ padding: '20px', background: 'var(--bg-card)', borderRadius: '12px' }}>
                    <h3 style={{ marginBottom: '15px' }}>⚙️ Training Configuration</h3>
                    <div className="form-grid">
                        <div className="form-group">
                            <label>Epochs</label>
                            <input type="number" value={hyperparams.epochs} onChange={(e) => handleParamChange('epochs', e.target.value)} min="1" max="1000" />
                        </div>
                        <div className="form-group">
                            <label>Batch Size (VRAM Dependent)</label>
                            <input type="number" value={hyperparams.batch_size} onChange={(e) => handleParamChange('batch_size', e.target.value)} min="1" max="128" />
                        </div>
                        <div className="form-group">
                            <label>Latent Dimension Z</label>
                            <input type="number" value={hyperparams.z_dim} onChange={(e) => handleParamChange('z_dim', e.target.value)} min="64" max="1024" />
                        </div>
                        <div className="form-group">
                            <label>Intermediate Latent Dimension W</label>
                            <input type="number" value={hyperparams.w_dim} onChange={(e) => handleParamChange('w_dim', e.target.value)} min="64" max="1024" />
                        </div>
                        <div className="form-group">
                            <label>Log Resolution</label>
                            <select value={hyperparams.log_resolution} onChange={(e) => handleParamChange('log_resolution', e.target.value)}>
                                <option value={6}>64x64 (Log2 6)</option>
                                <option value={7}>128x128 (Log2 7)</option>
                                <option value={8}>256x256 (Log2 8)</option>
                                <option value={9}>512x512 (Log2 9)</option>
                                <option value={10}>1024x1024 (Log2 10)</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Learning Rate</label>
                            <input type="number" step="0.00001" value={hyperparams.learning_rate} onChange={(e) => handleParamChange('learning_rate', e.target.value)} />
                        </div>
                    </div>
                </div>

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
                    
                    <div className="download-section" style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                        {(results.trained_model_drive_id || !results.session_id) && (
                            <DownloadTrainedModel 
                                selectedModel={MODEL_CODE} 
                                extension=".h5" 
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

