/**
 * Restores a training session's state when the user clicks "Replay" on the
 * Dashboard, so re-opening a model page shows it exactly as they left it:
 *
 *   - hyperparameters         → seeded into the form (returned as `hyperparams`)
 *   - completed session       → saved results restored (`restoredResults`)
 *   - in-progress session     → live progress polled (`liveLogs`, `liveMetrics`,
 *                               `liveStatus`); when it finishes the results
 *                               are surfaced via `restoredResults`
 *
 * Identity lives in the URL. The replayed session id is read from the
 * `?session=<id>` query param, so it survives a page refresh and a
 * navigate-away-then-back: polling re-attaches on every mount and keeps
 * appending live progress (the progress endpoint always returns the full
 * cumulative logs/metrics, so a fresh poll never loses earlier lines).
 *
 * The one-shot sessionStorage payload (written by Dashboard.handleReplaySession)
 * only supplies the seed values that aren't in the URL — the hyperparameters
 * and dataset_config to pre-fill the form. It's consumed once on mount.
 */
import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
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
    // The session id is the source of truth and lives in the URL (?session=…),
    // so it survives refresh and navigate-away-then-back. The one-shot
    // sessionStorage payload only seeds the form (hyperparams / dataset_config).
    const [searchParams] = useSearchParams();
    const sessionId = searchParams.get('session') || null;

    // Read the replay payload with a PURE peek (no mutation) so React 18
    // StrictMode's double-invoked lazy initializer can't "consume" it out from
    // under the committed render. The actual removal happens in an effect below.
    const [replay] = useState(() => peekReplaySession(modelCode));
    const [hyperparams] = useState(() => (replay?.hyperparams || {}));
    // Extra per-dataset selections (e.g. text_column / label_column for
    // fine-tuning) captured at training time, so the form restores them.
    const [datasetConfig] = useState(() => (replay?.dataset_config || {}));

    const [restoredResults, setRestoredResults] = useState(null);
    const [liveStatus, setLiveStatus] = useState(null);
    const [liveLogs, setLiveLogs] = useState([]);
    const [liveMetrics, setLiveMetrics] = useState([]);
    // We only know the status after the first poll, so optimistically show the
    // restoring spinner whenever a session id is present in the URL.
    const [restoring, setRestoring] = useState(!!sessionId);

    const pollRef = useRef(null);

    // Remove the one-shot seed payload after mount (not in the initializer), so
    // a later manual navigation that ISN'T a replay starts with a blank form.
    // The session id stays in the URL, so live re-attach still works on return.
    useEffect(() => {
        if (replay) clearReplaySession(modelCode);
    }, [replay, modelCode]);

    useEffect(() => {
        if (!sessionId) {
            // Not a replay/reconnect — reset any stale live state.
            setRestoring(false);
            return undefined;
        }
        let cancelled = false;
        let consecutiveErrors = 0;

        const scheduleNext = () => {
            // Recursive timeout (not setInterval) so a slow poll can't overlap
            // the next one. Re-armed at the end of each successful active poll.
            if (cancelled) return;
            stopPolling();
            pollRef.current = setTimeout(fetchProgress, POLL_INTERVAL_MS);
        };

        const fetchProgress = async () => {
            try {
                const data = await api.get(`/training-sessions/${sessionId}/progress`);
                if (cancelled) return;
                consecutiveErrors = 0;

                // Scope the session to THIS page: a session id left in the URL
                // for a different model (e.g. after switching pages) must not
                // hijack this page's console/chart. Ignore + stop polling.
                if (data.model_code && data.model_code !== modelCode) {
                    stopPolling();
                    setRestoring(false);
                    return;
                }

                if (Array.isArray(data.logs)) setLiveLogs(data.logs);
                if (Array.isArray(data.metrics)) setLiveMetrics(data.metrics);
                setLiveStatus(data.status);

                // Keep polling while the run is active; otherwise stop. Driven by
                // the freshly-fetched status (not the stale replay payload), so a
                // refresh or return trip resumes live polling correctly.
                if (ACTIVE_STATUSES.includes(data.status)) {
                    scheduleNext();
                } else {
                    stopPolling();
                }

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
                        const imgResp = await api.get(`/training-sessions/${sessionId}/result-images`);
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
                if (cancelled) return;
                // Tolerate transient blips (network/server) — keep retrying a few
                // times before giving up, so live updates don't stop on one hiccup.
                consecutiveErrors += 1;
                if (consecutiveErrors >= 3) {
                    setRestoring(false);
                    stopPolling();
                } else {
                    scheduleNext();
                }
            }
        };

        const stopPolling = () => {
            if (pollRef.current) {
                clearTimeout(pollRef.current);
                pollRef.current = null;
            }
        };

        // Immediate fetch to restore state on mount; the poll re-arms itself
        // (scheduleNext) while the run is active.
        fetchProgress();

        return () => {
            cancelled = true;
            stopPolling();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sessionId, modelCode]);

    return {
        hyperparams,        // seed for the model's useState
        datasetConfig,      // { text_column, label_column, ... } from the run
        restoredResults,    // completed-session results (normalised), or null
        liveStatus,         // 'running' | 'pending' | 'completed' | 'failed' | null
        liveLogs,           // accumulated progress log lines for live runs
        liveMetrics,        // accumulated per-epoch metric points for live runs
        restoring,          // true while we're fetching a completed session's results
        isReplaying: !!sessionId || !!replay,
    };
}
