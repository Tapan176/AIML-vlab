import React from 'react';
import modelsData from '../models.json'; // Assuming models.json is in the same directory
import { Collapse, Button } from 'react-bootstrap';
import './ModelDescription.css';

export default function ModelDescription({ modelCode }) {
  // Find the model with the matching code
  const model = modelsData.find(model => model.code === modelCode);

  if (!model) {
    return <div></div>;
  }

  // Recursive function to render parameters and their nested parameters
  const renderParameters = parameters => {
    return (
      <ul>
        {parameters.map(param => (
          <li key={param.parameter}>
            <strong>{param.parameter}:</strong> {param.description}
            {param.parameters && renderParameters(param.parameters)}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="description-sidebar" style={{ width: '300px', overflowY: 'auto', maxHeight: '92.5vh', padding: '20px' }}>
      <Button
        variant="primary"
        className="sidebar-toggle"
        data-bs-toggle="collapse"
        href={`#collapse-${modelCode}`}
        aria-expanded="false"
        aria-controls={`collapse-${modelCode}`}
      >
        {model.name}
      </Button>
      <Collapse id={`collapse-${modelCode}`}>
        <div className="sidebar-content">
          {renderParameters(model.description)}
        </div>
      </Collapse>
    </div>
  );
}
