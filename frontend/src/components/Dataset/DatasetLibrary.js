import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { API_URL } from '../../constants';
import './DatasetLibrary.css';

const DatasetLibrary = () => {
    const { token } = useAuth();
    const [datasets, setDatasets] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    const fetchDatasets = async () => {
        try {
            setLoading(true);
            const [defaultRes, userRes] = await Promise.all([
                fetch(`${API_URL}/datasets/default`, { headers: { 'Authorization': `Bearer ${token}` } }),
                fetch(`${API_URL}/user-datasets`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);

            if (!defaultRes.ok || !userRes.ok) throw new Error("Failed to load datasets.");

            const defaultData = await defaultRes.json();
            const userData = await userRes.json();
            
            // Deduplicate if necessary, though they should be distinct
            const combined = [...(defaultData.datasets || []), ...(userData.datasets || [])];
            // Sort by uploaded_at descending
            combined.sort((a, b) => new Date(b.uploaded_at || 0) - new Date(a.uploaded_at || 0));
            setDatasets(combined);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (token) {
            fetchDatasets();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    const handleDownload = (driveId) => {
        window.open(`https://drive.google.com/uc?export=download&id=${driveId}`, '_blank');
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            setUploading(true);
            setError(null);
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || 'Upload failed');
            }

            // Refresh datasets
            await fetchDatasets();
        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const filteredDatasets = datasets.filter(d => 
        d.filename?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading && datasets.length === 0) return <div className="library-loading">Loading datasets...</div>;

    return (
        <div className="dataset-library">
            <header className="library-header">
                <h1>📚 Datasets Library</h1>
                <p>Browse, search, and upload datasets for ML model training.</p>
                <div className="library-controls">
                    <input 
                        type="text" 
                        className="search-input" 
                        placeholder="Search datasets..." 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button 
                        className="btn-upload-dataset" 
                        onClick={handleUploadClick}
                        disabled={uploading}
                    >
                        {uploading ? <span className="spinner-sm"></span> : '⬆️ Upload Dataset'}
                    </button>
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        style={{ display: 'none' }} 
                        onChange={handleFileChange} 
                        accept=".csv,.zip"
                    />
                </div>
                {error && <div className="library-error" style={{marginTop: '1rem', color: '#ff3b30', fontSize: '0.9rem'}}>{error}</div>}
            </header>

            {filteredDatasets.length === 0 ? (
                <div className="empty-state">
                    <p>No datasets found.</p>
                </div>
            ) : (
                <div className="dataset-grid">
                    {filteredDatasets.map((dataset) => (
                        <div className="dataset-card" key={dataset._id}>
                            <div className="dataset-icon">
                                {dataset.file_type === 'csv' ? '📊' : dataset.file_type === 'zip' ? '🗂️' : '📄'}
                            </div>
                            <div className="dataset-info">
                                <h3>{dataset.filename}</h3>
                                <p className="dataset-date">Added {new Date(dataset.uploaded_at).toLocaleDateString()}</p>
                                <div className="dataset-badges">
                                    <span className="badge type-badge">{dataset.file_type?.toUpperCase()}</span>
                                    {dataset.is_default ? (
                                        <span className="badge model-badge" style={{background: 'rgba(52, 199, 89, 0.1)', color: '#34c759'}}>Default</span>
                                    ) : (
                                        <span className="badge model-badge" style={{background: 'rgba(255, 149, 0, 0.1)', color: '#ff9500'}}>Personal</span>
                                    )}
                                    {dataset.supported_models && dataset.supported_models.map(m => (
                                        <span key={m} className="badge model-badge">{m}</span>
                                    ))}
                                </div>
                            </div>
                            <button 
                                className="btn-download"
                                onClick={() => handleDownload(dataset.drive_id || dataset.profile_photo_id)}
                                disabled={!dataset.drive_id}
                                title={!dataset.drive_id ? "Drive ID missing" : "Download Dataset"}
                            >
                                ⬇️ Download
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default DatasetLibrary;
