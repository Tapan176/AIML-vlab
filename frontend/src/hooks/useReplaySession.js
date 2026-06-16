/**
 * Restores a training session's state when the user clicks "Replay" on the
 * Dashboard, so re-opening a model page shows it exactly as they left it:
 *
 *   - hyperparameters         → seeded into the form (returned as `hyperparams`)
 *   - completed session       → saved results restored (`restoredResults`)
 *   - in-progress session     → live progress polled + streamed (`liveLogs`,
 *                               `liveStatus`); when it finishes the results
 *                               are surfaced via `restoredResults`
 *
 * The replay payload (written by Dashboard.handleReplaySession to
 * sessionStorage) is consumed once on mount. A later manual navigation to the
 * same page therefore starts blank rather than silently re-attaching.
 */
import { useEffect, useRef, useState } from 'react';
import api from '../services/api';
import { peekReplaySession, clearReplaySession } from '../utils/replaySession';

// Normalise restored results for the <ImageCarousel>. On replay the trainer's
// local output PNGs have been deleted (they only live inside the Drive
// results.zip), so the `outputImageUrls` local paths would 404 — we therefore
// only trust base64 here. The actual images are injected by the caller after
// fetching them from /result-images. If neither is present, images stays empty
// so the carousel simply hides instead of showing broken thumbnails.
function normaliseResults(data) {
    if (!data) return null;
    const images = data.outputImageBase64?.length > 0 ? data.outputImageBase64 : [];
    return { ...data, images };
}

const POLL_INTERVAL_MS = 2500;
const ACTIVE_STATUSES = ['running', 'pending'];

export default function useReplaySession(modelCode) {
    // Read the replay payload with a PURE peek (no mutation) so React 18
    // StrictMode's double-invoked lazy initializer can't "consume" it out from
    // under the committed render. The actual removal happens in an effect below.
    const [replay] = useState(() => peekReplaySession(modelCode));
    const [hyperparams] = useState(() => (replay?.hyperparams || {}));
    // Extra per-dataset selections (e.g. text_column / label_column for
    // fine-tuning) captured at training time, so the form restores them.
    const [datasetConfig] = useState(() => (replay?.dataset_config || {}));

    const [restoredResults, setRestoredResults] = useState(null);
    const [liveStatus, setLiveStatus] = useState(replay && ACTIVE_STATUSES.includes(replay.status) ? replay.status : null);
    const [liveLogs, setLiveLogs] = useState([]);
    const [restoring, setRestoring] = useState(!!replay && replay.status === 'completed');

    const pollRef = useRef(null);

    // Remove the one-shot payload after mount (not in the initializer), so a
    // later manual navigation to this page starts blank. By the time this runs
    // the value is already captured in `replay` state, so nothing is lost.
    useEffect(() => {
        if (replay) clearReplaySession(modelCode);
    }, [replay, modelCode]);

    useEffect(() => {
        if (!replay || !replay.session_id) return undefined;
        let cancelled = false;

        const fetchProgress = async () => {
            try {
                const data = await api.get(`/training-sessions/${replay.session_id}/progress`);
                if (cancelled) return;

                if (Array.isArray(data.logs)) setLiveLogs(data.logs);
                setLiveStatus(data.status);

                if (data.status === 'completed') {
                    // Merge the drive ids / results so downloads + metrics render.
                    const merged = {
                        ...(data.results || {}),
                        outputImageUrls: data.output_images || data.results?.outputImageUrls,
                        trained_model_drive_id: data.trained_model_drive_id || data.results?.trained_model_drive_id,
                        results_zip_drive_id: data.results_zip_drive_id || data.results?.results_zip_drive_id,
                        session_id: data.session_id,
                    };

                    // The local output_images paths are deleted after upload, so
                    // rebuild the carousel images from the Drive results.zip
                    // (returned as base64 data URLs). Falls back to whatever
                    // normaliseResults can derive if the fetch fails.
                    let restoredImages = [];
                    try {
                        const imgResp = await api.get(`/training-sessions/${replay.session_id}/result-images`);
                        if (Array.isArray(imgResp?.images)) restoredImages = imgResp.images;
                    } catch (_) {
                        // Non-fatal — metrics/downloads still render without images.
                    }
                    if (cancelled) return;

                    const normalised = normaliseResults(merged);
                    if (restoredImages.length > 0) {
                        normalised.images = restoredImages;
                        normalised.outputImageBase64 = restoredImages;
                    }
                    setRestoredResults(normalised);
                    setRestoring(false);
                    stopPolling();
                } else if (data.status === 'failed') {
                    setRestoring(false);
                    stopPolling();
                }
            } catch (e) {
                // Session may have been deleted or errored — stop trying.
                if (!cancelled) {
                    setRestoring(false);
                    stopPolling();
                }
            }
        };

        const startPolling = () => {
            if (pollRef.current) return;
            pollRef.current = setInterval(fetchProgress, POLL_INTERVAL_MS);
        };
        const stopPolling = () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
        };

        // Always do an immediate fetch to restore state on mount.
        fetchProgress();
        // Keep polling only while the run is active.
        if (ACTIVE_STATUSES.includes(replay.status)) {
            startPolling();
        }

        return () => {
            cancelled = true;
            stopPolling();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [replay]);

    return {
        hyperparams,        // seed for the model's useState
        datasetConfig,      // { text_column, label_column, ... } from the run
        restoredResults,    // completed-session results (normalised), or null
        liveStatus,         // 'running' | 'pending' | 'completed' | 'failed' | null
        liveLogs,           // accumulated progress log lines for live runs
        restoring,          // true while we're fetching a completed session's results
        isReplaying: !!replay,
    };
}
