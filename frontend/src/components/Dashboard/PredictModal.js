/**
 * Predict-on-new-data modal (ROADMAP D3).
 *
 * Lets the user upload a CSV and run it through a completed classical model's
 * trained estimator (POST /predict/<session_id>). Shows the returned
 * predictions (and class probabilities when available) and offers a CSV
 * download of the results.
 *
 * Only mounted for classical sessions — the Dashboard gates the button on the
 * model registry's `streaming`/`category` flags.
 */
import { useState } from 'react';
import { motion } from 'framer-motion';
import api from '../../services/api';
import { useUI } from '../../context/UIDialog';
import { overlayVariants, modalVariants } from '../../utils/motion';
import './RunComparison.css';

function toCsv(result) {
    const label = result.prediction_label || 'prediction';
    const header = [label];
    const hasProba = Array.isArray(result.probabilities) && result.classes;
    if (hasProba) result.classes.forEach(c => header.push(`p_${c}`));
    const lines = [header.join(',')];
    result.predictions.forEach((p, i) => {
        const row = [p];
        if (hasProba && result.probabilities[i]) row.push(...result.probabilities[i]);
        lines.push(row.join(','));
    });
    return lines.join('\n');
}

export default function PredictModal({ session, onClose }) {
    const { notify } = useUI();
    const [file, setFile] = useState(null);
    const [busy, setBusy] = useState(false);
    const [result, setResult] = useState(null);

    const run = async () => {
        if (!file) { notify('Choose a CSV file first.', 'warning'); return; }
        setBusy(true);
        setResult(null);
        try {
            const fd = new FormData();
            fd.append('file', file);
            const res = await api.upload(`/predict/${session._id}`, fd);
            setResult(res);
        } catch (err) {
            notify(err.data?.error || err.message || 'Prediction failed.', 'error');
        } finally {
            setBusy(false);
        }
    };

    const downloadCsv = () => {
        const blob = new Blob([toCsv(result)], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${session.model_code}_v${session.version}_predictions.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const previewRows = result ? result.predictions.slice(0, 20) : [];

    return (
        <motion.div className="cmp-overlay" onClick={onClose}
            variants={overlayVariants} initial="hidden" animate="visible">
            <motion.div className="cmp-modal" style={{ maxWidth: 640 }} onClick={e => e.stopPropagation()}
                variants={modalVariants} initial="hidden" animate="visible">
                <div className="cmp-header">
                    <h2>🔮 Predict — {session.model_code} v{session.version}</h2>
                    <button className="cmp-close" onClick={onClose}>✕</button>
                </div>

                <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 0 }}>
                    Upload a CSV with the same feature columns the model was trained on.
                    The first few predictions are previewed below; download the full set as CSV.
                </p>

                <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', margin: '12px 0' }}>
                    <input type="file" accept=".csv" onChange={e => setFile(e.target.files?.[0] || null)} />
                    <button className="btn-compare-runs" onClick={run} disabled={busy || !file}>
                        {busy ? '⏳ Predicting…' : '▶ Run prediction'}
                    </button>
                </div>

                {result && (
                    <div style={{ marginTop: 12 }}>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
                            {result.n_rows} row(s) · features used: {result.columns_used.join(', ')}
                            <button className="btn-compare-runs" style={{ marginLeft: 12, padding: '4px 10px' }} onClick={downloadCsv}>
                                ⬇ Download CSV
                            </button>
                        </div>
                        <div className="cmp-table-wrap" style={{ maxHeight: 320 }}>
                            <table className="cmp-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>{result.prediction_label || 'prediction'}</th>
                                        {Array.isArray(result.classes) && result.classes.map(c => (
                                            <th key={c}>p({String(c)})</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {previewRows.map((p, i) => (
                                        <tr key={i}>
                                            <td>{i + 1}</td>
                                            <td>{String(p)}</td>
                                            {Array.isArray(result.probabilities) && result.probabilities[i] &&
                                                result.probabilities[i].map((pr, j) => (
                                                    <td key={j}>{pr.toFixed(3)}</td>
                                                ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {result.predictions.length > previewRows.length && (
                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6 }}>
                                Showing first {previewRows.length} of {result.predictions.length}. Download for all.
                            </div>
                        )}
                    </div>
                )}
            </motion.div>
        </motion.div>
    );
}
