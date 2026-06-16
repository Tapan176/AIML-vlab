import { useMemo, useState } from 'react';

/**
 * Client-side pagination state + slicing for an in-memory array.
 *
 * Returns the current page (clamped to valid range even if `items` shrinks,
 * e.g. after a delete or a search filter), the sliced page of items, total
 * page count, and a setter.
 *
 * @param {Array} items     The full, already-sorted/filtered array.
 * @param {number} pageSize Items per page.
 */
export default function usePagination(items, pageSize) {
    const [page, setPage] = useState(1);
    // Memoised so its identity is stable across renders (otherwise the
    // pageItems useMemo below would recompute every render).
    const list = useMemo(() => (Array.isArray(items) ? items : []), [items]);

    const totalPages = Math.max(1, Math.ceil(list.length / pageSize));
    const safePage = Math.min(page, totalPages);

    const pageItems = useMemo(() => {
        const start = (safePage - 1) * pageSize;
        return list.slice(start, start + pageSize);
    }, [list, safePage, pageSize]);

    return {
        page: safePage,
        setPage,
        totalPages,
        pageItems,
        totalItems: list.length,
        pageSize,
    };
}
