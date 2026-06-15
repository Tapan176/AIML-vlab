/* eslint-disable jsx-a11y/img-redundant-alt */
import { useState } from 'react';
import { consumeReplayHyperparams } from '../../utils/replaySession';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import ImageCarousel from '../shared/ImageCarousel';
import useDatasetCache from '../../hooks/useDatasetCache';
import useModelTrain from '../../hooks/useModelTrain';
import { formatMetric } from '../../utils/formatMetric';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'random_forest';

export default function RandomForest() {
    const [hyperparams, setHyperparams] = useState(() => consumeReplayHyperparams(MODEL_CODE));
    const [infoOpen, setInfoOpen] = useState(false);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);
    const { train, loading, error, results } = useModelTrain('/random-forest');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await train({ filename: datasetData?.filename, hyperparams });
        } catch (err) { /* error captured by hook */ }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>Random Forest</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>
            <div className="dataset-section"><ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}</div>
            <form className="model-form" onSubmit={handleSubmit}>
                <HyperparamPanel modelCode={MODEL_CODE} hyperparams={hyperparams} onChange={(n, v) => setHyperparams(p => ({ ...p, [n]: v }))} />
                <button type="submit" className="btn-run" disabled={loading}>{loading ? '⏳ Training...' : '▶ Run Model'}</button>
            </form>
            {error && <div className="model-error">❌ {error}</div>}
            {results && (
                <div className="results-card">
                    <h2>Classification Results</h2>
                    <div className="metrics-grid">
                        <div className="metric-item"><div className="metric-label">Accuracy</div><div className="metric-value">{formatMetric(results.accuracy, { percent: true, decimals: 2 })}</div></div>
                        <div className="metric-item"><div className="metric-label">Precision</div><div className="metric-value">{formatMetric(results.precision, { percent: true, decimals: 2 })}</div></div>
                        <div className="metric-item"><div className="metric-label">Recall</div><div className="metric-value">{formatMetric(results.recall, { percent: true, decimals: 2 })}</div></div>
                        <div className="metric-item"><div className="metric-label">F1 Score</div><div className="metric-value">{formatMetric(results.f1_score, { percent: true, decimals: 2 })}</div></div>
                    </div>
                </div>
            )}
            <ImageCarousel images={results?.images || []} modelName="random_forest" />
            {results && (
                <div className="download-section">
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel="random_forest" extension=".pkl" sessionId={results.session_id} label="Download" />
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
