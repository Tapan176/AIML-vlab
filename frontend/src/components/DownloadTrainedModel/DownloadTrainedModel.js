import React from 'react';
import constants from '../../constants';

export default function DownloadTrainedModel({ selectedModel, extension }) {
    const downloadTrainedModel = async () => {
        try {
            const response = await fetch(
                `${constants.API_BASE_URL}/download-trained-model?model_name=${selectedModel}&extension=${extension}`
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
            console.error('Error downloading model:', error);
        }
    };

    return (
        <button className="btn-download" onClick={downloadTrainedModel}>
            📦 Download Trained Model ({extension})
        </button>
    );
}
