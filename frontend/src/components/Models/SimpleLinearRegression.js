/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
// import { Carousel } from 'react-bootstrap';
import Plot from 'react-plotly.js';
import constants from '../../constants';
import ShowDataset from '../Dataset/ShowDataset';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowLeft, faArrowRight } from '@fortawesome/free-solid-svg-icons'; // Import icons from Font Awesome

export default function SimpleLinearRegression () {
    const [inputData, setInputData] = useState({ X: [], y: [] });
    const [results, setResults] = useState({ coefficients: [], intercept: 0, predictions: [] });

    const [datasetData, setDatasetData] = useState({ csvData: null });

    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const images = [
        'https://imgs.search.brave.com/MZcVw_uqMRXrrCdbi3wOUlSNxfZBENpSMzqYwLyE28c/rs:fit:500:0:0/g:ce/aHR0cHM6Ly93d3cu/aXN0b2NrcGhvdG8u/Y29tL3Jlc291cmNl/cy9pbWFnZXMvSG9t/ZVBhZ2UvRm91clBh/Y2svQzItUGhvdG9z/LWlTdG9jay0xMzU2/MTk3Njk1LmpwZw',
        'https://imgs.search.brave.com/BMuYABP7oP4l8HymmSOQIH30nF_YQMtJm-y7Bz-vc6Q/rs:fit:500:0:0/g:ce/aHR0cHM6Ly9idXJz/dC5zaG9waWZ5Y2Ru/LmNvbS9waG90b3Mv/dHdvLXRvbmUtaW5r/LWNsb3VkLmpwZz93/aWR0aD0xMDAwJmZv/cm1hdD1wanBnJmV4/aWY9MCZpcHRjPTA',
        'https://imgs.search.brave.com/Q5Z4-8Oz80F04pBk_PLfXcLcMXzGPX28h-Cl2eUk-OM/rs:fit:500:0:0/g:ce/aHR0cHM6Ly9pbWFn/ZXMuY3RmYXNzZXRz/Lm5ldC9ocmx0eDEy/cGw4aHEvNmJpNndL/SU01RERNNVUxUHRH/VkZjUC8xYzdmY2U2/ZGUzM2JiNjU3NTU0/OGE2NDZmZjliMDNh/YS9uYXR1cmUtcGhv/dG9ncmFwaHktcGlj/dHVyZXMuanBnP2Zp/dD1maWxsJnc9NjAw/Jmg9MTIwMA',
        'https://imgs.search.brave.com/Xw3NFxb1mDLhRHiFwZ6y4pqYJMU3dRW84i1nhdwXG8Q/rs:fit:500:0:0/g:ce/aHR0cHM6Ly9pbWFn/ZXMuY3RmYXNzZXRz/Lm5ldC9ocmx0eDEy/cGw4aHEvNTU5Nnoy/QkNSOUttVDFLZVJC/ck9RYS80MDcwZmQ0/ZTJmMWExM2Y3MWMy/YzQ2YWZlYjE4ZTQx/Yy9zaHV0dGVyc3Rv/Y2tfNDUxMDc3MDQz/LWhlcm8xLmpwZz9m/aXQ9ZmlsbCZ3PTYw/MCZoPTEyMDA',
        'https://imgs.search.brave.com/DhZ08alk6eRZuS4j5NkvQTGR9ENMJvCqYfdM9L0QqQg/rs:fit:500:0:0/g:ce/aHR0cHM6Ly9idXJz/dC5zaG9waWZ5Y2Ru/LmNvbS9waG90b3Mv/dGFubmVkLXNhbmQt/ZHVuZXMtc3Vycm91/bmRlZC1hbi1vcGVu/LXJlc2Vydm9pci5q/cGc_d2lkdGg9MTAw/MCZmb3JtYXQ9cGpw/ZyZleGlmPTAmaXB0/Yz0w',
    ];

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
