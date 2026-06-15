import { useState } from 'react';
import { consumeReplayHyperparams } from '../../utils/replaySession';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import useDatasetCache from '../../hooks/useDatasetCache';
import useModelTrain from '../../hooks/useModelTrain';
import { formatMetric } from '../../utils/formatMetric';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'sentiment_analysis';

export default function SentimentAnalysis() {
    const [textColumn, setTextColumn] = useState('');
    const [labelColumn, setLabelColumn] = useState('');
    const [hyperparams, setHyperparams] = useState(() => consumeReplayHyperparams(MODEL_CODE));
    const [infoOpen, setInfoOpen] = useState(false);
    const { datasetData, handleDatasetSelect } = useDatasetCache('sentimentanalysis');
    const { train, loading, error, results } = useModelTrain('/sentiment-analysis');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await train({
                filename: datasetData?.filename,
                text_column: textColumn || undefined,
                label_column: labelColumn || undefined,
                hyperparams,
            });
        } catch (err) { /* error captured by hook */ }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>Sentiment Analysis</h1>
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
                        <input type="text" placeholder="e.g. review" value={textColumn} onChange={(e) => setTextColumn(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>Label Column <small>(auto-detected if empty)</small></label>
                        <input type="text" placeholder="e.g. sentiment" value={labelColumn} onChange={(e) => setLabelColumn(e.target.value)} />
                    </div>
                </div>
                <HyperparamPanel
                    modelCode={MODEL_CODE}
                    hyperparams={hyperparams}
                    onChange={(name, value) => setHyperparams(prev => ({ ...prev, [name]: value }))}
                />
                <button type="submit" className="btn-run" disabled={loading}>{loading ? '⏳ Analyzing...' : '▶ Analyze Sentiment'}</button>
            </form>
            {error && <div className="model-error">❌ {error}</div>}
            {results && (
                <div className="results-card">
                    <h2>Results</h2>
                    <div className="metrics-grid">
                        <div className="metric-item"><div className="metric-label">Accuracy</div><div className="metric-value">{formatMetric(results.accuracy, { percent: true, decimals: 2 })}</div></div>
                        <div className="metric-item"><div className="metric-label">Precision</div><div className="metric-value">{formatMetric(results.precision, { percent: true, decimals: 2 })}</div></div>
                        <div className="metric-item"><div className="metric-label">Recall</div><div className="metric-value">{formatMetric(results.recall, { percent: true, decimals: 2 })}</div></div>
                        <div className="metric-item"><div className="metric-label">F1 Score</div><div className="metric-value">{formatMetric(results.f1_score, { percent: true, decimals: 2 })}</div></div>
                    </div>
                </div>
            )}
            {results && (
                <div className="download-section">
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel="sentiment_analysis" extension=".pkl" sessionId={results.session_id} label="Download" />
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
