import React, { useState } from 'react';
// import { Button, Form, FormControl, InputGroup, DropdownButton, Dropdown } from 'react-bootstrap';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import constants from '../../constants';

export default function CNN() {
  const [inputData, setInputData] = useState({
    numberOfNeuronsInInputLayer: 32,
    inputKernelSize: [3, 3],
    inputLayerActivationFunction: 'relu',
    inputShape: [64, 64, 3],
    hiddenLayerArray: [
        { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' },
        { type: 'pooling', poolingType: 'maxPool', poolingSize: [2, 2] },
        { type: 'conv', numberOfNeurons: 128, kernel: [3, 3], activationFunction: 'relu' },
        { type: 'pooling', poolingType: 'maxPool', poolingSize: [2, 2] },
        { type: 'flatten' },
        { type: 'dense', units: 128, activationFunction: 'relu' },
        { type: 'dropout', dropoutRate: 0.5 }
    ],
    optimizerObject: { type: 'adam', learning_rate: 0.0001 },
    lossFunction: { type: 'binary_crossentropy' },
    evaluationMetrics: ['accuracy'],
    numberOfEpochs: 25,
    batchSize: 32,
    classMode: 'binary'
  });

  const trainCNNModel = async () => {
      try {
          const response = await fetch(`${constants.API_BASE_URL}/cnn`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify(inputData)
          });

          if (!response.ok) {
              throw new Error('Failed to train model');
          }

          const responseData = await response.json();
          console.log(responseData); // Handle success message from server
      } catch (error) {
          console.error('Error:', error.message); // Handle error
      }
  };

  const handleInputChange = (event) => {
      const { name, value } = event.target;
      setInputData(prevData => ({
          ...prevData,
          [name]: value
      }));
  };

  const handleLayerChange = (event, index) => {
    const { name, value } = event.target;
    setInputData(prevData => ({
        ...prevData,
        hiddenLayerArray: prevData.hiddenLayerArray.map((layer, i) => {
            if (i === index) {
                return {
                    ...layer,
                    [name]: value
                };
            }
            return layer;
        })
    }));
  };

  return (
    <div>
        {/* Input fields for CNN parameters */}
        <label>
            Number of Neurons in Input Layer:
            <input
                type="number"
                name="numberOfNeuronsInInputLayer"
                value={inputData.numberOfNeuronsInInputLayer}
                onChange={handleInputChange}
            />
        </label>
        <label>
            Input Kernel Size (e.g., "3,3"):
            <input
                type="text"
                name="inputKernelSize"
                value={inputData.inputKernelSize.join(',')}
                onChange={handleInputChange}
            />
        </label>
        <label>
            Input Layer Activation Function:
            <input
                type="text"
                name="inputLayerActivationFunction"
                value={inputData.inputLayerActivationFunction}
                onChange={handleInputChange}
            />
        </label>
        <label>
            Input Shape (e.g., "64,64,3"):
            <input
                type="text"
                name="inputShape"
                value={inputData.inputShape.join(',')}
                onChange={handleInputChange}
            />
        </label>
        {/* Hidden Layers */}
        {inputData.hiddenLayerArray.map((layer, index) => (
            <div key={index}>
                <label>
                    Type: 
                    <input
                        type="text"
                        name={`hiddenLayerArray[${index}].type`}
                        value={layer.type}
                        onChange={(event) => handleLayerChange(event, index)}
                    />
                </label>
                {/* Add input fields for specific parameters of each layer type */}
                {/* For example, for convolutional layers */}
                {layer.type === 'conv' && (
                    <>
                        <label>
                            Number of Neurons:
                            <input
                                type="number"
                                name={`hiddenLayerArray[${index}].numberOfNeurons`}
                                value={layer.numberOfNeurons}
                                onChange={(event) => handleLayerChange(event, index)}
                            />
                        </label>
                        <label>
                            Kernel Size (e.g., "3,3"):
                            <input
                                type="text"
                                name={`hiddenLayerArray[${index}].kernel`}
                                value={layer.kernel.join(',')}
                                onChange={(event) => handleLayerChange(event, index)}
                            />
                        </label>
                        {/* Add more parameters as needed */}
                    </>
                )}
                {/* Add input fields for other types of layers */}
            </div>
        ))}
        {/* Add input fields for optimizer */}
        <label>
            Optimizer Type:
            <input
                type="text"
                name="optimizerObject.type"
                value={inputData.optimizerObject.type}
                onChange={handleInputChange}
            />
        </label>
        <label>
            Learning Rate:
            <input
                type="number"
                name="optimizerObject.learning_rate"
                value={inputData.optimizerObject.learning_rate}
                onChange={handleInputChange}
            />
        </label>
        {/* Add input fields for loss function */}
        <label>
            Loss Function Type:
            <input
                type="text"
                name="lossFunction.type"
                value={inputData.lossFunction.type}
                onChange={handleInputChange}
            />
        </label>
        {/* Add input fields for evaluation metrics */}
        <label>
            Evaluation Metrics:
            <input
                type="text"
                name="evaluationMetrics"
                value={inputData.evaluationMetrics.join(',')}
                onChange={(event) => setInputData(prevData => ({ ...prevData, evaluationMetrics: event.target.value.split(',') }))}
            />
        </label>
        <label>
            Number of Epochs:
            <input
                type="number"
                name="numberOfEpochs"
                value={inputData.numberOfEpochs}
                onChange={handleInputChange}
            />
        </label>
        <label>
            Batch Size:
            <input
                type="number"
                name="batchSize"
                value={inputData.batchSize}
                onChange={handleInputChange}
            />
        </label>
        <label>
            Class Mode:
            <input
                type="text"
                name="classMode"
                value={inputData.classMode}
                onChange={handleInputChange}
            />
        </label>
        <button onClick={trainCNNModel}>Train CNN Model</button>
        <DownloadTrainedModel selectedModel={'cnn'} extension={'.h5'} />
      </div>
    );
}

