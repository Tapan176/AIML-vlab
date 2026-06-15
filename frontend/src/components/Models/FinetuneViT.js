import React, { useState } from 'react';
import DownloadTrainedModel from '../DownloadTrainedModel/DownloadTrainedModel';
import '../shared/ModelStyles.css';

const FinetuneViT = () => {
    const [logs, setLogs] = useState([]);
    const [results, setResults] = useState(null);
    const [training, setTraining] = useState(false);
    const [error, setError] = useState(null);

    const startTraining = async (formData) => {
        setTraining(true);
        setError(null);
        setResults(null);
        setLogs(['🚀 Starting ViT fine-tuning...']);

        try {
            const { API_URL } = await import('../../constants');
            const token = localStorage.getItem('aiml_token');

            const response = await fetch(`${API_URL}/finetune/vit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Training failed');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let done = false;

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                if (value) {
                    buffer += decoder.decode(value, { stream: true });
                    const events = buffer.split('\n\n');
                    buffer = events.pop() || '';
                    events.forEach(event => {
                        if (event.startsWith('data: ')) {
                            try {
                                const parsed = JSON.parse(event.replace('data: ', ''));
                                if (parsed.log) setLogs(prev => [...prev, parsed.log]);
                                else if (parsed.status === 'completed' || parsed.evaluation_metrics) {
                                    setResults(parsed);
                                }
                            } catch (e) {}
                        }
                    });
                }
                done = readerDone;
            }
        } catch (err) {
            setError(err.message);
            setLogs(prev => [...prev, `❌ Error: ${err.message}`]);
        }
        setTraining(false);
    };

    return (
        <div className="model-container">
            <div className="model-header">
                <h2>🖼️ ViT Fine-Tuning (Image Classification)</h2>
                <p>Fine-tune Vision Transformer on your image dataset.</p>
                <div className="model-badge fine-tuning">HuggingFace Transformers</div>
            </div>

            <ViTForm onSubmit={startTraining} disabled={training} />

            {error && <div className="error-banner">{error}</div>}

            {logs.length > 0 && (
                <div className="training-console">
                    <h3>Training Logs</h3>
                    <div className="console-output">
                        {logs.map((log, i) => <div key={i}>{log}</div>)}
                    </div>
                </div>
            )}

            {results && (
                <div className="results-panel">
                    <h3>Results</h3>
                    <div className="metrics-grid">
                        {results.evaluation_metrics?.accuracy != null && (
                            <div className="metric-item">
                                <span className="metric-label">Accuracy</span>
                                <span className="metric-value">{(results.evaluation_metrics.accuracy * 100).toFixed(2)}%</span>
                            </div>
                        )}
                        {results.evaluation_metrics?.val_loss != null && (
                            <div className="metric-item">
                                <span className="metric-label">Val Loss</span>
                                <span className="metric-value">{results.evaluation_metrics.val_loss.toFixed(4)}</span>
                            </div>
                        )}
                        {results.classes && (
                            <div className="metric-item">
                                <span className="metric-label">Classes</span>
                                <span className="metric-value">{results.classes.join(', ')}</span>
                            </div>
                        )}
                    </div>
                    {results.session_id && (
                        <div className="download-section">
                            <DownloadTrainedModel selectedModel="vit_finetune" extension=".zip" sessionId={results.session_id} label="Download Fine-Tuned Model" />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const ViTForm = ({ onSubmit, disabled }) => {
    const [filename, setFilename] = useState('');
    const [hyperparams, setHyperparams] = useState({
        model_name: 'google/vit-base-patch16-224',
        epochs: 3,
        batch_size: 16,
        learning_rate: 2e-5,
        weight_decay: 0.01,
        test_size: 0.2,
        freeze_base: false,
    });

    const handleChange = (name, value) => setHyperparams(prev => ({ ...prev, [name]: value }));

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit({ filename, hyperparams });
    };

    return (
        <form className="model-form" onSubmit={handleSubmit}>
            <div className="form-section">
                <h4>Dataset</h4>
                <div className="form-group">
                    <label>ZIP Dataset Filename</label>
                    <input type="text" value={filename} onChange={e => setFilename(e.target.value)} placeholder="e.g. cats_dogs.zip (class-labeled subdirectories)" required />
                </div>
            </div>
            <div className="form-section">
                <h4>Hyperparameters</h4>
                <div className="form-row">
                    <div className="form-group">
                        <label>Base Model</label>
                        <select value={hyperparams.model_name} onChange={e => handleChange('model_name', e.target.value)}>
                            <option value="google/vit-base-patch16-224">ViT Base (224px)</option>
                            <option value="google/vit-base-patch16-224-in21k">ViT Base (ImageNet-21k)</option>
                            <option value="google/vit-large-patch16-224">ViT Large (224px)</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Epochs</label>
                        <input type="number" value={hyperparams.epochs} onChange={e => handleChange('epochs', parseInt(e.target.value))} min={1} max={50} />
                    </div>
                    <div className="form-group">
                        <label>Batch Size</label>
                        <input type="number" value={hyperparams.batch_size} onChange={e => handleChange('batch_size', parseInt(e.target.value))} min={1} max={128} />
                    </div>
                </div>
                <div className="form-row">
                    <div className="form-group">
                        <label>Learning Rate</label>
                        <input type="number" step="0.0000001" value={hyperparams.learning_rate} onChange={e => handleChange('learning_rate', parseFloat(e.target.value))} />
                    </div>
                    <div className="form-group">
                        <label>Weight Decay</label>
                        <input type="number" step="0.001" value={hyperparams.weight_decay} onChange={e => handleChange('weight_decay', parseFloat(e.target.value))} />
                    </div>
                    <div className="form-group">
                        <label>Test Split</label>
                        <input type="number" step="0.05" value={hyperparams.test_size} onChange={e => handleChange('test_size', parseFloat(e.target.value))} />
                    </div>
                </div>
                <label className="toggle-label">
                    <input type="checkbox" checked={hyperparams.freeze_base} onChange={e => handleChange('freeze_base', e.target.checked)} />
                    Freeze ViT Encoder (recommended for small datasets)
                </label>
            </div>
            <button type="submit" className="btn-train" disabled={disabled}>
                {disabled ? '⏳ Fine-Tuning...' : '🚀 Start Fine-Tuning'}
            </button>
        </form>
    );
};

export default FinetuneViT;
