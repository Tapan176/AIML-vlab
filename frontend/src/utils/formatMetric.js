/**
 * Nullish-safe metric formatter. Replaces the ~60 inline
 * `value != null ? value.toFixed(N) : '—'` ternaries scattered across the
 * Model components.
 */

export function formatMetric(value, options = {}) {
    const { decimals = 4, percent = false } = options;
    if (value == null || Number.isNaN(value)) return '—';
    const scaled = percent ? value * 100 : value;
    const formatted = scaled.toFixed(decimals);
    return percent ? `${formatted}%` : formatted;
}
