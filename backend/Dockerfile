# =============================================================================
#  Dockerfile — multi-stage build
#
#  STAGE 1 (builder) — installs all Python deps, compiles C extensions,
#                       pulls CPU wheels. Nothing from this stage bleeds
#                       into the final image except site-packages.
#
#  STAGE 2 (runtime) — fresh slim base, copies only the installed packages
#                       and app code. No pip, no build tools, no cache.
#
#  Result: final image is ~30-40% smaller than a single-stage equivalent.
# =============================================================================


# -----------------------------------------------------------------------------
# Stage 1 — builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Build-time only — no need to carry these env vars into runtime
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Install build-time system deps (compilers for any packages that need to
# build from source — e.g. some scipy/cryptography versions).
# These do NOT get copied to the runtime stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into an isolated prefix so we can
# copy just that directory into the runtime stage cleanly.
ARG REQUIREMENTS_FILE=requirements.txt
COPY ${REQUIREMENTS_FILE} ./requirements.txt

RUN pip install --upgrade pip \
    && pip install \
        --prefer-binary \
        --prefix=/install \
        -r requirements.txt


# -----------------------------------------------------------------------------
# Stage 2 — runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Runtime environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    # Tell Python where the packages installed by the builder live
    PYTHONPATH=/usr/local/lib/python3.11/site-packages

WORKDIR /app

# Runtime system libraries only — no compilers, no build tools.
# libgl1 + libglib2.0-0  →  opencv / ultralytics
# libgomp1               →  numpy / scikit-learn OpenMP threading
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder into the runtime Python prefix.
# /install mirrors the layout of /usr/local so a direct copy works cleanly.
COPY --from=builder /install/lib       /usr/local/lib
COPY --from=builder /install/bin       /usr/local/bin

# Copy application source
COPY . .

# Create directories the app writes to at runtime + harden with a non-root user
RUN mkdir -p static/uploads trainedModels static/images predictions \
    && useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

# Railway / Render inject $PORT at runtime; fallback to 5050 locally.
EXPOSE 5050

# Tuning notes:
#   WEB_CONCURRENCY  — number of gunicorn worker processes (default 2 for free tier ~512 MB RAM)
#   GUNICORN_THREADS — threads per worker (default 1; raise to 2-4 for I/O-heavy routes)
#   GUNICORN_TIMEOUT — seconds before a worker is killed (default 300 for long training jobs)
CMD ["sh", "-c", \
     "gunicorn app:app \
      --bind 0.0.0.0:${PORT:-5050} \
      --workers ${WEB_CONCURRENCY:-2} \
      --threads ${GUNICORN_THREADS:-1} \
      --timeout ${GUNICORN_TIMEOUT:-300} \
      --access-logfile - \
      --error-logfile -"]
