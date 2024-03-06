import React, { useState } from 'react';

export default function ShowDataset({ onDatasetUpload }) {
    const [csvData, setCsvData] = useState(null);
    const [showDataset, setShowDataset] = useState(false);

    function handleUpload() {
        const fileInput = document.getElementById('formFileMultiple');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a file.');
            return;
        }

        const reader = new FileReader();

        reader.onload = function(event) {
            const fileContent = event.target.result;
            // Save the uploaded file content
            setCsvData(fileContent);
            // Set showDataset to true to indicate that the dataset is ready to be displayed
            setShowDataset(true);

            // Parse CSV content and transform it into an array of objects
            const rows = fileContent.split('\n');
            const headers = rows[0].split(',');
            const data = headers.reduce((obj, header) => {
                obj[header.trim()] = [];
                return obj;
            }, {});

            rows.slice(1).forEach(row => {
                const rowData = row.split(',');
                headers.forEach((header, index) => {
                    if (rowData[index]) {
                        data[header.trim()].push(rowData[index].trim());
                    }
                });
            });

            // Pass the fileContent to the parent component
            onDatasetUpload({ csvData: data });
        };

        reader.onerror = function(event) {
            console.error('File could not be read! Code ' + event.target.error.code);
        };

        reader.readAsText(file);
    }

    function handleShow() {
        if (!csvData) {
            alert('Please upload a dataset first.');
            return;
        }
        // Toggle showDataset state to display or hide the dataset
        setShowDataset(!showDataset);
    }

    return (
        <div style={{ maxWidth: '50%' }}>
            <h2>Upload Your Dataset</h2>
            <input className="form-control" type="file" id="formFileMultiple" multiple />
            <button onClick={handleUpload}>Upload Dataset</button>
            <button onClick={handleShow}>{showDataset ? 'Hide Dataset' : 'Show Dataset'}</button>
            {/* Render CSV data if it's available */}
            {showDataset && csvData && (
                <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '200px' }}>
                    <table style={{ minWidth: '100%', tableLayout: 'fixed', border: '1px solid #000' }}>
                        {csvData.split('\n').map((row, index) => (
                            <tr key={index}>
                                {row.split(',').map((cell, cellIndex) => (
                                    <td key={cellIndex} style={{ border: '1px solid #000', padding: '8px' }}>{cell}</td>
                                ))}
                            </tr>
                        ))}
                    </table>
                </div>
            )}
        </div>
    );
}
