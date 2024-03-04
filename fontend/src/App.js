import React, { useState } from 'react';
import './App.css';
import Navbar from './components/Navbar/Navbar';
import Sidebar from './components/Sidebar/Sidebar';

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

  function handleUpload() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file.');
        return;
    }

    const reader = new FileReader();

    reader.onload = function(event) {
        const fileContent = event.target.result;
        // You can do something with the file content here
        console.log('File content:', fileContent);
    };

    reader.onerror = function(event) {
        console.error('File could not be read! Code ' + event.target.error.code);
    };

    reader.readAsText(file);
  };

  return (
    <>
      <div>
        <Navbar />
      </div>
      <div>
        <table>
          <tr>
            <td>
              <Sidebar loadComponent={loadComponent} />
            </td>
            <td>
              <table>
                <tr>
                  <td>
                    <h2>Upload Your Dataset</h2>
                    <input type="file" id="fileInput" />
                    <button onclick={handleUpload}>Upload</button>
                  </td>
                </tr>
                <tr>
                  {/* Render the selected component */}
                  {renderComponent()}
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </div>
    </>
  );
}

export default App;
