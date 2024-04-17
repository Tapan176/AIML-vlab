/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';

export default function DBSCAN() {
    const [inputData, setInputData] = useState({ X: [], eps: 0.5, min_samples: 5 });
    const [results, setResults] = useState({ labels: [], outputImageUrls: [] });
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
                dataToSend = {
                  filename: datasetData.filename,
                  eps: inputData.eps[0] ? inputData.eps[0] : 0.5,
                  min_samples: inputData.min_samples[0] ? inputData.min_samples[0] : 5
                };
            } else {
                dataToSend = {
                  X: inputData.X,
                  eps: inputData.eps[0] ? inputData.eps[0] : 0.5,
                  min_samples: inputData.min_samples[0] ? inputData.min_samples[0] : 5
                };
            }
            const response = await fetch(`${constants.API_BASE_URL}/dbscan`, {
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
            <h1>DBSCAN Clustering</h1>
            <ShowDataset onDatasetUpload={handleDatasetUpload} />

            <form className="my-4" onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label htmlFor="XInput" className="form-label">
                        X (comma separated values):
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
                    <label htmlFor="epsInput" className="form-label">
                        Epsilon (eps):
                    </label>
                    <input
                        type="text"
                        className="form-control"
                        id="epsInput"
                        name="eps"
                        value={inputData.eps}
                        onChange={handleChange}
                    />
                </div>
                <div className="mb-3">
                    <label htmlFor="minSamplesInput" className="form-label">
                        Min Samples:
                    </label>
                    <input
                        type="text"
                        className="form-control"
                        id="minSamplesInput"
                        name="min_samples"
                        value={inputData.min_samples}
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
                    <p>Labels: {results.labels.join(', ')}</p>
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
                <DownloadModelPredictions selectedModel={'dbscan'} extension={'.csv'} />
                <DownloadTrainedModel selectedModel={'dbscan'} extension={'.pkl'} />
            </div>
        </div>
    );
}
