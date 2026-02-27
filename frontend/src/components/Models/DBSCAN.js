/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'dbscan';

export default function DBSCAN() {
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [datasetData, setDatasetData] = useState('');
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);


    useEffect(() => {
        const cached = localStorage.getItem(`dbscan_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`dbscan_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`dbscan_dataset`);
        }
    };
    const images = results?.outputImageBase64?.length > 0 ? results.outputImageBase64 : (results?.outputImageUrls?.map(url => `${constants.API_BASE_URL}/${url}?timestamp=${Date.now()}`) || []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await fetch(`${constants.API_BASE_URL}/dbscan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(localStorage.getItem('aiml_token') ? { 'Authorization': `Bearer ${localStorage.getItem('aiml_token')}` } : {}) },
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
                <h1>DBSCAN</h1>
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
                        {results.n_noise != null && <div className="metric-item"><div className="metric-label">Noise Points</div><div className="metric-value">{results.n_noise}</div></div>}
                    </div>
                </div>
            )}
            {images.length > 0 && (
                <div className="output-section">
                    <h2>Cluster Visualization</h2>
                    <div className="image-carousel">
                        <button type="button" className="carousel-btn" onClick={() => setCurrentImageIndex(i => i === 0 ? images.length - 1 : i - 1)}><FontAwesomeIcon icon={faArrowLeft} /></button>
                        <img src={images[currentImageIndex]} alt={`Output ${currentImageIndex + 1}`} />
                        <button type="button" className="carousel-btn" onClick={() => setCurrentImageIndex(i => i === images.length - 1 ? 0 : i + 1)}><FontAwesomeIcon icon={faArrowRight} /></button>
                    </div>
                </div>
            )}
            {/* DBSCAN has no trained model to download */}
            <ModelInfoPanel modelCode={MODEL_CODE} isOpen={infoOpen} onClose={() => setInfoOpen(false)} />
        </div>
    );
}

