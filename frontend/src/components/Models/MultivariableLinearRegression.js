import React, { useState } from 'react';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';

export default function MultivariableLinearRegression() {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const [results, setResults] = useState({ coefficients: [], intercept: 0, predictions: [], evaluation_metrics: {}, outputImageUrls: [] });

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
        <div>
            <h1>Multivariable Linear Regression</h1>
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
            <p>Coefficients: {results.coefficients.join(', ')}</p>
            <p>Intercept: {results.intercept}</p>
            <p>Predictions: {results.predictions.join(', ')}</p>
            <h2>Evaluation Metrics:</h2>
            <p>Mean Absolute Error (MAE): {results.evaluation_metrics.MAE}</p>
            <p>Mean Squared Error (MSE): {results.evaluation_metrics.MSE}</p>
            <p>R-squared (R2) Score: {results.evaluation_metrics.R2}</p>
            <h2>Graph:</h2>
            {results.outputImageUrls.map((url, index) => (
                <img key={index} src={`${constants.API_BASE_URL}/${url}`} alt={`Graph ${index + 1}`} style={{ maxWidth: '100%', maxHeight: '100%' }} />
            ))}
            <DownloadTrainedModel selectedModel={'multivariable_linear_regression'} extension={'.pkl'} />
        </div>
    );
}
