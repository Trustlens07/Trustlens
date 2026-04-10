FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (includes scipy/scikit-learn requirements)
RUN apt-get update && apt-get install -y \
    gcc \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ml_service.py .

# Expose port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "ml_service:app", "--host", "0.0.0.0", "--port", "7860"]