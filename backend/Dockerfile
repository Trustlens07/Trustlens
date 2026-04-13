# Use official Python slim image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies required for psycopg2-binary, cryptography, etc.
# These are needed because your requirements include psycopg2-binary and other binary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend code (app/, migrations/, scripts/, etc.)
COPY . .

# Expose the port Cloud Run expects
ENV PORT=8080

# Run the FastAPI app
# main.py is inside the "app" folder, so module path is "app.main"
CMD [CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT]
