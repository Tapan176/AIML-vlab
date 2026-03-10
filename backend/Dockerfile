# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install minimal system dependencies (prefer wheels over compiling from source)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Common runtime libs for opencv/ultralytics and some ML wheels
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
ARG REQUIREMENTS_FILE=requirements.txt
COPY ${REQUIREMENTS_FILE} ./requirements.txt
RUN pip install --upgrade pip && pip install --prefer-binary -r requirements.txt

# Copy project files
COPY . .

# Create runtime directories and a non-root user for safer runtime
RUN mkdir -p static/uploads trainedModels static/images predictions \
    && useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port (Railway assigns PORT dynamically)
EXPOSE 5050

# Use 2 workers for free-tier hosts (~512 MB RAM)
# Bind to 0.0.0.0 and respect $PORT if set (Railway/Render), fallback to 5050
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5050} --workers ${WEB_CONCURRENCY:-2} --threads ${GUNICORN_THREADS:-1} --timeout ${GUNICORN_TIMEOUT:-300} --access-logfile - --error-logfile -"]
