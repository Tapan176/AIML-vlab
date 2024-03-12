import React from 'react';

export default function About() {
  return (
    <div className="container mt-5">
      <h1 className="mb-4">AI Model Hub - Empowering Users in AI & ML</h1>
      <div className="row">
        <div className="col-md-8">
          <div className="card">
            <div className="card-body">
              <h3 className="card-title">Overview:</h3>
              <p className="card-text">AI Model Hub is a web-based platform that empowers users to explore, experiment, and deploy various artificial intelligence (AI) and machine learning (ML) models seamlessly. The platform allows users to select a model, provide a dataset, tune parameters, and observe real-time results. Additionally, users have the option to train models on their own datasets and access the corresponding code for local deployment.</p>
            </div>
          </div>
          <div className="card mt-4">
            <div className="card-body">
              <h3 className="card-title">Features:</h3>
              <ul className="card-text">
                <li>Model Selection: Users can choose from a diverse range of pre-trained AI and ML models covering image recognition, natural language processing, regression, and more.</li>
                <li>Dataset Interaction: Users can upload their datasets or select from available sample datasets in various formats.</li>
                <li>Parameter Tuning: Intuitive sliders and input fields allow users to fine-tune model parameters with real-time feedback.</li>
                <li>Live Results: Users can observe the model's predictions on their dataset in real-time with visualizations and metrics.</li>
                <li>Model Training: Users can train selected models on their datasets with generated code provided for local deployment.</li>
                <li>Code Export: Option to export model training and inference code in commonly used programming languages like Python.</li>
              </ul>
            </div>
          </div>
          <div className="card mt-4">
            <div className="card-body">
              <h3 className="card-title">Usage Guidelines:</h3>
              <ol className="card-text">
                <li>Select Model: Choose a model from the available options.</li>
                <li>Dataset Input: Upload your dataset or select a sample dataset.</li>
                <li>Parameter Tuning: Adjust model parameters using the intuitive interface.</li>
                <li>Live Evaluation: Observe real-time results and performance metrics.</li>
                <li>Model Training: Optionally, train the selected model on your dataset.</li>
                <li>Code Export: If desired, export the generated code for local deployment.</li>
              </ol>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card mt-4">
            <div className="card-body">
              <h3 className="card-title">Technical Stack:</h3>
              <ul className="card-text">
                <li>Frontend: HTML, CSS, JavaScript, React.js</li>
                <li>Backend: Python Flask for server-side processing, RESTful API for model interactions</li>
                <li>Machine Learning Frameworks: TensorFlow, PyTorch, scikit-learn, etc.</li>
              </ul>
            </div>
          </div>
          <div className="card mt-4">
            <div className="card-body">
              <h3 className="card-title">Security and Privacy:</h3>
              <p className="card-text">User data is securely processed and stored, adhering to industry-standard security practices. Models and datasets are anonymized and stripped of sensitive information before processing.</p>
            </div>
          </div>
          <div className="card mt-4">
            <div className="card-body">
              <h3 className="card-title">Future Enhancements:</h3>
              <ul className="card-text">
                <li>Integration of additional models and algorithms.</li>
                <li>Collaboration features for sharing datasets and models.</li>
                <li>Support for custom model implementations.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
