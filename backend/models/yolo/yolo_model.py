import os
import json
import time
import yaml
import threading
import queue
from utils.saveTrainedModel import saveTrainedModel
from services.dataset_resolver import resolve_image_dataset_path


def train_yolo(request, validated_params, user_id=None, session_version=None):
    """Real implementation for YOLOv8 object detection model.
    
    Trains a YOLOv8 model on the user's dataset using all user-configured
    hyperparameters. Uses threaded training with queue-based SSE logging
    for real-time epoch updates.
    """
    from ultralytics import YOLO

    data = request.json
    epochs = int(validated_params.get('epochs', 50))
    batch_size = int(validated_params.get('batch_size', 16))
    imgsz = int(validated_params.get('imgsz', 640))
    optimizer = validated_params.get('optimizer', 'auto')
    lr0 = float(validated_params.get('lr0', 0.01))
    lrf = float(validated_params.get('lrf', 0.01))
    momentum = float(validated_params.get('momentum', 0.937))
    weight_decay = float(validated_params.get('weight_decay', 0.0005))
    warmup_epochs = int(validated_params.get('warmup_epochs', 3))
    augment = validated_params.get('augment', True)
    mosaic = float(validated_params.get('mosaic', 1.0))
    
    filename = data.get('filename')
    file_path = data.get('filePath')

    yield f"data: {json.dumps({'log': 'YOLOv8 Object Detection Process initialized.'})}\n\n"

    # --- Resolve dataset path ---
    try:
        dataset_path = resolve_image_dataset_path(user_id, filename=filename, file_path=file_path)
    except FileNotFoundError as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    try:
        # Check for data.yaml
        yaml_path = os.path.join(dataset_path, 'data.yaml')
        if not os.path.exists(yaml_path):
            # Attempt to auto-detect directory structure and create data.yaml
            yaml_content = _auto_detect_yolo_config(dataset_path)
            with open(yaml_path, 'w') as f:
                yaml.dump(yaml_content, f)
            yield f"data: {json.dumps({'log': f'Auto-generated data.yaml with {len(yaml_content.get(\"names\", {}))} classes.'})}\n\n"
        else:
            with open(yaml_path, 'r') as f:
                yaml_content = yaml.safe_load(f)
            # Fix path to be absolute
            yaml_content['path'] = os.path.abspath(dataset_path)
            with open(yaml_path, 'w') as f:
                yaml.dump(yaml_content, f)
            yield f"data: {json.dumps({'log': f'Found data.yaml with {len(yaml_content.get('names', {}))} class(es).'})}\n\n"

        yield f"data: {json.dumps({'log': 'Loading pre-trained YOLOv8n weights...'})}\n\n"
        model = YOLO('yolov8n.pt')

        yield f"data: {json.dumps({'log': f'Starting YOLOv8 Training for {epochs} epochs (batch={batch_size}, imgsz={imgsz}, optimizer={optimizer})...'})}\n\n"

        # Use a queue for real-time progress from the training thread
        progress_queue = queue.Queue()
        training_result = {'error': None, 'results': None}

        def _train_thread():
            try:
                # Add YOLO callbacks to capture per-epoch metrics
                def on_train_epoch_end(trainer):
                    epoch = trainer.epoch + 1
                    metrics = trainer.metrics or {}
                    box_loss = metrics.get('train/box_loss', 0)
                    cls_loss = metrics.get('train/cls_loss', 0)
                    dfl_loss = metrics.get('train/dfl_loss', 0)
                    total_loss = box_loss + cls_loss + dfl_loss
                    map50 = metrics.get('metrics/mAP50(B)', 0)
                    progress_queue.put({
                        'type': 'epoch',
                        'epoch': epoch,
                        'total_loss': total_loss,
                        'box_loss': box_loss,
                        'map50': map50
                    })

                model.add_callback('on_fit_epoch_end', on_train_epoch_end)
                
                results = model.train(
                    data=yaml_path,
                    epochs=epochs,
                    imgsz=imgsz,
                    batch=batch_size,
                    optimizer=optimizer,
                    lr0=lr0,
                    lrf=lrf,
                    momentum=momentum,
                    weight_decay=weight_decay,
                    warmup_epochs=warmup_epochs,
                    augment=augment,
                    mosaic=mosaic,
                    verbose=False
                )
                training_result['results'] = results
            except Exception as e:
                training_result['error'] = str(e)
            finally:
                progress_queue.put({'type': 'done'})

        # Start training in a separate thread
        train_thread = threading.Thread(target=_train_thread, daemon=True)
        train_thread.start()

        # Stream progress events
        while True:
            try:
                msg = progress_queue.get(timeout=2)
            except queue.Empty:
                # Send a keepalive / heartbeat
                if not train_thread.is_alive():
                    break
                continue

            if msg['type'] == 'done':
                break
            elif msg['type'] == 'epoch':
                log_msg = (
                    f"Epoch [{msg['epoch']}/{epochs}] "
                    f"Box Loss: {msg['box_loss']:.4f} - "
                    f"Total Loss: {msg['total_loss']:.4f} - "
                    f"mAP@50: {msg['map50']:.4f}"
                )
                yield f"data: {json.dumps({'log': log_msg})}\n\n"

        # Wait for thread to finish
        train_thread.join(timeout=10)

        if training_result['error']:
            yield f"data: {json.dumps({'error': f'YOLO Training failed: {training_result[\"error\"]}'})}\n\n"
            return

        # Save model
        best_model_path = None
        try:
            best_model_path = os.path.join(model.trainer.save_dir, 'weights', 'best.pt')
        except:
            pass
        
        final_save_path = saveTrainedModel(model, "yolo", "Ultralytics", user_id=user_id, version=session_version)

        # Extract final metrics
        final_metrics = {}
        try:
            results = training_result['results']
            if results:
                final_metrics['map50'] = float(results.results_dict.get('metrics/mAP50(B)', 0))
                final_metrics['map50_95'] = float(results.results_dict.get('metrics/mAP50-95(B)', 0))
        except:
            pass

        yield f"data: {json.dumps({'log': f'Training Complete! Model saved.'})}\n\n"
        yield f"data: {json.dumps({'status': 'training_complete', 'trained_model_path': final_save_path, 'epochs_trained': epochs, **final_metrics})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': f'YOLO Training failed: {str(e)}'})}\n\n"


