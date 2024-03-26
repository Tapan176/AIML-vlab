/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
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
        <div>
            <h1>DBSCAN Clustering</h1>
            <ShowDataset onDatasetUpload={handleDatasetUpload} />
            <form onSubmit={handleSubmit}>
                <label>
                    X (comma separated values):
                    <input type="text" name="X" onChange={handleChange} />
                </label>
                <br />
                <label>
                    Epsilon (eps):
                    <input type="text" name="eps" value={inputData.eps} onChange={handleChange} />
                </label>
                <br />
                <label>
                    Min Samples:
                    <input type="text" name="min_samples" value={inputData.min_samples} onChange={handleChange} />
                </label>
                <br />
                <button type="submit">Run</button>
            </form>
            <h2>Results:</h2>
            <p>Labels: {results.labels.join(', ')}</p>
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
            <DownloadTrainedModel selectedModel={'dbscan'} extension={'.pkl'} />
        </div>
    );
}
