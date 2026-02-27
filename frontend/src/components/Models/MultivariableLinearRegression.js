/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadResultsZip from '../DownloadResultsZip/DownloadResultsZip';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import HyperparamPanel from '../shared/HyperparamPanel';
import ModelInfoPanel from '../shared/ModelInfoPanel';
import '../ModelCss/ModelPage.css';

const MODEL_CODE = 'multivariable_linear_regression';

export default function MultivariableLinearRegression() {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const [hyperparams, setHyperparams] = useState({});
    const [results, setResults] = useState(null);
    const [datasetData, setDatasetData] = useState('');
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [infoOpen, setInfoOpen] = useState(false);


    useEffect(() => {
        const cached = localStorage.getItem(`multivariable_linear_regression_dataset`);
        if (cached) {
            try { setDatasetData(JSON.parse(cached)); } catch(e) {}
        }
    }, []);

    const handleDatasetSelect = (data) => {
        setDatasetData(data);
        if (data && data.filename) {
            localStorage.setItem(`multivariable_linear_regression_dataset`, JSON.stringify(data));
        } else {
            localStorage.removeItem(`multivariable_linear_regression_dataset`);
        }
    };
    const images = results?.outputImageBase64?.length > 0 ? results.outputImageBase64 : (results?.outputImageUrls?.map(url => `${constants.API_BASE_URL}/${url}?timestamp=${Date.now()}`) || []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setInputData({ ...inputData, [name]: value.split(',').map(parseFloat) });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            let dataToSend;
            if (datasetData && datasetData.filename) {
                dataToSend = { filename: datasetData.filename, hyperparams };
            } else {
                dataToSend = { X: inputData.X, y: inputData.y, hyperparams };
            }
            const response = await fetch(`${constants.API_BASE_URL}/multivariable-linear-regression`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(localStorage.getItem('aiml_token') ? { 'Authorization': `Bearer ${localStorage.getItem('aiml_token')}` } : {}) },
                body: JSON.stringify(dataToSend),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Request failed');
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
                <h1>Multivariable Linear Regression</h1>
                <button className="btn-info-toggle" onClick={() => setInfoOpen(true)}>📖 Info</button>
            </div>

            <div className="dataset-section">
                <ShowDataset onDatasetUpload={handleDatasetSelect} allowedTypes={['csv']} />
                {datasetData && datasetData.filename && (
                    <div style={{ marginTop: '10px', color: '#34c759' }}>
                        ✓ Cached dataset: <strong>{datasetData.filename}</strong>
                    </div>
                )}
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
                        {results.MAE != null && <div className="metric-item"><div className="metric-label">MAE</div><div className="metric-value">{results.MAE.toFixed(4)}</div></div>}
                        {results.MSE != null && <div className="metric-item"><div className="metric-label">MSE</div><div className="metric-value">{results.MSE.toFixed(4)}</div></div>}
                        {results.R2 != null && <div className="metric-item"><div className="metric-label">RÂ² Score</div><div className="metric-value">{results.R2.toFixed(4)}</div></div>}
                    </div>
                </div>
            )}

            {images.length > 0 && (
                <div className="output-section">
                    <h2>Visualizations</h2>
                    <div className="image-carousel">
                        <button type="button" className="carousel-btn" onClick={() => setCurrentImageIndex(i => i === 0 ? images.length - 1 : i - 1)}><FontAwesomeIcon icon={faArrowLeft} /></button>
                        <img src={images[currentImageIndex]} alt={`Output ${currentImageIndex + 1}`} />
                        <button type="button" className="carousel-btn" onClick={() => setCurrentImageIndex(i => i === images.length - 1 ? 0 : i + 1)}><FontAwesomeIcon icon={faArrowRight} /></button>
                    </div>
                </div>
            )}

            {results && (
                <div className="download-section">
                    <DownloadModelPredictions selectedModel="multivariable_linear_regression" extension=".csv" />
                    {(results.trained_model_drive_id || !results.session_id) && (
                        <DownloadTrainedModel selectedModel="multivariable_linear_regression" extension=".pkl" sessionId={results.session_id} label="Download" />
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


