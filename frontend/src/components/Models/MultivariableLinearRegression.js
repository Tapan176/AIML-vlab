/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';

import '../ModelCss/multivariableLinearRegression.css';

export default function MultivariableLinearRegression() {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const [results, setResults] = useState({ coefficients: [], intercept: 0, predictions: [], evaluation_metrics: {}, outputImageUrls: [] });

    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    // const images = results.outputImageUrls.length > 0 ? results.outputImageUrls.map(url => `${constants.API_BASE_URL}/${url}?timestamp=${Date.now()}`) : [];
    const images = results.outputImageUrls.map(url => `${constants.API_BASE_URL}/${url}?timestamp=${Date.now()}`);

    const prevImage = () => {
        setCurrentImageIndex((prevIndex) => (prevIndex === 0 ? images.length - 1 : prevIndex - 1));
    };

    const nextImage = () => {
        setCurrentImageIndex((prevIndex) => (prevIndex === images.length - 1 ? 0 : prevIndex + 1));
    };

    const handleDatasetUpload = (data) => {
        setInputData({
            ...inputData,
            X: data.X || [],
            y: data.y || []
        });
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setInputData({
            ...inputData,
            [name]: value.split(',').map(parseFloat)
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${constants.API_BASE_URL}/multivariable-linear-regression`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(inputData),
            });
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            setResults(data);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <div className="container mt-5">
            <h1>Multivariable Linear Regression</h1>
            <ShowDataset onDatasetUpload={handleDatasetUpload} />

            <form className="my-4" onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="XInput" className="form-label">X (comma separated values):</label>
                    <input type="text" className="form-control" id="XInput" name="X" onChange={handleChange} />
                </div>
                <div className="mb-3">
                    <label htmlFor="yInput" className="form-label">y (comma separated values):</label>
                    <input type="text" className="form-control" id="yInput" name="y" onChange={handleChange} />
                </div>
                <button type="submit" className="btn btn-primary">Run</button>
            </form>

            {results.coefficients.length > 0 && (
                <><div className="result-section mt-3">
                    <h2>Results:</h2>
                    <p>Coefficients: {results.coefficients.join(', ')}</p>
                    <p>Intercept: {results.intercept}</p>
                    <p>Predictions: {results.predictions.join(', ')}</p>
                </div>

                <div className="evaluation-metrics mt-3">
                    <h2>Evaluation Metrics:</h2>
                    <p>Mean Absolute Error (MAE): {results.evaluation_metrics.MAE}</p>
                    <p>Mean Squared Error (MSE): {results.evaluation_metrics.MSE}</p>
                    <p>R-squared (R2) Score: {results.evaluation_metrics.R2}</p>
                </div></>
            )}

            {results.outputImageUrls.length > 0 && (
                <div className="graph-section mt-3">
                    <h2>Output</h2>
                    <div className="image-carousel d-flex align-items-center justify-content-between">
                        <button className="btn btn-link" onClick={prevImage}>
                            <FontAwesomeIcon icon={faArrowLeft} />
                        </button>
                        <img src={images[currentImageIndex]} alt={`Image ${currentImageIndex + 1}`} className="img-fluid" />
                        <button className="btn btn-link" onClick={nextImage}>
                            <FontAwesomeIcon icon={faArrowRight} />
                        </button>
                    </div>
                </div>
            )}

            <div className="download-section mt-3">
                <DownloadModelPredictions selectedModel={'multivariable_linear_regression'} extension={'.csv'} />
                <DownloadTrainedModel selectedModel={'multivariable_linear_regression'} extension={'.pkl'} />
            </div>
        </div>
    );
}
