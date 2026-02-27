import React, { useState, useEffect } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

export default function GradientBoosting() {
    const [datasetData, setDatasetData] = useState('');
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);


    useEffect(() => {
        const cached = localStorage.getItem(`gradientboosting_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`gradientboosting_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`gradientboosting_dataset`);
        }
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${constants.API_BASE_URL}/gradient-boosting`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(localStorage.getItem('aiml_token') ? { 'Authorization': `Bearer ${localStorage.getItem('aiml_token')}` } : {}) },
                body: JSON.stringify({
                    filename: datasetData?.filename,
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
                <h1>Gradient Boosting Classifier</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>
            <div className="dataset-section"><ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}</div>
            <form className="model-form" onSubmit={handleSubmit}>
                <HyperparamPanel
                    modelCode="gradient_boosting"
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                />
                <button type="submit" className="btn-run" disabled={loading}>{loading ? 'â³ Training...' : '▶ Train Model'}</button>
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
                    <DownloadTrainedModel selectedModel="gradient_boosting" extension=".pkl" />
                    <DownloadResultsZip sessionId={results.session_id} />
                </div>
            )}
            <ModelInfoPanel modelCode="gradient_boosting" isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}


