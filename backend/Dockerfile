# Use official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (required for psycopg2-binary, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements from ROOT (build context is branch root)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code (inside 'backend/' folder of the context)
COPY backend/ .

# Cloud Run uses PORT=8080 by default
ENV PORT=8000

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run FastAPI app
# Use uvicorn to listen on 0.0.0.0 and the PORT env variable
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --timeout-keep-alive 65
