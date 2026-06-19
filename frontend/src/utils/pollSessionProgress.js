/**
 * Polls a training session's /progress endpoint until it reaches a terminal
 * state, returning the normalised completed results (or throwing on failure).
 *
 * Used by the async-training path: when TRAINING_ASYNC is enabled the backend
 * enqueues the run and responds 202 { session_id, status: 'queued' } instead of
 * blocking on training. The client then polls here for the outcome.
 *
 * Mirrors the completed-session restore logic in useReplaySession: on
 * completion it merges the Drive ids and rebuilds the carousel images from the
 * session's results.zip (the local PNGs are deleted after upload), so the
 * resolved object has the same shape as a synchronous train response.
 *
 * @param {object} api            the shared API client (services/api).
 * @param {string} sessionId      the session to poll.
 * @param {object} [opts]
 * @param {number} [opts.intervalMs=2000]  delay between polls.
 * @param {() => boolean} [opts.isCancelled] return true to abort polling.
 * @param {(snapshot) => void} [opts.onProgress] called with each poll snapshot
 *        ({ status, logs, metrics }) so the UI can show live progress.
 * @returns {Promise<object>} normalised results (with `images`).
 */
const TERMINAL = ['completed', 'failed', 'cancelled'];

function normaliseResults(data) {
    if (!data) return null;
    const images = data.outputImageBase64?.length > 0 ? data.outputImageBase64 : [];
    return { ...data, images };
}

function sleep(ms, isCancelled) {
    return new Promise((resolve) => {
        const t = setTimeout(resolve, ms);
        // Best-effort early-out: if cancelled mid-wait, resolve on the next tick.
        if (isCancelled) {
            const check = setInterval(() => {
                if (isCancelled()) { clearTimeout(t); clearInterval(check); resolve(); }
            }, 250);
            setTimeout(() => clearInterval(check), ms);
        }
    });
}

export default async function pollSessionProgress(api, sessionId, opts = {}) {
    const {
        intervalMs = 2000,
        isCancelled = () => false,
        onProgress = () => {},
    } = opts;

    // First poll immediately, then on an interval until terminal.
    // Tolerate a few transient errors so one network blip doesn't abort.
    let consecutiveErrors = 0;

    // eslint-disable-next-line no-constant-condition
    while (true) {
        if (isCancelled()) {
            const e = new Error('cancelled');
            e.cancelled = true;
            throw e;
        }
        let data;
        try {
            data = await api.get(`/training-sessions/${sessionId}/progress`, { ttl: 0, force: true });
            consecutiveErrors = 0;
        } catch (err) {
            consecutiveErrors += 1;
            if (consecutiveErrors >= 3) throw err;
            await sleep(intervalMs, isCancelled);
            continue;
        }

        onProgress({ status: data.status, logs: data.logs || [], metrics: data.metrics || [] });

        if (data.status === 'completed') {
            const merged = {
                ...(data.results || {}),
                outputImageUrls: data.output_images || data.results?.outputImageUrls,
                trained_model_drive_id: data.trained_model_drive_id || data.results?.trained_model_drive_id,
                results_zip_drive_id: data.results_zip_drive_id || data.results?.results_zip_drive_id,
                session_id: data.session_id,
            };
            // Local output PNGs are deleted after upload, so rebuild the carousel
            // images from the Drive results.zip (returned as base64 data URLs).
            let restoredImages = [];
            try {
                const imgResp = await api.get(`/training-sessions/${sessionId}/result-images`, { ttl: 0, force: true });
                if (Array.isArray(imgResp?.images)) restoredImages = imgResp.images;
            } catch (_) { /* non-fatal — metrics/downloads still render */ }

            const normalised = normaliseResults(merged);
            if (restoredImages.length > 0) {
                normalised.images = restoredImages;
                normalised.outputImageBase64 = restoredImages;
            }
            return normalised;
        }

        if (data.status === 'failed') {
            throw new Error(data.error || 'Training failed');
        }
        if (data.status === 'cancelled') {
            const e = new Error('Training cancelled');
            e.cancelled = true;
            throw e;
        }
        if (TERMINAL.includes(data.status)) {
            return normaliseResults(data.results || {});
        }

        await sleep(intervalMs, isCancelled);
    }
}
