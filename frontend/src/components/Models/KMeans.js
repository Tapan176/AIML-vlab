/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons'; // Import icons from Font Awesome

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
        <div>
            <h1>K-Means Clustering</h1>
            <ShowDataset onDatasetUpload={handleDatasetUpload} />

            <form onSubmit={handleSubmit}>
                <label>
                    Data Points (comma separated values):
                    <input type="text" name="X" onChange={handleChange} />
                </label>
                <br />
                <label>
                    Number of Clusters:
                    <input type="number" name="k" min="1" value={inputData.k} onChange={handleChange} />
                </label>
                <br />
                <button type="submit">Run</button>
            </form>

            <h2>Results:</h2>
            <p>Cluster Labels: {results.labels.join(', ')}</p>
            <p>Cluster Centers: {results.centers.map(center => `[${center.join(', ')}]`).join(', ')}</p>
            <p>Silhouette Score: {results.silhouette_score}</p>
            <h2>Graph:</h2>
            <div style={{ width: '600px', height: '400px' }}>
                <h1>Output</h1>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <button onClick={prevImage} style={{ border: 'none', backgroundColor: 'transparent' }}>
                        <FontAwesomeIcon icon={faArrowLeft} />
                    </button>
                    <img src={images[currentImageIndex]} alt={`Image ${currentImageIndex + 1}`} style={{ maxWidth: '100%', maxHeight: '100%' }} />
                    <button onClick={nextImage} style={{ border: 'none', backgroundColor: 'transparent' }}>
                        <FontAwesomeIcon icon={faArrowRight} />
                    </button>
                </div>
            </div>
            <DownloadModelPredictions selectedModel={'simple_linear_regression'} extension={'.csv'} />
            <DownloadTrainedModel selectedModel={'kmeans'} extension={'.pkl'} />
        </div>
    );
}
