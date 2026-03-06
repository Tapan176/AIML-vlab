/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState, useEffect, useCallback } from 'react';
import constants from '../../constants';

const TAB_CLOUD = 'cloud';
const TAB_UPLOAD = 'upload';

export default function ShowDataset({ onDatasetUpload, ...props }) {
    const [csvData, setCsvData] = useState(null);
    const [imageLinks, setImageLinks] = useState([]);
    const [showDataset, setShowDataset] = useState(false);
    const [activeTab, setActiveTab] = useState(TAB_CLOUD);
    const [loading, setLoading] = useState(false);

    // Cloud Dataset Selection State
    const [cloudDatasets, setCloudDatasets] = useState([]);
    const [selectedCloudDataset, setSelectedCloudDataset] = useState('');
    const [selectedDatasetId, setSelectedDatasetId] = useState(null);

    // Preview state for cloud datasets
    const [cloudPreview, setCloudPreview] = useState(null);
    const [previewLoading, setPreviewLoading] = useState(false);

    // ZIP navigation state
    const [zipCurrentFolder, setZipCurrentFolder] = useState('');

    // Version state
    const [versions, setVersions] = useState([]);
    const [selectedVersion, setSelectedVersion] = useState(null);

    const { allowedTypes } = props;

    const token = localStorage.getItem('aiml_token');

    useEffect(() => {
        const fetchDatasets = async () => {
            try {
                const [defaultRes, userRes] = await Promise.all([
                    fetch(`${constants.API_BASE_URL}/datasets/default`, { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch(`${constants.API_BASE_URL}/user-datasets`, { headers: { 'Authorization': `Bearer ${token}` } })
                ]);
                const defaultData = await defaultRes.json();
                const userData = await userRes.json();

                let combined = [
                    ...(defaultData.datasets || []).map(d => ({ ...d, group: 'Default' })),
                    ...(userData.datasets || []).map(d => ({ ...d, group: 'My Uploads' }))
                ];

                // Filter by allowedTypes if provided
                if (allowedTypes && allowedTypes.length > 0) {
                    combined = combined.filter(d => {
                        const ext = d.filename.split('.').pop().toLowerCase();
                        return allowedTypes.includes(ext);
                    });
                }

                // Group by filename to show only latest version in dropdown
                const latestByName = {};
                combined.forEach(d => {
                    const key = `${d.group}::${d.filename}`;
                    if (!latestByName[key] || (d.version || 1) > (latestByName[key].version || 1)) {
                        latestByName[key] = d;
                    }
                });
                setCloudDatasets(Object.values(latestByName));
            } catch (err) {
                console.error("Failed to fetch cloud datasets:", err);
            }
        };
        fetchDatasets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Fetch versions when a cloud dataset is selected
    const fetchVersions = useCallback(async (filename) => {
        try {
            const res = await fetch(`${constants.API_BASE_URL}/datasets/versions/${encodeURIComponent(filename)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            setVersions(data.versions || []);
        } catch (err) {
            console.error("Failed to fetch versions:", err);
            setVersions([]);
        }
    }, [token]);

    // Fetch preview for a specific dataset ID
    const fetchPreview = useCallback(async (datasetId) => {
        setPreviewLoading(true);
        setCloudPreview(null);
        try {
            const res = await fetch(`${constants.API_BASE_URL}/datasets/${datasetId}/preview`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            setCloudPreview(data);
            setZipCurrentFolder('');
        } catch (err) {
            console.error("Failed to fetch preview:", err);
            setCloudPreview({ error: 'Failed to load preview' });
        } finally {
            setPreviewLoading(false);
        }
    }, [token]);

    function handleCloudSelection(e) {
        const filename = e.target.value;
        setSelectedCloudDataset(filename);
        setCloudPreview(null);
        setVersions([]);
        setSelectedVersion(null);
        setShowDataset(false);

        if (filename) {
            setCsvData(null);
            setImageLinks([]);
            const selectedDs = cloudDatasets.find(d => d.filename === filename);
            setSelectedDatasetId(selectedDs?._id || null);
            onDatasetUpload({
                filename,
                dataset_id: selectedDs?._id || null,
                drive_id: selectedDs?.drive_id || null,
                file_type: selectedDs?.file_type || null,
            });
            fetchVersions(filename);
        } else {
            setSelectedDatasetId(null);
            onDatasetUpload(null);
        }
    }

    function handleVersionChange(e) {
        const versionId = e.target.value;
        if (!versionId) return;
        const ver = versions.find(v => v._id === versionId);
        if (ver) {
            setSelectedVersion(ver);
            setSelectedDatasetId(ver._id);
            onDatasetUpload({
                filename: ver.filename,
                dataset_id: ver._id,
                drive_id: ver.drive_id || null,
                file_type: ver.file_type || null,
                version: ver.version
            });
        }
    }

    function handlePreviewCloud() {
        const idToPreview = selectedVersion?._id || selectedDatasetId;
        if (idToPreview) {
            fetchPreview(idToPreview);
            setShowDataset(true);
        }
    }

    function handleUpload() {
        const fileInput = document.getElementById('formFileMultiple');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a file.');
            return;
        }

        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);

        fetch(`${constants.API_BASE_URL}/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.csv_data) {
                setCsvData(data.csv_data);
                setImageLinks([]);
                onDatasetUpload(data);
            } else if (data.image_links) {
                setImageLinks(data.image_links.map(link => `${constants.API_BASE_URL}/${link}`));
                setCsvData(null);
                onDatasetUpload(data);
            }
            setShowDataset(true);
            setCloudPreview(null);
        })
        .catch(error => console.error('Error uploading file:', error))
        .finally(() => setLoading(false));
    }

    function handleTogglePreview() {
        if (!csvData && imageLinks.length === 0 && !cloudPreview) {
            alert('Please upload or preview a dataset first.');
            return;
        }
        setShowDataset(!showDataset);
    }

    // --- Render Helpers ---

    const renderCSVTable = (columns, rows) => (
        <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '300px', borderRadius: '8px', border: '1px solid var(--border-color, #ddd)' }}>
            <table style={{ minWidth: '100%', borderCollapse: 'collapse' }}>
                <thead>
                    <tr>
                        {columns.map((col, i) => (
                            <th key={i} style={{ border: '1px solid var(--border-color, #ddd)', padding: '8px 12px', background: 'var(--bg-surface, #f5f5f5)', fontWeight: 600, fontSize: '0.85em', position: 'sticky', top: 0 }}>{col}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, ri) => (
                        <tr key={ri}>
                            {columns.map((col, ci) => (
                                <td key={ci} style={{ border: '1px solid var(--border-color, #ddd)', padding: '6px 12px', fontSize: '0.85em' }}>{row[col] ?? ''}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    const renderImageGrid = (images) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', padding: '10px 0', maxHeight: '300px', overflowY: 'auto' }}>
            {images.map((img, i) => (
                <div key={i} style={{ borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-color, #ddd)' }}>
                    <img
                        src={typeof img === 'string' ? img : img.data}
                        alt={typeof img === 'string' ? `Image ${i}` : img.path}
                        style={{ width: '120px', height: '120px', objectFit: 'cover' }}
                    />
                    {typeof img !== 'string' && img.path && (
                        <div style={{ fontSize: '0.7em', padding: '2px 4px', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '120px' }}>
                            {img.path.split('/').pop()}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );

    const renderZipPreview = (preview) => {
        if (!preview) return null;
        if (preview.error) return <div style={{ color: 'red', padding: '10px' }}>⚠ {preview.error}</div>;

        const { folder_tree = [], files_by_folder = {}, total_files = 0, total_images = 0, csv_previews = [], image_thumbnails = [] } = preview;

        // Get contents of current folder
        const currentFolderKey = zipCurrentFolder ? zipCurrentFolder + '/' : '';
        const subfolders = folder_tree.filter(f => {
            if (!zipCurrentFolder) return f.split('/').filter(Boolean).length === 1;
            return f.startsWith(currentFolderKey) && f !== currentFolderKey &&
                   f.replace(currentFolderKey, '').split('/').filter(Boolean).length === 1;
        });
        const currentFiles = files_by_folder[currentFolderKey] || [];

        // Image-related helpers
        const IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'];

        // Filter image thumbnails for current folder (folder-based match)
        const currentImages = image_thumbnails.filter(img => {
            const imgFolder = img.path.substring(0, img.path.lastIndexOf('/'));
            const imgFolderKey = imgFolder ? imgFolder + '/' : '';
            return imgFolderKey === currentFolderKey;
        });

        // Separate image files from other files for this folder
        const currentImageFiles = currentFiles.filter(f => {
            const ext = f.substring(f.lastIndexOf('.')).toLowerCase();
            return IMAGE_EXTS.includes(ext);
        });
        const nonImageFiles = currentFiles.filter(f => !currentImageFiles.includes(f));

        // Fallback: if no folder-based thumbnails, try matching by filename
        let fallbackImages = [];
        if (currentImages.length === 0 && currentImageFiles.length > 0 && image_thumbnails.length > 0) {
            const currentFileNames = new Set(currentImageFiles);
            fallbackImages = image_thumbnails.filter(img => currentFileNames.has(img.path.split('/').pop()));
        }

        const folderBtnStyle = {
            padding: '8px 14px', borderRadius: '8px',
            border: '2px solid #6c63ff', background: '#f0eeff',
            cursor: 'pointer', fontSize: '0.9em', fontWeight: 500,
            color: '#333', display: 'flex', alignItems: 'center', gap: '6px'
        };

        return (
            <div style={{ padding: '10px 0' }}>
                {/* Stats bar */}
                <div style={{ fontSize: '0.85em', color: '#666', marginBottom: '10px', display: 'flex', gap: '15px' }}>
                    <span>📁 {folder_tree.length} folders</span>
                    <span>📄 {total_files} files</span>
                    <span>🖼 {total_images} images</span>
                </div>

                {/* Breadcrumb navigation */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '10px', fontSize: '0.9em', flexWrap: 'wrap' }}>
                    <button onClick={() => setZipCurrentFolder('')}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6c63ff', fontWeight: !zipCurrentFolder ? 'bold' : 'normal', fontSize: '0.95em' }}>
                        📦 root
                    </button>
                    {zipCurrentFolder && zipCurrentFolder.split('/').filter(Boolean).map((part, i, arr) => {
                        const path = arr.slice(0, i + 1).join('/');
                        return (
                            <React.Fragment key={path}>
                                <span style={{ color: '#999' }}>/</span>
                                <button onClick={() => setZipCurrentFolder(path)}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6c63ff', fontWeight: i === arr.length - 1 ? 'bold' : 'normal', fontSize: '0.95em' }}>
                                    {part}
                                </button>
                            </React.Fragment>
                        );
                    })}
                </div>

                {/* Folder list */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
                    {zipCurrentFolder && (
                        <button onClick={() => {
                            const parts = zipCurrentFolder.split('/').filter(Boolean);
                            parts.pop();
                            setZipCurrentFolder(parts.join('/'));
                        }} style={{ ...folderBtnStyle, background: '#e8e8e8', border: '2px solid #ccc' }}>
                            📁 ..
                        </button>
                    )}
                    {subfolders.map(folder => {
                        const displayName = folder.replace(currentFolderKey, '').replace(/\/$/, '');
                        return (
                            <button key={folder} onClick={() => setZipCurrentFolder(folder.replace(/\/$/, ''))}
                                style={folderBtnStyle}>
                                📁 {displayName}
                            </button>
                        );
                    })}
                </div>

                {/* File list (non-image files only, since images are shown as thumbnails) */}
                {nonImageFiles.length > 0 && (
                    <div style={{ marginBottom: '10px', fontSize: '0.85em', color: '#555' }}>
                        <div style={{ fontWeight: 600, marginBottom: '4px' }}>Files ({nonImageFiles.length}):</div>
                        {nonImageFiles.slice(0, 50).map((f, i) => (
                            <div key={i} style={{ padding: '2px 0' }}>📄 {f}</div>
                        ))}
                        {nonImageFiles.length > 50 && <div style={{ fontStyle: 'italic' }}>...and {nonImageFiles.length - 50} more files</div>}
                    </div>
                )}

                {/* Image thumbnails for current folder (with fallbacks) */}
                {(currentImages.length > 0 || fallbackImages.length > 0 || (image_thumbnails.length > 0 && !zipCurrentFolder)) && (
                    <div>
                        <h5 style={{ margin: '10px 0 5px', color: '#333' }}>
                            🖼 Image Samples {currentImages.length > 0 || fallbackImages.length > 0 ? '' : `(${total_images} total)`}
                        </h5>
                        {renderImageGrid(
                            currentImages.length > 0
                                ? currentImages
                                : (fallbackImages.length > 0
                                    ? fallbackImages
                                    : image_thumbnails)
                        )}
                    </div>
                )}

                {/* If in a folder with image files but absolutely no thumbnails available */}
                {currentImages.length === 0 && fallbackImages.length === 0 && currentImageFiles.length > 0 && image_thumbnails.length === 0 && (
                    <div style={{ padding: '10px', color: '#666', fontStyle: 'italic' }}>
                        🖼 {currentImageFiles.length} image files in this folder
                    </div>
                )}

                {/* Inline CSV previews */}
                {csv_previews.length > 0 && csv_previews.map((csvP, idx) => (
                    <div key={idx} style={{ marginTop: '15px' }}>
                        <h5 style={{ margin: '5px 0' }}>📊 {csvP.path} ({csvP.total_rows_shown} rows shown)</h5>
                        {renderCSVTable(csvP.columns, csvP.rows)}
                    </div>
                ))}
            </div>
        );
    };


    const hasPreviewData = csvData || imageLinks.length > 0 || cloudPreview;

    return (
        <div className="dataset-selection-container" style={{ maxWidth: '100%', marginBottom: '20px' }}>
            <h2>Dataset Selection</h2>

            {/* Tab Toggle */}
            <div style={{ display: 'flex', gap: '0', marginBottom: '15px', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-color, #ddd)', width: 'fit-content' }}>
                <button onClick={() => setActiveTab(TAB_CLOUD)}
                    style={{ padding: '10px 20px', border: 'none', cursor: 'pointer', fontWeight: activeTab === TAB_CLOUD ? 'bold' : 'normal',
                             background: activeTab === TAB_CLOUD ? 'var(--primary, #6c63ff)' : 'var(--bg-card, #fff)',
                             color: activeTab === TAB_CLOUD ? '#fff' : 'var(--text-primary, #333)', transition: 'all 0.2s' }}>
                    ☁️ Cloud Library
                </button>
                <button onClick={() => setActiveTab(TAB_UPLOAD)}
                    style={{ padding: '10px 20px', border: 'none', cursor: 'pointer', fontWeight: activeTab === TAB_UPLOAD ? 'bold' : 'normal',
                             background: activeTab === TAB_UPLOAD ? 'var(--primary, #6c63ff)' : 'var(--bg-card, #fff)',
                             color: activeTab === TAB_UPLOAD ? '#fff' : 'var(--text-primary, #333)', transition: 'all 0.2s' }}>
                    ⬆️ Upload New
                </button>
            </div>

            {/* Cloud Tab */}
            {activeTab === TAB_CLOUD && (
                <div style={{ padding: '15px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', marginBottom: '15px' }}>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <select className="form-control" value={selectedCloudDataset} onChange={handleCloudSelection}
                            style={{ maxWidth: '350px', padding: '8px', borderRadius: '8px', border: '1px solid var(--border-color, #ddd)' }}>
                            <option value="">-- Choose a dataset --</option>
                            <optgroup label="Default Datasets">
                                {cloudDatasets.filter(d => d.group === 'Default').length === 0 ? (
                                    <option value="" disabled>No default datasets</option>
                                ) : cloudDatasets.filter(d => d.group === 'Default').map(d => (
                                    <option key={`def-${d._id}`} value={d.filename}>{d.filename} {d.version > 1 ? `(v${d.version})` : ''}</option>
                                ))}
                            </optgroup>
                            <optgroup label="My Uploads">
                                {cloudDatasets.filter(d => d.group === 'My Uploads').length === 0 ? (
                                    <option value="" disabled>No user datasets</option>
                                ) : cloudDatasets.filter(d => d.group === 'My Uploads').map(d => (
                                    <option key={`usr-${d._id}`} value={d.filename}>{d.filename} {d.version > 1 ? `(v${d.version})` : ''}</option>
                                ))}
                            </optgroup>
                        </select>

                        {/* Version selector */}
                        {versions.length > 1 && (
                            <select className="form-control" onChange={handleVersionChange}
                                value={selectedVersion?._id || selectedDatasetId || ''}
                                style={{ maxWidth: '180px', padding: '8px', borderRadius: '8px', border: '1px solid var(--border-color, #ddd)' }}>
                                {versions.map(v => (
                                    <option key={v._id} value={v._id}>v{v.version} — {v.uploaded_at ? new Date(v.uploaded_at).toLocaleDateString() : ''}</option>
                                ))}
                            </select>
                        )}

                        {selectedCloudDataset && (
                            <button onClick={handlePreviewCloud} disabled={previewLoading}
                                style={{ padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer', background: '#6c63ff', color: 'white', opacity: previewLoading ? 0.6 : 1 }}>
                                {previewLoading ? '⏳ Loading...' : '👁 Preview'}
                            </button>
                        )}
                    </div>
                    {selectedCloudDataset && <div style={{ color: 'green', fontSize: '0.9em', marginTop: '8px' }}>✓ Selected: {selectedCloudDataset}{selectedVersion ? ` (v${selectedVersion.version})` : ''}</div>}
                </div>
            )}

            {/* Upload Tab */}
            {activeTab === TAB_UPLOAD && (
                <div style={{ padding: '15px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', marginBottom: '15px' }}>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <input className="form-control" type="file" id="formFileMultiple" multiple
                               style={{ maxWidth: '300px' }}
                               accept={allowedTypes ? allowedTypes.map(t => typeof t === 'string' && !t.startsWith('.') ? `.${t}` : t).join(',') : undefined}
                        />
                        <button onClick={handleUpload} disabled={loading}
                            style={{ padding: '8px 16px', border: 'none', borderRadius: '8px', cursor: 'pointer', background: '#6c63ff', color: 'white', opacity: loading ? 0.6 : 1 }}>
                            {loading ? '⏳ Uploading...' : '⬆ Upload Dataset'}
                        </button>
                    </div>
                </div>
            )}

            {/* Show/Hide Preview toggle */}
            {hasPreviewData && (
                <button onClick={handleTogglePreview}
                    style={{ padding: '8px 16px', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer', background: 'var(--bg-card)', color: 'var(--text-primary)', marginBottom: '10px' }}>
                    {showDataset ? '👁 Hide Preview' : '👁 Show Preview'}
                </button>
            )}

            {/* Preview Content */}
            {showDataset && (
                <div style={{ marginTop: '10px' }}>
                    {/* Cloud preview */}
                    {cloudPreview && cloudPreview.preview_type === 'csv' && cloudPreview.rows && (
                        <div>
                            <h5 style={{ margin: '5px 0' }}>📊 CSV Preview ({cloudPreview.total_rows_shown} rows)</h5>
                            {renderCSVTable(cloudPreview.columns, cloudPreview.rows)}
                        </div>
                    )}
                    {cloudPreview && cloudPreview.preview_type === 'zip' && renderZipPreview(cloudPreview)}
                    {cloudPreview && cloudPreview.preview_type === 'unsupported' && (
                        <div style={{ padding: '15px', color: 'var(--text-secondary, #666)' }}>Preview not available for this file type.</div>
                    )}

                    {/* Local upload CSV preview */}
                    {csvData && !cloudPreview && (
                        <div>
                            <h5 style={{ margin: '5px 0' }}>📊 Uploaded CSV Preview</h5>
                            {renderCSVTable(Object.keys(csvData[0]), csvData)}
                        </div>
                    )}

                    {/* Local upload image preview */}
                    {imageLinks.length > 0 && !cloudPreview && (
                        <div>
                            <h5 style={{ margin: '5px 0' }}>🖼 Uploaded Images</h5>
                            {renderImageGrid(imageLinks)}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
