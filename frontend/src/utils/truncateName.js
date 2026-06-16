/**
 * Middle-truncates a long string so the start and end stay visible.
 *
 * Useful for dataset filenames where the meaningful part (e.g. the original
 * name or extension) can be at either end of a long Drive-id style string.
 *
 *   truncateName('a90ef7482477cf803618e776e173c007bf957.csv')
 *     -> 'a90ef74824…7bf957.csv'
 *
 * @param {string} name      The full name/string to shorten.
 * @param {number} maxLength Maximum number of characters before truncating.
 * @param {object} [opts]
 * @param {boolean} [opts.middle=true] Truncate in the middle (keep both ends)
 *                                     when true, otherwise truncate the end.
 * @returns {string}
 */
export function truncateName(name, maxLength = 28, { middle = true } = {}) {
    if (!name || typeof name !== 'string') return name || '';
    if (name.length <= maxLength) return name;

    const ellipsis = '…';

    if (!middle) {
        return name.slice(0, Math.max(0, maxLength - 1)) + ellipsis;
    }

    // Keep slightly more of the start than the end.
    const charsToKeep = maxLength - 1; // account for the ellipsis
    const front = Math.ceil(charsToKeep * 0.6);
    const back = Math.floor(charsToKeep * 0.4);
    return name.slice(0, front) + ellipsis + name.slice(name.length - back);
}

export default truncateName;