// import React, { useState } from 'react';
// // import { Button, Form, FormControl, InputGroup, DropdownButton, Dropdown } from 'react-bootstrap';
// import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
// import constants from '../../constants';

// export default function CNN() {
//   const [inputData, setInputData] = useState({
//     numberOfNeuronsInInputLayer: 32,
//     inputKernelSize: [3, 3],
//     inputLayerActivationFunction: 'relu',
//     inputShape: [64, 64, 3],
//     hiddenLayerCount: 1,
//     hiddenLayers: [
//         { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' },
//         { type: 'pooling', poolingType: 'maxPool', poolingSize: [2, 2] }
//     ],
//     optimizerObject: { type: 'adam', learning_rate: 0.0001 },
//     lossFunction: { type: 'binary_crossentropy' },
//     evaluationMetrics: ['accuracy'],
//     numberOfEpochs: 25,
//     batchSize: 32,
//     classMode: 'binary'
//   });

//   {
//     numberOfNeuronsInInputLayer: 32,
//     inputKernelSize: [3, 3],
//     inputLayerActivationFunction: 'relu',
//     inputShape: [64, 64, 3],
//     hiddenLayerArray: [
//         { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' },
//         { type: 'pooling', poolingType: 'maxPool', poolingSize: [2, 2] },
//         { type: 'conv', numberOfNeurons: 128, kernel: [3, 3], activationFunction: 'relu' },
//         { type: 'pooling', poolingType: 'maxPool', poolingSize: [2, 2] },
//         { type: 'flatten' },
//         { type: 'dense', units: 128, activationFunction: 'relu' },
//         { type: 'dropout', dropoutRate: 0.5 }
//     ],
//     optimizerObject: { type: 'adam', learning_rate: 0.0001 },
//     lossFunction: { type: 'binary_crossentropy' },
//     evaluationMetrics: ['accuracy'],
//     numberOfEpochs: 25,
//     batchSize: 32,
//     classMode: 'binary'
//   }
  
//   const trainCNNModel = async () => {
//     try {
//         const response = await fetch(`${constants.API_BASE_URL}/cnn`, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify(inputData)
//         });
  
//         if (!response.ok) {
//             throw new Error('Failed to train model');
//         }
  
//         const responseData = await response.json();
//         console.log(responseData); // Handle success message from server
//     } catch (error) {
//         console.error('Error:', error.message); // Handle error
//     }
//   };
  
//   const handleInputChange = (event) => {
//     const { name, value } = event.target;
//     setInputData(prevData => ({
//         ...prevData,
//         [name]: value
//     }));
//   };
  
