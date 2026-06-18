/**
 * Live training charts for the streaming (deep-learning) model pages.
 *
 * Consumes the structured per-epoch `metrics` events emitted by the backend
 * (see backend/utils/sse_helpers.py::epoch_event):
 *   { epoch, total_epochs, loss?, accuracy?, val_loss?, val_accuracy? }
 *
 * Renders up to two small line charts side-by-side:
 *   - Loss (train vs validation)
 *   - Accuracy (train vs validation)  — only when accuracy points exist.
 *
 * The component is purely presentational: pass it the accumulated `metrics`
 * array and it draws. Same data shape works for a live run (appended each
 * epoch over SSE) and for a replayed run (loaded from the session record), so
 * the Dashboard replay re-draws the chart for free.
 */
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const LOSS_COLOR = '#ef4444';
const VAL_LOSS_COLOR = '#f59e0b';
const ACC_COLOR = '#22d3ee';
const VAL_ACC_COLOR = '#34c759';

function MiniChart({ title, data, series }) {
    return (
        <div className="training-chart-card">
            <h4 className="training-chart-title">{title}</h4>
            <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" opacity={0.5} />
                    <XAxis
                        dataKey="epoch"
                        stroke="var(--text-secondary)"
                        fontSize={11}
                        tickLine={false}
                        label={{ value: 'epoch', position: 'insideBottom', offset: -2, fontSize: 11, fill: 'var(--text-secondary)' }}
                    />
                    <YAxis stroke="var(--text-secondary)" fontSize={11} tickLine={false} width={48} />
                    <Tooltip
                        contentStyle={{
                            background: 'var(--bg-card)',
                            border: '1px solid var(--border-color)',
                            borderRadius: 8,
                            fontSize: 12,
                        }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    {series.map(s => (
                        <Line
                            key={s.key}
                            type="monotone"
                            dataKey={s.key}
                            name={s.name}
                            stroke={s.color}
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false}
                            connectNulls
                        />
                    ))}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}

export default function TrainingChart({ metrics }) {
    if (!Array.isArray(metrics) || metrics.length === 0) return null;

    // Only plot panels we actually have data for.
    const hasLoss = metrics.some(m => m.loss != null || m.val_loss != null);
    const hasAcc = metrics.some(m => m.accuracy != null || m.val_accuracy != null);
    if (!hasLoss && !hasAcc) return null;

    const lossSeries = [];
    if (metrics.some(m => m.loss != null)) lossSeries.push({ key: 'loss', name: 'train loss', color: LOSS_COLOR });
    if (metrics.some(m => m.val_loss != null)) lossSeries.push({ key: 'val_loss', name: 'val loss', color: VAL_LOSS_COLOR });

    const accSeries = [];
    if (metrics.some(m => m.accuracy != null)) accSeries.push({ key: 'accuracy', name: 'train acc', color: ACC_COLOR });
    if (metrics.some(m => m.val_accuracy != null)) accSeries.push({ key: 'val_accuracy', name: 'val acc', color: VAL_ACC_COLOR });

    return (
        <div className="training-charts">
            {hasLoss && lossSeries.length > 0 && (
                <MiniChart title="📉 Loss" data={metrics} series={lossSeries} />
            )}
            {hasAcc && accSeries.length > 0 && (
                <MiniChart title="📈 Accuracy" data={metrics} series={accSeries} />
            )}
        </div>
    );
}
