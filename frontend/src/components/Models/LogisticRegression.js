/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons'; // Import icons from Font Awesome

import '../ModelCss/logisticRegression.css';

export default function LogisticRegression() {
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

            const response = await fetch(`${constants.API_BASE_URL}/logistic-regression`, {
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
        <div className="container mt-5">
            <h1>Logistic Regression</h1>
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

            {results.confusion_matrix.length > 0 && (
                <div className="result-section mt-3">
                    <h2>Results:</h2>
                    <p>Confusion Matrix: {results.confusion_matrix.join(', ')}</p>
                    <p>Predictions: {results.predictions.join(', ')}</p>
                    <p>Accuracy: {results.accuracy}</p>
                    <p>Precision: {results.precision}</p>
                    <p>Recall: {results.recall}</p>
                    <p>F1 Score: {results.f1_score}</p>
                </div>
            )}

            {results.outputImageUrls.length > 0 && (
                <div className="output-section mt-5">
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
                <DownloadModelPredictions selectedModel={'logistic_regression'} extension={'.csv'} />
                <DownloadTrainedModel selectedModel={'logistic_regression'} extension={'.pkl'} />
            </div>
        </div>
    );
}

// import React, { useState } from 'react';
// import ShowDataset from '../Dataset/ShowDataset';
// import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
// import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
// import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
// import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons';
// import constants from '../../constants';

// import '../ModelCss/logisticRegression.css';

// export default function LogisticRegression() {
//     const [inputData, setInputData] = useState({ X: [], y: [] });
//     const [results, setResults] = useState({
//         confusion_matrix: [],
//         predictions: [],
//         accuracy: 0,
//         precision: 0,
//         recall: 0,
//         f1_score: 0,
//         outputImageUrls: []
//     });
//     const [datasetData, setDatasetData] = useState('');
//     const [currentImageIndex, setCurrentImageIndex] = useState(0);

//     const images = results.outputImageUrls.map(url => `${constants.API_BASE_URL}/${url}?timestamp=${Date.now()}`);

//     const prevImage = () => {
//         setCurrentImageIndex((prevIndex) => (prevIndex === 0 ? images.length - 1 : prevIndex - 1));
//     };

//     const nextImage = () => {
//         setCurrentImageIndex((prevIndex) => (prevIndex === images.length - 1 ? 0 : prevIndex + 1));
//     };

//     const handleDatasetUpload = (data) => {
//         setDatasetData(data);
//     };

//     const handleChange = (e) => {
//         const { name, value } = e.target;
//         setInputData({ ...inputData, [name]: value });
//     };

//     const handleSubmit = async (e) => {
//         e.preventDefault();
//         try {
//             let dataToSend;
//             if (datasetData && datasetData.csv_data) {
//                 dataToSend = { filename: datasetData.filename };
//             } else {
//                 dataToSend = { X: inputData.X.split(','), y: inputData.y.split(',') };
//             }

//             const response = await fetch(`${constants.API_BASE_URL}/logistic-regression`, {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/json',
//                 },
//                 body: JSON.stringify(dataToSend),
//             });
//             if (!response.ok) {
//                 throw new Error('Network response was not ok');
//             }

//             const data = await response.json();
//             setResults(data);
//         } catch (error) {
//             console.error('Error:', error);
//         }
//     };

    // return (
    //     <div className="container mt-5">
    //         <h1>Logistic Regression</h1>
    //         <ShowDataset onDatasetUpload={handleDatasetUpload} />

    //         <form className="my-4" onSubmit={handleSubmit}>
    //             <div className="mb-3">
    //                 <label htmlFor="XInput" className="form-label">X (comma separated values):</label>
    //                 <input type="text" className="form-control" id="XInput" name="X" onChange={handleChange} />
    //             </div>
    //             <div className="mb-3">
    //                 <label htmlFor="yInput" className="form-label">y (comma separated values):</label>
    //                 <input type="text" className="form-control" id="yInput" name="y" onChange={handleChange} />
    //             </div>
    //             <button type="submit" className="btn btn-primary">Run</button>
    //         </form>

    //         <div className="result-section mt-3">
    //             <h2>Results:</h2>
    //             <p>Confusion Matrix: {results.confusion_matrix.join(', ')}</p>
    //             <p>Predictions: {results.predictions.join(', ')}</p>
    //             <p>Accuracy: {results.accuracy}</p>
    //             <p>Precision: {results.precision}</p>
    //             <p>Recall: {results.recall}</p>
    //             <p>F1 Score: {results.f1_score}</p>
    //         </div>

    //         {results.outputImageUrls.length > 0 && (
    //             <div className="output-section mt-5">
    //                 <h2>Graph:</h2>
    //                 <div className="image-carousel d-flex align-items-center justify-content-between">
    //                     <button className="btn btn-link" onClick={prevImage}>
    //                         <FontAwesomeIcon icon={faArrowLeft} />
    //                     </button>
    //                     <img src={images[currentImageIndex]} alt={`Image ${currentImageIndex + 1}`} className="img-fluid" />
    //                     <button className="btn btn-link" onClick={nextImage}>
    //                         <FontAwesomeIcon icon={faArrowRight} />
    //                     </button>
    //                 </div>
    //             </div>
    //         )}

    //         <div className="download-section mt-5">
    //             <DownloadModelPredictions selectedModel={'logistic_regression'} extension={'.csv'} />
    //             <DownloadTrainedModel selectedModel={'logistic_regression'} extension={'.pkl'} />
    //         </div>
    //     </div>
    // );
// }