//   const handleLayerChange = (event, index) => {
//     const { name, value } = event.target;
//     setInputData(prevData => ({
//         ...prevData,
//         hiddenLayers: prevData.hiddenLayers.map((layer, i) => {
//             if (i === index) {
//                 return {
//                     ...layer,
//                     [name]: value
//                 };
//             }
//             return layer;
//         })
//     }));
//   };
  
//   const addHiddenLayer = () => {
//     setInputData(prevData => ({
//         ...prevData,
//         hiddenLayerCount: prevData.hiddenLayerCount + 1,
//         hiddenLayers: [
//             ...prevData.hiddenLayers,
//             { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' }
//         ]
//     }));
//   };
  
//   return (
//     <div>
//         {/* Input fields for CNN parameters */}
//         <label>
//             Number of Neurons in Input Layer:
//             <input
//                 type="number"
//                 name="numberOfNeuronsInInputLayer"
//                 value={inputData.numberOfNeuronsInInputLayer}
//                 onChange={handleInputChange}
//             />
//         </label>
//         <label>
//             Input Kernel Size (e.g., "3,3"):
//             <input
//                 type="text"
//                 name="inputKernelSize"
//                 value={inputData.inputKernelSize.join(',')}
//                 onChange={handleInputChange}
//             />
//         </label>
//         <label>
//             Input Layer Activation Function:
//             <input
//                 type="text"
//                 name="inputLayerActivationFunction"
//                 value={inputData.inputLayerActivationFunction}
//                 onChange={handleInputChange}
//             />
//         </label>
//         <label>
//             Input Shape (e.g., "64,64,3"):
//             <input
//                 type="text"
//                 name="inputShape"
//                 value={inputData.inputShape.join(',')}
//                 onChange={handleInputChange}
//             />
//         </label>
//         {/* Hidden Layers */}
//         <label>
//             Number of Hidden Layers:
//             <input
//                 type="number"
//                 name="hiddenLayerCount"
//                 value={inputData.hiddenLayerCount}
//                 onChange={handleInputChange}
//             />
//         </label>
//         {inputData.hiddenLayers.map((layer, index) => (
//             <div key={index}>
//                 <label>
//                     Type: 
//                     <input
//                         type="text"
//                         name={`hiddenLayers[${index}].type`}
//                         value={layer.type}
//                         onChange={(event) => handleLayerChange(event, index)}
//                     />
//                 </label>
//                 {/* Add input fields for specific parameters of each layer type */}
//                 {/* For example, for convolutional layers */}
//                 {layer.type === 'conv' && (
//                     <>
//                         <label>
//                             Number of Neurons:
//                             <input
//                                 type="number"
//                                 name={`hiddenLayers[${index}].numberOfNeurons`}
//                                 value={layer.numberOfNeurons}
//                                 onChange={(event) => handleLayerChange(event, index)}
//                             />
//                         </label>
//                         <label>
//                             Kernel Size (e.g., "3,3"):
//                             <input
//                                 type="text"
//                                 name={`hiddenLayers[${index}].kernel`}
//                                 value={layer.kernel.join(',')}
//                                 onChange={(event) => handleLayerChange(event, index)}
//                             />
//                         </label>
//                         {/* Add more parameters as needed */}
//                     </>
//                 )}
//                 {/* Add input fields for other types of layers */}
//             </div>
//         ))}
//         <button onClick={addHiddenLayer}>Add Hidden Layer</button>
//         {/* Add input fields for optimizer */}
//         <label>
//             Optimizer Type:
//             <input
//                 type="text"
//                 name="optimizerObject.type"
//                 value={inputData.optimizerObject.type}
//                 onChange={handleInputChange}
//             />
//         </label>
//         <label>
//             Learning Rate:
//             <input
//                 type="number"
//                 name="optimizerObject.learning_rate"
//                 value={inputData.optimizerObject.learning_rate}
//                 onChange={handleInputChange}
//             />
//         </label>
//         {/* Add input fields for loss function */}
//         <label>
//             Loss Function Type:
//             <input
//                 type="text"
//                 name="lossFunction.type"
//                 value={inputData.lossFunction.type}
//                 onChange={handleInputChange}
//             />
//         </label>
//         {/* Add input fields for evaluation metrics */}
//         <label>
//             Evaluation Metrics:
//             <input
//                 type="text"
//                 name="evaluationMetrics"
//                 value={inputData.evaluationMetrics.join(',')}
//                 onChange={(event) => setInputData(prevData => ({ ...prevData, evaluationMetrics: event.target.value.split(',') }))}
//             />
//         </label>
//         <label>
//             Number of Epochs:
//             <input
//                 type="number"
//                 name="numberOfEpochs"
//                 value={inputData.numberOfEpochs}
//                 onChange={handleInputChange}
//             />
//         </label>
//         <label>
//             Batch Size:
//             <input
//                 type="number"
//                 name="batchSize"
//                 value={inputData.batchSize}
//                 onChange={handleInputChange}
//             />
//         </label>
//         <label>
//             Class Mode:
//             <input
//                 type="text"
//                 name="classMode"
//                 value={inputData.classMode}
//                 onChange={handleInputChange}
//             />
//         </label>
//         <button onClick={trainCNNModel}>Train CNN Model</button>
//         <DownloadTrainedModel selectedModel={'cnn'} extension={'.h5'} />
//     </div>
//   );
// }

