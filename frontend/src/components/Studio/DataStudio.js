import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faDatabase, faMagic, faTags, faChartBar, faCodeBranch, faSave, faFolderOpen, faPlay } from '@fortawesome/free-solid-svg-icons';
import { useAuth } from '../../context/AuthContext';
import { useUI } from '../../context/UIDialog';
import ShowDataset from '../Dataset/ShowDataset';
import ImageAnnotation from './ImageAnnotation';
import { truncateName } from '../../utils/truncateName';
import usePagination from '../../hooks/usePagination';
import Pagination from '../shared/Pagination';
import { useModelRegistry } from '../../hooks/useModelRegistry';
import { setTrainHandoff } from '../../utils/trainHandoff';
import { ROUTES } from '../../constants';
import './DataStudio.css';

export default function DataStudio() {
    const { isAuthenticated } = useAuth();
    const { notify, confirm } = useUI();
    const navigate = useNavigate();
    const registry = useModelRegistry();
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('manager'); // 'manager', 'preprocessing', 'annotation'
    
    // Preprocessing State
    const [selectedPrepDataset, setSelectedPrepDataset] = useState('');
    const [prepOperations, setPrepOperations] = useState([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [templates, setTemplates] = useState({});
    const [savedPipelines, setSavedPipelines] = useState([]);
    const [pipelineName, setPipelineName] = useState('');
    // Most recent preprocessing output, used by the "Train on this output" CTA.
    const [lastOutput, setLastOutput] = useState(null);

    // Profiling State
    const [profileDataset, setProfileDataset] = useState('');
    const [profile, setProfile] = useState(null);
    const [profiling, setProfiling] = useState(false);

    // Diff State
    const [diffA, setDiffA] = useState('');
    const [diffB, setDiffB] = useState('');
    const [diffResult, setDiffResult] = useState(null);
    const [diffing, setDiffing] = useState(false);

    // "Train on this output" handoff State. `trainTarget` holds the dataset
    // descriptor the user wants to train on; the modal then picks a model.
    const [trainTarget, setTrainTarget] = useState(null);   // {filename, dataset_id, drive_id, file_type}
    const [trainModelCode, setTrainModelCode] = useState('');

    // "Apply pipeline to dataset" State (D8). `applyPipeline` holds the saved
    // pipeline being applied; the modal picks the target dataset.
    const [applyPipeline, setApplyPipeline] = useState(null);   // {name, operations?}
    const [applyDatasetId, setApplyDatasetId] = useState('');
    const [applying, setApplying] = useState(false);

    // Paginate the Data Manager dataset list (same pattern as the Datasets
    // Library) so the table doesn't grow into an endless scroll.
    const {
        page: dsPage,
        setPage: setDsPage,
        totalPages: dsTotalPages,
        pageItems: dsPageItems,
        totalItems: dsTotalItems,
        pageSize: dsPageSize,
    } = usePagination(datasets, 8);

    const fetchDatasets = async () => {
        setLoading(true);
        try {
            const data = await api.get('/user-datasets');
            setDatasets(data.datasets || []);
        } catch (err) {
            console.error("Failed to fetch cloud datasets:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isAuthenticated) {
            fetchDatasets();
            fetchTemplates();
            fetchPipelines();
        } else {
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isAuthenticated]);

    const fetchTemplates = useCallback(async () => {
        try {
            setTemplates(await api.get('/pipelines/templates'));
        } catch {}
    }, []);

    const fetchPipelines = useCallback(async () => {
        try {
            setSavedPipelines(await api.get('/pipelines'));
        } catch {}
    }, []);

    const handleSavePipeline = async () => {
        if (!pipelineName.trim() || prepOperations.length === 0) { notify('Enter a name and add operations.', 'warning'); return; }
        try {
            await api.post('/pipelines', { name: pipelineName.trim(), operations: prepOperations });
            notify(`Pipeline '${pipelineName}' saved!`, 'success');
            fetchPipelines();
        } catch { notify('Failed to save pipeline.', 'error'); }
    };

    const handleLoadPipeline = async (name) => {
        try {
            const data = await api.get(`/pipelines/${encodeURIComponent(name)}`);
            setPrepOperations(data.operations || []);
            setPipelineName(name);
            setActiveTab('preprocessing');
            notify(`Loaded '${name}' (${data.operations.length} ops).`, 'success');
        } catch { notify('Failed to load pipeline.', 'error'); }
    };

    const handleApplyTemplate = (key) => {
        const tpl = templates[key];
        if (tpl?.operations) { setPrepOperations(tpl.operations); setActiveTab('preprocessing'); }
    };

    const handleLoadProfile = async () => {
        if (!profileDataset) return;
        setProfiling(true); setProfile(null);
        try {
            setProfile(await api.get(`/datasets/${profileDataset}/profile`));
        } catch { notify('Profiling failed.', 'error'); }
        setProfiling(false);
    };

    const handleDiff = async () => {
        if (!diffA || !diffB) return;
        setDiffing(true); setDiffResult(null);
        try {
            setDiffResult(await api.post('/datasets/diff', { dataset_id_a: diffA, dataset_id_b: diffB }));
        } catch { notify('Diff failed.', 'error'); }
        setDiffing(false);
    };

    // ── "Train on this output" handoff (D7) ──────────────────────────────
    // Open the model picker for a chosen dataset descriptor.
    const openTrainPicker = (dataset) => {
        if (!dataset || !dataset.filename) return;
        setTrainTarget({
            filename: dataset.filename,
            dataset_id: dataset._id || dataset.dataset_id || null,
            drive_id: dataset.drive_id || null,
            file_type: dataset.file_type || null,
        });
        setTrainModelCode('');
    };

    // Stash the dataset for the Lab and navigate. An empty model code means
    // "any model" — the first model page the user opens will claim it.
    const confirmTrain = () => {
        if (!trainTarget) return;
        setTrainHandoff({ ...trainTarget, model_code: trainModelCode || undefined });
        if (trainModelCode) {
            try { sessionStorage.setItem('auto_select_model', trainModelCode); } catch (e) {}
        }
        setTrainTarget(null);
        navigate(ROUTES.LAB);
    };

    // ── "Apply pipeline to dataset" (D8) ─────────────────────────────────
    // Open the dataset picker for a saved pipeline.
    const openApplyPipeline = async (pipeline) => {
        try {
            // We need the pipeline's operations; the list endpoint only returns
            // op_count, so fetch the full pipeline by name.
            const full = await api.get(`/pipelines/${encodeURIComponent(pipeline.name)}`);
            setApplyPipeline({ name: pipeline.name, operations: full.operations || [] });
            setApplyDatasetId('');
        } catch {
            notify('Failed to load pipeline operations.', 'error');
        }
    };

    // Run the saved pipeline against the chosen dataset directly (no detour
    // through the editor), producing a new versioned dataset.
    const confirmApplyPipeline = async () => {
        if (!applyPipeline || !applyDatasetId || !applyPipeline.operations?.length) return;
        setApplying(true);
        try {
            const data = await api.post('/datasets/preprocess', {
                dataset_id: applyDatasetId,
                operations: applyPipeline.operations,
            });
            notify(`Generated new dataset: ${data.dataset?.filename}`, 'success');
            try { window.dispatchEvent(new CustomEvent('aiml:usage')); } catch (e) {}
            setDatasets(prev => [data.dataset, ...prev]);
            setApplyPipeline(null);
            setApplyDatasetId('');
        } catch (err) {
            const code = err.data?.error;
            if (code !== 'quota_exceeded' && code !== 'storage_quota_exceeded') {
                notify(err.message || 'Failed to apply pipeline.', 'error');
            }
        } finally {
            setApplying(false);
        }
    };

    const handleDatasetUploadDirect = (data) => {
        if (data && data.filename) {
            fetchDatasets();
        }
    };

    const handleDelete = async (id, filename) => {
        const ok = await confirm({
            title: 'Delete dataset?',
            message: `This will permanently delete "${filename}" from your cloud library. This action cannot be undone.`,
            confirmText: 'Delete',
            danger: true,
        });
        if (!ok) return;

        try {
            await api.delete(`/datasets/${id}`);
            setDatasets(datasets.filter(d => d._id !== id));
            notify('Dataset deleted.', 'success');
        } catch (err) {
            console.error(err);
            notify(err.data?.error || err.message || 'Deletion failed', 'error');
        }
    };

    const handleRunPreprocessing = async () => {
        if (!selectedPrepDataset || prepOperations.length === 0) {
            notify("Please select a dataset and add at least one operation.", 'warning');
            return;
        }
        
        setIsProcessing(true);
        try {
            const data = await api.post('/datasets/preprocess', {
                dataset_id: selectedPrepDataset,
                operations: prepOperations
            });
            notify(`Generated new dataset: ${data.dataset?.filename}`, 'success');
            // Tell the subscription context to refresh usage (Data Studio runs
            // are metered under the 'datastudio' class).
            try { window.dispatchEvent(new CustomEvent('aiml:usage')); } catch (e) {}
            // Add the new versioned dataset to the library, but KEEP the user's
            // selected source dataset and their pipeline, and stay on this tab —
            // so they can tweak/re-run without re-selecting or being yanked away.
            setDatasets([data.dataset, ...datasets]);
            // Remember the freshly produced dataset so the user can jump
            // straight into the Lab and train on it ("Train on this output").
            setLastOutput(data.dataset || null);
        } catch (err) {
            console.error(err);
            // Quota / storage-cap errors surface via the global UpgradeModal
            // (api.js dispatches 'aiml:quota'); don't double-notify with an alert.
            const code = err.data?.error;
            if (code !== 'quota_exceeded' && code !== 'storage_quota_exceeded') {
                notify(err.message || 'Preprocessing request failed.', 'error');
            }
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
                    <button className={activeTab === 'profile' ? 'active' : ''} onClick={() => setActiveTab('profile')}>
                        <FontAwesomeIcon icon={faChartBar} /> Data Profiling
                    </button>
                    <button className={activeTab === 'annotation' ? 'active' : ''} onClick={() => setActiveTab('annotation')}>
                        <FontAwesomeIcon icon={faTags} /> Image Annotation
                    </button>
                    <button className={activeTab === 'pipelines' ? 'active' : ''} onClick={() => setActiveTab('pipelines')}>
                        <FontAwesomeIcon icon={faFolderOpen} /> Pipelines
                    </button>
                    <button className={activeTab === 'diff' ? 'active' : ''} onClick={() => setActiveTab('diff')}>
                        <FontAwesomeIcon icon={faCodeBranch} /> Version Diff
                    </button>
                </div>

                <div className="studio-body">
                    {!isAuthenticated ? (
                        <div className="auth-required-message" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-secondary)' }}>
                            <FontAwesomeIcon icon={faTags} size="3x" style={{ marginBottom: '20px' }} />
                            <h2>Authentication Required</h2>
                            <p>Please log in to your ML Lab account to securely manage your datasets, generate preprocessing pipelines, and establish deep learning annotations.</p>
                        </div>
                    ) : (
                    <>
                    {activeTab === 'manager' && (
                        <div className="manager-tab">
                            <h2>My Cloud Uploads</h2>
                            
                            <div className="upload-container" style={{ margin: '20px 0', padding: '20px', background: 'var(--bg-card)', borderRadius: '12px' }}>
                                <h3>Direct Dataset Upload</h3>
                                <ShowDataset onDatasetUpload={handleDatasetUploadDirect} />
                            </div>
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
                                        {dsPageItems.map(d => (
                                            <tr key={d._id}>
                                                <td title={d.filename} style={{ maxWidth: '260px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.filename}</td>
                                                <td><span className={`badge badge-${d.file_type}`}>{d.file_type.toUpperCase()}</span></td>
                                                <td>{new Date(d.uploaded_at).toLocaleString()}</td>
                                                <td style={{ display: 'flex', gap: '6px' }}>
                                                    {d.file_type === 'csv' && (
                                                        <button className="btn-train-handoff" onClick={() => openTrainPicker(d)} title="Train a model on this dataset">
                                                            <FontAwesomeIcon icon={faPlay} /> Train
                                                        </button>
                                                    )}
                                                    <button className="btn-delete" onClick={() => handleDelete(d._id, d.filename)}>
                                                        <FontAwesomeIcon icon={faTrash} /> Delete
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                            {!loading && datasets.length > 0 && (
                                <Pagination
                                    page={dsPage}
                                    totalPages={dsTotalPages}
                                    totalItems={dsTotalItems}
                                    pageSize={dsPageSize}
                                    onChange={setDsPage}
                                    unitLabel="datasets"
                                />
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
                                        <option key={d._id} value={d._id} title={d.filename}>{truncateName(d.filename, 42)}</option>
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
                                    <button onClick={() => addOperation('drop_columns')}>Drop Columns</button>
                                    <button onClick={() => addOperation('standard_scale')}>Standardize (Z-Score)</button>
                                    <button onClick={() => addOperation('minmax_scale')}>Normalize (MinMax)</button>
                                    <button onClick={() => addOperation('robust_scale')}>Robust Scaler (Outliers)</button>
                                    <button onClick={() => addOperation('label_encode')}>Label Encoding</button>
                                </div>
                            </div>

                            <button 
                                className="btn-run-prep" 
                                onClick={handleRunPreprocessing}
                                disabled={isProcessing || !selectedPrepDataset || prepOperations.length === 0}
                            >
                                {isProcessing ? '⏳ Processing Dataset...' : '▶ Run Pipeline Generator'}
                            </button>

                            {/* Train-on-output handoff: appears once a run produced a dataset. */}
                            {lastOutput && lastOutput.file_type === 'csv' && (
                                <div style={{ marginTop: '14px', padding: '14px', background: 'rgba(52,199,89,0.08)', border: '1px solid rgba(52,199,89,0.25)', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                                        ✅ Ready: <strong title={lastOutput.filename}>{truncateName(lastOutput.filename, 36)}</strong>
                                    </span>
                                    <button
                                        onClick={() => openTrainPicker(lastOutput)}
                                        style={{ padding: '8px 16px', background: 'var(--accent)', color: 'var(--text-on-accent)', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
                                    >
                                        <FontAwesomeIcon icon={faPlay} /> Train on this output
                                    </button>
                                </div>
                            )}

                            {/* Pipeline Templates */}
                            <div className="prep-actions" style={{ marginTop: '16px' }}>
                                <h4>Quick Templates</h4>
                                <div className="button-tray">
                                    {Object.entries(templates).map(([k, v]) => (
                                        <button key={k} onClick={() => handleApplyTemplate(k)} title={v.description}>
                                            📋 {v.name}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Save/Load Pipeline */}
                            <div className="prep-actions" style={{ marginTop: '16px', display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                                <div style={{ flex: 1 }}>
                                    <input type="text" className="form-control" placeholder="Pipeline name..." value={pipelineName} onChange={e => setPipelineName(e.target.value)} style={{ width: '100%' }} />
                                </div>
                                <button onClick={handleSavePipeline} style={{ padding: '8px 16px', background: 'var(--accent)', color: 'var(--text-on-accent)', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                                    <FontAwesomeIcon icon={faSave} /> Save
                                </button>
                            </div>
                            {savedPipelines.length > 0 && (
                                <div className="prep-actions" style={{ marginTop: '8px' }}>
                                    <h4>Saved Pipelines</h4>
                                    <div className="button-tray">
                                        {savedPipelines.map(p => (
                                            <button key={p._id} onClick={() => handleLoadPipeline(p.name)}>
                                                📂 {p.name} ({p.op_count} ops)
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── Profiling Tab ── */}
                    {activeTab === 'profile' && (
                        <div className="preprocessing-tab">
                            <h2>📊 Data Profiling</h2>
                            <p>Analyze column-level statistics: missing%, skew, cardinality, outliers, and quality score.</p>
                            <div className="prep-form-group">
                                <label>Select Dataset:</label>
                                <select className="form-control" value={profileDataset} onChange={e => setProfileDataset(e.target.value)}>
                                    <option value="">-- Choose a CSV dataset --</option>
                                    {datasets.filter(d => d.file_type === 'csv').map(d => <option key={d._id} value={d._id} title={d.filename}>{truncateName(d.filename, 42)}</option>)}
                                </select>
                            </div>
                            <button className="btn-run-prep" onClick={handleLoadProfile} disabled={profiling || !profileDataset}>
                                {profiling ? '⏳ Profiling...' : '🔍 Run Profile'}
                            </button>
                            {profile && (
                                <div style={{ marginTop: '20px' }}>
                                    <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', flexWrap: 'wrap' }}>
                                        <div style={{ padding: '16px', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)', minWidth: '120px', textAlign: 'center' }}>
                                            <div style={{ fontSize: '2rem', fontWeight: '800', color: profile.quality_score >= 70 ? 'var(--success)' : profile.quality_score >= 40 ? 'var(--warning)' : 'var(--danger)' }}>{profile.quality_score}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Quality Score</div>
                                        </div>
                                        <div style={{ padding: '16px', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)', minWidth: '100px', textAlign: 'center' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>{profile.total_rows}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Rows</div>
                                        </div>
                                        <div style={{ padding: '16px', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)', minWidth: '100px', textAlign: 'center' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>{profile.total_columns}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Columns</div>
                                        </div>
                                        <div style={{ padding: '16px', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)', minWidth: '100px', textAlign: 'center' }}>
                                            <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--danger)' }}>{profile.total_missing}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Missing</div>
                                        </div>
                                    </div>
                                    {profile.suggestions?.length > 0 && (
                                        <div style={{ marginBottom: '20px', padding: '12px', background: 'rgba(255,149,0,0.08)', border: '1px solid rgba(255,149,0,0.2)', borderRadius: '8px' }}>
                                            <h4 style={{ marginBottom: '8px' }}>💡 Suggestions</h4>
                                            {profile.suggestions.map((s, i) => <div key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '4px' }}>• {s}</div>)}
                                        </div>
                                    )}
                                    <h4>Column Details</h4>
                                    <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                                        <table className="dataset-table" style={{ fontSize: '12px' }}>
                                            <thead><tr>
                                                <th>Column</th><th>Dtype</th><th>Missing%</th><th>Cardinality</th><th>Mean</th><th>Std</th><th>Skew</th><th>Outliers%</th>
                                            </tr></thead>
                                            <tbody>
                                                {Object.entries(profile.columns).map(([col, c]) => (
                                                    <tr key={col}>
                                                        <td><strong>{col}</strong></td>
                                                        <td>{c.dtype}</td>
                                                        <td style={{ color: c.missing_pct > 20 ? 'var(--danger)' : 'inherit' }}>{c.missing_pct}%</td>
                                                        <td>{c.cardinality}</td>
                                                        <td>{c.mean?.toFixed(2) || '—'}</td>
                                                        <td>{c.std?.toFixed(2) || '—'}</td>
                                                        <td style={{ color: c.high_skew ? 'var(--warning)' : 'inherit' }}>{c.skew?.toFixed(2) || '—'}</td>
                                                        <td style={{ color: c.outlier_pct > 10 ? 'var(--danger)' : 'inherit' }}>{c.outlier_pct?.toFixed(1) || '0'}%</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ── Pipelines Tab ── */}
                    {activeTab === 'pipelines' && (
                        <div className="preprocessing-tab">
                            <h2>📂 Pipeline Library</h2>
                            <p>Your saved preprocessing pipelines and built-in templates.</p>
                            <h3 style={{ marginTop: '20px' }}>Templates</h3>
                            <div className="button-tray" style={{ marginBottom: '20px' }}>
                                {Object.entries(templates).map(([k, v]) => (
                                    <button key={k} onClick={() => handleApplyTemplate(k)} title={v.description}>
                                        📋 {v.name}
                                    </button>
                                ))}
                            </div>
                            <h3>Your Pipelines</h3>
                            {savedPipelines.length === 0 ? (
                                <p style={{ color: 'var(--text-secondary)' }}>No saved pipelines yet. Create one in the Preprocessing tab.</p>
                            ) : (
                                <table className="dataset-table">
                                    <thead><tr><th>Name</th><th>Operations</th><th>Updated</th><th>Actions</th></tr></thead>
                                    <tbody>
                                        {savedPipelines.map(p => (
                                            <tr key={p._id}>
                                                <td><strong>{p.name}</strong></td>
                                                <td>{p.op_count}</td>
                                                <td>{new Date(p.updated_at).toLocaleString()}</td>
                                                <td style={{ display: 'flex', gap: '6px' }}>
                                                    <button className="btn-apply-pipeline" onClick={() => openApplyPipeline(p)} title="Run this pipeline on a dataset">
                                                        <FontAwesomeIcon icon={faPlay} /> Apply to…
                                                    </button>
                                                    <button className="btn-delete" onClick={() => handleLoadPipeline(p.name)}>Load</button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    )}

                    {/* ── Version Diff Tab ── */}
                    {activeTab === 'diff' && (
                        <div className="preprocessing-tab">
                            <h2>🔀 Version Diff</h2>
                            <p>Compare two datasets side-by-side to see what changed after preprocessing.</p>
                            <div className="prep-form-group">
                                <label>Dataset A (Before):</label>
                                <select className="form-control" value={diffA} onChange={e => setDiffA(e.target.value)}>
                                    <option value="">-- Select dataset --</option>
                                    {datasets.filter(d => d.file_type === 'csv').map(d => <option key={d._id} value={d._id} title={d.filename}>{truncateName(d.filename, 42)}</option>)}
                                </select>
                            </div>
                            <div className="prep-form-group">
                                <label>Dataset B (After):</label>
                                <select className="form-control" value={diffB} onChange={e => setDiffB(e.target.value)}>
                                    <option value="">-- Select dataset --</option>
                                    {datasets.filter(d => d.file_type === 'csv').map(d => <option key={d._id} value={d._id} title={d.filename}>{truncateName(d.filename, 42)}</option>)}
                                </select>
                            </div>
                            <button className="btn-run-prep" onClick={handleDiff} disabled={diffing || !diffA || !diffB}>
                                {diffing ? '⏳ Comparing...' : '🔍 Compare'}
                            </button>
                            {diffResult && (
                                <div style={{ marginTop: '20px' }}>
                                    <div style={{ display: 'flex', gap: '20px', marginBottom: '16px', flexWrap: 'wrap' }}>
                                        <div style={{ padding: '12px', background: 'var(--bg-card)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                            <strong title={diffResult.dataset_a.filename}>{truncateName(diffResult.dataset_a.filename, 32)}</strong>: {diffResult.dataset_a.rows} rows, {diffResult.dataset_a.cols} cols
                                        </div>
                                        <div style={{ padding: '12px', background: 'var(--bg-card)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                            <strong title={diffResult.dataset_b.filename}>{truncateName(diffResult.dataset_b.filename, 32)}</strong>: {diffResult.dataset_b.rows} rows, {diffResult.dataset_b.cols} cols
                                        </div>
                                    </div>
                                    <div style={{ padding: '12px', background: diffResult.rows_delta !== 0 ? 'rgba(255,149,0,0.08)' : 'rgba(52,199,89,0.08)', borderRadius: '8px', marginBottom: '12px' }}>
                                        <strong>Rows Delta:</strong> {diffResult.rows_delta > 0 ? '+' : ''}{diffResult.rows_delta}
                                    </div>
                                    {diffResult.columns_added.length > 0 && (
                                        <div style={{ marginBottom: '8px' }}><strong>➕ Added:</strong> {diffResult.columns_added.join(', ') || 'None'}</div>
                                    )}
                                    {diffResult.columns_removed.length > 0 && (
                                        <div style={{ marginBottom: '8px' }}><strong>➖ Removed:</strong> {diffResult.columns_removed.join(', ') || 'None'}</div>
                                    )}
                                    {Object.keys(diffResult.numeric_drift).length > 0 && (
                                        <div style={{ marginTop: '16px' }}>
                                            <h4>Numeric Drift</h4>
                                            <table className="dataset-table" style={{ fontSize: '12px' }}>
                                                <thead><tr><th>Column</th><th>Mean Before</th><th>Mean After</th><th>Drift</th></tr></thead>
                                                <tbody>
                                                    {Object.entries(diffResult.numeric_drift).map(([col, d]) => (
                                                        <tr key={col}>
                                                            <td>{col}</td>
                                                            <td>{d.mean_before.toFixed(4)}</td>
                                                            <td>{d.mean_after.toFixed(4)}</td>
                                                            <td style={{ color: Math.abs(d.drift) > 1 ? 'var(--danger)' : 'var(--warning)' }}>{d.drift.toFixed(4)}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'annotation' && (
                        <div className="annotation-tab">
                            <ImageAnnotation />
                        </div>
                    )}
                    </>
                    )}
                </div>
            </div>

            {/* ── "Train on this output" model picker modal (D7) ── */}
            {trainTarget && (
                <div className="studio-modal-overlay" onClick={() => setTrainTarget(null)}>
                    <div className="studio-modal" onClick={e => e.stopPropagation()}>
                        <h3>Train a model</h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                            Dataset: <strong title={trainTarget.filename}>{truncateName(trainTarget.filename, 40)}</strong>
                        </p>
                        <label style={{ display: 'block', marginTop: '12px', marginBottom: '6px', fontSize: '13px' }}>Choose a model (optional):</label>
                        <select className="form-control" value={trainModelCode} onChange={e => setTrainModelCode(e.target.value)}>
                            <option value="">Let me pick in the Lab</option>
                            {registry && Object.entries(registry.categories).map(([cat, info]) => (
                                <optgroup key={cat} label={info.name}>
                                    {info.models.map(code => (
                                        <option key={code} value={code}>
                                            {registry.models[code]?.icon || ''} {registry.models[code]?.name || code}
                                        </option>
                                    ))}
                                </optgroup>
                            ))}
                        </select>
                        <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                            <button className="btn-modal-cancel" onClick={() => setTrainTarget(null)}>Cancel</button>
                            <button className="btn-modal-confirm" onClick={confirmTrain}>
                                <FontAwesomeIcon icon={faPlay} /> Open in Lab
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ── "Apply pipeline to dataset" picker modal (D8) ── */}
            {applyPipeline && (
                <div className="studio-modal-overlay" onClick={() => !applying && setApplyPipeline(null)}>
                    <div className="studio-modal" onClick={e => e.stopPropagation()}>
                        <h3>Apply pipeline</h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                            Pipeline: <strong>{applyPipeline.name}</strong> ({applyPipeline.operations?.length || 0} ops)
                        </p>
                        <label style={{ display: 'block', marginTop: '12px', marginBottom: '6px', fontSize: '13px' }}>Target dataset:</label>
                        <select className="form-control" value={applyDatasetId} onChange={e => setApplyDatasetId(e.target.value)}>
                            <option value="">-- Choose a CSV dataset --</option>
                            {datasets.filter(d => d.file_type === 'csv').map(d => (
                                <option key={d._id} value={d._id} title={d.filename}>{truncateName(d.filename, 42)}</option>
                            ))}
                        </select>
                        <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                            <button className="btn-modal-cancel" onClick={() => setApplyPipeline(null)} disabled={applying}>Cancel</button>
                            <button className="btn-modal-confirm" onClick={confirmApplyPipeline} disabled={applying || !applyDatasetId}>
                                {applying ? '⏳ Applying...' : <><FontAwesomeIcon icon={faPlay} /> Apply</>}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
