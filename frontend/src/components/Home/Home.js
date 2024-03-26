import React, { useState } from 'react';

import Sidebar from '../Sidebar/Sidebar';

import SimpleLinearRegression from '../Models/SimpleLinearRegression';
import MultivariableLinearRegression from '../Models/MultivariableLinearRegression';
import LogisticRegression from '../Models/LogisticRegression';
import KNN from '../Models/KNN';
import KMeans from '../Models/KMeans';
import DecisionTree from '../Models/DecisionTree';
import RandomForest from '../Models/RandomForest';
import SVM from '../Models/SVM';
import DBSCAN from '../Models/DBSCAN';
import ANN from '../Models/ANN';
import CNN from '../Models/CNN';
import NaiveBayes from '../Models/NaiveBayes';

export default function Home() {
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
      case 'naive_bayes':
        return <NaiveBayes />;
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
      <div style={{ display: 'flex' }}>
        <div style={{ flex: '0 0 auto' }}>
          <Sidebar loadComponent={loadComponent} />
        </div>
        <div style={{ flex: 1 }}>
          {/* Render the selected component */}
          {renderComponent()}
        </div>
      </div>
    </>
  );
};
