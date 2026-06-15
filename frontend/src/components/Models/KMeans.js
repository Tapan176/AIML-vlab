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

const MODEL_CODE = 'k_means';

export default function KMeans() {
    const [hyperparams, setHyperparams] = useState(() => consumeReplayHyperparams(MODEL_CODE));
    const [infoOpen, setInfoOpen] = useState(false);
    const { datasetData, handleDatasetSelect } = useDatasetCache(MODEL_CODE);
    const { train, loading, error, results } = useModelTrain('/k-means');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await train({ filename: datasetData?.filename, hyperparams });
        } catch (err) { /* error captured by hook */ }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>K-Means Clustering</h1>
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
                    <h2>Clustering Results</h2>
                    <div className="metrics-grid">
                        {results.n_clusters != null && <div className="metric-item"><div className="metric-label">Clusters</div><div className="metric-value">{results.n_clusters}</div></div>}
                        <div className="metric-item"><div className="metric-label">Inertia</div><div className="metric-value">{formatMetric(results.inertia, { decimals: 2 })}</div></div>
                    </div>
                </div>
            )}
            <ImageCarousel images={results?.images || []} modelName="k_means" />
            {results && (
                <div className="download-section">
                    <DownloadTrainedModel selectedModel="k_means" extension=".pkl" sessionId={results.session_id} label="Download" />
                    {results.results_zip_drive_id && (
                        <DownloadResultsZip sessionId={results.session_id} />
                    )}
                </div>
            )}
            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
