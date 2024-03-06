import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';

export default function SimpleLinearRegression () {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const [results, setResults] = useState({ coefficients: [], intercept: 0, predictions: [] });

    const [datasetData, setDatasetData] = useState({ csvData: null });
    // console.log(inputData);
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
            if (datasetData && datasetData.csvData) {
                dataToSend = { 
                  X: Object.values(datasetData.csvData)[0]?.map(value => parseFloat(value)),
                  y: Object.values(datasetData.csvData)[1]?.map(value => parseFloat(value))
                };
            } else {
                dataToSend = { X: inputData.X, y: inputData.y };
            }
            console.log(dataToSend);

            const response = await fetch(`${constants.API_BASE_URL}/linear-regression`, {
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
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <div>
            <h1>Simple Linear Regression</h1>
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
            <h2>Graph:</h2>
            <Plot
              data={[
                  {
                      x: (datasetData && datasetData.csvData && Object.values(datasetData.csvData)[0]) ? 
                          Object.values(datasetData.csvData)[0].map(value => parseFloat(value)) : 
                          inputData.X,
                      y: (datasetData && datasetData.csvData && Object.values(datasetData.csvData)[1]) ? 
                          Object.values(datasetData.csvData)[1].map(value => parseFloat(value)) : 
                          inputData.y,
                      type: 'scatter',
                      mode: 'markers+lines',
                      marker: { color: 'blue' },
                  },
              ]}
              layout={{ width: 600, height: 400, title: 'Linear Regression Prediction' }}
            />
        </div>
    );
};
