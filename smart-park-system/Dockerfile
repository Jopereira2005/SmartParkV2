# ================================
# SmartPark - Multi-stage Dockerfile
# ================================

# ================
# Stage 1: Builder
# ================
FROM python:3.13-slim-bookworm as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements/ /tmp/requirements/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements/base.txt

# =================
# Stage 2: Runtime
# =================
FROM python:3.13-slim-bookworm as runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=smartpark.settings.prod \
    PATH="/opt/venv/bin:$PATH"

# Create app user for security
RUN groupadd -r smartpark && \
    useradd -r -g smartpark -d /app -s /bin/bash smartpark

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app directory
WORKDIR /app

# Copy application code
COPY backend/ /app/
COPY scripts/ /app/scripts/

# Create necessary directories
RUN mkdir -p /app/static /app/media /app/logs && \
    chown -R smartpark:smartpark /app

# Copy entrypoint script
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Switch to non-root user
USER smartpark

# Collect static files
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/core/health/ || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gevent", "smartpark.wsgi:application"]

# ======================
# Stage 3: Development
# ======================
FROM runtime as development

# Switch back to root for development setup
USER root

# Install development dependencies
COPY requirements/dev.txt /tmp/requirements/dev.txt
RUN pip install -r /tmp/requirements/dev.txt

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Switch back to app user
USER smartpark

# Override command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]