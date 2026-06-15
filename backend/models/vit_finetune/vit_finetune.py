"""
HuggingFace Vision Transformer (ViT) Fine-Tuning module.
Fine-tunes a pre-trained ViT model on user-provided image classification data.
Uses SSE streaming for live epoch-by-epoch progress.
"""
import os
import json
import tempfile
import numpy as np
from config import HF_TOKEN, get_user_models_dir, ensure_dir


def train_vit_finetune(request, validated_params=None, user_id=None, session_version=None):
    """
    Fine-tune Vision Transformer for image classification.
    
    Expected request JSON:
        - filename: ZIP dataset filename with class-labeled subdirectories
        - filePath: optional direct path to extracted dataset
    
    Hyperparameters (from validated_params):
        - model_name: huggingface model ID (default: 'google/vit-base-patch16-224')
        - epochs: number of training epochs (default: 3)
        - batch_size: training batch size (default: 16)
        - learning_rate: peak learning rate (default: 2e-5)
        - weight_decay: weight decay for AdamW (default: 0.01)
        - test_size: validation split fraction (default: 0.2)
        - freeze_base: whether to freeze ViT encoder (default: False)
    """
    import torch
    from torch.utils.data import DataLoader
    from torchvision import transforms
    from torchvision.datasets import ImageFolder
    from torch.optim import AdamW  # transformers.AdamW was removed in v4.x
    from transformers import (
        AutoImageProcessor,
        AutoModelForImageClassification,
        get_linear_schedule_with_warmup,
    )

    data = request.json if hasattr(request, 'json') else request
    params = validated_params or {}

    model_name = params.get('model_name', 'google/vit-base-patch16-224')
    epochs = int(params.get('epochs', 3))
    batch_size = int(params.get('batch_size', 16))
    learning_rate = float(params.get('learning_rate', 2e-5))
    weight_decay = float(params.get('weight_decay', 0.01))
    test_size = float(params.get('test_size', 0.2))
    freeze_base = bool(params.get('freeze_base', False))

    hf_token = HF_TOKEN

    yield f"data: {json.dumps({'log': '🔧 Loading ViT model and image processor...'})}\n\n"

    # Load image processor
    processor = AutoImageProcessor.from_pretrained(
        model_name,
        token=hf_token if hf_token else None,
    )

    # Resolve image dataset
    yield f"data: {json.dumps({'log': '📂 Resolving dataset...'})}\n\n"

    from services.dataset_resolver import resolve_image_dataset_path
    dataset_path = resolve_image_dataset_path(
        user_id,
        filename=data.get('filename'),
        file_path=data.get('filePath'),
    )

    yield f"data: {json.dumps({'log': f'Dataset resolved to: {dataset_path}'})}\n\n"

    # Prepare transforms
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=processor.image_mean, std=processor.image_std),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=processor.image_mean, std=processor.image_std),
    ])

    # Load dataset
    full_dataset = ImageFolder(dataset_path, transform=train_transform)

    yield f"data: {json.dumps({'log': f'Found {len(full_dataset)} images across {len(full_dataset.classes)} classes: {full_dataset.classes}'})}\n\n"

    num_labels = len(full_dataset.classes)

    # Split
    from sklearn.model_selection import train_test_split
    indices = list(range(len(full_dataset)))
    train_idx, val_idx = train_test_split(
        indices, test_size=test_size, random_state=42, stratify=full_dataset.targets
    )

    from torch.utils.data import Subset
    train_dataset = Subset(full_dataset, train_idx)
    val_dataset = Subset(full_dataset, val_idx)
    val_dataset.dataset.transform = val_transform

    yield f"data: {json.dumps({'log': f'Train: {len(train_dataset)} images, Val: {len(val_dataset)} images'})}\n\n"

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # Load model
    yield f"data: {json.dumps({'log': '🏗️ Loading ViT model...'})}\n\n"

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = AutoModelForImageClassification.from_pretrained(
        model_name,
        num_labels=num_labels,
        ignore_mismatched_sizes=True,
        token=hf_token if hf_token else None,
    )
    model.to(device)

    if freeze_base:
        for param in model.vit.parameters():
            param.requires_grad = False
        yield f"data: {json.dumps({'log': '❄️ ViT encoder frozen.'})}\n\n"

    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=total_steps)

    # Training loop
    yield f"data: {json.dumps({'log': '🚀 Starting fine-tuning...'})}\n\n"

    best_val_acc = 0.0
    best_model_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0

        for batch_idx, batch in enumerate(train_loader):
            pixel_values = batch[0].to(device)
            labels = batch[1].to(device)

            optimizer.zero_grad()
            outputs = model(pixel_values=pixel_values, labels=labels)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

            if batch_idx % 5 == 0:
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
                pixel_values = batch[0].to(device)
                labels = batch[1].to(device)
                outputs = model(pixel_values=pixel_values, labels=labels)
                val_loss += outputs.loss.item()
                preds = torch.argmax(outputs.logits, dim=-1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

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

    if best_model_state:
        model.load_state_dict(best_model_state)

    # Save model
    user_dir = get_user_models_dir(user_id) if user_id else os.path.join(tempfile.gettempdir(), 'hf_models')
    ensure_dir(user_dir)
    save_dir = os.path.join(user_dir, f'vit_finetuned_{session_version or "latest"}')
    model.save_pretrained(save_dir)
    processor.save_pretrained(save_dir)

    # The SSE wrapper reads the YIELDED chunk containing 'status' +
    # 'training_complete' as the results payload; a generator's return is
    # discarded. trained_model_path MUST be in this chunk for the Drive
    # upload + download to work.
    final_payload = {
        'status': 'training_complete',
        'log': '✅ Fine-tuning complete!',
        'evaluation_metrics': {
            'accuracy': float(best_val_acc),
            'val_loss': float(avg_val_loss),
        },
        'trained_model_path': save_dir,
        'hyperparams_used': params,
        'num_classes': int(num_labels),
        'classes': full_dataset.classes,
    }
    yield f"data: {json.dumps(final_payload)}\n\n"
