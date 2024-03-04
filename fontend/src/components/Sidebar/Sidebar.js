import React from 'react';
import './styles.css';
import modelsData from '../models.json';

export default function Sidebar({ loadComponent }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h5 className="sidebar-title">Choose a model</h5>
      </div>
      <div className="sidebar-body">
        <ul className="list-unstyled">
          {modelsData.map((model, index) => (
            <li className="sidebar-list-item" key={index}>
              <button onClick={() => loadComponent(model.code)}>{model.name}</button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
