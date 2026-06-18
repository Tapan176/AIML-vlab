"""
Shared scaffolding for the six streaming-training routes (CNN, ANN, ResNet,
LSTM, YOLO, StyleGAN). Each of them previously duplicated ~30 lines that
- read hyperparams from the request body
- ran them through validate_hyperparams
- created a training session
- defined a `generate()` SSE producer that streamed chunks from the model
  trainer and finalised the session record on completion (or marked it
  failed on exception)
- built and returned a Flask SSE Response

This module owns that scaffolding so each route can be ~5 lines.
"""
import json

from flask import Response, jsonify, stream_with_context

from services.hyperparam_validator import validate_hyperparams
from services.training_session_service import (
    create_session,
    update_session_results,
    update_session_error,
    mark_session_running,
    append_session_progress,
    append_session_metric,
    is_cancel_requested,
    mark_session_cancelled,
)


def epoch_event(epoch, total_epochs, *, loss=None, accuracy=None,
                val_loss=None, val_accuracy=None, extra_log=None):
    """Build an SSE chunk carrying BOTH a human log line and structured metrics.

    The `metrics` field powers the live training chart on the frontend; the
    `log` field keeps the existing text console working unchanged. Any metric
    left as None is omitted from the payload (so e.g. an unsupervised model can
    emit just `loss`). Returns a ready-to-yield `data: {...}\n\n` string.

    Centralising the chunk shape here means every streaming trainer emits the
    same schema, so the chart + persistence layer never have to special-case a
    particular model.
    """
    metrics = {'epoch': int(epoch), 'total_epochs': int(total_epochs)}
    if loss is not None:
        metrics['loss'] = round(float(loss), 6)
    if accuracy is not None:
        metrics['accuracy'] = round(float(accuracy), 6)
    if val_loss is not None:
        metrics['val_loss'] = round(float(val_loss), 6)
    if val_accuracy is not None:
        metrics['val_accuracy'] = round(float(val_accuracy), 6)

    if extra_log:
        log = extra_log
    else:
        parts = [f"Epoch [{epoch}/{total_epochs}]"]
        if loss is not None:
            parts.append(f"loss: {loss:.4f}")
        if accuracy is not None:
            parts.append(f"accuracy: {accuracy:.4f}")
        if val_loss is not None:
            parts.append(f"val_loss: {val_loss:.4f}")
        if val_accuracy is not None:
            parts.append(f"val_accuracy: {val_accuracy:.4f}")
        log = " - ".join(parts) if len(parts) > 1 else parts[0]

    return f"data: {json.dumps({'log': log, 'metrics': metrics})}\n\n"


def _extract_log_line(chunk):
    """Best-effort pull of a human-readable progress line out of an SSE chunk.

    SSE chunks look like `data: {json}\n\n`. We persist either the `log`
    field (training progress messages) so a reconnecting client can replay
    the history. Returns None for chunks with nothing log-worthy.
    """
    try:
        payload = chunk.replace('data: ', '').strip()
        if not payload:
            return None
        parsed = json.loads(payload)
        if isinstance(parsed, dict) and parsed.get('log'):
            return parsed['log']
    except Exception:
        pass
    return None


def _extract_metric(chunk):
    """Best-effort pull of a structured per-epoch metric dict out of a chunk.

    Returns the `metrics` dict (for persistence) or None when absent.
    """
    try:
        payload = chunk.replace('data: ', '').strip()
        if not payload:
            return None
        parsed = json.loads(payload)
        if isinstance(parsed, dict) and isinstance(parsed.get('metrics'), dict):
            return parsed['metrics']
    except Exception:
        pass
    return None


