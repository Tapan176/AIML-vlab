

/**
 * A column picker for dataset-driven forms (e.g. fine-tuning text/label
 * columns). When the dataset's columns are known it renders a <select>; until
 * then (no dataset selected yet, or a non-CSV upload) it falls back to a free
 * text input so the user is never blocked.
 */
export default function ColumnSelect({ label, value, columns, onChange, placeholder }) {
    const hasColumns = Array.isArray(columns) && columns.length > 0;

    return (
        <div className="form-group">
            <label>{label}</label>
            {hasColumns ? (
                <select value={value} onChange={e => onChange(e.target.value)}>
                    {/* Keep an out-of-list value visible rather than silently
                        snapping to the first option. */}
                    {!columns.includes(value) && value && (
                        <option value={value}>{value} (not in dataset)</option>
                    )}
                    {columns.map(col => (
                        <option key={col} value={col}>{col}</option>
                    ))}
                </select>
            ) : (
                <input
                    type="text"
                    value={value}
                    onChange={e => onChange(e.target.value)}
                    placeholder={placeholder}
                />
            )}
        </div>
    );
}
