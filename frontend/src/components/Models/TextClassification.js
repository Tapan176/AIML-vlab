import React, { useState, useEffect } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

export default function TextClassification() {
    const [datasetData, setDatasetData] = useState('');
    const [textColumn, setTextColumn] = useState('');
    const [labelColumn, setLabelColumn] = useState('');
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);


    useEffect(() => {
        const cached = localStorage.getItem(`textclassification_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`textclassification_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`textclassification_dataset`);
        }
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${constants.API_BASE_URL}/text-classification`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(localStorage.getItem('aiml_token') ? { 'Authorization': `Bearer ${localStorage.getItem('aiml_token')}` } : {}) },
                body: JSON.stringify({
                    filename: datasetData?.filename,
                    text_column: textColumn || undefined,
                    label_column: labelColumn || undefined,
                    hyperparams,
                }),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Training failed');
            }
            setResults(await response.json());
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>Text Classification</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>
            <div className="dataset-section"><ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}</div>
            <form className="model-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Text Column <small>(auto-detected if empty)</small></label>
                        <input type="text" placeholder="e.g. text" value={textColumn} onChange={(e) => setTextColumn(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>Label Column <small>(auto-detected if empty)</small></label>
                        <input type="text" placeholder="e.g. category" value={labelColumn} onChange={(e) => setLabelColumn(e.target.value)} />
                    </div>
                </div>
                <HyperparamPanel
                    modelCode="text_classification"
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                />
                <button type="submit" className="btn-run" disabled={loading}>{loading ? '⏳ Classifying...' : '▶ Classify Text'}</button>
            </form>
            {error && <div className="model-error">❌ {error}</div>}
            {results && (
                <div className="results-card">
                    <h2>Results</h2>
                    <div className="metrics-grid">
                        <div className="metric-item"><div className="metric-label">Accuracy</div><div className="metric-value">{(results.accuracy * 100).toFixed(2)}%</div></div>
                        <div className="metric-item"><div className="metric-label">Precision</div><div className="metric-value">{(results.precision * 100).toFixed(2)}%</div></div>
                        <div className="metric-item"><div className="metric-label">Recall</div><div className="metric-value">{(results.recall * 100).toFixed(2)}%</div></div>
                        <div className="metric-item"><div className="metric-label">F1 Score</div><div className="metric-value">{(results.f1_score * 100).toFixed(2)}%</div></div>
                    </div>
                </div>
            )}
            {results && (
                <div className="download-section">
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel="text_classification" extension=".pkl" sessionId={results.session_id} label="Download" />
                    )}
                    {results.results_zip_drive_id && (
                        <DownloadResultsZip sessionId={results.session_id} />
                    )}
                </div>
            )}
            <ModelInfoPanel modelCode="text_classification" isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}