def run_sse_training(
    model_code,
    current_user,
    request_obj,
    make_chunks_iter,
    *,
    finalizing_log=None,
):
    """Validate, persist, stream, finalise — the full SSE training lifecycle.

    Args:
        model_code: validation schema + session record key (e.g. 'cnn').
        current_user: user dict from @token_required.
        request_obj: the Flask request object. We read its JSON body once
            to extract `hyperparams` and `dataset_id`.
        make_chunks_iter: a callable invoked with (validated_params, user_id,
            session_version) that returns the SSE chunk iterator from the
            model's training function. Letting the route own this factory
            keeps each route in charge of which extra kwargs (e.g.
            `hidden_layer_array`) it passes to its trainer, and whether to
            pass the raw `request` object or the pre-extracted `data` dict.
        finalizing_log: optional message to stream right before the
            update_session_results call (which can be slow because it does
            Drive uploads). ResNet/LSTM/StyleGAN use this to nudge the
            user that training itself is done. CNN/ANN/YOLO leave it None.

    Returns:
        A Flask SSE Response, or a 400 jsonify on validation failure.
    """
    data = request_obj.get_json() or {}
    user_hyperparams = data.get('hyperparams', {})
    try:
        validated_params = validate_hyperparams(model_code, user_hyperparams)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    user_id = current_user['_id']

    # Enforce subscription quota before doing any heavy work (no-op unless
    # SUBSCRIPTION_ENABLED). Returning a plain JSON 429 is consistent with the
    # validation-failure 400 return above; callers handle a non-stream return.
    from services.subscription_service import check_quota, record_usage
    ok, info = check_quota(current_user, model_code)
    if not ok:
        return jsonify(info), 429

    dataset_id = data.get('dataset_id')
    # Capture per-dataset selections that aren't hyperparams (so they survive
    # validation and can be restored on Dashboard "Replay"). Only keys actually
    # present are stored, so non-finetune SSE models simply store nothing here.
    _DATASET_CONFIG_KEYS = ('text_column', 'label_column', 'filename')
    dataset_config = {k: data[k] for k in _DATASET_CONFIG_KEYS if data.get(k)}
    session = create_session(user_id, model_code, validated_params, dataset_id, dataset_config)
    session_id = session['_id']
    session_version = session['version']
    record_usage(user_id, model_code)
    # Mark running + reset progress log so a reconnecting client (Dashboard
    # replay) can detect the live session and fetch accumulated logs.
    mark_session_running(session_id)

    def generate():
        # Only poll the cancel flag every few chunks to keep the DB load low
        # (training emits many log lines per epoch).
        cancel_check_every = 3
        chunk_count = 0
        # Tell the client its session id up front so a Cancel button can target
        # this run (the completion payload also carries it, but that's too late
        # to cancel). Harmless to ignore for clients that don't use it.
        yield f"data: {json.dumps({'session_id': session_id, 'status': 'started'})}\n\n"
        try:
            results_data = {}
            for chunk in make_chunks_iter(validated_params, user_id, session_version):
                # Cooperative cancellation: if the user asked to stop, close the
                # trainer generator and record the run as cancelled. Checked
                # between chunks so it takes effect within an epoch boundary.
                chunk_count += 1
                if chunk_count % cancel_check_every == 0 and is_cancel_requested(session_id):
                    mark_session_cancelled(session_id)
                    yield f"data: {json.dumps({'log': '🛑 Training cancelled by user.', 'status': 'cancelled', 'session_id': session_id})}\n\n"
                    return
                # Capture the 'training_complete' payload so we can pass it to
                # update_session_results. Other chunks are just passed through.
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
                    except Exception:
                        pass
                # Persist progress lines so the run can be re-attached after a
                # page navigation. Cheap best-effort; never block the stream.
                log_line = _extract_log_line(chunk)
                if log_line:
                    try:
                        append_session_progress(session_id, log_line)
                    except Exception:
                        pass
                # Persist structured per-epoch metrics so a reconnecting client
                # (Dashboard replay) can re-draw the live training chart.
                metric = _extract_metric(chunk)
                if metric:
                    try:
                        append_session_metric(session_id, metric)
                    except Exception:
                        pass
                yield chunk

            if finalizing_log:
                yield f"data: {json.dumps({'log': finalizing_log})}\n\n"

            db_results = update_session_results(
                session_id,
                results_data or {"message": "Training complete."},
                [],
                results_data.get('trained_model_path', ''),
                '',
            )
            db_results['status'] = 'completed'
            db_results['session_id'] = session_id
            yield f"data: {json.dumps(db_results)}\n\n"
        except Exception as e:
            update_session_error(session_id, str(e))
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response
