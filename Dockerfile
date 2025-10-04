# Multi-stage Dockerfile for Taiwan ECMO CDSS
# Optimized for production deployment

# Stage 1: Base Python Image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root for security)
RUN useradd -m -u 1000 -s /bin/bash ecmo-app

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Stage 2: Dashboard Application
FROM base as dashboard

# Copy application code
COPY --chown=ecmo-app:ecmo-app econ /app/econ
COPY --chown=ecmo-app:ecmo-app data_dictionary.yaml /app/

# Create required directories
RUN mkdir -p /app/data /app/models /app/exports && \
    chown -R ecmo-app:ecmo-app /app

# Switch to non-root user
USER ecmo-app

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run dashboard
CMD ["streamlit", "run", "/app/econ/dashboard.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]

# Stage 3: SMART on FHIR Application
FROM base as smart-app

# Install Gunicorn for production
RUN pip install gunicorn gevent

# Copy application code
COPY --chown=ecmo-app:ecmo-app smart-on-fhir /app/smart-on-fhir
COPY --chown=ecmo-app:ecmo-app nirs /app/nirs
COPY --chown=ecmo-app:ecmo-app data_dictionary.yaml /app/

# Create required directories
RUN mkdir -p /app/logs /app/models && \
    chown -R ecmo-app:ecmo-app /app

# Switch to non-root user
USER ecmo-app

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run SMART app with Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--worker-class", "gevent", \
     "--timeout", "120", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "--chdir", "/app/smart-on-fhir", \
     "app:app"]

# Stage 4: Model Training (for CI/CD)
FROM base as trainer

# Copy all application code
COPY --chown=ecmo-app:ecmo-app . /app

# Create directories
RUN mkdir -p /app/data /app/models /app/logs && \
    chown -R ecmo-app:ecmo-app /app

# Switch to non-root user
USER ecmo-app

# Default command: run training pipeline
CMD ["python", "/app/nirs/train_models.py", \
     "--features-csv", "/app/data/ecmo_features.csv", \
     "--output-dir", "/app/models/ecmo_risk"]

# Stage 5: ETL Pipeline
FROM base as etl

# Install additional ETL dependencies
RUN pip install sqlalchemy psycopg2-binary pyyaml

# Copy ETL code
COPY --chown=ecmo-app:ecmo-app etl /app/etl
COPY --chown=ecmo-app:ecmo-app sql /app/sql
COPY --chown=ecmo-app:ecmo-app data_dictionary.yaml /app/

# Create directories
RUN mkdir -p /app/data /app/logs && \
    chown -R ecmo-app:ecmo-app /app

# Switch to non-root user
USER ecmo-app

# Default command: run ETL
CMD ["python", "/app/etl/elso_mapper.py"]

# Stage 6: Development Environment
FROM base as development

# Install development tools
RUN pip install \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    ipython \
    jupyter

# Copy all code
COPY --chown=ecmo-app:ecmo-app . /app

# Create directories
RUN mkdir -p /app/data /app/models /app/logs && \
    chown -R ecmo-app:ecmo-app /app

# Switch to non-root user
USER ecmo-app

# Default: start bash
CMD ["/bin/bash"]
