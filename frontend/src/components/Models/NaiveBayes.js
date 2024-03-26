/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons'; // Import icons from Font Awesome

export default function NaiveBayes() {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const [results, setResults] = useState({
        confusion_matrix: [],
        predictions: [],
        accuracy: 0,
        precision: 0,
        recall: 0,
        f1_score: 0,
        outputImageUrls: []
    });
    const [datasetData, setDatasetData] = useState('');
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
                dataToSend = { filename: datasetData.filename };
            } else {
                dataToSend = { X: inputData.X, y: inputData.y };
            }

            const response = await fetch(`${constants.API_BASE_URL}/naive-bayes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dataToSend),
            });
            console.log(response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            setResults(data);
            // setShowCarousel(true);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <div>
            <h1>Naive Bayes</h1>
            <ShowDataset onDatasetUpload={handleDatasetUpload} />

            <form onSubmit={handleSubmit}>
                <label>
                    X (comma separated values):
                    <input type="text" name="X" onChange={handleChange} />
                </label>
                <br />
                <label>
                    y (comma separated values):
                    <input type="text" name="y" onChange={handleChange} />
                </label>
                <br />
                <button type="submit">Run</button>
            </form>
            <h2>Results:</h2>
            <p>Confusion Matrix: {results.confusion_matrix.join(', ')}</p>
            <p>Predictions: {results.predictions.join(', ')}</p>
            <p>Accuracy: {results.accuracy}</p>
            <p>Precision: {results.precision}</p>
            <p>Recall: {results.recall}</p>
            <p>F1 Score: {results.f1_score}</p>
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
            <DownloadTrainedModel selectedModel={'naive_bayes'} extension={'.pkl'} />
        </div>
    );
}
