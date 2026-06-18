/**
 * One-shot "Train on this output" handoff from Data Studio → the Lab.
 *
 * When the user clicks "Train on this output" on a preprocessed dataset, Data
 * Studio writes the dataset descriptor to sessionStorage under `train_handoff`:
 *
 *   { filename, dataset_id, drive_id, file_type, model_code? }
 *
 * and (when a model was chosen) `auto_select_model` so the Sidebar mounts that
 * model page. The targeted model page picks the dataset up via useDatasetCache,
 * which calls consumeTrainHandoff(modelCode) on mount.
 *
 * Matching rules (mirrors replaySession's keyed-consume behaviour):
 *   - If the payload carries a `model_code`, only that model consumes it.
 *   - If it has no `model_code` (user picked "any model"), the FIRST model page
 *     to mount consumes it. This is intentional: the Sidebar auto-selects a
 *     model, so exactly one page mounts from the handoff.
 *
 * The consume is destructive (removes the payload) so it fires exactly once.
 */

const STORAGE_KEY = 'train_handoff';

/**
 * Write a pending handoff. `payload` should contain at least `filename`.
 * Pass `model_code` to target a specific model page; omit it to let the first
 * mounted model page claim it.
 */
export function setTrainHandoff(payload) {
    if (!payload || !payload.filename) return;
    try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (e) {
        // sessionStorage unavailable (private mode / quota) — handoff just no-ops.
    }
}

/**
 * Consume (read + remove) the pending handoff for `modelCode`.
 *
 * Returns the payload when this model should claim it, else null. The removal
 * is one-shot so a later manual navigation starts blank.
 */
export function consumeTrainHandoff(modelCode) {
    try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const payload = JSON.parse(raw);
        if (!payload || !payload.filename) {
            sessionStorage.removeItem(STORAGE_KEY);
            return null;
        }
        // Targeted handoff: only the named model claims it.
        if (payload.model_code && payload.model_code !== modelCode) return null;
        sessionStorage.removeItem(STORAGE_KEY);
        return payload;
    } catch (e) {
        // Corrupt payload — drop it so it can't wedge future handoffs.
        try { sessionStorage.removeItem(STORAGE_KEY); } catch (_) {}
        return null;
    }
}
