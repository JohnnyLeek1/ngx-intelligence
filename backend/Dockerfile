# Multi-stage build for optimized production image
FROM python:3.11-slim as base

# Set environment variables
# Prevents Python from writing pyc files to disc (equivalent to python -B)
ENV PYTHONDONTWRITEBYTECODE=1 \
    # Prevents Python from buffering stdout and stderr (equivalent to python -u)
    PYTHONUNBUFFERED=1 \
    # Pip settings
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for building Python packages with C extensions
    gcc \
    # Required for some Python packages
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

# Create directories for volumes with proper permissions
RUN mkdir -p /app/data /app/logs /app/config \
    && chown -R appuser:appuser /app/data /app/logs /app/config

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)" || exit 1

# Run the application
# Using --host 0.0.0.0 to accept connections from outside the container
# --workers 1 for development, should be adjusted based on CPU cores in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
