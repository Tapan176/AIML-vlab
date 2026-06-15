"""
Base model sourcing for fine-tuning.

Downloads a base model from the HuggingFace Hub ONCE into a shared on-disk cache
(config.HF_CACHE_DIR) and returns a local path. Subsequent fine-tune runs of the
same base model — by any user — reuse that local snapshot instead of
re-downloading. A per-model lock serialises concurrent first-time downloads so
two simultaneous users selecting the same model can't race into a half-written
directory.

The snapshot is a faithful copy of the Hub repo (config + tokenizer/processor +
weights), so `from_pretrained(<path>, ...)` behaves identically to
`from_pretrained(<model_id>, ...)`. The base model is read-only and shared;
TRAINING isolation is handled separately — each run writes its fine-tuned output
to the caller's own per-user directory (see get_user_models_dir).

Resilience: get_cached_model_path NEVER raises. If sourcing fails for any reason
it returns the original model id, so the caller's from_pretrained() simply falls
back to fetching from the Hub — the cache is a best-effort optimisation, never a
hard dependency.

NOTE: this is a local (per-instance) cache. Cross-instance sharing via Google
Drive was considered but deliberately deferred — the HF Hub is already a CDN, and
on a single-worker deployment the local snapshot covers the realistic case. The
hook to add a Drive tier would live in _source_snapshot().
"""
import os
import shutil
import threading
from config import HF_CACHE_DIR, ensure_dir

# Weight formats we don't need for PyTorch fine-tuning — skip to save space/time.
_IGNORE_PATTERNS = ['*.msgpack', '*.h5', '*.onnx', '*.tflite', '*.ot']

# Per-model locks so concurrent first-time downloads of the same model serialise.
_download_locks = {}
_locks_lock = threading.Lock()

ensure_dir(HF_CACHE_DIR)


def _get_lock(model_name):
    with _locks_lock:
        if model_name not in _download_locks:
            _download_locks[model_name] = threading.Lock()
        return _download_locks[model_name]


def _local_dir(model_name):
    return os.path.join(HF_CACHE_DIR, model_name.replace('/', '__'))


def get_cached_model_path(model_name, hf_token=None):
    """Return a local path to `model_name`, sourcing it to the shared cache if
    needed. Falls back to returning `model_name` unchanged if sourcing fails."""
    target = _local_dir(model_name)
    # Fast path: already cached (config.json is the marker of a complete snapshot).
    if os.path.isdir(target) and os.path.exists(os.path.join(target, 'config.json')):
        return os.path.abspath(target)

    lock = _get_lock(model_name)
    with lock:
        # Re-check inside the lock — another thread may have just finished.
        if os.path.isdir(target) and os.path.exists(os.path.join(target, 'config.json')):
            return os.path.abspath(target)
        try:
            return _source_snapshot(model_name, target, hf_token)
        except Exception as e:
            print(f"[base_model_cache] sourcing '{model_name}' failed ({e}); "
                  f"falling back to Hub id at load time")
            # Leave no half-written dir behind to confuse the fast path next time.
            shutil.rmtree(target, ignore_errors=True)
            return model_name


def _source_snapshot(model_name, target, hf_token):
    """Download a faithful repo snapshot into `target` and return its abspath."""
    from huggingface_hub import snapshot_download
    print(f"[base_model_cache] sourcing {model_name} -> {target}")
    path = snapshot_download(
        repo_id=model_name,
        local_dir=target,
        token=hf_token or None,
        ignore_patterns=_IGNORE_PATTERNS,
    )
    return os.path.abspath(path)


def clear_cache(model_name=None):
    """Remove a cached model (or all of them when model_name is None)."""
    if model_name:
        p = _local_dir(model_name)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
    else:
        for d in os.listdir(HF_CACHE_DIR):
            full = os.path.join(HF_CACHE_DIR, d)
            if os.path.isdir(full):
                shutil.rmtree(full, ignore_errors=True)
