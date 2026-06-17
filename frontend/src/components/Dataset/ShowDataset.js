/* eslint-disable jsx-a11y/img-redundant-alt */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import constants from '../../constants';
import api from '../../services/api';
import { truncateName } from '../../utils/truncateName';

const TAB_CLOUD = 'cloud';
const TAB_UPLOAD = 'upload';

/**
 * Sub-component that fetches thumbnails on-demand for a specific folder
 * when the initial preview didn't include them (e.g. more than 50 images per folder).
 */
function OnDemandFolderImages({ datasetId, folder, imageCount, renderImageGrid }) {
    const [images, setImages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [fetched, setFetched] = useState(false);

    useEffect(() => {
        if (!datasetId || fetched) return;
        setLoading(true);
        api.get(`/datasets/${datasetId}/folder-images?folder=${encodeURIComponent(folder)}`)
        .then(data => {
            setImages(data.thumbnails || []);
            setFetched(true);
        })
        .catch(err => {
            console.error('Failed to fetch folder images:', err);
            setFetched(true);
        })
        .finally(() => setLoading(false));
    }, [datasetId, folder, fetched]);

    if (loading) {
        return (
            <div style={{ padding: '15px', textAlign: 'center', color: 'var(--accent)' }}>
                <span style={{ fontSize: '1.2em' }}>⏳</span> Loading {imageCount} images...
            </div>
        );
    }

    if (images.length > 0) {
        return (
            <div>
                <h5 style={{ margin: '10px 0 5px', color: 'var(--text-primary)' }}>
                    🖼 Images ({imageCount})
                </h5>
                {renderImageGrid(images)}
            </div>
        );
    }

    if (fetched && images.length === 0) {
        return (
            <div style={{ padding: '10px', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                🖼 {imageCount} image files in this folder (thumbnails unavailable)
            </div>
        );
    }

    return null;
}

export default function ShowDataset({ onDatasetUpload, initialFilename, onColumnsDetected, ...props }) {
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

    // Stable refs to the parent callbacks so column/restore effects don't
    // re-run just because the parent re-rendered with new function identities.
    const onColumnsDetectedRef = useRef(onColumnsDetected);
    onColumnsDetectedRef.current = onColumnsDetected;
    const onDatasetUploadRef = useRef(onDatasetUpload);
    onDatasetUploadRef.current = onDatasetUpload;
    // Guards the one-shot pre-selection of a cached/replayed dataset.
    const restoredRef = useRef(false);

    // Fetch a dataset's columns (CSV only) and hand them to the parent so it
    // can render column pickers (used by the fine-tuning pages). Best-effort —
    // a failure just leaves the parent on its manual-entry fallback.
    const loadColumns = useCallback(async (datasetId) => {
        if (!datasetId || !onColumnsDetectedRef.current) return;
        try {
            const data = await api.get(`/datasets/${datasetId}/preview`);
            if (data && data.preview_type === 'csv' && Array.isArray(data.columns)) {
                onColumnsDetectedRef.current(data.columns);
            }
        } catch (err) {
            // Non-fatal: parent keeps its manual column entry.
        }
    }, []);

    useEffect(() => {
        const fetchDatasets = async () => {
            try {
                const [defaultData, userData] = await Promise.all([
                    api.get('/datasets/default'),
                    api.get('/user-datasets'),
                ]);

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

    // Pre-select a cached/replayed dataset once the cloud list has loaded, so
    // re-opening a model page (or a Dashboard "Replay") shows the dataset that
    // was actually used instead of "-- Choose a dataset --". Runs once.
    useEffect(() => {
        if (restoredRef.current || !initialFilename || cloudDatasets.length === 0) return;
        const match = cloudDatasets.find(d => d.filename === initialFilename);
        if (!match) return;
        restoredRef.current = true;
        setSelectedCloudDataset(match.filename);
        setSelectedDatasetId(match._id || null);
        onDatasetUploadRef.current({
            filename: match.filename,
            dataset_id: match._id || null,
            drive_id: match.drive_id || null,
            file_type: match.file_type || null,
        });
        fetchVersions(match.filename);
        loadColumns(match._id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [cloudDatasets, initialFilename]);

    // Fetch versions when a cloud dataset is selected
    const fetchVersions = useCallback(async (filename) => {
        try {
            const data = await api.get(`/datasets/versions/${encodeURIComponent(filename)}`);
            setVersions(data.versions || []);
        } catch (err) {
            console.error("Failed to fetch versions:", err);
            setVersions([]);
        }
    }, []);

    // Fetch preview for a specific dataset ID
    const fetchPreview = useCallback(async (datasetId) => {
        setPreviewLoading(true);
        setCloudPreview(null);
        try {
            const data = await api.get(`/datasets/${datasetId}/preview`);
            setCloudPreview(data);
            setZipCurrentFolder('');
        } catch (err) {
            console.error("Failed to fetch preview:", err);
            setCloudPreview({ error: 'Failed to load preview' });
        } finally {
            setPreviewLoading(false);
        }
    }, []);

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
            loadColumns(selectedDs?._id);
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
            loadColumns(ver._id);
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

        api.upload('/upload', formData)
        .then(data => {
            if (data.csv_data) {
                setCsvData(data.csv_data);
                setImageLinks([]);
                onDatasetUpload(data);
                // Surface columns from the freshly uploaded CSV for column pickers.
                if (onColumnsDetectedRef.current && Array.isArray(data.csv_data) && data.csv_data.length > 0) {
                    onColumnsDetectedRef.current(Object.keys(data.csv_data[0]));
                }
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
                            <th key={i} style={{ border: '1px solid var(--border-color, #ddd)', padding: '8px 12px', background: 'var(--bg-elevated)', fontWeight: 600, fontSize: '0.85em', position: 'sticky', top: 0 }}>{col}</th>
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

        // Determine which images to show
        const imagesToShow = currentImages.length > 0 ? currentImages : [];
        const hasImageFiles = currentImageFiles.length > 0;
        const needsOnDemandFetch = hasImageFiles && currentImages.length === 0;

        const folderBtnStyle = {
            padding: '8px 14px', borderRadius: '8px',
            border: '2px solid var(--accent)', background: 'var(--accent-soft)',
            cursor: 'pointer', fontSize: '0.9em', fontWeight: 500,
            color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px'
        };

        return (
            <div style={{ padding: '10px 0' }}>
                {/* Stats bar */}
                <div style={{ fontSize: '0.85em', color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', gap: '15px' }}>
                    <span>📁 {folder_tree.length} folders</span>
                    <span>📄 {total_files} files</span>
                    <span>🖼 {total_images} images</span>
                </div>

                {/* Breadcrumb navigation */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '10px', fontSize: '0.9em', flexWrap: 'wrap' }}>
                    <button onClick={() => setZipCurrentFolder('')}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontWeight: !zipCurrentFolder ? 'bold' : 'normal', fontSize: '0.95em' }}>
                        📦 root
                    </button>
                    {zipCurrentFolder && zipCurrentFolder.split('/').filter(Boolean).map((part, i, arr) => {
                        const path = arr.slice(0, i + 1).join('/');
                        return (
                            <React.Fragment key={path}>
                                <span style={{ color: 'var(--text-tertiary)' }}>/</span>
                                <button onClick={() => setZipCurrentFolder(path)}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontWeight: i === arr.length - 1 ? 'bold' : 'normal', fontSize: '0.95em' }}>
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
                        }} style={{ ...folderBtnStyle, background: 'var(--bg-elevated)', border: '2px solid var(--border-strong)' }}>
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
                    <div style={{ marginBottom: '10px', fontSize: '0.85em', color: 'var(--text-secondary)' }}>
                        <div style={{ fontWeight: 600, marginBottom: '4px' }}>Files ({nonImageFiles.length}):</div>
                        {nonImageFiles.slice(0, 50).map((f, i) => (
                            <div key={i} style={{ padding: '2px 0' }}>📄 {f}</div>
                        ))}
                        {nonImageFiles.length > 50 && <div style={{ fontStyle: 'italic' }}>...and {nonImageFiles.length - 50} more files</div>}
                    </div>
                )}

                {/* Image thumbnails for current folder */}
                {imagesToShow.length > 0 && (
                    <div>
                        <h5 style={{ margin: '10px 0 5px', color: 'var(--text-primary)' }}>
                            🖼 {currentImageFiles.length > 0 ? `Images (${currentImageFiles.length})` : 'Image Samples'}
                        </h5>
                        {renderImageGrid(imagesToShow)}
                    </div>
                )}

                {/* On-demand fetch for folders that have image files but no pre-loaded thumbnails */}
                {needsOnDemandFetch && (
                    <OnDemandFolderImages
                        datasetId={selectedVersion?._id || selectedDatasetId}
                        folder={currentFolderKey}
                        imageCount={currentImageFiles.length}
                        renderImageGrid={renderImageGrid}
                    />
                )}

                {/* Root level: show all pre-loaded sample thumbnails when no specific folder */}
                {!zipCurrentFolder && imagesToShow.length === 0 && image_thumbnails.length > 0 && !hasImageFiles && (
                    <div>
                        <h5 style={{ margin: '10px 0 5px', color: 'var(--text-primary)' }}>
                            🖼 Image Samples ({total_images} total)
                        </h5>
                        {renderImageGrid(image_thumbnails)}
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
                             background: activeTab === TAB_CLOUD ? 'var(--accent)' : 'var(--bg-card, #fff)',
                             color: activeTab === TAB_CLOUD ? 'var(--text-on-accent)' : 'var(--text-primary)', transition: 'all 0.2s' }}>
                    ☁️ Cloud Library
                </button>
                <button onClick={() => setActiveTab(TAB_UPLOAD)}
                    style={{ padding: '10px 20px', border: 'none', cursor: 'pointer', fontWeight: activeTab === TAB_UPLOAD ? 'bold' : 'normal',
                             background: activeTab === TAB_UPLOAD ? 'var(--accent)' : 'var(--bg-card, #fff)',
                             color: activeTab === TAB_UPLOAD ? 'var(--text-on-accent)' : 'var(--text-primary)', transition: 'all 0.2s' }}>
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
                                    <option key={`def-${d._id}`} value={d.filename} title={d.filename}>{truncateName(d.filename, 40)} {d.version > 1 ? `(v${d.version})` : ''}</option>
                                ))}
                            </optgroup>
                            <optgroup label="My Uploads">
                                {cloudDatasets.filter(d => d.group === 'My Uploads').length === 0 ? (
                                    <option value="" disabled>No user datasets</option>
                                ) : cloudDatasets.filter(d => d.group === 'My Uploads').map(d => (
                                    <option key={`usr-${d._id}`} value={d.filename} title={d.filename}>{truncateName(d.filename, 40)} {d.version > 1 ? `(v${d.version})` : ''}</option>
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
                                style={{ padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer', background: 'var(--accent)', color: 'var(--text-on-accent)', opacity: previewLoading ? 0.6 : 1 }}>
                                {previewLoading ? '⏳ Loading...' : '👁 Preview'}
                            </button>
                        )}
                    </div>
                    {selectedCloudDataset && <div style={{ color: 'green', fontSize: '0.9em', marginTop: '8px' }} title={selectedCloudDataset}>✓ Selected: {truncateName(selectedCloudDataset, 48)}{selectedVersion ? ` (v${selectedVersion.version})` : ''}</div>}
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
                            style={{ padding: '8px 16px', border: 'none', borderRadius: '8px', cursor: 'pointer', background: 'var(--accent)', color: 'var(--text-on-accent)', opacity: loading ? 0.6 : 1 }}>
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
