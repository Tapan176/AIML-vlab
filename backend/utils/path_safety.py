"""
Path-traversal defenses for routes that build filesystem paths from user input.
"""
import os
from werkzeug.utils import secure_filename


ALLOWED_MODEL_EXTENSIONS = {'.pkl', '.h5', '.pt', '.zip'}
ALLOWED_PREDICTION_EXTENSIONS = {'.csv'}

# Caps for ZIP extraction (defense against decompression bombs). Generous for
# image datasets, but stops a few-MB archive from filling the disk. The request
# body is already capped by MAX_CONTENT_LENGTH, which bounds the compressed size.
MAX_EXTRACT_TOTAL_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB uncompressed total
MAX_EXTRACT_FILE_COUNT = 100_000


def safe_extract_zip(zip_ref, dest, max_total_bytes=MAX_EXTRACT_TOTAL_BYTES,
                     max_files=MAX_EXTRACT_FILE_COUNT):
    """Safely extract an open ``zipfile.ZipFile`` into ``dest``.

    Defends against:
      - **zip-slip / path traversal** — members whose resolved path would land
        outside ``dest`` (absolute paths, ``..`` components) are rejected.
      - **decompression bombs** — cumulative declared uncompressed size and file
        count are capped.

    Raises ``ValueError`` on a malicious archive (nothing is extracted).
    """
    dest_real = os.path.realpath(dest)
    total = 0
    count = 0
    for info in zip_ref.infolist():
        target = os.path.realpath(os.path.join(dest_real, info.filename))
        if target != dest_real and not target.startswith(dest_real + os.sep):
            raise ValueError(f"Unsafe path in archive: {info.filename!r}")
        if info.is_dir():
            continue
        count += 1
        if count > max_files:
            raise ValueError("Archive contains too many files")
        total += info.file_size
        if total > max_total_bytes:
            raise ValueError("Archive uncompressed size exceeds limit")
    # All members validated as safe — extractall additionally re-sanitizes names.
    zip_ref.extractall(dest)


def safe_join(root, *parts):
    """Join `parts` onto `root` and verify the resolved path stays inside `root`.

    Any user-supplied path component is run through secure_filename first.
    Raises ValueError if the result would escape `root`.
    """
    root_real = os.path.realpath(root)
    cleaned = [secure_filename(str(p)) for p in parts if p is not None and str(p) != '']
    candidate = os.path.realpath(os.path.join(root_real, *cleaned))
    if candidate != root_real and not candidate.startswith(root_real + os.sep):
        raise ValueError("Path escapes allowed root")
    return candidate


def validate_extension(extension, allowed):
    """Return `extension` (normalized to lowercase with leading dot) if it is in `allowed`.

    Raises ValueError otherwise.
    """
    if not extension:
        raise ValueError("Missing extension")
    ext = extension.lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    if ext not in allowed:
        raise ValueError(f"Extension {ext} not allowed")
    return ext
