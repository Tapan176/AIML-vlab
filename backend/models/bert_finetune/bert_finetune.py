"""
HuggingFace BERT Fine-Tuning module.
Fine-tunes a pre-trained BERT model on user-provided text classification data.
Uses SSE streaming for live epoch-by-epoch progress.
"""
import os
import json
import tempfile
from sklearn.model_selection import train_test_split
from config import HF_TOKEN, get_user_models_dir, ensure_dir


def train_bert_finetune(request, validated_params=None, user_id=None, session_version=None):
    """
    Fine-tune BERT for text classification.
    
    Expected request JSON:
        - filename: CSV dataset filename
        - text_column: name of the text column (e.g. 'review')
        - label_column: name of the label column (e.g. 'sentiment')
        - num_labels: (optional) number of output classes, auto-detected if omitted
    
    Hyperparameters (from validated_params):
        - model_name: huggingface model ID (default: 'bert-base-uncased')
        - epochs: number of training epochs (default: 3)
        - batch_size: training batch size (default: 16)
        - learning_rate: peak learning rate (default: 2e-5)
        - max_length: max token length (default: 256)
        - warmup_steps: warmup steps for scheduler (default: 0)
        - weight_decay: weight decay for AdamW (default: 0.01)
        - test_size: validation split fraction (default: 0.2)
        - freeze_base: whether to freeze BERT layers initially (default: False)
    """
    import torch
    from torch.optim import AdamW  # transformers.AdamW was removed in v4.x
    from torch.utils.data import DataLoader, Dataset
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        get_linear_schedule_with_warmup,
    )

    data = request.json if hasattr(request, 'json') else request
    params = validated_params or {}

    model_name = params.get('model_name', 'bert-base-uncased')
    epochs = int(params.get('epochs', 3))
    batch_size = int(params.get('batch_size', 16))
    learning_rate = float(params.get('learning_rate', 2e-5))
    max_length = int(params.get('max_length', 256))
    warmup_steps = int(params.get('warmup_steps', 0))
    weight_decay = float(params.get('weight_decay', 0.01))
    test_size = float(params.get('test_size', 0.2))
    freeze_base = bool(params.get('freeze_base', False))
    num_labels = data.get('num_labels')

    hf_token = HF_TOKEN

    yield f"data: {json.dumps({'log': '🔧 Loading BERT model and tokenizer...'})}\n\n"

    # Source the base model into the shared cache once; reuse across users.
    # Returns a local path, or the original id if sourcing fails (safe fallback).
    from services.base_model_cache import get_cached_model_path
    base_model = get_cached_model_path(model_name, hf_token)

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        base_model,
        token=hf_token if hf_token else None,
    )

    # Load dataset (text + labels). The shared loader honours
    # data['text_column'] / data['label_column'] and otherwise auto-detects
    # from the dataset's object columns — same heuristic the sentiment and
    # text-classification models use.
    yield f"data: {json.dumps({'log': '📂 Loading dataset...'})}\n\n"

    from utils.data_loader import load_text_classification_data
    X_text, y_series = load_text_classification_data(data, user_id)

    texts = X_text.astype(str).tolist()
    labels_raw = y_series.values

    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    labels = le.fit_transform(labels_raw)

    if num_labels is None:
        num_labels = len(le.classes_)

    yield f"data: {json.dumps({'log': f'Detected {num_labels} classes: {list(le.classes_)}'})}\n\n"

    # Train/test split
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=test_size, random_state=42, stratify=labels if num_labels > 1 else None
    )

    yield f"data: {json.dumps({'log': f'Train samples: {len(train_texts)}, Val samples: {len(val_texts)}'})}\n\n"

    # Tokenize
    yield f"data: {json.dumps({'log': '🔤 Tokenizing data...'})}\n\n"

    train_encodings = tokenizer(
        train_texts, truncation=True, padding=True, max_length=max_length
    )
    val_encodings = tokenizer(
        val_texts, truncation=True, padding=True, max_length=max_length
    )

    class TextDataset(Dataset):
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels

        def __getitem__(self, idx):
            item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
            item['labels'] = torch.tensor(self.labels[idx], dtype=torch.long)
            return item

        def __len__(self):
            return len(self.labels)

    train_dataset = TextDataset(train_encodings, train_labels)
    val_dataset = TextDataset(val_encodings, val_labels)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Load model
    yield f"data: {json.dumps({'log': '🏗️ Loading BERT model...'})}\n\n"

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = AutoModelForSequenceClassification.from_pretrained(
        base_model,
        num_labels=num_labels,
        token=hf_token if hf_token else None,
    )
    model.to(device)

    if freeze_base:
        for param in model.base_model.parameters():
            param.requires_grad = False
        yield f"data: {json.dumps({'log': '❄️ BERT base layers frozen.'})}\n\n"

    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    # Training loop
    yield f"data: {json.dumps({'log': '🚀 Starting fine-tuning...'})}\n\n"

    best_val_acc = 0.0
    best_model_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0

        for batch_idx, batch in enumerate(train_loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

            if batch_idx % 10 == 0:
                progress = (batch_idx + 1) / len(train_loader) * 100
                yield f"data: {json.dumps({'log': f'  Batch {batch_idx+1}/{len(train_loader)} ({progress:.0f}%)'})}\n\n"

        avg_train_loss = total_loss / len(train_loader)

        # Validation
        model.eval()
        correct = 0
        total = 0
        val_loss = 0

        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                outputs = model(**batch)
                val_loss += outputs.loss.item()
                preds = torch.argmax(outputs.logits, dim=-1)
                correct += (preds == batch['labels']).sum().item()
                total += batch['labels'].size(0)

        val_acc = correct / total
        avg_val_loss = val_loss / len(val_loader)

        log_msg = (f'Epoch [{epoch}/{epochs}] '
                   f'train_loss: {avg_train_loss:.4f} '
                   f'val_loss: {avg_val_loss:.4f} '
                   f'val_acc: {val_acc:.4f}')
        yield f"data: {json.dumps({'log': log_msg})}\n\n"

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            yield f"data: {json.dumps({'log': '  ✅ New best model saved!'})}\n\n"

    # Restore and save best model
    if best_model_state:
        model.load_state_dict(best_model_state)

    # Save model
    user_dir = get_user_models_dir(user_id) if user_id else os.path.join(tempfile.gettempdir(), 'hf_models')
    ensure_dir(user_dir)
    save_dir = os.path.join(user_dir, f'bert_finetuned_{session_version or "latest"}')
    model.save_pretrained(save_dir)
    tokenizer.save_pretrained(save_dir)

    # Save label encoder
    import pickle
    le_path = os.path.join(save_dir, 'label_encoder.pkl')
    with open(le_path, 'wb') as f:
        pickle.dump(le, f)

    # The SSE wrapper (utils/sse_helpers.run_sse_training) reads the YIELDED
    # chunk that contains both 'status' and 'training_complete' as the results
    # payload — a generator's `return` value is discarded. So everything
    # update_session_results needs (especially trained_model_path) must be in
    # this final chunk, not just returned.
    final_payload = {
        'status': 'training_complete',
        'log': '✅ Fine-tuning complete!',
        'evaluation_metrics': {
            'accuracy': float(best_val_acc),
            'val_loss': float(avg_val_loss),
        },
        'trained_model_path': save_dir,
        'hyperparams_used': params,
        'num_labels': int(num_labels),
        'classes': le.classes_.tolist(),
    }
    yield f"data: {json.dumps(final_payload)}\n\n"