// import React, { useState } from 'react';
// import { Button, Form, Row, Col } from 'react-bootstrap';
// import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
// import constants from '../../constants';

// export default function CNN() {
//   const [inputData, setInputData] = useState({
//     numberOfNeuronsInInputLayer: 32,
//     inputKernelSize: [3, 3],
//     inputLayerActivationFunction: 'relu',
//     inputShape: [64, 64, 3],
//     hiddenLayerCount: 1,
//     hiddenLayerArray: [
//         { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' },
//         { type: 'pooling', poolingType: 'maxPool', poolingSize: [2, 2] }
//     ],
//     optimizerObject: { type: 'adam', learning_rate: 0.0001 },
//     lossFunction: { type: 'binary_crossentropy' },
//     evaluationMetrics: ['accuracy'],
//     numberOfEpochs: 25,
//     batchSize: 32,
//     classMode: 'binary'
//   });
  
//   const trainCNNModel = async () => {
//     try {
//         console.log(inputData)
//         const response = await fetch(`${constants.API_BASE_URL}/cnn`, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify(inputData)
//         });
  
//         if (!response.ok) {
//             throw new Error('Failed to train model');
//         }
  
//         const responseData = await response.json();
//         console.log(responseData); // Handle success message from server
//     } catch (error) {
//         console.error('Error:', error.message); // Handle error
//     }
//   };
  
//   const handleInputChange = (event) => {
//     const { name, value } = event.target;
//     setInputData(prevData => ({
//         ...prevData,
//         [name]: value
//     }));
//   };
  
//   const handleLayerChange = (event, index) => {
//     const { name, value } = event.target;
//     setInputData(prevData => ({
//         ...prevData,
//         hiddenLayerArray: prevData.hiddenLayerArray.map((layer, i) => {
//             if (i === index) {
//                 return {
//                     ...layer,
//                     [name]: value
//                 };
//             }
//             return layer;
//         })
//     }));
//   };
  
//   const addHiddenLayer = () => {
//     setInputData(prevData => ({
//         ...prevData,
//         hiddenLayerCount: prevData.hiddenLayerCount + 1,
//         hiddenLayerArray: [
//             ...prevData.hiddenLayerArray,
//             { type: 'conv', numberOfNeurons: 64, kernel: [3, 3], activationFunction: 'relu' }
//         ]
//     }));
//   };
  
