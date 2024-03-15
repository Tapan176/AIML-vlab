/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
// import { Carousel } from 'react-bootstrap';
// import Plot from 'react-plotly.js';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons'; // Import icons from Font Awesome

export default function SimpleLinearRegression () {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const [results, setResults] = useState({ coefficients: [], intercept: 0, predictions: [], outputImageUrls: [] });

    const [datasetData, setDatasetData] = useState('');

    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const images = results.outputImageUrls.length > 0 ? results.outputImageUrls.map(url => `${constants.API_BASE_URL}/${url}`) : [];

    const prevImage = () => {
        setCurrentImageIndex((prevIndex) => (prevIndex === 0 ? images.length - 1 : prevIndex - 1));
    };

    const nextImage = () => {
        setCurrentImageIndex((prevIndex) => (prevIndex === images.length - 1 ? 0 : prevIndex + 1));
    };

    // const [showCarousel, setShowCarousel] = useState(false);
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
            if (datasetData && datasetData.csv_data) {
                // dataToSend = { 
                //   X: Object.values(datasetData.csv_data)[0]?.map(value => parseFloat(value)),
                //   y: Object.values(datasetData.csv_data)[1]?.map(value => parseFloat(value))
                // };
                dataToSend = { filename: datasetData.filename };
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
            // setShowCarousel(true);
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
            {/* <h2>Graph:</h2>
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
            /> */}
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
            {/* {showCarousel && ( */}
                {/* <div> */}
                    {/* <h2>Image Carousel:</h2> */}
                    {/* <Carousel> */}
                        {/* Map over your images and create Carousel.Item for each image */}
                        {/* {inputData.X.map((x, index) => ( */}
                            {/* <Carousel.Item key={index}> */}
                                {/* <img */}
                                    {/* className="d-block w-100" */}
                                    {/* src={`url/to/your/image/${x}`} // Replace this with your image URL */}
                                    {/* alt={`Image ${index + 1}`} */}
                                {/* /> */}
                            {/* </Carousel.Item> */}
                        {/* ))} */}
                    {/* </Carousel> */}
                {/* </div> */}
            {/* )} */}
        </div>
    );
};
