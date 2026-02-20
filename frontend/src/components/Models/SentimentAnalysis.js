import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

export default function SentimentAnalysis() {
    const [datasetData, setDatasetData] = useState('');
    const [textColumn, setTextColumn] = useState('');
    const [labelColumn, setLabelColumn] = useState('');
    const [maxFeatures, setMaxFeatures] = useState(5000);
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${constants.API_BASE_URL}/sentiment-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: datasetData?.filename,
                    text_column: textColumn || undefined,
                    label_column: labelColumn || undefined,
                    hyperparams: { max_features: maxFeatures },
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
                <h1>Sentiment Analysis</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>
            <div className="dataset-section"><ShowDataset onDatasetUpload={setDatasetData} /></div>
            <form className="model-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label>Text Column <small>(auto-detected if empty)</small></label>
                        <input type="text" placeholder="e.g. review" value={textColumn} onChange={(e) => setTextColumn(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>Label Column <small>(auto-detected if empty)</small></label>
                        <input type="text" placeholder="e.g. sentiment" value={labelColumn} onChange={(e) => setLabelColumn(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>Max Features (TF-IDF)</label>
                        <input type="number" min="100" max="50000" value={maxFeatures} onChange={(e) => setMaxFeatures(parseInt(e.target.value))} />
                    </div>
                </div>
                <button type="submit" className="btn-run" disabled={loading}>{loading ? '⏳ Analyzing...' : '▶ Analyze Sentiment'}</button>
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
            <div className="download-section"><DownloadTrainedModel selectedModel="sentiment_analysis" extension=".pkl" /></div>
            <ModelInfoPanel modelCode="sentiment_analysis" isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
