import React, { useState } from 'react'
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import DownloadModelPredictions from '../DownloadModelPredictions/DownloadModelPredictions';
import ShowDataset from '../Dataset/ShowDataset';

export default function ANN() {
  const [datasetData, setDatasetData] = useState('');

  const trainANNModel = (datasetData) => {
    console.log(datasetData);
  };

  const handleDatasetUpload = (data) => {
    setDatasetData(data);
  };

  return (
    <div className="container mt-5">
      <h1>Artificial Neural Network</h1>
      <ShowDataset onDatasetUpload={handleDatasetUpload} />
      <button className="mt-3" onClick={trainANNModel(datasetData)}>Train ANN Model</button>

      <div className="download-section mt-3">
        <DownloadModelPredictions selectedModel={'ann'} extension={'.csv'} />
        <DownloadTrainedModel selectedModel={'ann'} extension={'.pkl'} />
      </div>
    </div>
  )
}
