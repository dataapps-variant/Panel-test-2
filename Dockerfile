FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV BOKEH_ALLOW_WS_ORIGIN=*
ENV PYTHONPATH=/app/app

# Run Panel server - simple command
CMD ["panel", "serve", "app/app.py", "--port", "8080", "--address", "0.0.0.0", "--allow-websocket-origin", "*"]
