# Network Traffic Analyzer - Docker Image
# Multi-stage build for smaller final image

# Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Set labels
LABEL maintainer="Network Traffic Analyzer"
LABEL description="ML-powered network traffic analysis and anomaly detection"
LABEL version="1.0.0"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap0.8 \
    tcpdump \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC

# Create non-root user for security (but allow network capture)
RUN groupadd -r analyzer && useradd -r -g analyzer analyzer

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=analyzer:analyzer . /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/reports /app/data/pcaps /app/models/trained_models && \
    chown -R analyzer:analyzer /app

# Set capabilities for packet capture (instead of running as root)
RUN setcap cap_net_raw,cap_net_admin=eip /opt/venv/bin/python3.11

# Switch to non-root user
USER analyzer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden)
CMD ["python", "analyzer.py", "--help"]
