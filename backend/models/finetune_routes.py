"""
Fine-tuning routes for HuggingFace transformer models.
Each model is lazy-loaded via its own SSE streaming endpoint.
"""
from flask import Blueprint, request, jsonify
from auth.auth_middleware import token_required
from services.hyperparam_validator import validate_hyperparams
from utils.sse_helpers import run_sse_training
from services.training_session_service import create_session, update_session_results, update_session_error

finetune_routes = Blueprint('finetune_routes', __name__)


@finetune_routes.route('/finetune/bert', methods=['POST'])
@token_required
def bert_finetune(current_user):
    """BERT text classification fine-tuning — SSE streaming."""
    try:
        from models.bert_finetune.bert_finetune import train_bert_finetune as _train_bert
    except ImportError as e:
        return jsonify({"error": f"BERT fine-tuning requires HuggingFace Transformers: {e}"}), 500

    data = request.get_json() or {}
    text_column = data.get('text_column', 'text')
    label_column = data.get('label_column', 'label')

    return run_sse_training(
        'bert_finetune', current_user, request,
        lambda params, uid, v: _train_bert(
            request, validated_params=params, user_id=uid, session_version=v),
    )


@finetune_routes.route('/finetune/vit', methods=['POST'])
@token_required
def vit_finetune(current_user):
    """ViT image classification fine-tuning — SSE streaming."""
    try:
        from models.vit_finetune.vit_finetune import train_vit_finetune as _train_vit
    except ImportError as e:
        return jsonify({"error": f"ViT fine-tuning requires HuggingFace Transformers: {e}"}), 500

    return run_sse_training(
        'vit_finetune', current_user, request,
        lambda params, uid, v: _train_vit(
            request, validated_params=params, user_id=uid, session_version=v),
    )


@finetune_routes.route('/finetune/distilbert', methods=['POST'])
@token_required
def distilbert_finetune(current_user):
    """DistilBERT text classification fine-tuning — SSE streaming."""
    try:
        from models.bert_finetune.bert_finetune import train_bert_finetune as _train_bert
    except ImportError as e:
        return jsonify({"error": f"DistilBERT fine-tuning requires HuggingFace Transformers: {e}"}), 500

    return run_sse_training(
        'distilbert_finetune', current_user, request,
        lambda params, uid, v: _train_bert(
            request, validated_params=params, user_id=uid, session_version=v),
    )
