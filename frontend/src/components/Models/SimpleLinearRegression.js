/* eslint-disable jsx-a11y/img-redundant-alt */
import { useState } from 'react';
import useReplaySession from '../../hooks/useReplaySession';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import HyperparamPanel from '../shared/HyperparamPanel';
import CachedDatasetBadge from '../shared/CachedDatasetBadge';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import ImageCarousel from '../shared/ImageCarousel';
import useDatasetCache from '../../hooks/useDatasetCache';
import useModelTrain from '../../hooks/useModelTrain';
import { formatMetric } from '../../utils/formatMetric';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'simple_linear_regression';

export default function SimpleLinearRegression() {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const { hyperparams: replayHyperparams, restoredResults } = useReplaySession(MODEL_CODE);
    const [hyperparams, setHyperparams] = useState(replayHyperparams);
    const [infoOpen, setInfoOpen] = useState(false);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);
    const { train, loading, error, results: freshResults } = useModelTrain('/linear-regression');
    // Prefer a fresh run's results; otherwise fall back to the replayed
    // (previously completed) session's restored results.
    const results = freshResults || restoredResults;

    const handleChange = (e) => {
        const { name, value } = e.target;
        setInputData({ ...inputData, [name]: value.split(',').map(parseFloat) });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            let dataToSend;
            if (datasetData && datasetData.filename) {
                dataToSend = { filename: datasetData.filename, hyperparams };
            } else {
                dataToSend = { X: inputData.X, y: inputData.y, hyperparams };
            }
            await train(dataToSend);
        } catch (err) { /* error captured by hook */ }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>Simple Linear Regression</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} initialFilename={datasetData?.filename} />
                <CachedDatasetBadge filename={datasetData?.filename} />
            </div>

            <form className="model-form" onSubmit={handleSubmit}>
                <div className="form-grid">
                    <div className="form-group">
                        <label>X (comma separated)</label>
                        <input type="text" name="X" onChange={handleChange} placeholder="Feature values" />
                    </div>
                    <div className="form-group">
                        <label>y (comma separated)</label>
                        <input type="text" name="y" onChange={handleChange} placeholder="Target values" />
                    </div>
                </div>
                <HyperparamPanel modelCode={MODEL_CODE} hyperparams={hyperparams} onChange={(n, v) => setHyperparams(p => ({ ...p, [n]: v }))} />
                <button type="submit" className="btn-run" disabled={loading}>
                    {loading ? '⏳ Training...' : '▶ Run Model'}
                </button>
            </form>

            {error && <div className="model-error">❌ {error}</div>}

            {results && (
                <div className="results-card">
                    <h2>Regression Results</h2>
                    <div className="metrics-grid">
                        <div className="metric-item"><div className="metric-label">MAE</div><div className="metric-value">{formatMetric(results.MAE)}</div></div>
                        <div className="metric-item"><div className="metric-label">MSE</div><div className="metric-value">{formatMetric(results.MSE)}</div></div>
                        <div className="metric-item"><div className="metric-label">R² Score</div><div className="metric-value">{formatMetric(results.R2)}</div></div>
                    </div>
                </div>
            )}

            <ImageCarousel images={results?.images || []} modelName="simple_linear_regression" />

            {results && (
                <div className="download-section">
                    <DownloadModelPredictions selectedModel="simple_linear_regression" extension=".csv" />
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel="simple_linear_regression" extension=".pkl" sessionId={results.session_id} label="Download" />
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
