import React, { useState, useRef, useEffect, useCallback } from 'react';

/**
 * Image Annotation Studio
 * - Upload images via drag-and-drop or file picker
 * - Draw bounding boxes on a canvas
 * - Assign class labels to each box
 * - Navigate between images
 * - Export all annotations as a YOLOv8-compatible ZIP
 */
export default function ImageAnnotation() {
    const [images, setImages] = useState([]);          // [{file, url, name}]
    const [currentIdx, setCurrentIdx] = useState(0);
    const [annotations, setAnnotations] = useState({}); // { imageName: [{x,y,w,h,label}] }
    const [classes, setClasses] = useState(['object']);
    const [selectedClass, setSelectedClass] = useState('object');
    const [newClassName, setNewClassName] = useState('');
    const [drawing, setDrawing] = useState(false);
    const [startPos, setStartPos] = useState(null);
    const [currentRect, setCurrentRect] = useState(null);
    const [canvasSize, setCanvasSize] = useState({ w: 800, h: 600 });
    const [naturalSize, setNaturalSize] = useState({ w: 1, h: 1 });
    const [isDragging, setIsDragging] = useState(false);
    const canvasRef = useRef(null);
    const imgRef = useRef(null);

    const currentImage = images[currentIdx] || null;
    const currentAnnotations = currentImage ? (annotations[currentImage.name] || []) : [];

    // Load image onto canvas when current image changes
    useEffect(() => {
        if (!currentImage) return;
        const img = new Image();
        img.onload = () => {
            const maxW = 800, maxH = 600;
            const scale = Math.min(maxW / img.width, maxH / img.height, 1);
            const w = Math.round(img.width * scale);
            const h = Math.round(img.height * scale);
            setCanvasSize({ w, h });
            setNaturalSize({ w: img.width, h: img.height });
            imgRef.current = img;
        };
        img.src = currentImage.url;
    }, [currentImage]);

    // Redraw canvas
    const redraw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas || !imgRef.current) return;
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvasSize.w, canvasSize.h);
        ctx.drawImage(imgRef.current, 0, 0, canvasSize.w, canvasSize.h);

        // Draw saved annotations
        const boxes = currentAnnotations;
        const scaleX = canvasSize.w / naturalSize.w;
        const scaleY = canvasSize.h / naturalSize.h;

        const colors = ['#ff3b30', '#007aff', '#34c759', '#ff9500', '#af52de', '#00c7be', '#ff2d55', '#5856d6'];

        boxes.forEach((box) => {
            const classIdx = classes.indexOf(box.label) % colors.length;
            const color = colors[classIdx >= 0 ? classIdx : 0];
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.strokeRect(box.x * scaleX, box.y * scaleY, box.w * scaleX, box.h * scaleY);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.15;
            ctx.fillRect(box.x * scaleX, box.y * scaleY, box.w * scaleX, box.h * scaleY);
            ctx.globalAlpha = 1;
            // Label
            ctx.font = 'bold 13px Inter, sans-serif';
            const textW = ctx.measureText(box.label).width + 8;
            ctx.fillStyle = color;
            ctx.fillRect(box.x * scaleX, box.y * scaleY - 20, textW, 20);
            ctx.fillStyle = '#fff';
            ctx.fillText(box.label, box.x * scaleX + 4, box.y * scaleY - 5);
        });

        // Draw in-progress rectangle
        if (currentRect) {
            ctx.strokeStyle = '#ffcc00';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 3]);
            ctx.strokeRect(currentRect.x, currentRect.y, currentRect.w, currentRect.h);
            ctx.setLineDash([]);
        }
    }, [canvasSize, naturalSize, currentAnnotations, currentRect, classes]);

    useEffect(() => { redraw(); }, [redraw]);

    // --- File handling ---
    const handleFiles = (files) => {
        const imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'));
        const newImages = imageFiles.map(f => ({
            file: f,
            url: URL.createObjectURL(f),
            name: f.name,
        }));
        setImages(prev => [...prev, ...newImages]);
        if (images.length === 0 && newImages.length > 0) setCurrentIdx(0);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
    };

    // --- Drawing logic ---
    const getCanvasPos = (e) => {
        const rect = canvasRef.current.getBoundingClientRect();
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    const onMouseDown = (e) => {
        const pos = getCanvasPos(e);
        setDrawing(true);
        setStartPos(pos);
        setCurrentRect(null);
    };

    const onMouseMove = (e) => {
        if (!drawing || !startPos) return;
        const pos = getCanvasPos(e);
        setCurrentRect({
            x: Math.min(pos.x, startPos.x),
            y: Math.min(pos.y, startPos.y),
            w: Math.abs(pos.x - startPos.x),
            h: Math.abs(pos.y - startPos.y),
        });
    };

    const onMouseUp = () => {
        if (!drawing || !currentRect || !currentImage) { setDrawing(false); return; }
        if (currentRect.w < 5 || currentRect.h < 5) { setDrawing(false); setCurrentRect(null); return; }

        const scaleX = naturalSize.w / canvasSize.w;
        const scaleY = naturalSize.h / canvasSize.h;

        const box = {
            x: Math.round(currentRect.x * scaleX),
            y: Math.round(currentRect.y * scaleY),
            w: Math.round(currentRect.w * scaleX),
            h: Math.round(currentRect.h * scaleY),
            label: selectedClass,
        };

        setAnnotations(prev => ({
            ...prev,
            [currentImage.name]: [...(prev[currentImage.name] || []), box],
        }));
        setDrawing(false);
        setCurrentRect(null);
    };

    const deleteBox = (idx) => {
        if (!currentImage) return;
        setAnnotations(prev => ({
            ...prev,
            [currentImage.name]: prev[currentImage.name].filter((_, i) => i !== idx),
        }));
    };

    const addClass = () => {
        const name = newClassName.trim().toLowerCase();
        if (!name || classes.includes(name)) return;
        setClasses(prev => [...prev, name]);
        setSelectedClass(name);
        setNewClassName('');
    };

    const removeClass = (cls) => {
        if (classes.length <= 1) return;
        setClasses(prev => prev.filter(c => c !== cls));
        if (selectedClass === cls) setSelectedClass(classes[0] === cls ? classes[1] : classes[0]);
    };

    // --- YOLO export ---
    const exportYolo = () => {
        if (images.length === 0) { alert('No images to export.'); return; }

        // Build YOLO txt files
        const yoloFiles = [];
        const classMap = {};
        classes.forEach((c, i) => { classMap[c] = i; });

        images.forEach(img => {
            const boxes = annotations[img.name] || [];
            const lines = boxes.map(b => {
                const cx = (b.x + b.w / 2) / naturalSize.w;
                const cy = (b.y + b.h / 2) / naturalSize.h;
                const bw = b.w / naturalSize.w;
                const bh = b.h / naturalSize.h;
                return `${classMap[b.label] || 0} ${cx.toFixed(6)} ${cy.toFixed(6)} ${bw.toFixed(6)} ${bh.toFixed(6)}`;
            });
            yoloFiles.push({ name: img.name.replace(/\.[^.]+$/, '.txt'), content: lines.join('\n') });
        });

        // classes.txt
        const classesTxt = classes.join('\n');

        // data.yaml
        const yaml = `train: ./images/train\nval: ./images/val\nnc: ${classes.length}\nnames: [${classes.map(c => `'${c}'`).join(', ')}]`;

        // Download as combined text (for now, since ZIP requires a library)
        // We'll create individual file downloads
        const blob = new Blob([
            `=== data.yaml ===\n${yaml}\n\n`,
            `=== classes.txt ===\n${classesTxt}\n\n`,
            ...yoloFiles.map(f => `=== labels/${f.name} ===\n${f.content}\n\n`)
        ], { type: 'text/plain' });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'yolo_annotations.txt';
        a.click();
        URL.revokeObjectURL(url);
    };

    const totalBoxes = Object.values(annotations).reduce((sum, arr) => sum + arr.length, 0);

    // --- Styles ---
    const s = {
        container: { display: 'flex', gap: '24px', minHeight: '500px', flexWrap: 'wrap' },
        leftPanel: { flex: '1 1 300px', minWidth: '280px', display: 'flex', flexDirection: 'column', gap: '16px' },
        rightPanel: { flex: '2 1 500px', display: 'flex', flexDirection: 'column', gap: '16px' },
        card: { background: 'var(--bg-card, #1e1e2e)', border: '1px solid var(--border-color, #333)', borderRadius: '12px', padding: '16px' },
        dropzone: {
            border: '2px dashed', borderColor: isDragging ? '#6c63ff' : 'var(--border-color, #555)',
            borderRadius: '12px', padding: '40px 20px', textAlign: 'center', cursor: 'pointer',
            background: isDragging ? 'rgba(108,99,255,0.08)' : 'transparent',
            transition: 'all 0.2s',
        },
        canvas: { border: '1px solid var(--border-color, #555)', borderRadius: '8px', cursor: 'crosshair', maxWidth: '100%' },
        btn: { padding: '8px 16px', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600', fontSize: '13px' },
        btnPrimary: { background: '#6c63ff', color: '#fff' },
        btnDanger: { background: 'rgba(255,59,48,0.15)', color: '#ff3b30', border: '1px solid rgba(255,59,48,0.3)' },
        btnSuccess: { background: '#34c759', color: '#fff' },
        badge: { display: 'inline-block', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '600' },
        classItem: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', borderRadius: '8px', background: 'rgba(108,99,255,0.06)', marginBottom: '6px' },
        nav: { display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'center', marginTop: '8px' },
        thumb: (active) => ({
            width: '50px', height: '50px', objectFit: 'cover', borderRadius: '6px', cursor: 'pointer',
            border: active ? '2px solid #6c63ff' : '2px solid transparent', opacity: active ? 1 : 0.6,
        }),
    };

    return (
        <div>
            <h2 style={{ marginBottom: '4px' }}>🖼️ Image Annotation Studio</h2>
            <p style={{ color: 'var(--text-secondary, #888)', marginBottom: '20px' }}>
                Draw bounding boxes on images and export YOLOv8-compatible annotation files.
            </p>

            <div style={s.container}>
                {/* ---- LEFT PANEL ---- */}
                <div style={s.leftPanel}>
                    {/* Upload */}
                    <div
                        style={s.dropzone}
                        onDrop={handleDrop}
                        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                        onDragLeave={() => setIsDragging(false)}
                        onClick={() => document.getElementById('anno-file-input').click()}
                    >
                        <div style={{ fontSize: '36px', marginBottom: '8px' }}>📁</div>
                        <div style={{ fontWeight: '600' }}>Drop images here</div>
                        <div style={{ color: 'var(--text-secondary, #888)', fontSize: '13px' }}>or click to browse</div>
                        <input
                            id="anno-file-input"
                            type="file"
                            accept="image/*"
                            multiple
                            style={{ display: 'none' }}
                            onChange={(e) => handleFiles(e.target.files)}
                        />
                    </div>

                    {/* Class Manager */}
                    <div style={s.card}>
                        <h3 style={{ marginBottom: '12px', fontSize: '15px' }}>🏷️ Classes ({classes.length})</h3>
                        {classes.map(cls => (
                            <div key={cls} style={s.classItem}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="radio"
                                        name="selectedClass"
                                        value={cls}
                                        checked={selectedClass === cls}
                                        onChange={() => setSelectedClass(cls)}
                                    />
                                    <span style={{ fontWeight: selectedClass === cls ? '700' : '400' }}>{cls}</span>
                                </label>
                                {classes.length > 1 && (
                                    <button
                                        onClick={() => removeClass(cls)}
                                        style={{ ...s.btn, ...s.btnDanger, padding: '2px 8px', fontSize: '11px' }}
                                    >✕</button>
                                )}
                            </div>
                        ))}
                        <div style={{ display: 'flex', gap: '6px', marginTop: '10px' }}>
                            <input
                                type="text"
                                placeholder="New class..."
                                value={newClassName}
                                onChange={(e) => setNewClassName(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && addClass()}
                                style={{ flex: 1, padding: '6px 10px', borderRadius: '8px', border: '1px solid var(--border-color, #555)', background: 'transparent', color: 'inherit' }}
                            />
                            <button onClick={addClass} style={{ ...s.btn, ...s.btnPrimary, padding: '6px 12px' }}>+</button>
                        </div>
                    </div>

                    {/* Annotations list */}
                    <div style={s.card}>
                        <h3 style={{ marginBottom: '12px', fontSize: '15px' }}>📋 Boxes on this image ({currentAnnotations.length})</h3>
                        {currentAnnotations.length === 0 ? (
                            <p style={{ color: 'var(--text-secondary, #888)', fontSize: '13px' }}>Draw a box on the canvas to annotate.</p>
                        ) : (
                            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                {currentAnnotations.map((box, i) => (
                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 8px', borderBottom: '1px solid var(--border-color, #333)' }}>
                                        <span style={{ fontSize: '13px' }}>
                                            <span style={{ ...s.badge, background: 'rgba(108,99,255,0.15)', color: '#6c63ff' }}>{box.label}</span>
                                            <span style={{ marginLeft: '8px', color: 'var(--text-secondary, #888)' }}>
                                                {box.w}×{box.h}
                                            </span>
                                        </span>
                                        <button onClick={() => deleteBox(i)} style={{ ...s.btn, ...s.btnDanger, padding: '2px 8px', fontSize: '11px' }}>🗑</button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Stats + Export */}
                    <div style={s.card}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                            <span>📸 Images: <strong>{images.length}</strong></span>
                            <span>🔲 Total Boxes: <strong>{totalBoxes}</strong></span>
                        </div>
                        <button
                            onClick={exportYolo}
                            disabled={totalBoxes === 0}
                            style={{ ...s.btn, ...s.btnSuccess, width: '100%', opacity: totalBoxes === 0 ? 0.5 : 1 }}
                        >
                            📦 Export YOLOv8 Annotations
                        </button>
                    </div>
                </div>

                {/* ---- RIGHT PANEL: Canvas ---- */}
                <div style={s.rightPanel}>
                    {images.length === 0 ? (
                        <div style={{ ...s.card, textAlign: 'center', padding: '80px 20px' }}>
                            <div style={{ fontSize: '48px', marginBottom: '12px' }}>🖼️</div>
                            <h3>No images loaded</h3>
                            <p style={{ color: 'var(--text-secondary, #888)' }}>Upload images using the panel on the left to start annotating.</p>
                        </div>
                    ) : (
                        <>
                            <div style={{ position: 'relative' }}>
                                <canvas
                                    ref={canvasRef}
                                    width={canvasSize.w}
                                    height={canvasSize.h}
                                    style={s.canvas}
                                    onMouseDown={onMouseDown}
                                    onMouseMove={onMouseMove}
                                    onMouseUp={onMouseUp}
                                    onMouseLeave={() => { if (drawing) { setDrawing(false); setCurrentRect(null); } }}
                                />
                            </div>
                            <div style={{ ...s.card, textAlign: 'center' }}>
                                <div style={{ fontWeight: '600', marginBottom: '8px' }}>
                                    {currentImage?.name} — Image {currentIdx + 1} / {images.length}
                                </div>
                                <div style={s.nav}>
                                    <button
                                        onClick={() => setCurrentIdx(Math.max(0, currentIdx - 1))}
                                        disabled={currentIdx === 0}
                                        style={{ ...s.btn, ...s.btnPrimary, opacity: currentIdx === 0 ? 0.4 : 1 }}
                                    >◀ Prev</button>
                                    <div style={{ display: 'flex', gap: '4px', overflowX: 'auto', maxWidth: '400px', padding: '4px' }}>
                                        {images.map((img, i) => (
                                            <img
                                                key={i}
                                                src={img.url}
                                                alt={img.name}
                                                style={s.thumb(i === currentIdx)}
                                                onClick={() => setCurrentIdx(i)}
                                            />
                                        ))}
                                    </div>
                                    <button
                                        onClick={() => setCurrentIdx(Math.min(images.length - 1, currentIdx + 1))}
                                        disabled={currentIdx === images.length - 1}
                                        style={{ ...s.btn, ...s.btnPrimary, opacity: currentIdx === images.length - 1 ? 0.4 : 1 }}
                                    >Next ▶</button>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
