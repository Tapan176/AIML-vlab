/**
 * One-shot "replay" of a past training session.
 *
 * When the user clicks Replay on the Dashboard, it writes the chosen session's
 * config to sessionStorage under `replay_session` ({ model_code, hyperparams,
 * dataset_info }) and the dataset selection to localStorage under
 * `${model_code}_dataset` (consumed by useDatasetCache).
 *
 * A model page calls consumeReplayHyperparams(MODEL_CODE) from its hyperparams
 * useState initializer to seed the form with the previous run's values. The
 * payload is consumed (removed) once it matches, so a later manual navigation
 * to the same page starts blank rather than silently reusing an old config.
 */

export function consumeReplayHyperparams(modelCode) {
    try {
        const raw = sessionStorage.getItem('replay_session');
        if (!raw) return {};
        const payload = JSON.parse(raw);
        if (payload && payload.model_code === modelCode && payload.hyperparams) {
            sessionStorage.removeItem('replay_session');
            return payload.hyperparams;
        }
    } catch (e) {
        // Corrupt payload — fall through to a blank form.
    }
    return {};
}
