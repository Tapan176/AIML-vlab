/**
 * One-shot "replay" of a past training session.
 *
 * When the user clicks Replay on the Dashboard, it writes the chosen session's
 * config to sessionStorage under `replay_session`
 * ({ session_id, status, model_code, hyperparams, dataset_info, dataset_config })
 * and the dataset selection to localStorage under `${model_code}_dataset`
 * (consumed by useDatasetCache).
 *
 * Model pages consume the payload via the useReplaySession hook. The read and
 * the removal are deliberately SPLIT into two functions:
 *
 *   - peekReplaySession() is a PURE read used inside a useState lazy
 *     initializer. It must not mutate sessionStorage, because React 18
 *     StrictMode double-invokes initializers in dev — an impure initializer
 *     that removed the payload on the first pass left the committed render with
 *     null, so every hyperparam fell back to its schema default (the original
 *     "replay shows defaults" bug).
 *   - clearReplaySession() removes the payload and runs once from a useEffect
 *     after commit, so a later manual navigation to the same page starts blank
 *     while StrictMode's double render still sees a stable value.
 */

const STORAGE_KEY = 'replay_session';

/**
 * Pure read of the pending replay payload for a model. Does NOT mutate storage,
 * so it is safe to call from a render-phase lazy initializer (and idempotent
 * under StrictMode's double invocation).
 *
 * Returns null when there is no pending replay for this model. Otherwise:
 *   { session_id, status, hyperparams, model_code, dataset_info, dataset_config }
 */
export function peekReplaySession(modelCode) {
    try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const payload = JSON.parse(raw);
        if (payload && payload.model_code === modelCode) return payload;
    } catch (e) {
        // Corrupt payload — treat as no replay.
    }
    return null;
}

/**
 * Removes the pending replay payload (only if it belongs to this model), so a
 * later manual navigation does not silently re-attach. Idempotent: safe to call
 * twice (StrictMode runs cleanup/setup of the consuming effect more than once).
 */
export function clearReplaySession(modelCode) {
    try {
        const raw = sessionStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        const payload = JSON.parse(raw);
        if (!modelCode || (payload && payload.model_code === modelCode)) {
            sessionStorage.removeItem(STORAGE_KEY);
        }
    } catch (e) {
        // Corrupt payload — drop it so it can't wedge future replays.
        sessionStorage.removeItem(STORAGE_KEY);
    }
}
