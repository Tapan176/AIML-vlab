import React from 'react';

const HiddenLayer = ({ index, layer, onChange, onRemove }) => {
  const handleInputChange = (e, key) => {
    onChange(index, { ...layer, [key]: e.target.value });
  };

  return (
    <div>
      <h3>Hidden Layer {index + 1}</h3>
      <label>Type:</label>
      <select value={layer.type} onChange={(e) => handleInputChange(e, 'type')}>
        <option value="conv">Convolutional</option>
        <option value="pooling">Pooling</option>
        <option value="flatten">Flatten</option>
        <option value="dense">Dense</option>
        <option value="dropout">Dropout</option>
      </select>
      {layer.type === 'conv' && (
        <div>
          <label>Number of Neurons:</label>
          <input
            type="number"
            value={layer.numberOfNeurons}
            onChange={(e) => handleInputChange(e, 'numberOfNeurons')}
          />
          <label>Kernel:</label>
          <input
            type="text"
            value={layer.kernel}
            onChange={(e) => handleInputChange(e, 'kernel')}
          />
          <label>Activation Function:</label>
          <input
            type="text"
            value={layer.activationFunction}
            onChange={(e) => handleInputChange(e, 'activationFunction')}
          />
        </div>
      )}
      {layer.type === 'pooling' && (
        <div>
          <label>Pooling Type:</label>
          <select
            value={layer.poolingType}
            onChange={(e) => handleInputChange(e, 'poolingType')}
          >
            <option value="maxPool">Max Pooling</option>
            <option value="avgPool">Average Pooling</option>
          </select>
          <label>Pooling Size:</label>
          <input
            type="text"
            value={layer.poolingSize}
            onChange={(e) => handleInputChange(e, 'poolingSize')}
          />
        </div>
      )}
      {layer.type === 'dense' && (
        <div>
          <label>Units:</label>
          <input
            type="number"
            value={layer.units}
            onChange={(e) => handleInputChange(e, 'units')}
          />
          <label>Activation Function:</label>
          <input
            type="text"
            value={layer.activationFunction}
            onChange={(e) => handleInputChange(e, 'activationFunction')}
          />
        </div>
      )}
      {layer.type === 'dropout' && (
        <div>
          <label>Dropout Rate:</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1"
            value={layer.dropoutRate}
            onChange={(e) => handleInputChange(e, 'dropoutRate')}
          />
        </div>
      )}
      <button onClick={() => onRemove(index)}>Remove Layer</button>
    </div>
  );
};

const CnnHiddenLayer = ({ layers, onChange, onAddLayer, onRemoveLayer }) => {
  return (
    <div>
      {layers.map((layer, index) => (
        <HiddenLayer
          key={index}
          index={index}
          layer={layer}
          onChange={onChange}
          onRemove={onRemoveLayer}
        />
      ))}
      <button onClick={onAddLayer}>Add Layer</button>
    </div>
  );
};

export default CnnHiddenLayer;
