import os
import json
import time
import tempfile
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.optimizers import SGD, Adam, RMSprop, Adagrad, Adadelta
from utils.saveTrainedModel import saveTrainedModel


def _get_optimizer(validated_params):
    """Build optimizer from validated hyperparameters."""
    opt_type = validated_params.get('optimizer', 'adam')
    lr = float(validated_params.get('learning_rate', 0.001))
    
    if opt_type == 'adam':
        return Adam(learning_rate=lr)
    elif opt_type == 'sgd':
        return SGD(learning_rate=lr)
    elif opt_type == 'rmsprop':
        return RMSprop(learning_rate=lr)
    elif opt_type == 'adagrad':
        return Adagrad(learning_rate=lr)
    elif opt_type == 'adadelta':
        return Adadelta(learning_rate=lr)
    else:
        return Adam(learning_rate=lr)


def train_lstm(request, validated_params, hidden_layer_array=None, class_mode='categorical', user_id=None, session_version=None):
    """Real implementation for LSTM deep learning model.
    
    Builds an LSTM model based on user-configured architecture and
    hyperparameters, trains on the user's CSV dataset, and streams
    epoch progress via SSE.
    """
    data = request.json
    epochs = int(validated_params.get('epochs', 100))
    batch_size = int(validated_params.get('batch_size', 32))
    loss_type = validated_params.get('loss', 'mse')
    validation_split = float(validated_params.get('validation_split', 0.15))
    sequence_length = int(validated_params.get('sequence_length', 20))
    
    filename = data.get('filename')
    file_path = data.get('filePath')

    yield f"data: {json.dumps({'log': 'LSTM Recurrent Neural Network Process initialized.'})}\n\n"

    # --- Load dataset ---
    if not filename and not file_path:
        yield f"data: {json.dumps({'error': 'No dataset provided. Please upload a CSV dataset or select one from the library.'})}\n\n"
        return

    try:
        from services.dataset_service import get_dataset_df
        
        # Use filename if available (works with Drive + local fallback)
        lookup_name = filename or (os.path.basename(file_path) if file_path else None)
        
        if not lookup_name:
            yield f"data: {json.dumps({'error': 'Could not determine dataset filename.'})}\n\n"
            return
        
        df = get_dataset_df(user_id, lookup_name)
        yield f"data: {json.dumps({'log': f'Loaded dataset \"{lookup_name}\" with {len(df)} rows and {len(df.columns)} columns.'})}\n\n"
    except FileNotFoundError as e:
        yield f"data: {json.dumps({'error': f'Dataset not found: {str(e)}'})}\n\n"
        return
    except Exception as e:
        yield f"data: {json.dumps({'error': f'Failed to load dataset: {str(e)}'})}\n\n"
        return

    try:
        # --- Prepare sequences ---
        # Use all columns except the last as features, last column as target
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values

        # Handle non-numeric columns
        try:
            X = X.astype(float)
        except ValueError:
            # Try to encode categorical features
            from sklearn.preprocessing import LabelEncoder
            for col_idx in range(X.shape[1]):
                try:
                    X[:, col_idx] = X[:, col_idx].astype(float)
                except ValueError:
                    le = LabelEncoder()
                    X[:, col_idx] = le.fit_transform(X[:, col_idx].astype(str))
            X = X.astype(float)

        # Encode target if categorical
        is_regression = (class_mode == 'linear')
        if not is_regression:
            try:
                y = y.astype(float)
            except ValueError:
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y = le.fit_transform(y.astype(str)).astype(float)

        y = y.astype(float)

        # Scale features
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        # Create sequences
        window_size = min(sequence_length, len(X_scaled) - 1)
        if window_size < 1:
            yield f"data: {json.dumps({'error': f'Dataset too small ({len(X_scaled)} rows) for sequence length {sequence_length}.'})}\n\n"
            return

        X_seq = []
        y_seq = []
        for i in range(len(X_scaled) - window_size):
            X_seq.append(X_scaled[i:i + window_size])
            y_seq.append(y[i + window_size])

        X_seq, y_seq = np.array(X_seq), np.array(y_seq)

        yield f"data: {json.dumps({'log': f'Created {len(X_seq)} sequences of length {window_size} with {X.shape[1]} features.'})}\n\n"

        # --- Build model from user-configured layers ---
        model = Sequential()

        if hidden_layer_array and len(hidden_layer_array) > 0:
            lstm_layers_added = 0
            total_lstm_layers = sum(1 for l in hidden_layer_array if l.get('type', 'lstm') == 'lstm')
            
            for i, layer_config in enumerate(hidden_layer_array):
                layer_type = layer_config.get('type', 'lstm')
                units = int(layer_config.get('units', 64))
                dropout_rate = float(layer_config.get('dropout', 0))

                if layer_type == 'lstm':
                    lstm_layers_added += 1
                    # return_sequences must be True for stacked LSTMs (except last LSTM)
                    return_sequences = layer_config.get('return_sequences', lstm_layers_added < total_lstm_layers)
                    
                    if i == 0:
                        model.add(LSTM(units, return_sequences=return_sequences, input_shape=(window_size, X.shape[1])))
                    else:
                        model.add(LSTM(units, return_sequences=return_sequences))
                    
                    if dropout_rate > 0:
                        model.add(Dropout(dropout_rate))
                    
                    yield f"data: {json.dumps({'log': f'  Added LSTM({units}, return_sequences={return_sequences}) + Dropout({dropout_rate})'})}\n\n"
                    
                elif layer_type == 'dense':
                    activation = layer_config.get('activation', 'relu')
                    model.add(Dense(units, activation=activation))
                    if dropout_rate > 0:
                        model.add(Dropout(dropout_rate))
                    yield f"data: {json.dumps({'log': f'  Added Dense({units}, activation={activation}) + Dropout({dropout_rate})'})}\n\n"
        else:
            # Default architecture
            model.add(LSTM(64, input_shape=(window_size, X.shape[1]), return_sequences=True))
            model.add(Dropout(0.2))
            model.add(LSTM(32, return_sequences=False))
            model.add(Dropout(0.2))
            yield f"data: {json.dumps({'log': '  Using default LSTM architecture: LSTM(64) → LSTM(32)'})}\n\n"

        # Output layer
        if is_regression:
            model.add(Dense(1, activation='linear'))
            compile_loss = loss_type if loss_type in ['mse', 'mae', 'huber_loss'] else 'mse'
            compile_metrics = ['mae']
            yield f"data: {json.dumps({'log': f'Output: Dense(1, linear) — Regression mode'})}\n\n"
        else:
            num_classes = len(np.unique(y_seq))
            if num_classes > 2:
                model.add(Dense(num_classes, activation='softmax'))
                compile_loss = 'sparse_categorical_crossentropy'
                compile_metrics = ['accuracy']
                yield f"data: {json.dumps({'log': f'Output: Dense({num_classes}, softmax) — {num_classes}-class classification'})}\n\n"
            else:
                model.add(Dense(1, activation='sigmoid'))
                compile_loss = 'binary_crossentropy'
                compile_metrics = ['accuracy']
                yield f"data: {json.dumps({'log': f'Output: Dense(1, sigmoid) — Binary classification'})}\n\n"

        # Compile
        optimizer = _get_optimizer(validated_params)
        model.compile(optimizer=optimizer, loss=compile_loss, metrics=compile_metrics)

        yield f"data: {json.dumps({'log': f'Model compiled. Optimizer: {validated_params.get("optimizer", "adam")}, Loss: {compile_loss}, LR: {validated_params.get("learning_rate", 0.001)}'})}\n\n"
        yield f"data: {json.dumps({'log': f'Starting Sequential Training for {epochs} epochs (batch_size={batch_size}, val_split={validation_split})...'})}\n\n"

        # --- Training loop ---
        best_val_loss = float('inf')
        patience = 5
        patience_counter = 0
        last_metrics = {}
        stopped_epoch = epochs

        for epoch in range(1, epochs + 1):
            try:
                history = model.fit(
                    X_seq, y_seq,
                    epochs=1,
                    batch_size=batch_size,
                    verbose=0,
                    validation_split=validation_split
                )

                train_loss = history.history['loss'][0]
                val_loss = history.history.get('val_loss', [train_loss])[0]
                
                log_parts = [f'Epoch [{epoch}/{epochs}] loss: {train_loss:.4f} - val_loss: {val_loss:.4f}']
                last_metrics = {'loss': train_loss, 'val_loss': val_loss}
                
                if 'accuracy' in history.history:
                    train_acc = history.history['accuracy'][0]
                    val_acc = history.history.get('val_accuracy', [train_acc])[0]
                    log_parts.append(f'accuracy: {train_acc:.4f} - val_accuracy: {val_acc:.4f}')
                    last_metrics['accuracy'] = val_acc
                
                if 'mae' in history.history:
                    train_mae = history.history['mae'][0]
                    val_mae = history.history.get('val_mae', [train_mae])[0]
                    log_parts.append(f'mae: {train_mae:.4f} - val_mae: {val_mae:.4f}')
                    last_metrics['rmse'] = float(np.sqrt(val_loss))  # Approximate RMSE from MSE loss

                yield f"data: {json.dumps({'log': ' - '.join(log_parts)})}\n\n"

                # Early stopping with cross-platform temp directory
                temp_weights_path = os.path.join(tempfile.gettempdir(), f'best_lstm_weights_{user_id or "guest"}.h5')
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    try:
                        model.save_weights(temp_weights_path)
                    except Exception:
                        pass
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        yield f"data: {json.dumps({'log': f'Early stopping triggered at epoch {epoch}. Restoring best weights...'})}\n\n"
                        try:
                            if os.path.exists(temp_weights_path):
                                model.load_weights(temp_weights_path)
                        except:
                            pass
                        stopped_epoch = epoch
                        break

                time.sleep(0.05)
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Training aborted during epoch {epoch}: {str(e)}'})}\n\n"
                return

        yield f"data: {json.dumps({'log': 'Training Complete. Saving model artifacts...'})}\n\n"

        save_path = saveTrainedModel(model, "lstm", "Keras", user_id=user_id, version=session_version)

        completion_data = {
            'status': 'training_complete',
            'trained_model_path': save_path,
            'epochs_trained': stopped_epoch,
            'loss': float(last_metrics.get('val_loss', last_metrics.get('loss', 0))),
        }
        if 'accuracy' in last_metrics:
            completion_data['accuracy'] = float(last_metrics['accuracy'])
        if 'rmse' in last_metrics:
            completion_data['rmse'] = float(last_metrics['rmse'])

        yield f"data: {json.dumps(completion_data)}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': f'LSTM Training failed: {str(e)}'})}\n\n"
