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
import { MODEL_PAGE_CONFIG } from './modelPageConfig';
import '../ModelCss/ModelPage.css';

function renderMetricValue(value, format) {
  switch (format) {
    case 'percent': return formatMetric(value, { percent: true, decimals: 2 });
    case 'dec2': return formatMetric(value, { decimals: 2 });
    case 'raw': return value;
    default: return formatMetric(value);
  }
}

/**
 * Config-driven page shared by all classical models (Phase 6). Behaviour per
 * model comes entirely from MODEL_PAGE_CONFIG[modelCode]; deep-learning /
 * streaming / generative models keep their own bespoke components.
 */
export default function ModelPage({ modelCode }) {
  const config = MODEL_PAGE_CONFIG[modelCode];
  const {
    endpoint,
    title,
    runIdle = '▶ Run Model',
    runBusy = '⏳ Training...',
    heading,
    metrics = [],
    inputMode = 'none',
    textPlaceholder = '',
    labelPlaceholder = '',
    showImages = true,
    hasPredictionsDownload = false,
    alwaysShowModelDownload = false,
    cacheKey = modelCode,
  } = config;

  const [xy, setXy] = useState({ X: [], y: [] });
  const [textColumn, setTextColumn] = useState('');
  const [labelColumn, setLabelColumn] = useState('');
  const { hyperparams: replayHyperparams, restoredResults } = useReplaySession(modelCode);
  const [hyperparams, setHyperparams] = useState(replayHyperparams);
  const [infoOpen, setInfoOpen] = useState(false);
  const { datasetData, handleDatasetSelect } = useDatasetCache(cacheKey);
  const { train, loading, error, results: freshResults } = useModelTrain(endpoint);
  // Prefer a fresh run's results; otherwise fall back to the replayed
  // (previously completed) session's restored results.
  const results = freshResults || restoredResults;

  const handleXyChange = (e) => {
    const { name, value } = e.target;
    setXy((prev) => ({ ...prev, [name]: value.split(',').map(parseFloat) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    let body;
    if (inputMode === 'xy') {
      body = datasetData?.filename
        ? { filename: datasetData.filename, hyperparams }
        : { X: xy.X, y: xy.y, hyperparams };
    } else if (inputMode === 'text-label') {
      body = {
        filename: datasetData?.filename,
        text_column: textColumn || undefined,
        label_column: labelColumn || undefined,
        hyperparams,
      };
    } else {
      body = { filename: datasetData?.filename, hyperparams };
    }
    try {
      await train(body);
    } catch (err) { /* error captured by hook */ }
  };

  return (
    <div className="model-page">
      <div className="model-header">
        <h1>{title}</h1>
        <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
      </div>

      <div className="dataset-section">
        <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} initialFilename={datasetData?.filename} />
        <CachedDatasetBadge filename={datasetData?.filename} />
      </div>

      <form className="model-form" onSubmit={handleSubmit}>
        {inputMode === 'xy' && (
          <div className="form-grid">
            <div className="form-group">
              <label>X (comma separated)</label>
              <input type="text" name="X" onChange={handleXyChange} placeholder="Feature values" />
            </div>
            <div className="form-group">
              <label>y (comma separated)</label>
              <input type="text" name="y" onChange={handleXyChange} placeholder="Target values" />
            </div>
          </div>
        )}
        {inputMode === 'text-label' && (
          <div className="form-grid">
            <div className="form-group">
              <label>Text Column <small>(auto-detected if empty)</small></label>
              <input type="text" placeholder={textPlaceholder} value={textColumn} onChange={(e) => setTextColumn(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Label Column <small>(auto-detected if empty)</small></label>
              <input type="text" placeholder={labelPlaceholder} value={labelColumn} onChange={(e) => setLabelColumn(e.target.value)} />
            </div>
          </div>
        )}
        <HyperparamPanel modelCode={modelCode} hyperparams={hyperparams} onChange={(n, v) => setHyperparams((p) => ({ ...p, [n]: v }))} />
        <button type="submit" className="btn-run" disabled={loading}>{loading ? runBusy : runIdle}</button>
      </form>

      {error && <div className="model-error">❌ {error}</div>}

      {results && (
        <div className="results-card">
          <h2>{heading}</h2>
          <div className="metrics-grid">
            {metrics.map((m) => {
              if (m.cond && !m.cond(results)) return null;
              const value = m.get ? m.get(results) : results[m.key];
              return (
                <div className="metric-item" key={m.label}>
                  <div className="metric-label">{m.label}</div>
                  <div className="metric-value">{renderMetricValue(value, m.format)}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {showImages && <ImageCarousel images={results?.images || []} modelName={modelCode} />}

      {results && (
        <div className="download-section">
          {hasPredictionsDownload && results.predictions_drive_id && (
            <DownloadModelPredictions extension=".csv" sessionId={results.session_id} />
          )}
          {(alwaysShowModelDownload || results.trained_model_drive_id || !results.session_id) && (
            <DownloadTrainedModel selectedModel={modelCode} extension=".pkl" sessionId={results.session_id} label="Download" />
          )}
          {results.results_zip_drive_id && (
            <DownloadResultsZip sessionId={results.session_id} />
          )}
        </div>
      )}

      <ModelInfoPanel modelCode={modelCode} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
    </div>
  );
}
