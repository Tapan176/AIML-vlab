import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

export default function XGBoost() {
    const [datasetData, setDatasetData] = useState('');
    const [nEstimators, setNEstimators] = useState(100);
    const [learningRate, setLearningRate] = useState(0.1);
    const [maxDepth, setMaxDepth] = useState(6);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${constants.API_BASE_URL}/xgboost`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: datasetData?.filename,
                    hyperparams: { n_estimators: nEstimators, learning_rate: learningRate, max_depth: maxDepth },
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
                <h1>XGBoost Classifier</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>
            <div className="dataset-section"><ShowDataset onDatasetUpload={setDatasetData} /></div>
            <form className="model-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Number of Estimators</label>
                        <input type="number" min="10" max="1000" value={nEstimators} onChange={(e) => setNEstimators(parseInt(e.target.value))} />
                    </div>
                    <div className="form-group">
                        <label>Learning Rate</label>
                        <input type="number" step="0.01" min="0.001" max="1.0" value={learningRate} onChange={(e) => setLearningRate(parseFloat(e.target.value))} />
                    </div>
                    <div className="form-group">
                        <label>Max Depth</label>
                        <input type="number" min="1" max="20" value={maxDepth} onChange={(e) => setMaxDepth(parseInt(e.target.value))} />
                    </div>
                </div>
                <button type="submit" className="btn-run" disabled={loading}>{loading ? '⏳ Training...' : '▶ Train Model'}</button>
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
            <div className="download-section"><DownloadTrainedModel selectedModel="xgboost" extension=".pkl" /></div>
            <ModelInfoPanel modelCode="xgboost" isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
