/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState } from 'react';
import constants from '../../constants';

export default function ShowDataset({ onDatasetUpload }) {
    const [csvData, setCsvData] = useState(null);
    const [imageLinks, setImageLinks] = useState([]);
    const [showDataset, setShowDataset] = useState(false);

    function handleUpload() {
        const fileInput = document.getElementById('formFileMultiple');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a file.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        fetch(`${constants.API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.csv_data) {
                setCsvData(data.csv_data);
                setImageLinks([]);
                onDatasetUpload(data);
            } else if (data.image_links) {
                setImageLinks(data.image_links.map(link => `${constants.API_BASE_URL}/${link}`));
                console.log(imageLinks);
                setCsvData(null);
                onDatasetUpload(data);
            }
            // Set showDataset to true to indicate that the dataset is ready to be displayed
            setShowDataset(true);
        })
        .catch(error => {
            console.error('Error uploading file:', error);
        });
    }

    function handleShow() {
        if (!csvData && imageLinks.length === 0) {
            alert('Please upload a dataset first.');
            return;
        }
        // Toggle showDataset state to display or hide the dataset
        setShowDataset(!showDataset);
    }

    return (
        <div style={{ maxWidth: '100%' }}>
            <h2>Upload Your Dataset</h2>
            <input className="form-control" type="file" id="formFileMultiple" multiple /><br/>
            <button onClick={handleUpload}>Upload Dataset</button>&nbsp;&nbsp;
            <button onClick={handleShow}>{showDataset ? 'Hide Dataset' : 'Show Dataset'}</button>
            {/* Render CSV data if it's available */}
            {showDataset && csvData && (
                <><br /><br />
                <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '200px' }}>
                    <table style={{ minWidth: '100%', tableLayout: 'fixed', border: '1px solid #000' }}>
                        <tr>
                            {/* Display column names */}
                            {Object.keys(csvData[0]).map((columnName, columnIndex) => (
                                <th key={columnIndex} style={{ border: '1px solid #000', padding: '8px' }}>{columnName}</th>
                            ))}
                        </tr>
                        {/* Display data rows */}
                        {csvData.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                                {Object.values(row).map((cell, cellIndex) => (
                                    <td key={cellIndex} style={{ border: '1px solid #000', padding: '8px' }}>{cell}</td>
                                ))}
                            </tr>
                        ))}
                    </table>
                </div></>
            )}
            {/* Render image links if they're available */}
            {showDataset && imageLinks.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', overflowX: 'auto', overflowY: 'auto', maxHeight: '200px', maxWidth: '600px'  }}>
                    {imageLinks.map((link, index) => (
                        <div key={index} style={{ margin: '10px' }}>
                            <img src={link} alt={`Image ${index}`} style={{ width: '200px', height: '200px', objectFit: 'cover' }} />
                        </div>
                    ))}
                </div>
            )}
            {/* {showDataset && imageLinks.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', overflowX: 'auto', overflowY: 'auto', maxHeight: '400px', maxWidth: '450px' }}>
                    {imageLinks.map((link, index) => (
                        // Render pairs of images
                        index % 2 === 0 && ( // Check if it's the first image in a pair
                            <div key={index} style={{ display: 'flex' }}>
                                <div style={{ margin: '10px' }}>
                                    <img src={link} alt={`Image ${index}`} style={{ width: '200px', height: '200px', objectFit: 'cover' }} />
                                </div>
                                {index + 1 < imageLinks.length && ( // Ensure there's a second image in the pair
                                    <div style={{ margin: '10px' }}>
                                        <img src={imageLinks[index + 1]} alt={`Image ${index + 1}`} style={{ width: '200px', height: '200px', objectFit: 'cover' }} />
                                    </div>
                                )}
                            </div>
                        )
                    ))}
                </div>
            )} */}

        </div>
    );
}
// /* eslint-disable jsx-a11y/img-redundant-alt */
// import React, { useState, useRef } from 'react';
// import constants from '../../constants';
// import { List } from 'react-virtualized';
// import Image from './Image';

// export default function ShowDataset({ onDatasetUpload }) {
//     const [csvData, setCsvData] = useState(null);
//     const [imageLinks, setImageLinks] = useState([]);
//     const [showDataset, setShowDataset] = useState(false);
//     const listRef = useRef(null);

//     function handleUpload() {
//         const fileInput = document.getElementById('formFileMultiple');
//         const file = fileInput.files[0];

//         if (!file) {
//             alert('Please select a file.');
//             return;
//         }

//         const formData = new FormData();
//         formData.append('file', file);

//         fetch(`${constants.API_BASE_URL}/upload`, {
//             method: 'POST',
//             body: formData,
//         })
//         .then(response => {
//             if (!response.ok) {
//                 throw new Error('Network response was not ok');
//             }
//             return response.json();
//         })
//         .then(data => {
//             if (data.csv_data) {
//                 setCsvData(data.csv_data);
//                 setImageLinks([]);
//                 onDatasetUpload(data);
//             } else if (data.image_links) {
//                 setImageLinks(data.image_links.map(link => `${constants.API_BASE_URL}/${link}`));
//                 setCsvData(null);
//                 onDatasetUpload(data);
//             }
//             setShowDataset(true); // Set showDataset to true after processing data
//         })
//         .catch(error => {
//             console.error('Error uploading file:', error);
//         });
//     }

//     function handleShow() {
//         if (!csvData && imageLinks.length === 0) {
//             alert('Please upload a dataset first.');
//             return;
//         }
//         setShowDataset(!showDataset); // Toggle showDataset state
//     }

//     // Function to render a single image
//     const imageRenderer = ({ index, style }) => {
//         const firstIndex = index * 2;
//         const secondIndex = firstIndex + 1;

//         // Check if the image links are valid and exist at the specified indices
//         const firstImage = imageLinks[firstIndex];
//         const secondImage = secondIndex < imageLinks.length ? imageLinks[secondIndex] : null;

//         return (
//             <div key={index} style={{ display: 'flex' }}>
//                 {firstImage && (
//                     <Image
//                         src={firstImage}
//                         alt={`Image ${firstIndex}`}
//                         style={{ width: '200px', height: '200px', objectFit: 'cover' }}
//                     />
//                 )}&nbsp;&nbsp;&nbsp;&nbsp;
//                 {secondImage && (
//                     <Image
//                         src={secondImage}
//                         alt={`Image ${secondIndex}`}
//                         style={{ width: '200px', height: '200px', objectFit: 'cover' }}
//                     />
//                 )}
//             </div>
//         );
//     };

//     return (
//         <div style={{ maxWidth: '100%' }}>
//             <h2>Upload Your Dataset</h2>
//             <input className="form-control" type="file" id="formFileMultiple" multiple /><br />
//             <button onClick={handleUpload}>Upload Dataset</button>&nbsp;&nbsp;
//             <button onClick={handleShow}>{showDataset ? 'Hide Dataset' : 'Show Dataset'}</button>

//             {showDataset && (
//                 <>
//                     <br /><br />
//                     {/* Render CSV data if it's available (not virtualized) */}
//                     {csvData && (
//                         <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '200px' }}>
//                             <table style={{ minWidth: '100%', tableLayout: 'fixed', border: '1px solid #000' }}>
//                                 <tbody>
//                                     {csvData.map((row, rowIndex) => (
//                                         <tr key={rowIndex}>
//                                             {Object.values(row).map((cell, cellIndex) => (
//                                                 <td key={cellIndex} style={{ border: '1px solid #000', padding: '8px' }}>{cell}</td>
//                                             ))}
//                                         </tr>
//                                     ))}
//                                 </tbody>
//                             </table>
//                         </div>
//                     )}

//                     {/* Render image links in pairs using react-virtualized List */}
//                     {imageLinks.length > 0 && (
//                         <div style={{ display: 'flex', flexWrap: 'wrap', overflowY: 'auto', maxHeight: '400px', maxWidth: '450px' }}>
//                             <List
//                                 ref={listRef}
//                                 width={600}
//                                 height={200}
//                                 rowCount={Math.ceil(imageLinks.length / 2)}
//                                 rowHeight={250}
//                                 rowRenderer={imageRenderer}
//                             />
//                         </div>
//                     )}
//                 </>
//             )}
//         </div>
//     );
// }
