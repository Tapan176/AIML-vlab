import React from 'react';
import { Button } from 'react-bootstrap';
import constants from '../../constants';

export default function DownloadTrainedModel({ selectedModel, extension }) {
  const downloadTrainedModel = async () => {
    try {
      const response = await fetch(`${constants.API_BASE_URL}/download-trained-model?model_name=${selectedModel}&extension=${extension}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedModel}${extension}`); // Use selected model name and extension for the file name
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <Button variant="info" onClick={downloadTrainedModel}>Download Trained Model</Button>
  );
}
