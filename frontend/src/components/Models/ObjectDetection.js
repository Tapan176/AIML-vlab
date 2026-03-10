import { useState, useEffect } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'yolo';

export default function ObjectDetection() {
    const [datasetData, setDatasetData] = useState('');
    const [classMode, setClassMode] = useState('detection');
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);
    const [logs, setLogs] = useState([]);

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
                hyperparams,
                classMode: classMode,
            };

            const response = await fetch(`${constants.API_URL}/yolo`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('aiml_token')}`
                },
                body: JSON.stringify(bodyPayload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Training failed');
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
                <h1>YOLOv8 (Object Detection)</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['zip']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached YOLO format directory: <strong>{datasetData.filename}</strong>
                    </div>
                )}
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Architecture Task</label>
                        <select value={classMode} onChange={(e) => setClassMode(e.target.value)}>
                            <option value="detection">Bounding Box Detection</option>
                            <option value="segmentation">Instance Segmentation</option>
                        </select>
                    </div>
                </div>

                <HyperparamPanel
                    modelCode={MODEL_CODE}
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                />

                <button type="submit" className="btn-run" disabled={loading} style={{ marginTop: 16 }}>
                    {loading ? '⏳ Compiling Architecture...' : '▶ Train YOLO'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {logs.length > 0 && (
                <div className="terminal-container" style={{ marginTop: '20px', background: '#1e1e1e', color: '#00ff00', padding: '15px', borderRadius: '8px', fontFamily: 'monospace', height: '300px', overflowY: 'auto' }}>
                    <div style={{ borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '10px', color: '#888' }}>
                        🖥️ Live Training Console
                    </div>
                    {logs.map((log, index) => (
                        <div key={index}>{log}</div>
                    ))}
                    {loading && <div className="cursor-blink" style={{ marginTop: '10px' }}>_</div>}
                </div>
            )}

            {results && (
                <div className="results-card">
                    <h2>Training Results</h2>
                    {results.message && <p>{results.message}</p>}
                    <div className="metrics-grid">
                        {results.map50 != null && <div className="metric-item"><div className="metric-label">mAP50</div><div className="metric-value">{(results.map50 * 100).toFixed(2)}%</div></div>}
                        {results.loss != null && <div className="metric-item"><div className="metric-label">Loss</div><div className="metric-value">{results.loss.toFixed(4)}</div></div>}
                    </div>
                </div>
            )}

            {results && (
                <div className="download-section" style={{ marginTop: '20px' }}>
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel={MODEL_CODE} extension=".pt" sessionId={results.session_id} label="Download" />
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



