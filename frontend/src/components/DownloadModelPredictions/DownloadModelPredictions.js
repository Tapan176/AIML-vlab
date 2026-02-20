import React from 'react';
import constants from '../../constants';

export default function DownloadModelPredictions({ selectedModel, extension }) {
    const downloadModelPredictions = async () => {
        try {
            const response = await fetch(
                `${constants.API_BASE_URL}/download-model-predictions?model_name=${selectedModel}&extension=${extension}`
            );
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${selectedModel}${extension}`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading predictions:', error);
        }
    };

    return (
        <button className="btn-download" onClick={downloadModelPredictions}>
            📊 Download Predictions ({extension})
        </button>
    );
}
