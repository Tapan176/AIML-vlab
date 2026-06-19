/**
 * Per-session cache of a completed run's result images (base64 data URLs).
 *
 * GET /result-images is expensive server-side — it streams the run's results.zip
 * back from Google Drive and unzips it on every call. The images are immutable
 * once a run has completed, so cache them by session_id for the lifetime of the
 * SPA session: navigating away from a completed run and back, or any replay
 * re-mount, then serves them instantly instead of re-downloading + re-unzipping.
 *
 * In-memory (not localStorage): a base64 image set is easily several MB and
 * would blow the ~5MB localStorage quota. A hard reload re-fetches once — fine.
 */
const _cache = new Map();   // sessionId -> string[] (base64 data URLs)

export async function getResultImages(api, sessionId) {
    if (!sessionId) return [];
    if (_cache.has(sessionId)) return _cache.get(sessionId);
    try {
        const resp = await api.get(`/training-sessions/${sessionId}/result-images`, { ttl: 0, force: true });
        const images = Array.isArray(resp?.images) ? resp.images : [];
        // Only cache a non-empty result so a transient failure can be retried.
        if (images.length > 0) _cache.set(sessionId, images);
        return images;
    } catch (_) {
        return [];
    }
}

/** Test seam. */
export function _clearResultImagesCache() {
    _cache.clear();
}
