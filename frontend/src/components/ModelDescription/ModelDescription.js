import { useState, useEffect } from 'react';
import { API_URL } from '../../constants';
import { Collapse, Button } from 'react-bootstrap';
import './ModelDescription.css';

export default function ModelDescription({ modelCode }) {
  const [model, setModel] = useState(null);

  useEffect(() => {
      const fetchModel = async () => {
          try {
              const res = await fetch(`${API_URL}/models/info`);
              if (res.ok) {
                  const modelsData = await res.json();
                  setModel(modelsData.find(m => m.code === modelCode) || null);
              }
          } catch (err) {
              console.error(err);
          }
      };
      fetchModel();
  }, [modelCode]);

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
    <div className="description-sidebar" style={{ width: '400px', overflowY: 'auto', maxHeight: '92.5vh', padding: '20px' }}>
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
