/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'logistic_regression';

export default function LogisticRegression() {
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [datasetData, setDatasetData] = useState('');
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);


    useEffect(() => {
        const cached = localStorage.getItem(`logistic_regression_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`logistic_regression_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`logistic_regression_dataset`);
        }
    };
    const images = results?.outputImageUrls?.map(url => `${constants.API_BASE_URL}/${url}?timestamp=${Date.now()}`) || [];

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${constants.API_BASE_URL}/logistic-regression`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: datasetData?.filename, hyperparams }),
            });
            if (!response.ok) { const err = await response.json(); throw new Error(err.error || 'Failed'); }
            setResults(await response.json());
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    };

    return (
        <div className="model-page">
            <div className="model-header">
                <h1>Logistic Regression</h1>
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
                        {results.accuracy != null && <div className="metric-item"><div className="metric-label">Accuracy</div><div className="metric-value">{(results.accuracy * 100).toFixed(2)}%</div></div>}
                        {results.precision != null && <div className="metric-item"><div className="metric-label">Precision</div><div className="metric-value">{(results.precision * 100).toFixed(2)}%</div></div>}
                        {results.recall != null && <div className="metric-item"><div className="metric-label">Recall</div><div className="metric-value">{(results.recall * 100).toFixed(2)}%</div></div>}
                        {results.f1_score != null && <div className="metric-item"><div className="metric-label">F1 Score</div><div className="metric-value">{(results.f1_score * 100).toFixed(2)}%</div></div>}
                    </div>
                </div>
            )}
            {images.length > 0 && (
                <div className="output-section">
                    <h2>Confusion Matrix</h2>
                    <div className="image-carousel">
                        <button type="button" className="carousel-btn" onClick={() => setCurrentImageIndex(i => i === 0 ? images.length - 1 : i - 1)}><FontAwesomeIcon icon={faArrowLeft} /></button>
                        <img src={images[currentImageIndex]} alt={`Output ${currentImageIndex + 1}`} />
                        <button type="button" className="carousel-btn" onClick={() => setCurrentImageIndex(i => i === images.length - 1 ? 0 : i + 1)}><FontAwesomeIcon icon={faArrowRight} /></button>
                    </div>
                </div>
            )}
            <div className="download-section">
                <DownloadTrainedModel selectedModel="logistic_regression" extension=".pkl" />
            </div>
            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}
