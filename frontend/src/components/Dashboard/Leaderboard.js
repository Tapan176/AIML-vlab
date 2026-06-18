/**
 * Per-dataset leaderboard (ROADMAP D5).
 *
 * Groups the user's COMPLETED training sessions by the dataset they were
 * trained on and ranks the runs within each dataset by a single "key metric":
 *   - accuracy / f1_score for classifiers,
 *   - R² for regressors,
 *   - mAP50 for detection.
 * Higher is better for all of these, so ranking is a simple descending sort.
 *
 * Pure frontend over the sessions the Dashboard already fetched — no API call.
 */
import { useMemo, useState } from 'react';
import { truncateName } from '../../utils/truncateName';

// Ordered preference: the first metric present on a run becomes its key metric.
const KEY_METRICS = [
    { key: 'accuracy', label: 'Accuracy', percent: true },
    { key: 'f1_score', label: 'F1', percent: false },
    { key: 'R2', label: 'R²', percent: false },
    { key: 'map50', label: 'mAP@50', percent: false },
];

function keyMetricFor(session) {
    const r = session.results || {};
    const em = r.evaluation_metrics || {};
    for (const m of KEY_METRICS) {
        const v = (typeof r[m.key] === 'number') ? r[m.key]
            : (typeof em[m.key] === 'number') ? em[m.key] : null;
        if (v != null) return { ...m, value: v };
    }
    return null;
}

export default function Leaderboard({ sessions }) {
    const [open, setOpen] = useState(false);

    const groups = useMemo(() => {
        const byDataset = {};
        (sessions || [])
            .filter(s => s.status === 'completed')
            .forEach(s => {
                const name = s.dataset_info?.filename || '(no dataset)';
                const km = keyMetricFor(s);
                if (!km) return;
                (byDataset[name] = byDataset[name] || []).push({
                    label: `${s.model_code} v${s.version}`,
                    metricLabel: km.label,
                    percent: km.percent,
                    value: km.value,
                });
            });
        // Sort each group's runs by value desc, and drop empty groups.
        return Object.entries(byDataset)
            .map(([name, runs]) => ({
                name,
                runs: runs.sort((a, b) => b.value - a.value),
            }))
            .filter(g => g.runs.length > 0)
            .sort((a, b) => b.runs.length - a.runs.length);
    }, [sessions]);

    if (groups.length === 0) return null;

    const fmt = (run) => run.percent
        ? `${(run.value * 100).toFixed(1)}%`
        : run.value.toFixed(4);

    return (
        <div className="dashboard-section">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ margin: 0 }}>🏆 Leaderboard by dataset</h2>
                <button className="btn-compare-runs" onClick={() => setOpen(o => !o)}>
                    {open ? 'Hide' : 'Show'}
                </button>
            </div>
            {open && (
                <div style={{ marginTop: 16, display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
                    {groups.map(g => (
                        <div key={g.name} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 12, padding: 14 }}>
                            <div style={{ fontWeight: 700, marginBottom: 10 }} title={g.name}>
                                📂 {truncateName(g.name, 30)}
                            </div>
                            <ol style={{ margin: 0, paddingLeft: 0, listStyle: 'none' }}>
                                {g.runs.slice(0, 5).map((run, i) => (
                                    <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-color)' }}>
                                        <span>
                                            <span style={{ color: i === 0 ? 'var(--success)' : 'var(--text-secondary)', fontWeight: 700, marginRight: 8 }}>
                                                {i === 0 ? '🥇' : `#${i + 1}`}
                                            </span>
                                            {run.label}
                                        </span>
                                        <strong>{fmt(run)} <span style={{ color: 'var(--text-secondary)', fontWeight: 400, fontSize: 12 }}>{run.metricLabel}</span></strong>
                                    </li>
                                ))}
                            </ol>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
