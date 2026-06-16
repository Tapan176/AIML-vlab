import './Pagination.css';

/**
 * Reusable, presentational pagination control (Prev / page info / Next).
 *
 * Used by the Dashboard (sessions + datasets) and the Datasets Library so
 * paging looks and behaves identically across the app. Pair it with
 * usePagination() to slice the data, or drive it manually.
 *
 * @param {object} props
 * @param {number} props.page        Current 1-based page.
 * @param {number} props.totalPages  Total number of pages (>= 1).
 * @param {number} [props.totalItems] Total item count (for the "x–y of N" hint).
 * @param {number} [props.pageSize]   Items per page (for the "x–y of N" hint).
 * @param {(page:number)=>void} props.onChange Called with the new page.
 * @param {string} [props.unitLabel='items'] Label used in the count hint.
 */
export default function Pagination({ page, totalPages, totalItems, pageSize, onChange, unitLabel = 'items' }) {
    if (totalPages <= 1) return null;

    const start = totalItems != null && pageSize != null ? (page - 1) * pageSize + 1 : null;
    const end = totalItems != null && pageSize != null ? Math.min(page * pageSize, totalItems) : null;

    return (
        <div className="pagination">
            <button
                className="pagination-btn"
                onClick={() => onChange(Math.max(1, page - 1))}
                disabled={page <= 1}
            >
                ‹ Prev
            </button>
            <span className="pagination-info">
                Page {page} of {totalPages}
                {start != null && (
                    <span className="pagination-count">
                        ({start}–{end} of {totalItems} {unitLabel})
                    </span>
                )}
            </span>
            <button
                className="pagination-btn"
                onClick={() => onChange(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
            >
                Next ›
            </button>
        </div>
    );
}
