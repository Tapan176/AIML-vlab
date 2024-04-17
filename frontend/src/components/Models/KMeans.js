/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons'; // Import icons from Font Awesome

import '../ModelCss/kMeans.css';

export default function KMeans() {
    const [inputData, setInputData] = useState({ X: [], k: 3 });
    const [results, setResults] = useState({ labels: [], centers: [], silhouette_score: 0, outputImageUrls: [] });
    const [datasetData, setDatasetData] = useState('');
    const [currentImageIndex, setCurrentImageIndex] = useState(0);

    const images = results.outputImageUrls.map(url => `${constants.API_BASE_URL}/${url}?timestamp=${Date.now()}`);

    const prevImage = () => {
        setCurrentImageIndex((prevIndex) => (prevIndex === 0 ? images.length - 1 : prevIndex - 1));
    };

    const nextImage = () => {
        setCurrentImageIndex((prevIndex) => (prevIndex === images.length - 1 ? 0 : prevIndex + 1));
    };

    const handleDatasetUpload = (data) => {
        setDatasetData(data);
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setInputData({ ...inputData, [name]: value.split(',').map(parseFloat) });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            let dataToSend;
            if (datasetData && datasetData.csv_data) {
                dataToSend = { filename: datasetData.filename, k: inputData.k[0] ? inputData.k[0] : 3 };
            } else {
                dataToSend = { X: inputData.X, k: inputData.k[0] ? inputData.k[0] : 3 };
            }
            const response = await fetch(`${constants.API_BASE_URL}/k-means`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dataToSend),
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
            <h1>K-Means Clustering</h1>
            <ShowDataset onDatasetUpload={handleDatasetUpload} />

            <form className="my-4" onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="XInput" className="form-label">
                        Data Points (comma separated values):
                    </label>
                    <input
                        type="text"
                        className="form-control"
                        id="XInput"
                        name="X"
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="kInput" className="form-label">
                        Number of Clusters:
                    </label>
                    <input
                        type="number"
                        className="form-control"
                        id="kInput"
                        name="k"
                        min="1"
                        value={inputData.k}
                        onChange={handleChange}
                    />
                </div>
                <button type="submit" className="btn btn-primary">
                    Run
                </button>
            </form>

            {results.labels.length > 0 && (
                <div className="result-section mt-3">
                    <h2>Results:</h2>
                    <p>Cluster Labels: {results.labels.join(', ')}</p>
                    <p>
                        Cluster Centers: {results.centers.map(center => `[${center.join(', ')}]`).join(', ')}
                    </p>
                    <p>Silhouette Score: {results.silhouette_score}</p>
                </div>
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
                <DownloadModelPredictions selectedModel={'kmeans'} extension={'.csv'} />
                <DownloadTrainedModel selectedModel={'kmeans'} extension={'.pkl'} />
            </div>
        </div>
    );
}