def _auto_detect_yolo_config(dataset_path):
    """Auto-detect YOLO directory structure and generate data.yaml config."""
    config = {
        'path': os.path.abspath(dataset_path),
        'names': {}
    }
    
    # Check for standard YOLO directory structures
    # Structure 1: images/train, images/val, labels/train, labels/val
    if os.path.isdir(os.path.join(dataset_path, 'images', 'train')):
        config['train'] = 'images/train'
        config['val'] = 'images/val' if os.path.isdir(os.path.join(dataset_path, 'images', 'val')) else 'images/train'
    # Structure 2: train/images, val/images
    elif os.path.isdir(os.path.join(dataset_path, 'train', 'images')):
        config['train'] = 'train/images'
        config['val'] = 'val/images' if os.path.isdir(os.path.join(dataset_path, 'val', 'images')) else 'train/images'
    # Structure 3: train, val (flat)
    elif os.path.isdir(os.path.join(dataset_path, 'train')):
        config['train'] = 'train'
        config['val'] = 'val' if os.path.isdir(os.path.join(dataset_path, 'val')) else 'train'
    else:
        config['train'] = '.'
        config['val'] = '.'
    
    # Try to detect class names from label files
    labels_dir = None
    for candidate in ['labels/train', 'train/labels', 'labels']:
        p = os.path.join(dataset_path, candidate)
        if os.path.isdir(p):
            labels_dir = p
            break
    
    if labels_dir:
        class_ids = set()
        for label_file in os.listdir(labels_dir)[:100]:  # Sample first 100
            if label_file.endswith('.txt'):
                try:
                    with open(os.path.join(labels_dir, label_file), 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if parts:
                                class_ids.add(int(parts[0]))
                except:
                    pass
        if class_ids:
            config['names'] = {i: f'class_{i}' for i in sorted(class_ids)}
    
    if not config['names']:
        config['names'] = {0: 'object'}
    
    return config
