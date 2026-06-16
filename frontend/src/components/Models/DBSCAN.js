/* eslint-disable jsx-a11y/img-redundant-alt */
import { useState } from 'react';
import useReplaySession from '../../hooks/useReplaySession';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import HyperparamPanel from '../shared/HyperparamPanel';
import CachedDatasetBadge from '../shared/CachedDatasetBadge';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import ImageCarousel from '../shared/ImageCarousel';
import useDatasetCache from '../../hooks/useDatasetCache';
import useModelTrain from '../../hooks/useModelTrain';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'dbscan';

export default function DBSCAN() {
    const { hyperparams: replayHyperparams, restoredResults } = useReplaySession(MODEL_CODE);
    const [hyperparams, setHyperparams] = useState(replayHyperparams);
    const [infoOpen, setInfoOpen] = useState(false);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);
    const { train, loading, error, results: freshResults } = useModelTrain('/dbscan');
    // Prefer a fresh run's results; otherwise fall back to the replayed
    // (previously completed) session's restored results.
    const results = freshResults || restoredResults;

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await train({ filename: datasetData?.filename, hyperparams });
        } catch (err) { /* error captured by hook */ }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>DBSCAN</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>
            <div className="dataset-section"><ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} initialFilename={datasetData?.filename} />
                <CachedDatasetBadge filename={datasetData?.filename} /></div>
            <form className="model-form" onSubmit={handleSubmit}>
                <HyperparamPanel modelCode={MODEL_CODE} hyperparams={hyperparams} onChange={(n, v) => setHyperparams(p => ({ ...p, [n]: v }))} />
                <button type="submit" className="btn-run" disabled={loading}>{loading ? '⏳ Training...' : '▶ Run Model'}</button>
            </form>
            {error && <div className="model-error">❌ {error}</div>}
            {results && (
                <div className="results-card">
                    <h2>Clustering Results</h2>
                    <div className="metrics-grid">
                        {results.n_clusters != null && <div className="metric-item"><div className="metric-label">Clusters</div><div className="metric-value">{results.n_clusters}</div></div>}
                        {(results.n_noise != null || results.n_noise_points != null) && (
                            <div className="metric-item">
                                <div className="metric-label">Noise Points</div>
                                <div className="metric-value">{results.n_noise ?? results.n_noise_points}</div>
                            </div>
                        )}
                    </div>
                </div>
            )}
            <ImageCarousel images={results?.images || []} modelName="dbscan" />
            {results && (
                <div className="download-section">
                    <DownloadTrainedModel selectedModel="dbscan" extension=".pkl" sessionId={results.session_id} label="Download" />
                    {results.results_zip_drive_id && (
                        <DownloadResultsZip sessionId={results.session_id} />
                    )}
                </div>
            )}
            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
