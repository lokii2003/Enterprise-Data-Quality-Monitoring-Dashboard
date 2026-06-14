# ============================================================
# Dockerfile
# Phase 11 — Containerize the Data Quality Pipeline
#
# Build:  docker build -t data-quality-pipeline .
# Run:    docker compose up   (see docker-compose.yml)
# ============================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for mysqlclient)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create log directory
RUN mkdir -p logs reports

# Default command: run the full pipeline
CMD ["python", "scripts/data_quality_checks.py"]