//   return (
//     <div className="container">
//         <h2>CNN Model Configuration</h2>
//         <Form>
//             <Form.Group as={Row} controlId="numberOfNeuronsInInputLayer">
//                 <Form.Label column sm="4">Number of Neurons in Input Layer:</Form.Label>
//                 <Col sm="8">
//                     <Form.Control
//                         type="number"
//                         name="numberOfNeuronsInInputLayer"
//                         value={inputData.numberOfNeuronsInInputLayer}
//                         onChange={handleInputChange}
//                     />
//                 </Col>
//             </Form.Group>
//             {/* Add more form groups for other input fields */}
//             {/* Hidden Layers */}
//             <Form.Group as={Row} controlId="hiddenLayerCount">
//                 <Form.Label column sm="4">Number of Hidden Layers:</Form.Label>
//                 <Col sm="8">
//                     <Form.Control
//                         type="number"
//                         name="hiddenLayerCount"
//                         value={inputData.hiddenLayerCount}
//                         onChange={handleInputChange}
//                     />
//                 </Col>
//             </Form.Group>
//             {inputData.hiddenLayerArray.map((layer, index) => (
//                 <div key={index}>
//                     <Form.Group as={Row} controlId={`hiddenLayer-${index}-type`}>
//                         <Form.Label column sm="4">Type:</Form.Label>
//                         <Col sm="8">
//                             <Form.Control
//                                 type="text"
//                                 name={`hiddenLayerArray[${index}].type`}
//                                 value={layer.type}
//                                 onChange={(event) => handleLayerChange(event, index)}
//                             />
//                         </Col>
//                     </Form.Group>
//                     {/* Add input fields for specific parameters of each layer type */}
//                     {/* For example, for convolutional layers */}
//                     {layer.type === 'conv' && (
//                         <>
//                             <Form.Group as={Row} controlId={`hiddenLayer-${index}-numberOfNeurons`}>
//                                 <Form.Label column sm="4">Number of Neurons:</Form.Label>
//                                 <Col sm="8">
//                                     <Form.Control
//                                         type="number"
//                                         name={`hiddenLayerArray[${index}].numberOfNeurons`}
//                                         value={layer.numberOfNeurons}
//                                         onChange={(event) => handleLayerChange(event, index)}
//                                     />
//                                 </Col>
//                             </Form.Group>
//                             <Form.Group as={Row} controlId={`hiddenLayer-${index}-kernel`}>
//                                 <Form.Label column sm="4">Kernel Size (e.g., "3,3"):</Form.Label>
//                                 <Col sm="8">
//                                     <Form.Control
//                                         type="text"
//                                         name={`hiddenLayerArray[${index}].kernel`}
//                                         value={layer.kernel.join(',')}
//                                         onChange={(event) => handleLayerChange(event, index)}
//                                     />
//                                 </Col>
//                             </Form.Group>
//                             {/* Add more parameters as needed */}
//                         </>
//                     )}
//                     {/* Add input fields for other types of layers */}
//                 </div>
//             ))}
//             <Button variant="primary" onClick={addHiddenLayer}>Add Hidden Layer</Button>
//             {/* Add input fields for optimizer */}
//             <label>
//                 Optimizer Type:
//                 <input
//                     type="text"
//                     name="optimizerObject.type"
//                     value={inputData.optimizerObject.type}
//                     onChange={handleInputChange}
//                 />
//             </label>
//             <label>
//                 Learning Rate:
//                 <input
//                     type="number"
//                     name="optimizerObject.learning_rate"
//                     value={inputData.optimizerObject.learning_rate}
//                     onChange={handleInputChange}
//                 />
//             </label>
//             {/* Add input fields for loss function */}
//             <label>
//                 Loss Function Type:
//                 <input
//                     type="text"
//                     name="lossFunction.type"
//                     value={inputData.lossFunction.type}
//                     onChange={handleInputChange}
//                 />
//             </label>
//             {/* Add input fields for evaluation metrics */}
//             <label>
//                 Evaluation Metrics:
//                 <input
//                     type="text"
//                     name="evaluationMetrics"
//                     value={inputData.evaluationMetrics.join(',')}
//                     onChange={(event) => setInputData(prevData => ({ ...prevData, evaluationMetrics: event.target.value.split(',') }))}
//                 />
//             </label>
//             <label>
//                 Number of Epochs:
//                 <input
//                     type="number"
//                     name="numberOfEpochs"
//                     value={inputData.numberOfEpochs}
//                     onChange={handleInputChange}
//                 />
//             </label>
//             <label>
//                 Batch Size:
//                 <input
//                     type="number"
//                     name="batchSize"
//                     value={inputData.batchSize}
//                     onChange={handleInputChange}
//                 />
//             </label>
//             <label>
//                 Class Mode:
//                 <input
//                     type="text"
//                     name="classMode"
//                     value={inputData.classMode}
//                     onChange={handleInputChange}
//                 />
//             </label>
//             <Button variant="success" onClick={trainCNNModel}>Train CNN Model</Button>
//             <DownloadTrainedModel selectedModel={'cnn'} extension={'.h5'} />
//         </Form>
//     </div>
//   );
// }
