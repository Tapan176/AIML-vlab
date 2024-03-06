import React, { useState } from 'react';
import './App.css';

import Navbar from './components/Navbar/Navbar';
import Sidebar from './components/Sidebar/Sidebar';
// import ShowDataset from './components/Dataset/ShowDataset';

import SimpleLinearRegression from './components/Models/SimpleLinearRegression';
import MultivariableLinearRegression from './components/Models/MultivariableLinearRegression';
import LogisticRegression from './components/Models/LogisticRegression';
import KNN from './components/Models/KNN';
import KMeans from './components/Models/KMeans';
import DecisionTree from './components/Models/DecisionTree';
import RandomForest from './components/Models/RandomForest';
import SVM from './components/Models/SVM';
import DBSCAN from './components/Models/DBSCAN';
import ANN from './components/Models/ANN';
import CNN from './components/Models/CNN';

function App() {
  // const [inputData, setInputData] = useState({ csvData: null });
  // // console.log(inputData);
  // const handleDatasetUpload = (data) => {
  //   setInputData(data);
  // };

  // State to keep track of the selected model
  const [selectedModel, setSelectedModel] = useState(null);

  // Function to update the selected model
  const loadComponent = (model) => {
    setSelectedModel(model);
  };

  // Function to render the selected component
  const renderComponent = () => {
    switch (selectedModel) {
      case 'simple_linear_regression':
        return <SimpleLinearRegression />;
      case 'multivariable_linear_regression':
        return <MultivariableLinearRegression />;
      case 'logistic_regression':
        return <LogisticRegression />;
      case 'knn':
        return <KNN />;
      case 'k_means':
        return <KMeans />;
      case 'decision_tree':
        return <DecisionTree />;
      case 'random_forest':
        return <RandomForest />;
      case 'svm':
        return <SVM />;
      case 'dbscan':
        return <DBSCAN />;
      case 'ann':
        return <ANN />;
      case 'cnn':
        return <CNN />;
      default:
        return null;
    }
  };

  return (
    <>
      <div>
        <Navbar />
      </div>
      <div style={{ display: 'flex' }}>
        <div style={{ flex: '0 0 auto' }}>
          <Sidebar loadComponent={loadComponent} />
        </div>
        <div style={{ flex: 1 }}>
          {/* <ShowDataset onDatasetUpload={handleDatasetUpload} /> */}
          {/* Render the selected component */}
          {renderComponent()}
        </div>
      </div>
    </>
  );
}

export default App;
