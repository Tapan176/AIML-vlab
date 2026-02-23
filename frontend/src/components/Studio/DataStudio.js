import React, { useState, useEffect } from 'react';
import constants from '../../constants';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faDatabase, faMagic, faTags } from '@fortawesome/free-solid-svg-icons';
import Sidebar from '../Sidebar/Sidebar';
import './DataStudio.css';

export default function DataStudio() {
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('manager'); // 'manager', 'preprocessing', 'annotation'
    
    // Preprocessing State
    const [selectedPrepDataset, setSelectedPrepDataset] = useState('');
    const [prepOperations, setPrepOperations] = useState([]);
    const [isProcessing, setIsProcessing] = useState(false);

    const fetchDatasets = async () => {
        setLoading(true);
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(`${constants.API_BASE_URL}/user-datasets`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            setDatasets(data.datasets || []);
        } catch (err) {
            console.error("Failed to fetch cloud datasets:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDatasets();
    }, []);

    const handleDelete = async (id, filename) => {
        if (!window.confirm(`Are you sure you want to permanently delete "${filename}" from your cloud library?`)) return;
        
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(`${constants.API_BASE_URL}/datasets/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setDatasets(datasets.filter(d => d._id !== id));
            } else {
                const err = await res.json();
                alert(err.error || 'Failed to delete dataset');
            }
        } catch (err) {
            console.error(err);
            alert('Deletion failed');
        }
    };

    const handleRunPreprocessing = async () => {
        if (!selectedPrepDataset || prepOperations.length === 0) {
            alert("Please select a dataset and add at least one operation.");
            return;
        }
        
        setIsProcessing(true);
        const token = localStorage.getItem('token');
        try {
            const res = await fetch(`${constants.API_BASE_URL}/datasets/preprocess`, {
                method: 'POST',
                headers: { 
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dataset_id: selectedPrepDataset,
                    operations: prepOperations
                })
            });
            
            const data = await res.json();
            if (res.ok) {
                alert(`Success! Generated new dataset: ${data.dataset?.filename}`);
                setDatasets([data.dataset, ...datasets]);
                setSelectedPrepDataset('');
                setPrepOperations([]);
                setActiveTab('manager'); // Switch back to view it
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (err) {
            console.error(err);
            alert('Preprocessing request failed.');
        } finally {
            setIsProcessing(false);
        }
    };

    const addOperation = (action) => {
        setPrepOperations([...prepOperations, { action, columns: [] }]);
    };

    const removeOperation = (index) => {
        setPrepOperations(prepOperations.filter((_, i) => i !== index));
    };

    const updateOperationColumns = (index, value) => {
        const newOps = [...prepOperations];
        newOps[index].columns = value.split(',').map(c => c.trim()).filter(c => c);
        setPrepOperations(newOps);
    };

    return (
        <div className="layout-container">
            <div className="main-content">
                <div className="studio-header">
                    <h1>Data Studio</h1>
                    <p>Manage, clean, and annotate your datasets securely in the cloud.</p>
                </div>

                <div className="studio-tabs">
                    <button className={activeTab === 'manager' ? 'active' : ''} onClick={() => setActiveTab('manager')}>
                        <FontAwesomeIcon icon={faDatabase} /> Data Manager
                    </button>
                    <button className={activeTab === 'preprocessing' ? 'active' : ''} onClick={() => setActiveTab('preprocessing')}>
                        <FontAwesomeIcon icon={faMagic} /> Preprocessing Pipeline
                    </button>
                    <button className={activeTab === 'annotation' ? 'active' : ''} onClick={() => setActiveTab('annotation')}>
                        <FontAwesomeIcon icon={faTags} /> Image Annotation
                    </button>
                </div>

                <div className="studio-body">
                    {activeTab === 'manager' && (
                        <div className="manager-tab">
                            <h2>My Cloud Uploads</h2>
                            {loading ? (
                                <p>Loading datasets...</p>
                            ) : datasets.length === 0 ? (
                                <p>You have not uploaded any datasets yet. Upload one from any ML model page to see it here.</p>
                            ) : (
                                <table className="dataset-table">
                                    <thead>
                                        <tr>
                                            <th>Filename</th>
                                            <th>Type</th>
                                            <th>Uploaded (UTC)</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {datasets.map(d => (
                                            <tr key={d._id}>
                                                <td>{d.filename}</td>
                                                <td><span className={`badge badge-${d.file_type}`}>{d.file_type.toUpperCase()}</span></td>
                                                <td>{new Date(d.uploaded_at).toLocaleString()}</td>
                                                <td>
                                                    <button className="btn-delete" onClick={() => handleDelete(d._id, d.filename)}>
                                                        <FontAwesomeIcon icon={faTrash} /> Delete
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    )}

                    {activeTab === 'preprocessing' && (
                        <div className="preprocessing-tab">
                            <h2>Data Preprocessing Pipeline</h2>
                            <p>Select a CSV dataset to apply cleaning functions. A new dataset will be generated and saved to your library.</p>
                            
                            <div className="prep-form-group">
                                <label>Select Target Dataset:</label>
                                <select 
                                    className="form-control" 
                                    value={selectedPrepDataset}
                                    onChange={(e) => setSelectedPrepDataset(e.target.value)}
                                >
                                    <option value="">-- Choose a CSV dataset --</option>
                                    {datasets.filter(d => d.file_type === 'csv').map(d => (
                                        <option key={d._id} value={d._id}>{d.filename}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="prep-pipeline">
                                <h3>Operations Pipeline</h3>
                                {prepOperations.length === 0 ? (
                                    <div className="empty-pipeline">No operations added.</div>
                                ) : (
                                    <div className="pipeline-chain">
                                        {prepOperations.map((op, index) => (
                                            <div key={index} className="pipeline-node">
                                                <div className="node-header">
                                                    <strong>Step {index + 1}: {op.action.toUpperCase()}</strong>
                                                    <button className="btn-remove" onClick={() => removeOperation(index)}>✖</button>
                                                </div>
                                                <input 
                                                    type="text" 
                                                    className="form-control" 
                                                    placeholder="Target Columns (comma separated). Leave blank for all numeric."
                                                    value={op.columns.join(', ')}
                                                    onChange={(e) => updateOperationColumns(index, e.target.value)}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="prep-actions">
                                <h4>Add Operation</h4>
                                <div className="button-tray">
                                    <button onClick={() => addOperation('dropna')}>Drop Nulls (DropNA)</button>
                                    <button onClick={() => addOperation('fillna_mean')}>Impute Mean</button>
                                    <button onClick={() => addOperation('fillna_median')}>Impute Median</button>
                                    <button onClick={() => addOperation('fillna_mode')}>Impute Mode</button>
                                    <button onClick={() => addOperation('drop_columns')}>Drop Columns</button>
                                    <button onClick={() => addOperation('standard_scale')}>Standard Scaler</button>
                                    <button onClick={() => addOperation('minmax_scale')}>Min-Max Scaling</button>
                                    <button onClick={() => addOperation('label_encode')}>Label Encoding</button>
                                    <button onClick={() => addOperation('one_hot_encode')}>One-Hot Encoding</button>
                                </div>
                            </div>

                            <button 
                                className="btn-run-prep" 
                                onClick={handleRunPreprocessing}
                                disabled={isProcessing || !selectedPrepDataset || prepOperations.length === 0}
                            >
                                {isProcessing ? '⏳ Processing Dataset...' : '▶ Run Pipeline Generator'}
                            </button>
                        </div>
                    )}

                    {activeTab === 'annotation' && (
                        <div className="placeholder-tab">
                            <h2>Image Annotation Studio</h2>
                            <p>Draw bounding boxes around objects within your image datasets to export YOLOv8-compatible training architectures.</p>
                            <div className="coming-soon">Construction in Progress Phase 10</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
