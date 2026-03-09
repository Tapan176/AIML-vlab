# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
# Ensure gunicorn and gridfs are installed (Flask-Limiter will be added)
RUN pip install gunicorn pymongo gridfs Flask-Limiter

# Copy project files
COPY . .

# Expose port
EXPOSE 5050

# Run the Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "4", "app:app"]
