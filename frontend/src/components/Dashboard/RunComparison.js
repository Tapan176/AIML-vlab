/**
 * Run comparison panel (ROADMAP D2).
 *
 * Given a set of selected training sessions (the full session docs the
 * Dashboard already fetched), render:
 *   - a side-by-side metrics table (union of all numeric metrics found), and
 *   - overlaid loss / accuracy curves from each run's persisted
 *     `progress_metrics` (deep-learning runs only — classical runs simply
 *     contribute to the table).
 *
 * Pure frontend: no extra API calls. Best metric per column is highlighted so
 * the winning run is obvious at a glance.
 */
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { motion } from 'framer-motion';
import { formatMetric } from '../../utils/formatMetric';
import { overlayVariants, modalVariants } from '../../utils/motion';
import './RunComparison.css';

// A small palette to colour each run consistently across the table + charts.
const RUN_COLORS = ['#22d3ee', '#34c759', '#f59e0b', '#ef4444', '#a855f7', '#06b6d4'];

// Metrics where a HIGHER value is better vs LOWER. Anything unknown is treated
// as "higher is better" except obvious loss/error names.
const LOWER_IS_BETTER = new Set([
    'loss', 'val_loss', 'test_loss', 'mae', 'mse', 'rmse', 'MAE', 'MSE', 'RMSE',
]);

function extractMetrics(session) {
    // Metrics can live in a few places depending on model type.
    const r = session.results || {};
    const em = r.evaluation_metrics || session.evaluation_metrics || {};
    const merged = { ...em };
    // Pull common top-level numeric result fields too (accuracy/loss/R2/etc).
    ['accuracy', 'val_accuracy', 'loss', 'val_loss', 'R2', 'f1_score',
     'precision', 'recall', 'map50', 'map50_95'].forEach(k => {
        if (typeof r[k] === 'number') merged[k] = r[k];
    });
    return merged;
}

function isBetter(metricName, a, b) {
    if (a == null) return false;
    if (b == null) return true;
    return LOWER_IS_BETTER.has(metricName) ? a < b : a > b;
}

export default function RunComparison({ sessions, onClose }) {
    if (!sessions || sessions.length === 0) return null;

    const runs = sessions.map((s, i) => ({
        session: s,
        label: `${s.model_code} v${s.version}`,
        color: RUN_COLORS[i % RUN_COLORS.length],
        metrics: extractMetrics(s),
        curve: Array.isArray(s.progress_metrics) ? s.progress_metrics : [],
    }));

    // Union of all metric names across runs, preserving a sensible order.
    const metricNames = [];
    runs.forEach(run => {
        Object.keys(run.metrics).forEach(k => {
            if (!metricNames.includes(k) && typeof run.metrics[k] === 'number') metricNames.push(k);
        });
    });

    // Per-metric best value (for highlighting the winner).
    const bestByMetric = {};
    metricNames.forEach(name => {
        let best = null;
        runs.forEach(run => {
            const v = run.metrics[name];
            if (typeof v === 'number' && isBetter(name, v, best)) best = v;
        });
        bestByMetric[name] = best;
    });

    // Build overlaid loss/accuracy chart data keyed by epoch. Each run becomes
    // a `loss__<label>` / `acc__<label>` series so they overlay on one axis.
    const anyLoss = runs.some(r => r.curve.some(p => p.loss != null || p.val_loss != null));
    const anyAcc = runs.some(r => r.curve.some(p => p.accuracy != null || p.val_accuracy != null));

    const buildChartData = (field) => {
        const maxEpochs = Math.max(0, ...runs.map(r => r.curve.length));
        const rows = [];
        for (let e = 1; e <= maxEpochs; e++) {
            const row = { epoch: e };
            runs.forEach(run => {
                const pt = run.curve.find(p => p.epoch === e);
                if (pt && pt[field] != null) row[run.label] = pt[field];
            });
            rows.push(row);
        }
        return rows;
    };

    const renderOverlay = (title, field) => {
        const data = buildChartData(field);
        if (data.length === 0) return null;
        return (
            <div className="cmp-chart-card">
                <h4>{title}</h4>
                <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 4 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.5} />
                        <XAxis dataKey="epoch" stroke="var(--text-secondary)" fontSize={11} tickLine={false} />
                        <YAxis stroke="var(--text-secondary)" fontSize={11} tickLine={false} width={48} />
                        <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, fontSize: 12 }} />
                        <Legend wrapperStyle={{ fontSize: 12 }} />
                        {runs.map(run => (
                            <Line key={run.label} type="monotone" dataKey={run.label} stroke={run.color}
                                  strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        );
    };

    return (
        <motion.div className="cmp-overlay" onClick={onClose}
            variants={overlayVariants} initial="hidden" animate="visible">
            <motion.div className="cmp-modal" onClick={e => e.stopPropagation()}
                variants={modalVariants} initial="hidden" animate="visible">
                <div className="cmp-header">
                    <h2>⚖️ Compare {runs.length} runs</h2>
                    <button className="cmp-close" onClick={onClose}>✕</button>
                </div>

                {/* Metrics table */}
                <div className="cmp-table-wrap">
                    <table className="cmp-table">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                {runs.map(run => (
                                    <th key={run.label}>
                                        <span className="cmp-dot" style={{ background: run.color }} />
                                        {run.label}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {metricNames.length === 0 ? (
                                <tr><td colSpan={runs.length + 1} style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No comparable metrics on these runs.</td></tr>
                            ) : metricNames.map(name => (
                                <tr key={name}>
                                    <td className="cmp-metric-name">{name}</td>
                                    {runs.map(run => {
                                        const v = run.metrics[name];
                                        const isWin = typeof v === 'number' && v === bestByMetric[name] && runs.length > 1;
                                        return (
                                            <td key={run.label} className={isWin ? 'cmp-win' : ''}>
                                                {typeof v === 'number' ? formatMetric(v) : '—'}
                                                {isWin && <span className="cmp-trophy" title="best"> 🏆</span>}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Overlaid curves */}
                {(anyLoss || anyAcc) && (
                    <div className="cmp-charts">
                        {anyLoss && renderOverlay('📉 Loss', 'loss')}
                        {anyAcc && renderOverlay('📈 Accuracy', 'accuracy')}
                    </div>
                )}
            </motion.div>
        </motion.div>
    );
}
