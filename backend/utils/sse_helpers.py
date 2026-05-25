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
)


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
    dataset_id = data.get('dataset_id')
    session = create_session(user_id, model_code, validated_params, dataset_id)
    session_id = session['_id']
    session_version = session['version']

    def generate():
        try:
            results_data = {}
            for chunk in make_chunks_iter(validated_params, user_id, session_version):
                # Capture the 'training_complete' payload so we can pass it to
                # update_session_results. Other chunks are just passed through.
                if 'status' in chunk and 'training_complete' in chunk:
                    try:
                        data_part = chunk.replace('data: ', '').strip()
                        results_data = json.loads(data_part)
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
