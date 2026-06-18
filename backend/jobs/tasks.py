"""Worker-side training tasks.

`run_training_job` is what the RQ worker executes. It mirrors the persistence
half of `models/route._train_model` (mark running → train → store results /
error) but runs out-of-process, driven entirely by a serializable payload
instead of a live Flask request.

The classical scikit-learn trainers read their dataset reference from
`request.json` only (e.g. `simpleLinearRegression` does `data = request.json`),
so `JobRequest` — a tiny stand-in exposing `.json` / `.get_json()` — lets them
run unchanged on the worker. Image/SSE trainers that read `request.files` are
out of scope for this first cut (they stay synchronous).
"""
import logging

log = logging.getLogger(__name__)


class JobRequest:
    """Minimal Flask-request stand-in for worker-side training.

    Exposes the only attributes the classical trainers touch: `.json` and
    `.get_json()`. Reconstructed from the request body captured by the route at
    enqueue time.
    """

    def __init__(self, json_body=None):
        self._json = json_body or {}

    @property
    def json(self):
        return self._json

    def get_json(self, *args, **kwargs):
        return self._json


def resolve_train_fn(model_code):
    """Look up the training function for a model code.

    Imported lazily (and as its own seam) so the worker doesn't import the Flask
    app eagerly, and so tests can monkeypatch this to inject a stub trainer.
    """
    from models.route import MODEL_FUNCTIONS
    return MODEL_FUNCTIONS.get(model_code)


def run_training_job(payload):
    """Execute one training run and persist its outcome to the session record.

    payload keys: model_code, session_id, user_id, session_version, params
    (validated hyperparams), request_json (the original request body, for the
    trainer's dataset lookup).

    Returns a small status dict (handy for RQ result inspection / logging). All
    failures are caught and recorded on the session as 'failed' rather than
    re-raised, so a crash never leaves the session stuck in 'running'.
    """
    from services.training_session_service import (
        mark_session_running,
        update_session_results,
        update_session_error,
    )

    model_code = payload["model_code"]
    session_id = payload["session_id"]
    user_id = payload.get("user_id")
    session_version = payload.get("session_version")
    params = payload.get("params") or {}
    req = JobRequest(payload.get("request_json"))

    mark_session_running(session_id)
    try:
        train_fn = resolve_train_fn(model_code)
        if train_fn is None:
            raise ValueError(f"No training function registered for model '{model_code}'")

        results = train_fn(
            req, validated_params=params, user_id=user_id, session_version=session_version,
        )

        if isinstance(results, dict) and results.get("error"):
            update_session_error(session_id, results["error"])
            return {"status": "error", "session_id": session_id, "error": results["error"]}

        update_session_results(
            session_id,
            results.get("evaluation_metrics") or results.get("results") or results,
            results.get("outputImageUrls", []),
            results.get("trained_model_path", ""),
            results.get("predictions_output_file", ""),
        )
        return {"status": "completed", "session_id": session_id}
    except Exception as e:
        log.exception("Training job failed for session %s", session_id)
        update_session_error(session_id, str(e))
        return {"status": "error", "session_id": session_id, "error": str(e)}
